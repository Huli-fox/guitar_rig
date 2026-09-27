import math
import random
import unittest

import bpy
from mathutils import Euler, Quaternion, Vector

import rigs
from guitar_rig.core import calibrate, ik, solver
from guitar_rig.rig import build
from test_guitar import reset_scene


def prepare(build_rig, **kwargs):
    """A rig from tests/rigs.py, auto-mapped and calibrated, with both arms bent (character-frame rotations)."""
    obj = build_rig(**kwargs)
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
    assert bpy.ops.gtr.calibrate() == {'FINISHED'}
    cal = obj.gtr_char.calibration
    frame = calibrate.char_frame_world(Quaternion(cal.char_frame), obj.matrix_world)
    bone_map = obj.gtr_char.bone_map
    for side, sign in (('L', 1.0), ('R', -1.0)):
        turns = ((getattr(bone_map, f"chain_upper_arm_{side}"), Euler((0.4, 0.3 * sign, -1.0 * sign))),
                 (getattr(bone_map, f"chain_forearm_{side}"), Euler((0.2, -1.3 * sign, 0.1))),
                 (getattr(bone_map, f"chain_hand_{side}"), Euler((0.5, -0.3, 0.6 * sign))))
        for name, turn in turns:
            rigs.rotate_bone(obj, name, frame @ turn.to_quaternion() @ frame.inverted())
    return obj


def world(obj, name):
    return obj.matrix_world @ obj.pose.bones[name].matrix


class PoleMathTest(unittest.TestCase):
    def test_rest_pole_angle(self):
        rng = random.Random(2)
        for _ in range(20):
            axes = Euler([rng.uniform(-3.0, 3.0) for _ in range(3)]).to_matrix()
            arm = axes.col[1] + Vector([rng.uniform(-0.2, 0.2) for _ in range(3)])
            bend = Vector([rng.uniform(-1.0, 1.0) for _ in range(3)])
            angle = ik.rest_pole_angle(axes.col[0], axes.col[2], arm, bend)
            up = ik.up_axis(axes.col[0], axes.col[2], angle)
            a = arm.normalized()
            up_side, bend_side = up - a * up.dot(a), bend - a * bend.dot(a)
            self.assertGreater(up_side.normalized().dot(bend_side.normalized()), 1.0 - 1e-6)

    def test_pole_position(self):
        shoulder, elbow, tip = Vector((0.0, 0.0, 0.0)), Vector((0.3, 0.0, -0.1)), Vector((0.5, 0.0, 0.0))
        up = Vector((0.2, 0.0, -1.0))
        pole = ik.pole_position(shoulder, elbow, tip, up, tip, 0.2)
        self.assertLess((pole - Vector((0.3, 0.0, -0.2))).length, 1e-6)
        # A goal off the arm: the pole swings with the arm, at the same distance from the goal line.
        goal = Vector((0.0, 0.0, 0.5))
        pole = ik.pole_position(shoulder, elbow, tip, up, goal, 0.2)
        self.assertLess((pole - Vector((0.2, 0.0, 0.3))).length, 1e-6)
        # A bias turns the arm first: a half turn about the arm puts the pole on the other side.
        bias = Quaternion((1.0, 0.0, 0.0), math.pi)
        pole = ik.pole_position(shoulder, elbow, tip, up, tip, 0.2, bias)
        self.assertLess((pole - Vector((0.3, 0.0, 0.2))).length, 1e-6)

    def test_reach_clamp(self):
        point, clamped = ik.reach_clamp(Vector((3.0, 4.0, 0.0)), Vector(), 2.5)
        self.assertTrue(clamped)
        self.assertLess((point - Vector((1.5, 2.0, 0.0))).length, 1e-6)
        point, clamped = ik.reach_clamp(Vector((0.3, 0.4, 0.0)), Vector(), 2.5)
        self.assertFalse(clamped)
        # Never shorter than the FK arm.
        point, clamped = ik.reach_clamp(Vector((0.0, 3.0, 0.0)), Vector(), 2.5, 3.0)
        self.assertFalse(clamped)
        point, clamped = ik.reach_clamp(Vector((0.0, 4.0, 0.0)), Vector(), 2.5, 3.0)
        self.assertTrue(clamped)
        self.assertLess((point - Vector((0.0, 3.0, 0.0))).length, 1e-6)

    def test_seed_bend(self):
        shoulder, elbow, tip = Vector((0.0, 0.0, 0.0)), Vector((0.3, 0.0, 0.0)), Vector((0.55, 0.0, 0.0))
        up, forearm = Vector((0.0, 0.3, 1.0)), Euler((0.3, -0.2, 0.5)).to_quaternion()
        seed = ik.seed_bend(shoulder, elbow, tip, up, forearm, Vector((0.4, 0.0, 0.0)))
        # The seed goes after the forearm's own rotation and turns the tip away from the pole's side, in the plane
        # of the arm and that side, so the elbow is on the pole's side of the arm.
        turned = elbow + (forearm @ seed @ forearm.inverted()) @ (tip - elbow)
        side = up.normalized()
        self.assertAlmostEqual((tip - elbow).angle(turned - elbow), ik.SEED_BEND, places=5)
        self.assertLess(turned.dot(side), -1e-4)
        self.assertAlmostEqual(turned.dot(Vector((1.0, 0.0, 0.0)).cross(side)), 0.0, places=6)
        # No seed for a bent arm or a goal the straight arm reaches by turning.
        self.assertEqual(ik.seed_bend(shoulder, Vector((0.3, 0.0, 0.05)), tip, up, forearm, Vector((0.4, 0.0, 0.0))),
                         Quaternion())
        self.assertEqual(ik.seed_bend(shoulder, elbow, tip, up, forearm, Vector((0.0, 0.55, 0.0))), Quaternion())


