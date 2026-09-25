import math
import random
import unittest

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

import rigs
from guitar_rig.core import bake, bonemap

MODES = ('QUATERNION', 'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX', 'AXIS_ANGLE')


def random_quaternion(rng):
    return Quaternion([rng.gauss(0.0, 1.0) for _ in range(4)]).normalized()


def randomize_pose(obj, rng, unit, scale=True):
    """Random rotation modes and rotations on every bone, locations on unconnected bones, and scales."""
    for pbone in obj.pose.bones:
        pbone.rotation_mode = rng.choice(MODES)
        loc = Vector() if pbone.bone.use_connect else Vector([rng.uniform(-1.0, 1.0) for _ in range(3)]) * 0.03 * unit
        size = Vector([rng.uniform(0.8, 1.25) for _ in range(3)]) if scale else Vector((1.0, 1.0, 1.0))
        pbone.matrix_basis = Matrix.LocRotScale(loc, random_quaternion(rng), size)
    bpy.context.view_layer.update()


def assert_matrices(test, actual, expected, unit, msg=""):
    actual, expected = np.asarray(actual), np.asarray(expected)
    np.testing.assert_allclose(actual[..., :3, :3], expected[..., :3, :3], rtol=0, atol=2e-5, err_msg=msg)
    np.testing.assert_allclose(actual[..., :3, 3], expected[..., :3, 3], rtol=0, atol=2e-4 * unit, err_msg=msg)


def rotate_about(matrix, pivot, rotation):
    to_pivot = Matrix.Translation(pivot)
    return to_pivot @ rotation.to_matrix().to_4x4() @ to_pivot.inverted() @ matrix


class RoundTripTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_every_bone_of_every_rig(self):
        """pose -> basis recovers matrix_basis for random poses, rolled bones and any inheritance option."""
        rng = random.Random(7)
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                unit = rigs.RIG_UNITS[build]
                randomize_pose(obj, rng, unit)
                basis = bake.pose_to_basis(obj.data.bones, rigs.pose_arrays(obj))
                self.assertEqual(len(basis), len(obj.pose.bones))
                for pbone in obj.pose.bones:
                    assert_matrices(self, basis[pbone.name][0], np.array(pbone.matrix_basis), unit, pbone.name)

    def test_vectorised_matches_blender(self):
        """The vectorised default-inheritance path agrees with Bone.convert_local_to_pose both ways."""
        rng = random.Random(3)
        obj = rigs.mixamo()
        randomize_pose(obj, rng, 100.0)
        poses = rigs.pose_arrays(obj)
        for pbone in obj.pose.bones:
            bone = pbone.bone
            self.assertTrue(bake.has_default_inheritance(bone))
            parent = bake.as_matrices(poses[bone.parent.name]) if bone.parent else None
            pose = bake.as_matrices(poses[bone.name])
            fast = bake.bone_pose_to_basis(bone, pose, parent)
            assert_matrices(self, fast, bake._convert(bone, pose, parent, invert=True), 100.0, bone.name)
            assert_matrices(self, bake.bone_basis_to_pose(bone, fast, parent), pose, 100.0, bone.name)

    def test_many_frames(self):
        rng = random.Random(5)
        obj = rigs.rigify()
        frames = []
        for _ in range(12):
            randomize_pose(obj, rng, 1.0)
            frames.append((rigs.pose_arrays(obj), {pb.name: np.array(pb.matrix_basis) for pb in obj.pose.bones}))
        stacked = {name: np.concatenate([poses[name] for poses, _ in frames]) for name in frames[0][0]}
        basis = bake.pose_to_basis(obj.data.bones, stacked)
        for i, (_, expected) in enumerate(frames):
            for name, value in expected.items():
                assert_matrices(self, basis[name][i], value, 1.0, f"{name} frame {i}")

    def test_missing_parent_pose(self):
        obj = rigs.vroid()
        poses = rigs.pose_arrays(obj, ["J_Bip_L_LowerArm"])
        with self.assertRaises(KeyError):
            bake.pose_to_basis(obj.data.bones, poses)

    def test_world_to_armature(self):
        rng = np.random.default_rng(3)
        n = 6
        arm = np.tile(np.eye(4), (n, 1, 1))
        arm[:, :3, :] = rng.normal(size=(n, 3, 4))
        obj = np.array([np.array(Matrix.LocRotScale(Vector(rng.normal(size=3)),
                                                    Quaternion(rng.normal(size=4)).normalized(),
                                                    Vector([rng.uniform(0.01, 2.0)] * 3))) for _ in range(n)])
        np.testing.assert_allclose(bake.world_to_armature(obj @ arm, obj), arm, atol=1e-9)
        np.testing.assert_allclose(bake.world_to_armature(obj[0] @ arm, obj[0]), arm, atol=1e-9)


