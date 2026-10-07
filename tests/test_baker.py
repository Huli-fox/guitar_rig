import math
import unittest
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

import rigs
from guitar_rig.core import baker, calibrate, collider, keys, landmarks, mount, solver
from guitar_rig.core.bonemap import SIDES
from guitar_rig.core.mathx import rotation_angle
from guitar_rig.ops import bake as bake_ops
from guitar_rig.rig import build
from guitar_rig.ui import overlay, panels
from test_addon import FakeLayout
from test_solve import chain, setup_scene

FRAMES = range(1, 9)
TOLERANCE = 1e-4            # metres between a played-back bake and its solve: keys are 32-bit floats


def rotation_prop(pbone):
    return baker.rotation_path(pbone.rotation_mode)


def animate(obj, root, frames=FRAMES, bones=None, right=True):
    """Key a performance: the chest turns, the left hand moves along the neck and in and out of the fretboard,
    and (with `right`) the right hand moves about the strum line. Keys rotations of `bones` (default: every pose
    bone) on every frame."""
    scene = bpy.context.scene
    unit = 1.0 / scene.unit_settings.scale_length
    assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
    bpy.context.view_layer.update()
    found = landmarks.find(root)
    nut, pivot, strum = (found[role].matrix_world.translation.copy() for role in ("NUT", "NECK_PIVOT", "STRUM_A"))
    chest = obj.pose.bones[obj.gtr_char.bone_map.chest]
    rest = chest.matrix_basis.copy()
    names = bones if bones is not None else [pbone.name for pbone in obj.pose.bones]
    for f in frames:
        scene.frame_set(f)
        t = (f - frames[0]) / max(len(frames) - 1, 1)
        chest.matrix_basis = rest @ Euler((0.0, 0.15 * t, 0.08 * t)).to_matrix().to_4x4()
        bpy.context.view_layer.update()
        target = pivot.lerp(nut, 0.3 + 0.4 * t) + Vector((0.0, -0.05, 0.06 - 0.1 * t)) * unit
        rigs.reach(obj, *chain(obj, 'L'), target, Vector((0.0, 0.5, -1.0)))
        if right:
            rigs.reach(obj, *chain(obj, 'R'), strum + Vector((0.0, -0.05, 0.08 * (t - 0.5))) * unit,
                       Vector((0.0, 0.5, -1.0)))
        for name in names:
            pbone = obj.pose.bones[name]
            pbone.keyframe_insert(rotation_prop(pbone))
            pbone.keyframe_insert("location")
    scene.frame_start, scene.frame_end = frames[0], frames[-1]
    scene.frame_set(frames[0])


def plain(settings):
    """No filters and no hysteresis: each baked frame is then what Solve Frame gives on it."""
    settings.use_filters = False
    for item in settings.magnets:
        item.hysteresis = 1.0


def played(obj, root, rig, frame):
    """(wrist and elbow world positions per side, GTR_ROOT's world matrix) of the bake played back at `frame`."""
    bpy.context.scene.frame_set(frame)
    mw = obj.matrix_world
    arms = {side: (mw @ obj.pose.bones[rig.chains[side].hand].head, mw @ obj.pose.bones[rig.chains[side].forearm].head)
            for side in SIDES}
    return arms, root.matrix_world.copy()


class BakeTest(unittest.TestCase):
    unit = 1.0
    build_rig = None

    def setUp(self):
        self.obj, self.root = setup_scene(self.unit, self.build_rig)
        self.scene = bpy.context.scene
        self.settings = self.scene.gtr
        self.rig = build.find(self.settings)

    def tracks(self, owner):
        return [track.name for track in owner.animation_data.nla_tracks]

    def assert_matches_solve(self, frames=FRAMES, tolerance=TOLERANCE):
        """The played-back bake equals Solve Frame, frame by frame (for a bake without filters or hysteresis)."""
        tolerance = tolerance / self.scene.unit_settings.scale_length
        for frame in frames:
            arms, guitar = played(self.obj, self.root, self.rig, frame)
            result = solver.solve(bpy.context, self.rig)
            for side in SIDES:
                self.assertLess((arms[side][0] - result.sides[side].wrist).length, tolerance, (frame, side))
                self.assertLess((arms[side][1] - result.sides[side].elbow).length, tolerance, (frame, side))
            expected = result.guitar.matrix()
            self.assertLess((guitar.translation - expected.translation).length, tolerance, frame)
            self.assertLess(rotation_angle(guitar.to_quaternion(), expected.to_quaternion()), 1e-4, frame)
            build.deactivate(self.settings)