class BuildTest(unittest.TestCase):
    def setUp(self):
        reset_scene()

    def test_every_rig(self):
        """The rig builds on every convention, leaves the pose alone while off, and reproduces it when on."""
        for build_rig in rigs.ALL_RIGS:
            with self.subTest(build_rig.__name__):
                reset_scene()
                obj = prepare(build_rig)
                before = rigs.pose_arrays(obj)
                assert bpy.ops.gtr.build_rig() == {'FINISHED'}
                settings = bpy.context.scene.gtr
                rig = build.find(settings)
                self.assertIsNotNone(rig)
                self.assertEqual(len(rig.collection.objects), len(build.ROLES))
                for side in "LR":
                    self.assertEqual(rig.ik[side].influence, 0.0)
                    self.assertEqual(rig.bend[side].influence, 0.0)
                    self.assertEqual(rig.wrist[side].influence, 0.0)
                    self.assertEqual(rig.ik[side].chain_count, rig.chains[side].count)
                bpy.context.view_layer.update()
                after = rigs.pose_arrays(obj)
                unit = rigs.RIG_UNITS[build_rig]
                for name, matrix in before.items():
                    self.assertLess(abs(after[name][0, :3, :3] - matrix[0, :3, :3]).max(), 1e-5, name)
                    self.assertLess(abs(after[name][0, :3, 3] - matrix[0, :3, 3]).max(), 1e-6 * unit, name)
                errors = solver.check_rig(bpy.context, rig)
                for side, pair in errors.items():
                    self.assertLess(max(pair), 1e-5, side)

    def test_ik_swings_the_fk_arm(self):
        """With the pole from ik.pole_position, the IK elbow stays in the FK arm's plane swung onto the goal."""
        rng = random.Random(9)
        for build_rig in rigs.ALL_RIGS:
            with self.subTest(build_rig.__name__):
                reset_scene()
                obj = prepare(build_rig)
                assert bpy.ops.gtr.build_rig() == {'FINISHED'}
                rig = build.find(bpy.context.scene.gtr)
                cal = calibrate.load(obj.gtr_char.calibration)
                arms = solver.sample_arms(bpy.context, rig, cal)
                for _ in range(4):
                    goals = {}
                    for side, arm in arms.items():
                        goal = arm.tip + Vector([rng.uniform(-0.1, 0.1) for _ in range(3)])
                        l1, l2 = (arm.elbow - arm.shoulder).length, (arm.tip - arm.elbow).length
                        if (goal - arm.shoulder).length > 0.97 * (l1 + l2):
                            goal = arm.shoulder + (goal - arm.shoulder).normalized() * 0.97 * (l1 + l2)
                        goals[side] = goal
                        solver.place_goal(rig, side, arm, goal, cal)
                    rig.set_active(True)
                    bpy.context.view_layer.update()
                    for side, arm in arms.items():
                        chain = rig.chains[side]
                        swing = (arm.tip - arm.shoulder).rotation_difference(goals[side] - arm.shoulder)
                        normal = (swing @ (arm.elbow - arm.shoulder)).cross(goals[side] - arm.shoulder).normalized()
                        elbow = world(obj, chain.forearm).translation
                        tip = obj.matrix_world @ obj.pose.bones[chain.forearm].tail
                        self.assertLess((tip - goals[side]).length, 1e-5)
                        self.assertLess(abs((elbow - arm.shoulder).dot(normal)), 1e-5)
                    rig.set_active(False)

    def test_straight_arm_shortens(self):
        """A straight FK arm (the rest T-pose) reaches a goal nearer than its tip, bending toward the pole."""
        for build_rig in rigs.ALL_RIGS:
            with self.subTest(build_rig.__name__):
                reset_scene()
                obj = build_rig()
                bpy.context.view_layer.objects.active = obj
                assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
                assert bpy.ops.gtr.calibrate() == {'FINISHED'}
                assert bpy.ops.gtr.build_rig() == {'FINISHED'}
                rig = build.find(bpy.context.scene.gtr)
                cal = calibrate.load(obj.gtr_char.calibration)
                arms = solver.sample_arms(bpy.context, rig, cal)
                goals = {}
                for side, arm in arms.items():
                    self.assertLess((arm.elbow - arm.shoulder).angle(arm.tip - arm.elbow), ik.STRAIGHT)
                    goals[side] = arm.shoulder + (arm.tip - arm.shoulder) * 0.9
                    solver.place_goal(rig, side, arm, goals[side], cal)
                rig.set_active(True)
                bpy.context.view_layer.update()
                scale = obj.matrix_world.to_scale()[0]
                for side, arm in arms.items():
                    chain = rig.chains[side]
                    tip = obj.matrix_world @ obj.pose.bones[chain.forearm].tail
                    # The IK converges a little less tightly from a near-straight start: well within the solver's
                    # tolerance (solver.TOLERANCE_M).
                    self.assertLess((tip - goals[side]).length, 5e-5 * scale * rigs.RIG_UNITS[build_rig])
                    direction = (goals[side] - arm.shoulder).normalized()
                    elbow = world(obj, chain.forearm).translation - arm.shoulder
                    pole = rig.helper("POLE", side).matrix_world.translation - arm.shoulder
                    elbow_side = elbow - direction * elbow.dot(direction)
                    pole_side = pole - direction * pole.dot(direction)
                    self.assertGreater(elbow_side.normalized().dot(pole_side.normalized()), 1.0 - 1e-4)

    def test_twist_bones_are_locked_and_restored(self):
        obj = prepare(rigs.mmd)
        twist = obj.pose.bones["左腕捩"]
        twist.lock_ik_y = True
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        self.assertEqual((twist.lock_ik_x, twist.lock_ik_y, twist.lock_ik_z), (True, True, True))
        self.assertEqual(build.find(bpy.context.scene.gtr).chains['L'].count, 3)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}         # rebuilding keeps the user's own locks
        assert bpy.ops.gtr.clean_rig() == {'FINISHED'}
        self.assertEqual((twist.lock_ik_x, twist.lock_ik_y, twist.lock_ik_z), (False, True, False))

    def test_clean(self):
        obj = prepare(rigs.vroid)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        coll = settings.rig_collection
        mine = bpy.data.objects.new("Mine", None)
        coll.objects.link(mine)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}         # a rebuild replaces, it does not stack
        names = [con.name for pbone in obj.pose.bones for con in pbone.constraints]
        self.assertEqual(sorted(names), sorted([build.BEND_NAME, build.IK_NAME, build.WRIST_NAME] * 2))
        assert bpy.ops.gtr.clean_rig() == {'FINISHED'}
        self.assertEqual([con for pbone in obj.pose.bones for con in pbone.constraints], [])
        self.assertEqual([o.name for o in coll.objects], ["Mine"])    # the collection stays for the user's object
        self.assertIsNone(settings.rig_collection)
        self.assertFalse(bpy.ops.gtr.clean_rig.poll())
        bpy.data.objects.remove(mine)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        coll = settings.rig_collection
        assert bpy.ops.gtr.clean_rig() == {'FINISHED'}
        self.assertNotIn(coll, list(bpy.data.collections))

    def test_stale_after_bone_map_change(self):
        obj = prepare(rigs.vroid)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        self.assertIsNotNone(build.find(settings))
        obj.gtr_char.bone_map.chain_forearm_L = "J_Bip_L_Hand"
        self.assertIsNone(build.find(settings))
        obj.gtr_char.bone_map.chain_forearm_L = "J_Bip_L_LowerArm"
        self.assertIsNotNone(build.find(settings))

    def test_refusals_and_warnings(self):
        obj = prepare(rigs.vroid)
        settings = bpy.context.scene.gtr
        obj.pose.ik_solver = 'ITASC'
        with self.assertRaises(RuntimeError):
            bpy.ops.gtr.build_rig()
        obj.pose.ik_solver = 'LEGACY'
        obj.gtr_char.bone_map.chain_hand_L = "J_Bip_R_Hand"
        with self.assertRaises(build.RigError):
            build.build(bpy.context, settings)
        obj.gtr_char.bone_map.chain_hand_L = "J_Bip_L_Hand"
        con = obj.pose.bones["J_Bip_L_UpperArm"].constraints.new('IK')
        _, messages = build.build(bpy.context, settings)
        self.assertTrue(any("own IK" in text for level, text in messages if level == 'WARNING'))
        con.mute = True
        _, messages = build.build(bpy.context, settings)
        self.assertEqual(messages, [])

    def test_root_bias_turns_the_elbow(self):
        """SAO's root_rotation turns the right arm before the IK: with the goal on the FK wrist, the elbow turns
        about the shoulder-wrist line by the bias, and the wrist stays."""
        obj = prepare(rigs.vroid)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        settings.use_right_root_bias = True
        rig = build.find(settings)
        cal = calibrate.load(obj.gtr_char.calibration)
        arm = solver.sample_arms(bpy.context, rig, cal)['R']
        bias = solver.root_bias(settings, 'R', arm)
        self.assertIsNotNone(bias)
        self.assertIsNone(solver.root_bias(settings, 'L', arm))
        solver.place_goal(rig, 'R', arm, arm.tip, cal, bias)
        rig.set_active(True)
        bpy.context.view_layer.update()
        direction = (arm.tip - arm.shoulder).normalized()
        turn = (bias @ direction).rotation_difference(direction) @ bias
        expected = arm.shoulder + turn @ (arm.elbow - arm.shoulder)
        chain = rig.chains['R']
        self.assertLess((world(obj, chain.forearm).translation - expected).length, 1e-5)
        self.assertLess((obj.matrix_world @ obj.pose.bones[chain.forearm].tail - arm.tip).length, 1e-5)
        self.assertGreater((expected - arm.elbow).length, 0.002)

    def test_frame_change_switches_the_rig_off(self):
        obj = prepare(rigs.vroid)
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        scene = bpy.context.scene
        settings = scene.gtr
        scene.frame_set(5)
        rig = build.find(settings)
        rig.set_active(True)
        settings.solve_active, settings.solve_frame = True, 5
        scene.frame_set(5)
        self.assertEqual(rig.ik['L'].influence, 1.0)
        scene.frame_set(6)
        self.assertFalse(settings.solve_active)
        self.assertEqual((rig.ik['L'].influence, rig.wrist['R'].influence), (0.0, 0.0))
