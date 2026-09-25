import math
import unittest

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

import rigs
from guitar_rig.core import bonemap, calibrate
from guitar_rig.core.mathx import auto_scale_factor, rotation_angle

# C_char in world space for a character that faces -Y with Z up.
FACING_MINUS_Y = rigs.BLENDER_AXES.to_quaternion()


def calibrated(obj, **kwargs):
    mapping = bonemap.guess(obj).mapping
    return mapping, calibrate.compute(obj, mapping, **kwargs)


def texts(cal, level=None):
    return [text for lvl, text in cal.messages if level is None or lvl == level]


def world_frame(obj, cal):
    return calibrate.char_frame_world(cal.char_frame, obj.matrix_world)


class CharacterFrameTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_all_rigs(self):
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                _, cal = calibrated(obj)
                expected = FACING_MINUS_Y
                if build is rigs.unreal:
                    expected = Quaternion((0.0, 0.0, 1.0), math.pi / 2.0) @ expected
                self.assertLess(rotation_angle(world_frame(obj, cal), expected), 1e-4)

    def test_axes(self):
        obj = rigs.unreal()  # faces +X in world
        _, cal = calibrated(obj)
        frame = world_frame(obj, cal)
        for axis, expected in (((1, 0, 0), (0, 1, 0)), ((0, 1, 0), (0, 0, 1)), ((0, 0, 1), (1, 0, 0))):
            self.assertLess((frame @ Vector(axis) - Vector(expected)).length, 1e-5, axis)

    def test_flip(self):
        obj = rigs.vroid()
        mapping, _ = calibrated(obj)
        frame = world_frame(obj, calibrate.compute(obj, mapping, flip=True))
        self.assertLess((frame @ Vector((0, 0, 1)) - Vector((0, 1, 0))).length, 1e-5)
        self.assertLess((frame @ Vector((0, 1, 0)) - Vector((0, 0, 1))).length, 1e-5)

    def test_swapped_sides_warn(self):
        obj = rigs.vroid()
        mapping, cal = calibrated(obj)
        self.assertFalse(any("swapped" in text for text in texts(cal)))
        swapped = {key: mapping[key[:-1] + ('R' if key.endswith('L') else 'L')] if bonemap.SLOT_BY_KEY[key].side
                   else name for key, name in mapping.items()}
        cal = calibrate.compute(obj, swapped)
        self.assertTrue(any("swapped" in text for text in texts(cal, 'WARNING')))
        # Flipping the frame makes it consistent with the swapped map again.
        self.assertFalse(any("swapped" in text for text in texts(calibrate.compute(obj, swapped, flip=True))))

    def test_degenerate(self):
        obj = rigs.vroid()
        mapping = dict(bonemap.guess(obj).mapping, upper_arm_R="J_Bip_L_UpperArm")
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.compute(obj, mapping)


class MeasurementTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def assert_body(self, cal):
        self.assertAlmostEqual(cal.arm_len, rigs.ARM_LEN, places=5)
        self.assertAlmostEqual(cal.palm_len, rigs.PALM_LEN, places=5)
        self.assertAlmostEqual(cal.spine_len, rigs.SPINE_LEN, places=5)
        self.assertAlmostEqual(cal.chain_len['L'], rigs.CHAIN_LEN, places=5)
        self.assertAlmostEqual(cal.chain_len['R'], rigs.CHAIN_LEN, places=5)
        self.assertAlmostEqual(cal.height, rigs.HEIGHT, places=4)

    def test_all_rigs(self):
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                _, cal = calibrated(build())
                self.assert_body(cal)
                self.assertEqual(texts(cal, 'WARNING'), [])

    def test_ratios(self):
        _, cal = calibrated(rigs.vroid())
        self.assertAlmostEqual(cal.ratio_arm, rigs.ARM_LEN / 0.468508, places=4)
        self.assertAlmostEqual(cal.ratio_palm, rigs.PALM_LEN / 0.0820044, places=4)
        self.assertAlmostEqual(cal.ratio_spine, rigs.SPINE_LEN / 0.452238, places=4)

    def test_scene_unit_scale(self):
        obj = rigs.vroid(unit=100.0)  # 175 units tall in a scene where a unit is a centimetre
        mapping = bonemap.guess(obj).mapping
        cal = calibrate.compute(obj, mapping, metres_per_bu=0.01)
        self.assert_body(cal)
        self.assertEqual(texts(cal, 'WARNING'), [])

    def test_scale_warnings(self):
        _, cal = calibrated(rigs.vroid(matrix_world=Matrix.Scale(10.0, 4)))
        self.assertAlmostEqual(cal.height, 10.0 * rigs.HEIGHT, places=3)
        self.assertTrue(any("tall" in text for text in texts(cal, 'WARNING')))
        rigs.clear_scene()
        _, cal = calibrated(rigs.vroid(matrix_world=Matrix.Diagonal((1.0, 1.0, 1.2, 1.0))))
        self.assertTrue(any("non-uniform" in text for text in texts(cal, 'WARNING')))

    def test_missing_optional_bones(self):
        obj = rigs.vroid()
        mapping = bonemap.guess(obj).mapping
        for key in ("neck", "thigh_L", "middle_proximal_L"):
            mapping[key] = ""
        for key, slot in bonemap.SLOT_BY_KEY.items():
            if slot.group == 'FINGERS' and slot.side == 'R':
                mapping[key] = ""
        cal = calibrate.compute(obj, mapping)
        warnings = " ".join(texts(cal, 'WARNING'))
        for word in ("neck", "upper-leg", "palm"):
            self.assertIn(word, warnings)
        self.assertTrue(any("right hand" in text for text in texts(cal, 'INFO')))
        self.assertEqual({tip.side for tip in cal.fingertips}, {'L'})
        self.assertAlmostEqual(cal.spine_len, 0.55, places=5)   # head above the hips
        self.assertAlmostEqual(cal.palm_len, 0.08, places=5)    # the hand bone itself

    def test_missing_required_bone(self):
        obj = rigs.vroid()
        mapping = dict(bonemap.guess(obj).mapping, hand_L="")
        with self.assertRaises(calibrate.CalibrationError):
            calibrate.compute(obj, mapping)


class AxisRotTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_t_pose_is_identity(self):
        for build in (rigs.vroid, rigs.mixamo, rigs.rigify, rigs.unreal, rigs.generic):
            with self.subTest(build.__name__):
                rigs.clear_scene()
                _, cal = calibrated(build())
                for side in "LR":
                    self.assertLess(rotation_angle(cal.axis_rot[side], Quaternion()), 1e-5)

    def test_a_pose(self):
        angle = math.radians(35.0)
        obj = rigs.mmd(a_pose=angle)
        mapping, cal = calibrated(obj)
        down_l = Vector((math.cos(angle), -math.sin(angle), 0.0))
        down_r = Vector((-math.cos(angle), -math.sin(angle), 0.0))
        self.assertLess((cal.axis_rot['L'] @ Vector((1, 0, 0)) - down_l).length, 1e-5)
        self.assertLess((cal.axis_rot['R'] @ Vector((-1, 0, 0)) - down_r).length, 1e-5)
        matched = calibrate.compute(obj, mapping, ref_angle=angle)
        for side in "LR":
            self.assertLess(rotation_angle(matched.axis_rot[side], Quaternion()), 1e-5)

    def test_offset_follows_the_forearm(self):
        """Posed alike, a T-pose and an A-pose rig put the axis_rot-rotated hand offset at the same place."""
        results = []
        for a_pose in (0.0, math.radians(35.0)):
            rigs.clear_scene()
            obj = rigs.vroid(a_pose=a_pose)
            mapping, cal = calibrated(obj)
            frame = world_frame(obj, cal)
            # Raise the arm by the A-pose angle: both rigs then hold the arm horizontally.
            rigs.rotate_bone(obj, mapping["upper_arm_L"], frame @ Quaternion((0, 0, 1), a_pose) @ frame.inverted())
            hand = obj.pose.bones[mapping["hand_L"]]
            q_hand = calibrate.rest_aligned((obj.matrix_world @ hand.matrix).to_quaternion(),
                                            calibrate.rest_aligned_offset(hand.bone, cal.char_frame))
            results.append((obj.matrix_world @ hand.head, q_hand @ cal.axis_rot['L'] @ Vector((0.6, -0.25, 0.0))))
        (head_t, offset_t), (head_a, offset_a) = results
        self.assertLess((head_t - head_a).length, 1e-5)
        self.assertLess((offset_t - offset_a).length, 1e-5)


class RestAlignedTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def frame(self, obj, cal, name):
        pbone = obj.pose.bones[name]
        q_world = (obj.matrix_world @ pbone.matrix).to_quaternion()
        return calibrate.rest_aligned(q_world, calibrate.rest_aligned_offset(pbone.bone, cal.char_frame))

    def test_rest_pose(self):
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                mapping, cal = calibrated(obj)
                expected = world_frame(obj, cal)
                for key, name in mapping.items():
                    self.assertLess(rotation_angle(self.frame(obj, cal, name), expected), 1e-4, key)

    def test_same_pose_same_frames(self):
        """Rigs with different rolls, axes, units and rest poses give Q_b = C_char @ (rotation from rest)."""
        deltas = {
            "chest": Euler((0.1, 0.25, -0.15)).to_quaternion(),
            "upper_arm_L": Euler((0.3, -0.5, 0.8)).to_quaternion(),
            "forearm_L": Euler((-0.2, 1.1, 0.3)).to_quaternion(),
            "hand_L": Euler((0.9, 0.2, -0.6)).to_quaternion(),
            "index_intermediate_L": Euler((0.0, 0.0, -1.2)).to_quaternion(),
            "upper_arm_R": Euler((-0.4, 0.3, -0.7)).to_quaternion(),
        }
        # Deltas are applied in this order, so each bone carries its own and its ancestors'.
        expected = {
            "chest": deltas["chest"],
            "upper_arm_L": deltas["upper_arm_L"] @ deltas["chest"],
            "forearm_L": deltas["forearm_L"] @ deltas["upper_arm_L"] @ deltas["chest"],
            "hand_L": deltas["hand_L"] @ deltas["forearm_L"] @ deltas["upper_arm_L"] @ deltas["chest"],
            "index_intermediate_L": (deltas["index_intermediate_L"] @ deltas["hand_L"] @ deltas["forearm_L"]
                                     @ deltas["upper_arm_L"] @ deltas["chest"]),
            "upper_arm_R": deltas["upper_arm_R"] @ deltas["chest"],
        }
        for build in rigs.ALL_RIGS:
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                mapping, cal = calibrated(obj)
                frame = world_frame(obj, cal)
                for key, delta in deltas.items():
                    rigs.rotate_bone(obj, mapping[key], frame @ delta @ frame.inverted())
                for key, rotation in expected.items():
                    q = frame.inverted() @ self.frame(obj, cal, mapping[key])
                    self.assertLess(rotation_angle(q, rotation), 1e-4, key)


class FingertipTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_bone_tails(self):
        for build in (rigs.vroid, rigs.rigify, rigs.mmd, rigs.unreal, rigs.generic):
            with self.subTest(build.__name__):
                rigs.clear_scene()
                obj = build()
                _, cal = calibrated(obj)
                self.assertEqual(len(cal.fingertips), 6)
                for tip in cal.fingertips:
                    bone = obj.data.bones[tip.bone]
                    self.assertEqual(tip.source, 'TAIL')
                    error = (bone.matrix_local @ tip.tip_local - bone.tail_local).length
                    self.assertLess(error, 1e-5 * rigs.RIG_UNITS[build])

    def test_estimated_from_joints(self):
        obj = rigs.mixamo()  # the distal tails point sideways
        mapping, cal = calibrated(obj)
        self.assertEqual(len(cal.fingertips), 6)
        self.assertTrue(any("estimated" in text for text in texts(cal, 'INFO')))
        for tip in cal.fingertips:
            self.assertEqual(tip.source, 'ESTIMATE')
            distal = obj.data.bones[tip.bone]
            intermediate = obj.data.bones[mapping[f"{tip.finger}_intermediate_{tip.side}"]]
            expected = distal.head_local + 0.5 * (distal.head_local - intermediate.head_local)
            self.assertLess((distal.matrix_local @ tip.tip_local - expected).length, 1e-3)  # centimetres

    def test_tips_follow_the_pose(self):
        obj = rigs.vroid()
        mapping, cal = calibrated(obj)
        frame = world_frame(obj, cal)
        rigs.rotate_bone(obj, mapping["hand_L"], frame @ Euler((0.4, 0.2, -0.9)).to_quaternion() @ frame.inverted())
        rigs.rotate_bone(obj, mapping["index_intermediate_L"], Quaternion((0, 0, 1), 0.7))
        for tip in cal.fingertips:
            pbone = obj.pose.bones[tip.bone]
            self.assertLess((pbone.matrix @ tip.tip_local - pbone.tail).length, 1e-5)


class StorageTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_fingerprint(self):
        obj = rigs.vroid()
        mapping, cal = calibrated(obj)
        self.assertEqual(calibrate.fingerprint(obj, mapping, False, 0.0, 1.0), cal.fingerprint)
        obj.pose.bones["J_Bip_L_UpperArm"].rotation_quaternion = Quaternion((0, 0, 1), 0.5)
        obj.location = (1.0, 2.0, 3.0)
        bpy.context.view_layer.update()
        self.assertEqual(calibrate.fingerprint(obj, mapping, False, 0.0, 1.0), cal.fingerprint)
        for args in ((True, 0.0, 1.0), (False, 0.1, 1.0), (False, 0.0, 0.01)):
            self.assertNotEqual(calibrate.fingerprint(obj, mapping, *args), cal.fingerprint, args)
        self.assertNotEqual(calibrate.fingerprint(obj, dict(mapping, neck=""), False, 0.0, 1.0), cal.fingerprint)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        obj.data.edit_bones["J_Bip_L_Hand"].roll += 0.3
        bpy.ops.object.mode_set(mode='OBJECT')
        self.assertNotEqual(calibrate.fingerprint(obj, mapping, False, 0.0, 1.0), cal.fingerprint)

    def test_store_and_load(self):
        obj = rigs.mixamo()
        _, cal = calibrated(obj)
        calibrate.store(cal, obj.gtr_char.calibration)
        loaded = calibrate.load(obj.gtr_char.calibration)
        self.assertLess(rotation_angle(loaded.char_frame, cal.char_frame), 1e-6)
        for name in ("metres_per_bu", "height", "arm_len", "palm_len", "spine_len", "ratio_arm", "ratio_palm",
                     "ratio_spine"):
            self.assertAlmostEqual(getattr(loaded, name), getattr(cal, name), places=5, msg=name)
        for side in "LR":
            self.assertAlmostEqual(loaded.chain_len[side], cal.chain_len[side], places=5)
            self.assertLess(rotation_angle(loaded.axis_rot[side], cal.axis_rot[side]), 1e-6)
        self.assertEqual([(t.side, t.finger, t.bone, t.source) for t in loaded.fingertips],
                         [(t.side, t.finger, t.bone, t.source) for t in cal.fingertips])
        for a, b in zip(loaded.fingertips, cal.fingertips):
            self.assertLess((a.tip_local - b.tip_local).length, 1e-4)
        self.assertEqual(loaded.messages, cal.messages)
        self.assertEqual(loaded.fingerprint, cal.fingerprint)
        obj.gtr_char.calibration.is_valid = False
        self.assertIsNone(calibrate.load(obj.gtr_char.calibration))

    def test_auto_scale_of_palm(self):
        _, cal = calibrated(rigs.vroid())
        self.assertAlmostEqual(auto_scale_factor(cal.ratio_palm), cal.ratio_palm * 0.9, places=6)
