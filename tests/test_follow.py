import json
import math
import os
import random
import unittest
from types import SimpleNamespace
from unittest import mock

import bpy
from mathutils import Euler, Quaternion, Vector

import rigs
from guitar_rig.core import aim, calibrate, landmarks, magnets, presets, solver, wrist
from guitar_rig.core.mathx import rotation_angle
from guitar_rig.rig import build
from guitar_rig.ui import overlay, panels
from test_addon import FakeLayout
from test_guitar import TMP_DIR
from test_magnets import PLANE, assert_vector
from test_solve import chain, mounted_landmarks, pose_left, setup_scene

TOLERANCE = 1e-4            # metres, for fingertips 0.2 m from an IK wrist


class AimMathTest(unittest.TestCase):
    def pose(self, rotation=None, scale=1.0):
        rotation = rotation or Euler((0.3, -0.2, 0.9)).to_quaternion()
        return magnets.GuitarPose(Vector((0.1, 0.2, 1.1)), rotation, rotation.copy(), Vector((scale,) * 3))

    def test_pivot(self):
        a, p = Vector((1.0, 1.0, 0.0)), Vector((3.0, 1.0, 0.0))
        assert_vector(self, aim.pivot(a, p), (0.0, 1.0, 0.0))
        assert_vector(self, aim.pivot(a, a), a)

    def test_index_js(self):
        """The aim recomputed with index.js's formulas (L712-840), for a uniformly scaled guitar."""
        rng = random.Random(4)
        a, p = Vector((4.373398, -2.754097, 6.2819)), Vector((64.4079, -1.828405, 7.2436))   # GLB units
        for _ in range(10):
            guitar = self.pose(scale=0.008)
            target = guitar.point(p) + Vector([rng.uniform(-0.15, 0.15) for _ in range(3)])
            m = p - a
            reference_origin = a + m * (-a.dot(m) / m.length_squared)
            axis_origin = reference_origin * 0.008
            axis_origin = guitar.default_rotation @ axis_origin + guitar.location
            axis_ext = target - axis_origin
            axis_ref = (guitar.default_rotation @ (p - reference_origin).normalized()) * axis_ext.length
            axis_ref += axis_origin - guitar.location
            axis_ext += axis_origin - guitar.location
            expected = axis_ref.rotation_difference(axis_ext) @ guitar.default_rotation
            result = aim.aim(guitar, a, p, target)
            self.assertLess(rotation_angle(result.rotation, expected), 5e-5)      # float32 on GLB-sized numbers
            self.assertLess((result.axis_origin - axis_origin).length, 1e-6)
            # The swung neck point lies on the line from the guitar origin to the target.
            swung = (result.rotation @ guitar.default_rotation.inverted()) @ axis_ref      # from the origin
            self.assertLess(swung.angle(target - guitar.location), 5e-5)

    def test_swing_only(self):
        """The aim turns the guitar about an axis square to both the neck point and the target direction, as seen
        from the guitar origin: no twist about them."""
        guitar = self.pose()
        a, p = Vector((0.0, 0.0, 0.05)), Vector((0.6, 0.0, 0.05))
        target = guitar.point(p) + Vector((0.0, 0.1, -0.05))
        result = aim.aim(guitar, a, p, target)
        swing = result.rotation @ guitar.default_rotation.inverted()
        axis, angle = swing.to_axis_angle()
        self.assertGreater(angle, 0.05)
        foot = aim.pivot(a, p)
        reach = (target - result.axis_origin).length
        neck_point = result.axis_origin - guitar.location + guitar.default_rotation @ (p - foot).normalized() * reach
        self.assertAlmostEqual(axis.dot(neck_point.normalized()), 0.0, places=5)
        self.assertAlmostEqual(axis.dot((target - guitar.location).normalized()), 0.0, places=5)

    def test_limits(self):
        guitar = self.pose(Quaternion())
        a, p = Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0))
        target = Vector((0.1, 0.2, 1.1)) + Vector((0.0, 1.0, 0.0))      # 90° off the neck
        result = aim.aim(guitar, a, p, target, max_swing=math.radians(35.0))
        self.assertTrue(result.clamped)
        self.assertAlmostEqual(rotation_angle(result.rotation, Quaternion()), math.radians(35.0), places=4)
        half = aim.aim(guitar, a, p, target, weight=0.5)
        self.assertAlmostEqual(rotation_angle(half.rotation, Quaternion()), math.radians(45.0), places=4)

    def test_limit_gap_and_move(self):
        """What Max Swing leaves between the target and the neck axis: nothing up to the limit, growing from zero
        past it, and nothing at weight 0. The move covers it across the shown neck."""
        guitar = self.pose(Quaternion())
        a, p = Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0))        # the axis starts at the guitar origin
        limit = math.radians(35.0)
        for degrees in (10.0, 34.9, 35.1, 36.0, 60.0, 90.0):
            angle = math.radians(degrees)
            target = guitar.location + Vector((math.cos(angle), math.sin(angle), 0.0)) * 0.5
            gap = aim.limit_gap(guitar, a, p, target, limit)
            self.assertAlmostEqual(gap, 0.5 * math.sin(max(angle - limit, 0.0)), places=5, msg=degrees)
            self.assertEqual(aim.limit_gap(guitar, a, p, target, limit, 0.0), 0.0)
            self.assertLessEqual(aim.limit_gap(guitar, a, p, target, limit, 0.5), gap + 1e-6)
            # Onto the axis of the guitar as the limited aim shows it, square to that axis.
            shown = aim.aim(guitar, a, p, target, limit).rotation
            move = aim.limit_move(guitar, shown, a, p, target, limit)
            self.assertAlmostEqual(move.length, gap, places=5)
            self.assertAlmostEqual(move.dot(shown @ (p - a)), 0.0, places=5)
            if gap > 0.0:
                self.assertLess(aim.axis_foot(guitar, shown, a, p, target + move)[1], 1e-5)
            else:
                self.assertEqual(move.length, 0.0)
            # A guitar shown further off (here: not swung at all) is approached by the same distance, no more.
            move = aim.limit_move(guitar, guitar.rotation, a, p, target, limit)
            self.assertAlmostEqual(move.length, gap, places=5)
            self.assertAlmostEqual(aim.axis_foot(guitar, guitar.rotation, a, p, target + move)[1],
                                   0.5 * math.sin(angle) - gap, places=5)
        foot, distance = aim.axis_foot(guitar, guitar.rotation, a, p, guitar.location + Vector((2.0, 0.3, 0.4)))
        assert_vector(self, foot - guitar.location, (2.0, 0.0, 0.0))           # past the nut: the line goes on
        self.assertAlmostEqual(distance, 0.5)

    def test_aim_shift(self):
        assert_vector(self, aim.aim_shift((0.0, 0.0, 2.0), 0.01, Vector((0.5, 0.5, 0.5))), (0.0, 0.0, 0.02))

    def test_axis_follows_the_last_fingertip_magnet(self):
        """SAO sets the aim axis from the fingertip magnets of the fretting hand, the last one in list order
        winning even at weight 0."""
        plane = SimpleNamespace(kind='PLANE', fingertip_mode='V2')
        settings = SimpleNamespace(magnets=[plane, SimpleNamespace(kind='PLANE', fingertip_mode='NONE'), plane])
        shapes = {i: magnets.Shape('PLANE', Vector(), normal=Vector((0.0, 0.0, 1.0))) for i in range(3)}

        def hit(shift, weight, tip=True):
            return magnets.Hit(Vector(), Vector(), Vector(), 0.0, 1.0, weight, False, Vector(), shift,
                               Vector() if tip else None)
        scale = Vector((0.5, 0.5, 0.5))
        shift = solver.aim_axis_shift(settings, shapes, [(0, hit(-0.01, 1.0)), (1, hit(0.3, 1.0))], scale)
        assert_vector(self, shift, (0.0, 0.0, 0.02))
        shift = solver.aim_axis_shift(settings, shapes, [(0, hit(-0.01, 1.0)), (2, hit(-0.01, 0.0))], scale)
        assert_vector(self, shift, (0.0, 0.0, 0.0))