class BakeVRoidTest(BakeTest):
    def test_bake_plays_the_solve(self):
        animate(self.obj, self.root)
        plain(self.settings)
        before = {}
        for frame in (2, 6):
            self.scene.frame_set(frame)
            before[frame] = solver.solve(bpy.context, self.rig)
        build.deactivate(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertFalse(self.settings.solve_active)
        self.assertIn("Played back within", self.settings.bake_report)
        self.assert_matches_solve()
        # Solve Frame after the bake still solves the mocap, not the bake.
        for frame, result in before.items():
            self.scene.frame_set(frame)
            again = solver.solve(bpy.context, self.rig)
            for side in SIDES:
                self.assertLess((again.sides[side].wrist - result.sides[side].wrist).length, 1e-6)

    def test_nla_layers(self):
        animate(self.obj, self.root)
        source = self.obj.animation_data.action
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        data = self.obj.animation_data
        self.assertIsNone(data.action)
        self.assertEqual(self.tracks(self.obj), [source.name, "GuitarBake", "GuitarRefine"])
        bake_strip, refine_strip = data.nla_tracks["GuitarBake"].strips[0], data.nla_tracks["GuitarRefine"].strips[0]
        self.assertEqual((bake_strip.blend_type, bake_strip.extrapolation), ('REPLACE', 'NOTHING'))
        self.assertEqual(refine_strip.blend_type, 'COMBINE')
        self.assertEqual(bake_strip.action.name, "VRoid_GuitarBake")
        self.assertEqual(bake_strip.action[keys.TAG], keys.ARM)
        self.assertEqual(keys.fcurves(refine_strip.action), [])
        self.assertEqual(tuple(refine_strip.action.frame_range), (1.0, 8.0))
        # One key per frame, on the arm chains only: rotations of the three mapped bones of each arm.
        curves = keys.fcurves(bake_strip.action)
        mapped = {name for side in SIDES for name in chain(self.obj, side)}
        self.assertEqual({c.data_path.split('"')[1] for c in curves}, mapped)
        self.assertTrue(all(len(c.keyframe_points) == len(FRAMES) for c in curves))
        self.assertTrue(all(c.data_path.endswith(rotation_prop(self.obj.pose.bones[c.data_path.split('"')[1]]))
                            for c in curves))
        # The guitar: keyed relative to the chest bone, which it is parented to.
        self.assertEqual(self.tracks(self.root), ["GuitarBake", "GuitarRefine"])
        self.assertIs(self.root.parent, self.obj)
        self.assertEqual((self.root.parent_type, self.root.parent_bone), ('BONE', self.obj.gtr_char.bone_map.chest))
        guitar_curves = keys.fcurves(self.root.animation_data.nla_tracks["GuitarBake"].strips[0].action)
        self.assertEqual(len(guitar_curves), 9 if self.root.rotation_mode in baker.bake.EULER_ORDERS else 10)
        # The bake follows the chest: moving the character afterwards carries the guitar along.
        self.scene.frame_set(4)
        before = self.root.matrix_world.copy()
        self.obj.location.x += 1.0
        bpy.context.view_layer.update()
        self.assertLess((self.root.matrix_world.translation - before.translation - Vector((1.0, 0.0, 0.0))).length,
                        1e-5)

    def test_rebake_keeps_the_refine_layer(self):
        animate(self.obj, self.root)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        refine = self.obj.animation_data.nla_tracks["GuitarRefine"].strips[0].action
        hand = self.obj.pose.bones[chain(self.obj, 'L')[2]]
        channels = keys.Channels(refine, self.obj)
        curve = channels.new(hand.path_from_id("location"), 0, hand.name)
        keys.write(curve, [1.0, 8.0], [0.0, 0.0])
        actions = len(bpy.data.actions)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertEqual(len(bpy.data.actions), actions)
        self.assertNotIn("WARNING", self.settings.bake_report)
        for owner in (self.obj, self.root):
            self.assertEqual(self.tracks(owner)[-2:], ["GuitarBake", "GuitarRefine"])
            self.assertEqual(owner.animation_data.nla_tracks["GuitarBake"].strips[0].action.name,
                             f"{owner.name}_GuitarBake")
        self.assertEqual(self.obj.animation_data.nla_tracks["GuitarRefine"].strips[0].action, refine)
        # Remove Bake keeps the refine action that holds keys.
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertIn(refine.name, bpy.data.actions)
        self.assertTrue(refine.use_fake_user)
        self.assertNotIn("GTR_ROOT_GuitarRefine", bpy.data.actions)

    def test_remove_bake_restores(self):
        animate(self.obj, self.root)
        source = self.obj.animation_data.action
        self.scene.frame_set(3)
        fk = rigs.pose_arrays(self.obj)
        root_matrix = self.root.matrix_world.copy()
        actions = set(bpy.data.actions.keys())
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.scene.frame_set(3)
        self.assertGreater((self.root.matrix_world.translation - root_matrix.translation).length, 1e-3)
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertEqual(set(bpy.data.actions.keys()), actions)
        self.assertEqual(self.obj.animation_data.action, source)
        self.assertEqual(len(self.obj.animation_data.nla_tracks), 0)
        self.assertIsNone(self.root.parent)
        self.assertNotIn(keys.STATIC_PROP, self.obj)
        self.assertNotIn(baker.ROOT_PARENT_PROP, self.root)
        self.scene.frame_set(3)
        for got, expected in zip(self.root.matrix_world, root_matrix):
            self.assertLess((Vector(got) - Vector(expected)).length, 1e-6)
        after = rigs.pose_arrays(self.obj)
        for name, matrix in fk.items():
            np.testing.assert_allclose(after[name], matrix, atol=1e-6)

    def test_static_channels(self):
        """Channels the mocap does not animate (the right arm here) play their own values again whenever the
        bake is muted or removed, although the bake wrote into them."""
        names = [chain(self.obj, 'L')[i] for i in range(3)] + [self.obj.gtr_char.bone_map.chest]
        animate(self.obj, self.root, bones=names, right=False)
        plain(self.settings)
        right = chain(self.obj, 'R')
        self.scene.frame_set(5)
        static = rigs.pose_arrays(self.obj, right)
        before = solver.solve(bpy.context, self.rig)
        build.deactivate(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.scene.frame_set(5)
        baked = rigs.pose_arrays(self.obj, right)
        self.assertGreater(max(np.abs(baked[n] - static[n]).max() for n in right), 1e-4)
        again = solver.solve(bpy.context, self.rig)
        self.assertLess((again.sides['R'].wrist - before.sides['R'].wrist).length, 1e-6)
        build.deactivate(self.settings)
        first = {c.data_path + str(c.array_index): keys.read(c)[1]
                 for c in keys.fcurves(self.obj.animation_data.nla_tracks["GuitarBake"].strips[0].action)}
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        second = {c.data_path + str(c.array_index): keys.read(c)[1]
                  for c in keys.fcurves(self.obj.animation_data.nla_tracks["GuitarBake"].strips[0].action)}
        self.assertEqual(first.keys(), second.keys())
        for key, values in first.items():
            np.testing.assert_allclose(second[key], values, atol=1e-6)
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.scene.frame_set(5)
        restored = rigs.pose_arrays(self.obj, right)
        for name in right:
            np.testing.assert_allclose(restored[name], static[name], atol=1e-6)

    def test_world_space_guitar(self):
        animate(self.obj, self.root)
        plain(self.settings)
        self.settings.guitar_space = 'WORLD'
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertIsNone(self.root.parent)
        self.assert_matches_solve(frames=(1, 5, 8))

    def test_rotation_modes(self):
        left, right = chain(self.obj, 'L'), chain(self.obj, 'R')
        for name, mode in zip(left + right, ('XYZ', 'ZXY', 'YZX', 'AXIS_ANGLE', 'XZY', 'QUATERNION')):
            self.obj.pose.bones[name].rotation_mode = mode
        self.root.rotation_mode = 'QUATERNION'
        animate(self.obj, self.root)
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assert_matches_solve(frames=(1, 4, 8))

    def test_animated_object_and_frame_range(self):
        animate(self.obj, self.root)
        for f in FRAMES:
            self.obj.location = (0.02 * f, 0.0, 0.01 * f)
            self.obj.keyframe_insert("location", frame=f)
        plain(self.settings)
        self.settings.use_scene_frame_range = False
        self.settings.frame_start, self.settings.frame_end = 3, 6
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        strip = self.obj.animation_data.nla_tracks["GuitarBake"].strips[0]
        self.assertEqual((strip.frame_start, strip.frame_end), (3.0, 6.0))
        self.assert_matches_solve(frames=(3, 6))
        self.settings.frame_start, self.settings.frame_end = 6, 3
        with self.assertRaisesRegex(RuntimeError, "frame range is empty"):
            bpy.ops.gtr.bake()

    def test_job_cancel_and_hidden_meshes(self):
        animate(self.obj, self.root)
        meshes = [obj for obj in self.scene.objects if obj.type == 'MESH']
        meshes[0].hide_viewport = True
        actions = set(bpy.data.actions.keys())
        self.scene.frame_set(4)
        job = baker.BakeJob(bpy.context, self.rig)
        job.step(bpy.context)
        job.step(bpy.context)
        self.assertTrue(all(obj.hide_viewport for obj in meshes))
        self.assertTrue(all(track.mute for track, _ in keys._our_tracks(self.obj)))
        self.assertAlmostEqual(job.progress, 2 / (len(job.prepass) + len(FRAMES)))     # with the pass-through pre-pass
        job.cancel(bpy.context)
        self.assertEqual(self.scene.frame_current, 4)
        self.assertEqual([obj.hide_viewport for obj in meshes], [True] + [False] * (len(meshes) - 1))
        self.assertEqual(set(bpy.data.actions.keys()), actions)
        self.assertEqual(len(self.obj.animation_data.nla_tracks), 0)
        # A run to the end puts everything back the same way.
        job = baker.BakeJob(bpy.context, self.rig)
        messages = job.run(bpy.context)
        self.assertTrue(messages)
        self.assertEqual(self.scene.frame_current, 4)
        self.assertEqual([obj.hide_viewport for obj in meshes], [True] + [False] * (len(meshes) - 1))
        self.assertFalse(any(track.mute for track in self.obj.animation_data.nla_tracks))

    def test_filters_smooth_from_the_second_frame(self):
        animate(self.obj, self.root)
        results = {}
        for use in (False, True):
            self.settings.use_filters = use
            self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
            results[use] = {f: played(self.obj, self.root, self.rig, f) for f in (1, 4)}
        for side in SIDES:
            self.assertLess((results[True][1][0][side][0] - results[False][1][0][side][0]).length, 1e-6)
        self.assertGreater((results[True][4][0]['L'][0] - results[False][4][0]['L'][0]).length, 1e-4)

    def test_smooth(self):
        animate(self.obj, self.root)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        action = self.obj.animation_data.nla_tracks["GuitarBake"].strips[0].action
        before = {(c.data_path, c.array_index): keys.read(c)[1] for c in keys.fcurves(action)}
        self.settings.smooth_cutoff_arms = 2.0
        self.assertEqual(bpy.ops.gtr.smooth_bake(), {'FINISHED'})
        after = {(c.data_path, c.array_index): keys.read(c) for c in keys.fcurves(action)}
        self.assertTrue(any(np.abs(after[key][1] - values).max() > 1e-4 for key, values in before.items()))
        np.testing.assert_array_equal(next(iter(after.values()))[0], np.arange(1.0, 9.0))
        # Quaternions stay unit length.
        for name in chain(self.obj, 'L'):
            pbone = self.obj.pose.bones[name]
            if pbone.rotation_mode == 'QUATERNION':
                q = np.stack([after[(pbone.path_from_id("rotation_quaternion"), i)][1] for i in range(4)], axis=1)
                np.testing.assert_allclose(np.linalg.norm(q, axis=1), 1.0, atol=1e-5)
        self.settings.smooth_cutoff_arms = 100.0
        self.assertEqual(bpy.ops.gtr.smooth_bake(), {'FINISHED'})
        self.assertIn("nothing changed", self.settings.bake_report)

    def test_reclamp(self):
        """A collider switched on after the bake: re-clamp pushes the baked left hand out of it, and changes only
        the frames it had to."""
        animate(self.obj, self.root)
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        cal = calibrate.load(self.obj.gtr_char.calibration)
        chest = self.obj.gtr_char.bone_map.chest
        settings = self.settings
        settings.collider_enabled, settings.collider_hands, settings.collider_fingertips = True, {'L'}, False
        settings.collider_radius_m, settings.collider_top_m, settings.collider_bottom_m = 0.6, 0.6, -0.6
        # Put the capsule's front 2 cm in front of the baked left wrist at frame 5.
        arms, _ = played(self.obj, self.root, self.rig, 5)
        body = collider.capsule(settings, cal, *mount.chest_pose(self.obj, cal, chest))
        x, _, z = body.local(arms['L'][0])
        unit = body.radius / 0.6
        settings.collider_depth_m = (z - math.sqrt(body.radius ** 2 - x * x) + 0.02 * unit) / unit
        action = self.obj.animation_data.nla_tracks["GuitarBake"].strips[0].action
        before = {(c.data_path, c.array_index): keys.read(c)[1] for c in keys.fcurves(action)}
        needs = {}
        for frame in FRAMES:
            arms, _ = played(self.obj, self.root, self.rig, frame)
            body = collider.capsule(settings, cal, *mount.chest_pose(self.obj, cal, chest))
            needs[frame] = body.push(arms['L'][0])
        self.assertAlmostEqual(needs[5], 0.02, places=6)
        self.assertEqual(bpy.ops.gtr.reclamp(), {'FINISHED'})
        self.assertIn("Re-clamped", settings.bake_report)
        after = {(c.data_path, c.array_index): keys.read(c)[1] for c in keys.fcurves(action)}
        self.assertEqual(before.keys(), after.keys())
        changed = set()
        for key, values in before.items():
            changed |= {FRAMES[i] for i in np.nonzero(np.abs(after[key] - values) > 1e-6)[0]}
        self.assertEqual(changed, {f for f, push in needs.items() if push > settings.reclamp_tolerance_m})
        arms, _ = played(self.obj, self.root, self.rig, 5)
        body = collider.capsule(settings, cal, *mount.chest_pose(self.obj, cal, chest))
        self.assertLess(body.push(arms['L'][0]), 1e-4)
        self.assertEqual(bpy.ops.gtr.reclamp(), {'FINISHED'})
        self.assertIn("No frame", settings.bake_report)

    def test_polls_and_panels(self):
        animate(self.obj, self.root)
        labels = []

        def draw():
            labels.clear()
            for cls in panels.CLASSES:
                poll = getattr(cls, "poll", None)
                if poll is None or poll(bpy.context):
                    cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
            return labels

        self.assertTrue(any("Bake keys the arms" in label for label in draw()))
        for op in (bpy.ops.gtr.reclamp, bpy.ops.gtr.smooth_bake, bpy.ops.gtr.remove_bake):
            self.assertFalse(op.poll())
        self.assertTrue(bpy.ops.gtr.flip_frame.poll())
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        for op in (bpy.ops.gtr.reclamp, bpy.ops.gtr.smooth_bake, bpy.ops.gtr.remove_bake, bpy.ops.gtr.select_landmark):
            self.assertTrue(op.poll())
        for op in (bpy.ops.gtr.flip_frame, bpy.ops.gtr.load_preset, bpy.ops.gtr.normalize_frame):
            self.assertFalse(op.poll())
        self.assertTrue(any(label.startswith("Baked frames 1-8") for label in draw()))
        self.settings.active_magnet_index = 5
        self.assertTrue(any("acts from frame to frame" in label for label in draw()))
        self.assertEqual(bpy.ops.gtr.clean_rig(), {'FINISHED'})
        self.assertFalse(bpy.ops.gtr.bake.poll())
        self.assertTrue(bpy.ops.gtr.remove_bake.poll())
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertFalse(bpy.ops.gtr.remove_bake.poll())


class BakeCentimetreTest(BakeTest):
    unit = 100.0

    def test_bake_plays_the_solve(self):
        animate(self.obj, self.root, frames=range(1, 5))
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assert_matches_solve(frames=(1, 4))


class BakeMMDTest(BakeTest):
    build_rig = staticmethod(rigs.mmd)

    def test_twist_bones(self):
        """The twist bones between the mapped ones keep playing the mocap: they are not keyed."""
        animate(self.obj, self.root, frames=range(1, 5))
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        keyed = {c.data_path.split('"')[1]
                 for c in keys.fcurves(self.obj.animation_data.nla_tracks["GuitarBake"].strips[0].action)}
        mapped = {name for side in SIDES for name in chain(self.obj, side)}
        path = {name for side in SIDES for name in baker.chain_path(self.obj, self.rig.chains[side])}
        self.assertGreater(len(path), len(mapped))
        self.assertEqual(keyed, mapped)
        self.assert_matches_solve(frames=(1, 4))


class BakeRigifyTest(BakeTest):
    build_rig = staticmethod(rigs.rigify)

    def test_bake_plays_the_solve(self):
        animate(self.obj, self.root, frames=range(1, 5))
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assert_matches_solve(frames=(1, 4))


class ChannelsTest(unittest.TestCase):
    def test_channels_near(self):
        rng = np.random.default_rng(3)
        for mode in ('QUATERNION', 'AXIS_ANGLE', 'XYZ', 'ZYX'):
            rotations = [Euler(rng.uniform(-3.0, 3.0, 3)).to_matrix() for _ in range(6)]
            rot = np.array([np.array(m) for m in rotations])
            reference = baker.bake.rotation_channels(rot, mode)
            if mode == 'QUATERNION':
                reference[::2] *= -1.0
            elif mode == 'AXIS_ANGLE':
                reference[:, 0] += 2.0 * math.pi
            else:
                reference += 2.0 * math.pi
            near = baker.channels_near(rot, mode, reference)
            np.testing.assert_allclose(near, reference, atol=1e-6)     # mathutils is single precision
            back = baker.quaternion_matrices(baker.channel_quaternions(near, mode))
            np.testing.assert_allclose(back, rot, atol=1e-6)


class ColliderSolveTest(BakeTest):
    def test_solve_frame_pushes_the_wrist_out(self):
        settings = self.settings
        settings.aim_enabled, settings.wrist_blend = False, 0.0
        for item in settings.magnets:
            item.enabled = False
        settings.collider_enabled, settings.collider_hands, settings.collider_fingertips = True, {'L'}, False
        settings.collider_radius_m, settings.collider_top_m, settings.collider_bottom_m = 0.6, 0.6, -0.6
        cal = self.obj.gtr_char.calibration
        chest = self.obj.gtr_char.bone_map.chest
        chest_pos, chest_frame = mount.chest_pose(self.obj, cal, chest)
        rigs.reach(self.obj, *chain(self.obj, 'L'), chest_pos + chest_frame @ Vector((0.15, -0.1, 0.25)),
                   Vector((0.0, 0.5, -1.0)))
        wrist = rigs.world_head(self.obj, chain(self.obj, 'L')[2])
        body = collider.capsule(settings, cal, *mount.chest_pose(self.obj, cal, chest))
        x, _, z = body.local(wrist)
        settings.collider_depth_m = (z - math.sqrt(body.radius ** 2 - x * x) + 0.03) / (body.radius / 0.6)
        lines = len(overlay_geometry()[0])
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(self.scene)
        contact = result.sides['L'].collider
        self.assertEqual(contact.weight, 1.0)
        self.assertAlmostEqual(contact.moved.length, 0.03, places=5)
        self.assertGreater(contact.moved.normalized().dot(body.forward), 0.9999)
        self.assertLess((result.sides['L'].wrist - wrist - contact.moved).length, TOLERANCE)
        self.assertIsNone(result.sides['R'].collider and result.sides['R'].collider.deepest)
        self.assertIn("chest collider 3.0 cm", solver.summary(result, settings.magnets))
        self.assertGreater(len(overlay_geometry()[0]), lines)
        self.assertIn("Chest collider: 3.0 cm", [text for _, _, text, _ in overlay.build_labels(bpy.context)])
        settings.collider_enabled = False
        self.assertIsNone(solver.solve(bpy.context, self.rig).sides['L'].collider)


def overlay_geometry():
    return overlay.build_geometry(bpy.context)


class ModalTest(BakeTest):
    class Runner(bake_ops._JobOperator):
        bl_label = "Bake"

        def __init__(self, job):
            self._job = job
            self.reports = []

        def report(self, level, text):
            self.reports.append((level, text))

    def context(self):
        return SimpleNamespace(scene=self.scene, view_layer=bpy.context.view_layer, screen=None, workspace=None,
                               window_manager=bpy.context.window_manager)

    def test_timer_steps_and_escape(self):
        animate(self.obj, self.root)
        context = self.context()
        runner = self.Runner(baker.BakeJob(bpy.context, self.rig))
        self.assertEqual(runner.modal(context, SimpleNamespace(type='MOUSEMOVE')), {'RUNNING_MODAL'})
        self.assertEqual(runner._job.index, 0)
        state = {'RUNNING_MODAL'}
        while state == {'RUNNING_MODAL'}:
            state = runner.modal(context, SimpleNamespace(type='TIMER'))
        self.assertEqual(state, {'FINISHED'})
        self.assertTrue(keys.has_bake(self.obj))
        self.assertTrue(any(text.startswith("Baked frames") for _, text in runner.reports))
        runner = self.Runner(baker.BakeJob(bpy.context, self.rig))
        runner._job.step(bpy.context)
        self.assertEqual(runner.modal(context, SimpleNamespace(type='ESC')), {'CANCELLED'})
        self.assertIn("nothing was changed", runner.reports[-1][1])
        self.assertFalse(any(track.mute for track in self.obj.animation_data.nla_tracks))