class SolvedChainTest(unittest.TestCase):
    """Bake the IK chain after a solve: parents come from the solved set, helper bones are carried along."""

    def setUp(self):
        rigs.clear_scene()

    def solve_like(self, fk, chain, rng):
        """New armature-space poses for the chain: turned about the shoulder, the elbow and the wrist."""
        upper, forearm, hand = (Matrix(fk[name][0].tolist()) for name in chain)
        r1, r2, r3 = (random_quaternion(rng) for _ in range(3))
        upper, forearm, hand = (rotate_about(m, upper.translation, r1) for m in (upper, forearm, hand))
        forearm, hand = (rotate_about(m, forearm.translation, r2) for m in (forearm, hand))
        hand = rotate_about(hand, hand.translation, r3)
        return {name: np.array(m)[None] for name, m in zip(chain, (upper, forearm, hand))}

    def test_chains(self):
        rng = random.Random(11)
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                unit = rigs.RIG_UNITS[build]
                mapping = bonemap.guess(obj).mapping
                randomize_pose(obj, rng, unit, scale=False)
                fk = rigs.pose_arrays(obj)
                for side in "LR":
                    chain = [mapping[f"chain_{part}_{side}"] for part in ("upper_arm", "forearm", "hand")]
                    targets = self.solve_like(fk, chain, rng)
                    solved = bake.complete_chain(obj.data.bones, targets, fk)
                    basis = bake.pose_to_basis(obj.data.bones, solved, fk)
                    for name, value in basis.items():
                        obj.pose.bones[name].matrix_basis = Matrix(value[0].tolist())
                    bpy.context.view_layer.update()
                    for name, target in targets.items():
                        assert_matrices(self, np.array(obj.pose.bones[name].matrix), target[0], unit, name)

    def test_helper_bones_are_completed(self):
        obj = rigs.mmd()
        fk = rigs.pose_arrays(obj)
        solved = bake.complete_chain(obj.data.bones, {n: fk[n] for n in ("左腕", "左ひじ", "左手首")}, fk)
        self.assertEqual(set(solved), {"左腕", "左腕捩", "左ひじ", "左手捩", "左手首"})
        rigs.clear_scene()
        obj = rigs.rigify()
        fk = rigs.pose_arrays(obj)
        solved = bake.complete_chain(obj.data.bones, {n: fk[n] for n in ("upper_arm_fk.L", "hand_fk.L")}, fk)
        self.assertEqual(set(solved), {"upper_arm_fk.L", "forearm_fk.L", "MCH-hand_fk.L", "hand_fk.L"})


def sweep(axis, frames=240):
    """Two full turns about `axis` with a small wobble: angles cross ±180° several times."""
    mats = []
    for i in range(frames):
        t = i / (frames - 1)
        q = (Quaternion(axis, 4.0 * math.pi * t)
             @ Quaternion((1.0, 0.0, 0.0), 0.2 * math.sin(6.0 * math.pi * t))
             @ Quaternion((0.0, 1.0, 0.0), 0.15 * math.sin(10.0 * math.pi * t)))
        mats.append(np.array(q.to_matrix()))
    return np.array(mats)


class ChannelTest(unittest.TestCase):
    def test_decompose(self):
        rotation = Euler((0.3, -1.1, 2.0)).to_matrix().to_4x4()
        matrix = Matrix.Translation((1.0, -2.0, 3.0)) @ rotation @ Matrix.Diagonal((0.5, 2.0, 1.5, 1.0))
        loc, rot, scale = bake.decompose(np.array(matrix))
        np.testing.assert_allclose(loc[0], (1.0, -2.0, 3.0), atol=1e-6)
        np.testing.assert_allclose(scale[0], (0.5, 2.0, 1.5), atol=1e-6)
        np.testing.assert_allclose(rot[0], np.array(rotation.to_3x3()), atol=1e-6)
        loc, rot, scale = bake.decompose(np.array(matrix @ Matrix.Diagonal((-1.0, 1.0, 1.0, 1.0))))
        self.assertTrue(np.all(scale[0] < 0.0))
        self.assertAlmostEqual(np.linalg.det(rot[0]), 1.0, places=6)

    def check_rotations(self, values, mode, rot):
        # mathutils works in float32, so round trips through quaternions and axis-angle drift by ~1e-5.
        for value, expected in zip(values, rot):
            if mode == 'QUATERNION':
                got = Quaternion(value).to_matrix()
            elif mode == 'AXIS_ANGLE':
                got = Quaternion(value[1:], value[0]).to_matrix()
            else:
                got = Euler(value, mode).to_matrix()
            np.testing.assert_allclose(np.array(got), expected, atol=5e-5)

    def test_continuity(self):
        for axis_name, axis in (("Z", (0.05, 0.02, 1.0)), ("X", (1.0, 0.03, -0.04)), ("Y", (0.02, 1.0, 0.05)),
                                ("tilted", (0.3, -0.5, 0.8))):
            rot = sweep(Vector(axis).normalized())
            for mode in MODES:
                with self.subTest(axis=axis_name, mode=mode):
                    values = bake.rotation_channels(rot, mode)
                    self.check_rotations(values, mode, rot)
                    steps = np.abs(np.diff(values, axis=0))
                    if mode == 'QUATERNION':
                        self.assertTrue(np.all(np.sum(values[1:] * values[:-1], axis=1) > 0.0))
                    elif mode == 'AXIS_ANGLE':
                        self.assertLess(steps[:, 0].max(), 0.2)
                        self.assertGreater(abs(values[-1, 0] - values[0, 0]), 3.0 * math.pi)
                    elif axis_name in mode[0] + mode[2]:
                        # Turning about an outer axis of the order never meets gimbal lock, so the angles
                        # must run on smoothly past ±180°.
                        self.assertLess(steps.max(), 0.2)
                        self.assertGreater(np.abs(values[-1] - values[0]).max(), 3.0 * math.pi)

    def test_channels(self):
        matrix = Matrix.LocRotScale((0.1, 0.2, 0.3), Euler((0.5, 0.4, -0.3)), (1.0, 1.1, 0.9))
        loc, rot, scale = bake.channels(np.array([matrix, matrix]), 'YXZ')
        np.testing.assert_allclose(loc, [(0.1, 0.2, 0.3)] * 2, atol=1e-6)
        np.testing.assert_allclose(scale, [(1.0, 1.1, 0.9)] * 2, atol=1e-6)
        self.assertEqual(rot.shape, (2, 3))
        with self.assertRaises(ValueError):
            bake.rotation_channels(np.eye(3)[None], 'XYZW')