class WristMathTest(unittest.TestCase):
    char = Quaternion((1.0, 0.0, 0.0), math.pi / 2.0)      # a character facing -Y, Z up

    def test_weights(self):
        hand = Euler((0.2, 0.4, -0.3)).to_quaternion()
        guitar = Euler((0.5, 0.1, 1.0)).to_quaternion()
        offset = Euler((0.3, 0.2, 0.1)).to_quaternion()
        same, _ = wrist.blend(hand, guitar, offset, 0.0, self.char, direction=0)
        self.assertLess(rotation_angle(same, hand), 1e-6)
        full, _ = wrist.blend(hand, guitar, offset, 1.0, self.char, direction=0)
        self.assertLess(rotation_angle(full, guitar @ offset), 1e-5)
        half, _ = wrist.blend(hand, guitar, offset, 0.5, self.char, direction=0)
        self.assertAlmostEqual(rotation_angle(half, hand), 0.5 * rotation_angle(hand, guitar @ offset), places=4)

    def test_axis_rot(self):
        """On an A-pose rig the offset is for the T-pose-aligned hand frame, Q_hand @ axis_rot."""
        axis_rot = Quaternion((0.0, 0.0, 1.0), math.radians(-35.0))
        hand, guitar = Euler((1.2, -0.4, 0.3)).to_quaternion(), Euler((0.5, 0.1, 1.0)).to_quaternion()
        offset = wrist.capture(guitar, hand, axis_rot)
        self.assertLess(rotation_angle(guitar @ offset, hand @ axis_rot), 1e-5)
        self.assertLess(rotation_angle(wrist.target_frame(guitar, offset, axis_rot), hand), 1e-5)
        full, _ = wrist.blend(hand.slerp(guitar, 0.3), guitar, offset, 1.0, self.char, axis_rot=axis_rot)
        self.assertLess(rotation_angle(full, hand), 1e-5)

    def test_capture_round_trip(self):
        hand, guitar = Euler((1.2, -0.4, 0.3)).to_quaternion(), Euler((0.5, 0.1, 1.0)).to_quaternion()
        offset = wrist.capture(guitar, hand)
        self.assertLess(rotation_angle(wrist.target_frame(guitar, offset), hand), 1e-6)
        turned = Euler((0.0, 0.4, -0.2)).to_quaternion() @ guitar       # the offset stays with the guitar
        self.assertLess(rotation_angle(wrist.target_frame(turned, offset), turned @ guitar.inverted() @ hand), 1e-5)

    def test_constrained_yaw(self):
        """SAO's constrained direction: a yaw difference over 120° turns the negative way, not the shorter way."""
        g = Euler((0.1, math.radians(-10.0), 0.05), 'ZXY').to_quaternion()
        d = Euler((0.0, math.radians(150.0), 0.0), 'ZXY').to_quaternion()     # 160° away, the short way +
        result, constrained = wrist.constrained_blend(g, d, 0.5, -1)
        self.assertTrue(constrained)
        # Half of the 200° the negative way; blending pitch and roll adds a trace of yaw.
        self.assertAlmostEqual(math.degrees(result.to_euler('ZXY').y), -110.0, delta=0.5)
        free, constrained = wrist.constrained_blend(g, d, 0.5, 0)
        self.assertFalse(constrained)
        self.assertAlmostEqual(math.degrees(free.to_euler('ZXY').y), 70.0, delta=2.0)
        # At full weight it is the target either way.
        full, _ = wrist.constrained_blend(g, d, 1.0, -1)
        self.assertLess(rotation_angle(full, d), 1e-5)
        # Within 120° the blend is a plain slerp.
        near = Euler((0.0, math.radians(60.0), 0.0), 'ZXY').to_quaternion()
        result, constrained = wrist.constrained_blend(g, near, 0.5, -1)
        self.assertFalse(constrained)
        self.assertLess(rotation_angle(result, g.slerp(near, 0.5)), 1e-6)

    def test_format_1_presets(self):
        """Presets saved before format 2 stored the wrist offset for SAO's tracking frame and apply_axis_rot off."""
        preset = presets.load("acoustic")
        data = dict(preset.raw, format=1, wrist={"rotation": list(presets.sao_euler_xyz((60.0, 180.0, 0.0))),
                                                 "weight": 0.5})
        data["magnets"] = [dict(m, apply_axis_rot=False) for m in preset.raw["magnets"]]
        os.makedirs(TMP_DIR, exist_ok=True)
        path = os.path.join(TMP_DIR, "format_1_preset.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        frame = Quaternion(preset.raw["frame"])        # the preset's axes -> the guitar frame
        old = presets.load(path)
        self.assertLess(rotation_angle(old.wrist_offset, frame @ presets.sao_wrist((60.0, 180.0, 0.0))), 1e-5)
        self.assertLess(rotation_angle(old.wrist_offset, preset.wrist_offset), 1e-5)
        self.assertTrue(all("apply_axis_rot" not in m for m in old.magnets))
        data["format"] = 2
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        new = presets.load(path)
        self.assertLess(rotation_angle(new.wrist_offset, frame @ presets.sao_euler_xyz((60.0, 180.0, 0.0))), 1e-5)
        self.assertTrue(all(m["apply_axis_rot"] is False for m in new.magnets))

    def test_sao_offset(self):
        """SAO's (60°, 180°, 0°) puts the fretting palm facing the neck with the fingers across the fretboard."""
        offset = presets.sao_wrist((60.0, 180.0, 0.0))
        fingers = offset @ Vector((1.0, 0.0, 0.0))
        thumb_side = offset @ Vector((0.0, 0.0, 1.0))
        assert_vector(self, fingers, (0.0, 0.5, math.sqrt(0.75)), 5)
        assert_vector(self, thumb_side, (1.0, 0.0, 0.0), 5)        # toward the headstock


class FingertipMathTest(unittest.TestCase):
    """Fingertip v2 on the plane z = 1 (normal +Z)."""

    def test_snap_puts_the_lowest_tip_at_the_margin(self):
        tips = [Vector((0.1, 0.0, -0.3)), Vector((0.1, 0.02, -0.2))]
        point = Vector((0.0, 0.0, 1.4))
        new, hit = magnets.pull(point, PLANE, magnets.Params(1.0, power=1.0), tips=[point + t for t in tips],
                                margin=0.02)
        # The point snaps onto the plane, and the hand is shifted so that the lowest tip (0.3 below the point)
        # ends 0.02 above the plane.
        self.assertAlmostEqual(new.z - 0.3, 1.0 + 0.02, places=6)
        self.assertAlmostEqual(hit.shift, (0.1 - 0.02) - 0.4, places=6)

    def test_push_only(self):
        barrier = magnets.Params(0.3, power=-99.0, crossable=False)
        low, high = Vector((0.0, 0.0, -0.1)), Vector((0.0, 0.0, 0.1))
        # Tips above the point (less the margin): push-only leaves the point alone, near or far.
        for z in (1.05, 1.5):
            point = Vector((0.0, 0.0, z))
            new, hit = magnets.pull(point, PLANE, barrier, tips=[point + high], margin=0.02, push_only=True)
            assert_vector(self, new, point)
            self.assertEqual(hit.shift, 0.0)
        # Tips hanging below it: the hand is lifted so that the lowest tip is level with the point plus the
        # margin, however far in front of the barrier it is (SAO shifts whatever the weight)...
        for z in (1.05, 1.5):
            point = Vector((0.0, 0.0, z))
            new, _ = magnets.pull(point, PLANE, barrier, tips=[point + low], margin=0.02, push_only=True)
            self.assertAlmostEqual(new.z + low.z, z + 0.02, places=6)
        # ...and behind it, the point is clamped onto the plane with the lowest tip at the margin.
        point = Vector((0.0, 0.0, 0.95))
        new, _ = magnets.pull(point, PLANE, barrier, tips=[point + low], margin=0.02, push_only=True)
        self.assertAlmostEqual(new.z + low.z, 1.02, places=6)
        # Without push-only the hand also moves toward the plane: the tip is level with the point again.
        point = Vector((0.0, 0.0, 1.5))
        new, _ = magnets.pull(point, PLANE, barrier, tips=[point + high], margin=0.02)
        self.assertAlmostEqual(new.z + high.z, 1.5 + 0.02, places=6)


def tip_heights(obj, side, point, normal, fingers=('INDEX', 'MIDDLE', 'RING')):
    """{finger: signed height of its calibrated fingertip above the plane} in the current pose."""
    bpy.context.view_layer.update()
    heights = {}
    for tip in obj.gtr_char.calibration.fingertips:
        if tip.side == side and tip.finger in fingers:
            world = obj.matrix_world @ (obj.pose.bones[tip.bone].matrix @ Vector(tip.tip_local))
            heights[tip.finger] = (world - point).dot(normal)
    return heights


def point_fingers(obj, side, direction):
    """Turn the hand of `side` so that its fingers (wrist to middle fingertip) point along `direction`."""
    bpy.context.view_layer.update()
    hand = chain(obj, side)[2]
    tip = next(t for t in obj.gtr_char.calibration.fingertips if t.side == side and t.finger == 'MIDDLE')
    head = rigs.world_head(obj, hand)
    fingers = obj.matrix_world @ (obj.pose.bones[tip.bone].matrix @ Vector(tip.tip_local)) - head
    rigs.rotate_bone(obj, hand, fingers.rotation_difference(direction))


class FollowSolveTest(unittest.TestCase):
    def setUp(self):
        self.obj, self.root = setup_scene()
        self.settings = bpy.context.scene.gtr
        self.scene = bpy.context.scene
        self.cal = self.obj.gtr_char.calibration

    def magnet(self, preset_id):
        return next(item for item in self.settings.magnets if item.preset_id == preset_id)

    def margin(self, item):
        """The fingertip margin of a magnet in metres, as the solver computes it."""
        return (item.fingertip_offset_m * self.root.matrix_world.to_scale()[0]
                + self.settings.palm_margin_m * self.cal.ratio_arm)

    def pose_fretting(self):
        """Put the left hand near the neck of the mounted guitar, away from where the neck points."""
        assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
        bpy.context.view_layer.update()
        found = landmarks.find(self.root)
        nut = found["NUT"].matrix_world.translation
        pivot = found["NECK_PIVOT"].matrix_world.translation
        target = pivot.lerp(nut, 0.5) + Vector((0.0, -0.05, 0.08))
        rigs.reach(self.obj, *chain(self.obj, 'L'), target, Vector((0.0, 0.5, -1.0)))

    def test_follow_aims_and_converges(self):
        self.pose_fretting()
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(self.scene)
        self.assertIsNotNone(result.neck)
        self.assertTrue(result.converged, result.messages)
        self.assertGreater(result.swing, math.radians(1.0))
        self.assertLessEqual(result.iterations, self.settings.iterations + 1)
        # The guitar the rig shows is the aimed one, aimed at the solved hand's aim point.
        self.assertLess(rotation_angle(self.root.matrix_world.to_quaternion(), result.guitar.rotation), 1e-4)
        cal = calibrate.load(self.cal)
        rig = build.find(self.settings)
        arm = solver.sample_arm(self.obj, rig.chains['L'], cal.char_frame, 0.0)
        target = solver.aim_target(self.obj, rig.chains['L'], arm, self.settings, cal)
        self.assertLess((target - result.neck.target).length, 1e-5)
        mounted = solver.mount_pose(self.obj, cal, self.settings, self.root)
        a, p = solver.aim_axis(self.root)
        shift = solver.aim_axis_shift(self.settings, solver.magnet_shapes(self.root, self.settings.magnets)[0],
                                      result.sides['L'].hits, mounted.scale)
        again = aim.aim(mounted, a + shift, p + shift, target, self.settings.aim_max_swing, self.settings.aim_weight)
        self.assertLess(rotation_angle(again.rotation, result.guitar.rotation), solver.TOLERANCE_ANGLE)
        # The fretting wrist turned toward the guitar, and the picking wrist kept its mocap rotation.
        self.assertGreater(result.wrist_turn, math.radians(1.0))
        hand = self.obj.pose.bones[chain(self.obj, 'R')[2]]
        self.assertLess(rotation_angle((self.obj.matrix_world @ hand.matrix).to_quaternion(),
                                       arm_rotation_fk(self, 'R')), 1e-4)

    def test_align_does_not_aim(self):
        self.settings.mode = 'ALIGN'
        self.pose_fretting()
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(self.scene)
        self.assertIsNone(result.neck)
        self.assertLess(result.swing, 1e-4)

    def test_relax_takes_more_passes(self):
        self.pose_fretting()
        passes = {}
        for relax in (1.0, 0.5):
            self.settings.relax = relax
            passes[relax] = solver.solve(bpy.context, build.find(self.settings), iterations=12).iterations
        self.assertGreater(passes[0.5], passes[1.0])

    def test_string_barrier_fingertips(self):
        """SAO's string barrier (push-only fingertips) on the picking hand, its fingers pointing at the strings."""
        self.settings.aim_enabled = False       # the string plane turns with the aimed guitar
        for item in self.settings.magnets:
            item.enabled = item.preset_id == "STRING_BARRIER"
        found = mounted_landmarks(self.root)
        a, b = found["STRUM_A"][0], found["STRUM_B"][0]
        point, normal = found["STRING_PLANE"]
        margin = self.margin(self.magnet("STRING_BARRIER"))
        for height in (-0.02, 0.05):
            with self.subTest(height=height):
                build.deactivate(self.settings)         # pose the FK arm, not the solved one
                rigs.reach(self.obj, *chain(self.obj, 'R'), (a + b) * 0.5 + normal * height,
                           Vector((0.0, 0.5, -1.0)))
                point_fingers(self.obj, 'R', (-normal + (b - a).normalized() * 0.3).normalized())
                fk = (rigs.world_head(self.obj, chain(self.obj, 'R')[2]) - point).dot(normal)
                self.assertLess(min(tip_heights(self.obj, 'R', point, normal).values()), fk - 0.1)
                assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
                lowest = min(tip_heights(self.obj, 'R', point, normal).values())
                # Behind the plane: the lowest tip at the margin. In front: level with the wrist plus the margin.
                self.assertAlmostEqual(lowest, max(fk, 0.0) + margin, delta=TOLERANCE)

    def test_no_finger_bones(self):
        """Without finger bones, a fingertip magnet keeps the hand point itself the palm margin from its plane."""
        bone_map = self.obj.gtr_char.bone_map
        for finger in ("index", "middle", "ring"):
            for part in ("proximal", "intermediate", "distal"):
                setattr(bone_map, f"{finger}_{part}_R", "")
        bpy.context.view_layer.objects.active = self.obj
        assert bpy.ops.gtr.calibrate() == {'FINISHED'}
        self.assertFalse(any(tip.side == 'R' for tip in self.cal.fingertips))
        self.settings.aim_enabled = False
        for item in self.settings.magnets:
            item.enabled = item.preset_id == "STRING_BARRIER"
        found = mounted_landmarks(self.root)
        point, normal = found["STRING_PLANE"]
        middle = (found["STRUM_A"][0] + found["STRUM_B"][0]) * 0.5
        margin = self.settings.palm_margin_m * self.cal.ratio_arm
        for height in (-0.03, 0.05):
            with self.subTest(height=height):
                build.deactivate(self.settings)
                rigs.reach(self.obj, *chain(self.obj, 'R'), middle + normal * height, Vector((0.0, 0.5, -1.0)))
                fk = (rigs.world_head(self.obj, chain(self.obj, 'R')[2]) - point).dot(normal)
                self.assertAlmostEqual(fk, height, delta=0.01)
                assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
                result = solver.shown_result(self.scene)
                self.assertFalse(result.sides['R'].clamped)
                solved = (rigs.world_head(self.obj, chain(self.obj, 'R')[2]) - point).dot(normal)
                self.assertAlmostEqual(solved, max(fk, 0.0) + margin, delta=TOLERANCE)

    def test_fretboard_fingertips(self):
        """SAO's fretboard snap with fingertips: the lowest fingertip ends the margin above the fretboard."""
        self.settings.aim_enabled = False
        self.settings.wrist_blend = 0.0
        found, _, _ = pose_left(self.obj, self.root, 0.06, 0.04)
        point, normal = found["FRETBOARD_PLANE"]
        point_fingers(self.obj, 'L', (-normal + found["FRETBOARD_EDGE"][1]).normalized())
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        heights = tip_heights(self.obj, 'L', point, normal)
        self.assertAlmostEqual(min(heights.values()), self.margin(self.magnet("FRETBOARD_PLANE")), delta=TOLERANCE)
        result = solver.shown_result(self.scene)
        index = list(self.settings.magnets).index(self.magnet("FRETBOARD_PLANE"))
        self.assertNotEqual(result.hit(index).shift, 0.0)

    def test_capture_wrist_offset(self):
        self.pose_fretting()
        rigs.rotate_bone(self.obj, chain(self.obj, 'L')[2], Quaternion((0.2, 0.9, 0.1), 0.7))
        cal = calibrate.load(self.cal)
        self.root.matrix_world = solver.mount_pose(self.obj, cal, self.settings, self.root).matrix()
        assert bpy.ops.gtr.capture_wrist_offset() == {'FINISHED'}
        self.assertEqual(self.settings.wrist_source, 'CAPTURE')
        # With full blend and the guitar left on its mount, the solved hand keeps the captured pose.
        self.settings.mode = 'ALIGN'
        self.settings.wrist_blend = 1.0
        for item in self.settings.magnets:
            item.enabled = False
        hand = self.obj.pose.bones[chain(self.obj, 'L')[2]]
        bpy.context.view_layer.update()
        before = (self.obj.matrix_world @ hand.matrix).to_quaternion()
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        bpy.context.view_layer.update()
        self.assertLess(rotation_angle((self.obj.matrix_world @ hand.matrix).to_quaternion(), before), 1e-3)
        # A new preset keeps the captured offset by default, and a flip keeps it on the guitar.
        offset = Quaternion(self.settings.wrist_offset)
        assert bpy.ops.gtr.load_preset('INVOKE_DEFAULT') == {'FINISHED'}
        self.assertLess(rotation_angle(Quaternion(self.settings.wrist_offset), offset), 1e-5)
        target = wrist.target_frame(self.root.matrix_world.to_quaternion(), self.settings.wrist_offset)
        assert bpy.ops.gtr.flip_frame(axis='Z') == {'FINISHED'}
        flipped = wrist.target_frame(self.root.matrix_world.to_quaternion(), self.settings.wrist_offset)
        self.assertLess(rotation_angle(flipped, target), 1e-4)


class RobustnessTest(unittest.TestCase):
    def test_random_poses_converge(self):
        """Random fretting and strumming poses and hand turns: every FOLLOW solve settles within the iterations,
        and the IK reaches every wrist target."""
        obj, root = setup_scene()
        settings = bpy.context.scene.gtr
        rng = random.Random(1)
        results = []
        for _ in range(20):
            build.deactivate(settings)
            found = {role: point for role, (point, _) in mounted_landmarks(root).items()}
            left = found["NECK_PIVOT"].lerp(found["NUT"], rng.uniform(-0.1, 1.0))
            right = found["STRUM_A"].lerp(found["STRUM_B"], rng.uniform(0.0, 1.0))
            for side, point in (('L', left), ('R', right)):
                point = point + Vector([rng.uniform(-0.12, 0.12) for _ in range(3)])
                rigs.reach(obj, *chain(obj, side), point, Vector((rng.uniform(-0.3, 0.3), 0.5, -1.0)))
                turn = Quaternion(Vector([rng.uniform(-1.0, 1.0) for _ in range(3)]), rng.uniform(0.0, 2.0))
                rigs.rotate_bone(obj, chain(obj, side)[2], turn)
            results.append(solver.solve(bpy.context, build.find(settings)))
        self.assertTrue(all(result.converged for result in results), [r.iterations for r in results])
        self.assertTrue(all(side.error < solver.TOLERANCE_M for r in results for side in r.sides.values()))
        self.assertGreater(max(result.swing for result in results), math.radians(10.0))


class UnitTest(unittest.TestCase):
    def solve_at(self, unit):
        """The FOLLOW solve of one fretting pose in a scene with `unit` scene units per metre."""
        obj, root = setup_scene(unit)
        found = mounted_landmarks(root)
        target = found["NECK_PIVOT"][0].lerp(found["NUT"][0], 0.5) + Vector((0.0, -0.05, 0.08)) * unit
        rigs.reach(obj, *chain(obj, 'L'), target, Vector((0.0, 0.5, -1.0)))
        rigs.rotate_bone(obj, chain(obj, 'L')[2], Quaternion((0.3, -0.2, 0.9), 0.8))
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        return solver.shown_result(bpy.context.scene)

    def test_centimetres(self):
        """The aim, the wrist blend and the fingertips give the same result in a centimetre scene."""
        metres, centimetres = self.solve_at(1.0), self.solve_at(100.0)
        self.assertTrue(centimetres.converged)
        self.assertGreater(metres.swing, math.radians(1.0))
        self.assertAlmostEqual(centimetres.swing, metres.swing, delta=1e-3)
        self.assertAlmostEqual(centimetres.wrist_turn, metres.wrist_turn, delta=1e-3)
        for side in "LR":
            moved = [(r.sides[side].target - r.sides[side].fk_wrist).length / unit
                     for r, unit in ((metres, 1.0), (centimetres, 100.0))]
            self.assertAlmostEqual(moved[1], moved[0], delta=1e-4)


class InterfaceTest(unittest.TestCase):
    def test_panels_and_overlay(self):
        obj, root = setup_scene()
        labels = []
        for cls in panels.CLASSES:
            if getattr(cls, "poll", None) is None or cls.poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        self.assertIn("Neck Aim", labels)
        self.assertIn("Wrist", labels)
        rigs.reach(obj, *chain(obj, 'L'), mounted_landmarks(root)["NUT"][0], Vector((0.0, 0.5, -1.0)))
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        labels = []
        for cls in panels.CLASSES:
            if getattr(cls, "poll", None) is None or cls.poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        for label in ("Neck swing", "Fretting wrist", "Passes", "Preset"):
            self.assertIn(label, labels)
        # The overlay draws the aim: from the neck pivot to the aim point on the hand.
        result = solver.shown_result(bpy.context.scene)
        lines, _, _, _ = overlay.build_geometry(bpy.context)
        pairs = list(zip(lines[0::2], lines[1::2]))
        self.assertTrue(any((a - result.neck.axis_origin).length < 1e-6 and (b - result.neck.target).length < 1e-6
                            for a, b in pairs))


def arm_rotation_fk(test, side):
    """The FK world rotation of the IK hand of `side`, with the rig switched off (the solve is left shown)."""
    rig = build.find(test.settings)
    obj = test.obj
    hand = obj.pose.bones[chain(obj, side)[2]]
    influences = [(con, con.influence) for con in (rig.ik[side], rig.bend[side], rig.wrist[side])]
    for con, _ in influences:
        con.influence = 0.0
    bpy.context.view_layer.update()
    rotation = (obj.matrix_world @ hand.matrix).to_quaternion()
    for con, value in influences:
        con.influence = value
    bpy.context.view_layer.update()
    return rotation


class CrossRigWristTest(unittest.TestCase):
    """SAO's wrist offset puts the fretting hand in the same place on the guitar on T-pose and A-pose rigs."""

    def hand_on_guitar(self, build_rig):
        obj, root = setup_scene(build_rig=build_rig)
        settings = bpy.context.scene.gtr
        settings.mode = 'ALIGN'
        settings.wrist_blend = 1.0
        for item in settings.magnets:
            item.enabled = False
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        bpy.context.view_layer.update()
        tips = {t.finger: obj.matrix_world @ (obj.pose.bones[t.bone].matrix @ Vector(t.tip_local))
                for t in obj.gtr_char.calibration.fingertips if t.side == 'L'}
        head = rigs.world_head(obj, chain(obj, 'L')[2])
        to_guitar = root.matrix_world.to_quaternion().inverted()
        return (to_guitar @ (tips['MIDDLE'] - head)).normalized(), (to_guitar @ (tips['INDEX'] - tips['RING'])).normalized()

    def test_t_and_a_pose(self):
        fingers_t, across_t = self.hand_on_guitar(None)
        fingers_a, across_a = self.hand_on_guitar(rigs.mmd)
        offset = Quaternion(bpy.context.scene.gtr.wrist_offset)
        # The fingers run along the T-pose-aligned frame's X, and the index side is its Z.
        self.assertLess(fingers_t.angle(offset @ Vector((1.0, 0.0, 0.0))), 1e-3)
        self.assertLess(fingers_a.angle(fingers_t), 1e-3)
        self.assertLess(across_a.angle(across_t), 1e-2)


class NeckContactTest(unittest.TestCase):
    """Follow with the neck aim at Max Swing: the fretting wrist covers the distance the limit leaves."""

    setUp = FollowSolveTest.setUp
    magnet = FollowSolveTest.magnet
    margin = FollowSolveTest.margin
    pose_fretting = FollowSolveTest.pose_fretting

    def solve(self, max_swing=None):
        if max_swing is not None:
            self.settings.aim_max_swing = math.radians(max_swing)
        result = solver.solve(bpy.context, build.find(self.settings))
        bpy.context.view_layer.update()
        return result

    def local_axis(self, result, scale):
        """The ends of the neck axis in GTR_ROOT space, shifted as the fretting hand's fingertip magnet has it."""
        a, p = solver.aim_axis(self.root)
        shift = solver.aim_axis_shift(self.settings, solver.magnet_shapes(self.root, self.settings.magnets)[0],
                                      result.sides['L'].hits, scale)
        return a + shift, p + shift

    def evaluated_gap(self, result):
        """The distance of the evaluated hand's aim point from the neck line of the guitar the rig shows."""
        cal = calibrate.load(self.cal)
        links = build.find(self.settings).chains['L']
        arm = solver.sample_arm(self.obj, links, cal.char_frame, 0.0)
        point = solver.aim_target(self.obj, links, arm, self.settings, cal)
        shown = self.root.matrix_world
        a, p = self.local_axis(result, shown.to_scale())
        start, end = shown @ a, shown @ p
        along = (end - start).normalized()
        return ((point - start) - along * (point - start).dot(along)).length

    def expected_move(self, result):
        """The move across the shown neck for what the limit added, recomputed from this solve's aim."""
        mounted = solver.mount_pose(self.obj, calibrate.load(self.cal), self.settings, self.root)
        a, p = self.local_axis(result, mounted.scale)
        return aim.limit_move(mounted, result.guitar.rotation, a, p, result.neck.target, self.settings.aim_max_swing,
                              self.settings.aim_weight)

    def transforms(self, result):
        points = [getattr(result.sides[side], name).copy() for side in "LR" for name in ("wrist", "elbow")]
        return points + [result.guitar.location.copy()], result.guitar.rotation.copy()

    def assert_same(self, first, second):
        for one, other in zip(first[0], second[0]):
            self.assertLess((one - other).length, 1e-5)
        self.assertLess(rotation_angle(first[1], second[1]), 1e-5)

    def test_wrist_covers_what_the_limit_leaves(self):
        self.pose_fretting()
        free = self.solve()
        self.assertFalse(free.neck.clamped)
        self.assertIsNone(free.neck_contact)
        self.assertGreater(free.swing, math.radians(15.0))
        result = self.solve(8.0)
        self.assertTrue(result.neck.clamped)
        self.assertLessEqual(math.degrees(result.swing), 8.05)
        self.assertTrue(result.converged, result.messages)
        contact = result.neck_contact
        self.assertIsNotNone(contact)
        self.assertIsNone(contact.limit)
        self.assertGreater(contact.moved.length, 0.04)
        self.assertLess((contact.moved - self.expected_move(result)).length, 1e-5)
        # The evaluated hand is on the shown neck line, as near as the unlimited aim leaves it; the result says so.
        gap = self.evaluated_gap(result)
        self.assertLess(gap, 0.005)
        self.assertAlmostEqual(result.neck_gap, gap, places=5)
        self.assertLess(abs(gap - free.neck_gap), 0.001)
        self.assertLess(result.sides['L'].error, 2e-5)
        # The fingertips clear the shown fretboard by the magnet's margin.
        plane = landmarks.find(self.root)["FRETBOARD_PLANE"].matrix_world
        normal = (plane.to_3x3().inverted().transposed() @ Vector((0.0, 0.0, 1.0))).normalized()
        lowest = min(tip_heights(self.obj, 'L', plane.translation, normal).values())
        self.assertLess(abs(lowest - self.margin(self.magnet("FRETBOARD_PLANE"))), 0.005)
        texts = [text for _, text in result.messages]
        self.assertTrue(any("the fretting wrist moved" in text for text in texts), texts)
        self.assertIn("neck contact", solver.summary(result, self.settings.magnets))

    def test_nothing_changes_without_the_limit(self):
        """Below the limit, in Align and with the Fretboard Plane off, the solve is the one without the contact."""
        self.pose_fretting()

        def both(max_swing):
            result = self.solve(max_swing)
            self.assertIsNone(result.neck_contact)
            with mock.patch.object(aim, "limit_move", side_effect=lambda *args: Vector((0.0, 0.0, 0.0))):
                self.assert_same(self.transforms(result), self.transforms(self.solve(max_swing)))
            return result
        result = both(35.0)
        self.assertFalse(result.neck.clamped)
        self.assertIsNotNone(result.neck_gap)
        self.magnet("FRETBOARD_PLANE").enabled = False
        result = both(8.0)
        self.assertTrue(result.neck.clamped)
        self.assertTrue(any("the fretting hand is far from the neck" in text for _, text in result.messages))
        self.magnet("FRETBOARD_PLANE").enabled = True
        self.settings.mode = 'ALIGN'
        result = both(8.0)
        self.assertIsNone(result.neck)
        self.assertIsNone(result.neck_gap)

    def test_grows_from_zero_past_the_limit(self):
        self.pose_fretting()
        free = self.solve()
        swing = math.degrees(free.swing)
        moved = []
        for under in (0.1, 0.5, 1.0, 2.0, 4.0):
            result = self.solve(swing - under)
            moved.append(result.neck_contact.moved.length)
            if under == 0.1:
                self.assertLess(moved[0], 0.002)
                self.assertLess((result.sides['L'].wrist - free.sides['L'].wrist).length, 0.002)
        self.assertEqual(moved, sorted(moved))
        self.assertGreater(moved[-1], 0.015)
        for first, second, step in zip(moved, moved[1:], (0.4, 0.5, 1.0, 2.0)):
            self.assertLess(second - first, 0.012 * step)              # about 5 mm a degree on this neck

    def test_fades_with_the_aim_and_contact_weights(self):
        self.pose_fretting()
        moved = []
        for weight in (1.0, 0.75, 0.5, 0.25, 0.0):
            self.settings.aim_weight = weight
            result = self.solve(8.0)
            contact = result.neck_contact
            moved.append(0.0 if contact is None else contact.moved.length)
            if weight > 0.0:
                self.assertAlmostEqual(result.neck_gap, self.evaluated_gap(result), places=5)
        self.assertEqual(moved, sorted(moved, reverse=True))
        self.assertEqual(moved[-1], 0.0)
        self.assertGreater(moved[-2], 0.0)
        self.assertLess(max(one - other for one, other in zip(moved, moved[1:])), 0.5 * moved[0])
        # A Fretboard Plane that holds the hand at a part weight asks for that part of the move.
        self.settings.aim_weight = 1.0
        item = self.magnet("FRETBOARD_PLANE")
        item.power = 0.0
        result = self.solve(8.0)
        weight = result.hit(list(self.settings.magnets).index(item)).weight
        self.assertTrue(0.05 < weight < 0.95, weight)
        self.assertLess((result.neck_contact.moved - self.expected_move(result) * weight).length, 1e-5)

    def test_neck_beyond_reach(self):
        """The reach clamp holds the wrist short of the neck: the result reports the gap of the evaluated hand
        and what held it, though the wrist is on its (clamped) IK target."""
        self.pose_fretting()
        found = landmarks.find(self.root)
        neck = found["NECK_PIVOT"].matrix_world.translation.lerp(found["NUT"].matrix_world.translation, 0.5)
        names = chain(self.obj, 'L')
        rigs.reach(self.obj, *names, rigs.world_head(self.obj, names[0]).lerp(neck, 0.5), Vector((0.0, 0.5, -1.0)))
        self.settings.reach_clamp = 0.5
        cal = calibrate.load(self.cal)
        mocap = solver.sample_arm(self.obj, build.find(self.settings).chains['L'], cal.char_frame, 0.0)
        result = self.solve(2.0)
        left = result.sides['L']
        self.assertTrue(left.clamped)
        self.assertEqual(result.neck_contact.limit, 'REACH')
        allowed = max(0.5 * mocap.length, (mocap.wrist - mocap.shoulder).length)
        self.assertLess((left.wrist - mocap.shoulder).length, allowed + 1e-4)
        self.assertLess(left.error, 2e-5)
        gap = self.evaluated_gap(result)
        self.assertGreater(gap, 0.01)
        self.assertAlmostEqual(result.neck_gap, gap, places=5)
        warnings = [text for level, text in result.messages if level == 'WARNING']
        self.assertTrue(any(f"The fretting hand is {gap * 100.0:.1f} cm from the neck" in text
                            and "the arm cannot reach further" in text for text in warnings), result.messages)

    def test_panel_and_overlay(self):
        self.pose_fretting()
        self.settings.aim_max_swing = math.radians(8.0)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(self.scene)
        labels = []
        for cls in panels.CLASSES:
            if getattr(cls, "poll", None) is None or cls.poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        self.assertIn("Neck contact", labels)
        target = result.sides['L'].target
        lines, _, _, _ = overlay.build_geometry(bpy.context)
        self.assertTrue(any((a - (target - result.neck_contact.moved)).length < 1e-6 and (b - target).length < 1e-6
                            for a, b in zip(lines[0::2], lines[1::2])))
