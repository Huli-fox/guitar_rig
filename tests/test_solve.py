import unittest
from types import SimpleNamespace

import bpy
from mathutils import Matrix, Quaternion, Vector

import guitars
import rigs
from guitar_rig.core import landmarks, magnets, solver
from guitar_rig.rig import build
from guitar_rig.ui import overlay, panels
from test_addon import FakeLayout
from test_guitar import normalize, reset_scene

TOLERANCE = 2e-5            # metres: the IK reaches its goal to about 1e-7 m, float32 adds the rest


def setup_scene(unit=1.0, build_rig=None, preset='acoustic'):
    """A character (VRoid, or `build_rig()`) and the synthetic guitar with `preset`, the rig built.
    `unit`: scene units per metre (100 for a centimetre scene). Returns the armature and GTR_ROOT."""
    reset_scene()
    scene = bpy.context.scene
    scene.unit_settings.scale_length = 1.0 / unit
    obj = rigs.vroid(unit=unit) if build_rig is None else build_rig()
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
    assert bpy.ops.gtr.calibrate() == {'FINISHED'}
    objects, _ = guitars.build(matrix=Matrix.Scale(unit, 4) @ guitars.world_placement())
    root = normalize(objects)
    scene.gtr.preset = preset
    assert bpy.ops.gtr.load_preset() == {'FINISHED'}
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.gtr.build_rig() == {'FINISHED'}
    return obj, root


def magnets_only(settings):
    """Leave only the M2 magnet geometry: no neck aim, no wrist blend and no fingertips."""
    settings.aim_enabled = False
    settings.wrist_blend = 0.0
    for item in settings.magnets:
        item.fingertip_mode = 'NONE'


def mounted_landmarks(root):
    """{role: (world point, world unit normal)} with the guitar on its mount in the current pose."""
    assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
    bpy.context.view_layer.update()
    found = {}
    for role, item in landmarks.find(root).items():
        m = item.matrix_world
        normal = (m.to_3x3().inverted().transposed() @ Vector((0.0, 0.0, 1.0))).normalized()
        found[role] = (m.translation.copy(), normal)
    return found


def chain(obj, side):
    bone_map = obj.gtr_char.bone_map
    return [getattr(bone_map, f"chain_{part}_{side}") for part in ("upper_arm", "forearm", "hand")]


def palm_point(obj):
    """The fretboard magnets' hand point on the left hand in the current pose: the wrist plus their PARENT_BONE
    offset (the aim hand offset), turned by axis_rot_L when the magnet applies it."""
    settings = bpy.context.scene.gtr
    cal = obj.gtr_char.calibration
    hand = obj.pose.bones[obj.gtr_char.bone_map.chain_hand_L]
    head, frame = overlay.rest_aligned_world(obj, hand, Quaternion(cal.char_frame))
    scale = magnets.offset_scale(settings.autoscale_policy, cal.ratio_arm, cal.ratio_palm) / cal.metres_per_bu
    item = next(m for m in settings.magnets if m.preset_id == "FRETBOARD_PLANE")
    axis_rot = Quaternion(cal.axis_rot_L) if item.apply_axis_rot else None
    return head + magnets.hand_offset(settings.aim_hand_offset, frame, scale, axis_rot)


def wrist(obj, side):
    bpy.context.view_layer.update()
    return rigs.world_head(obj, chain(obj, side)[2])


def pose_left(obj, root, offset_fret, offset_edge, along=0.25):
    """Pose the left arm so that its wrist is `along` metres up the neck from the neck pivot, off the edge line
    by the given amounts (metres) along the fretboard and edge normals. Returns the landmarks on the mounted guitar
    ({role: (point, normal)}), the neck pivot and the direction of the edge line."""
    found = mounted_landmarks(root)
    unit = 1.0 / bpy.context.scene.unit_settings.scale_length
    pivot, fret = found["FRETBOARD_PLANE"]
    _, edge = found["FRETBOARD_EDGE"]
    direction = fret.cross(edge).normalized()
    if direction.dot(found["NUT"][0] - pivot) < 0.0:
        direction.negate()
    target = pivot + (direction * along + fret * offset_fret + edge * offset_edge) * unit
    rigs.reach(obj, *chain(obj, 'L'), target, Vector((0.0, 0.5, -1.0)))
    return found, pivot, direction


class FretboardTest(unittest.TestCase):
    """The fretting hand against the acoustic preset's fretboard magnets (SAO magnets 3, 4 and 5)."""

    def pose_left(self, obj, root, offset_fret, offset_edge, along=0.25):
        return pose_left(obj, root, offset_fret, offset_edge, along)

    def expected_on_line(self, point, pivot, direction):
        return pivot + direction * (point - pivot).dot(direction)

    def expected_align(self, point, found):
        """SAO's result for full-weight fretboard and edge planes: onto one, then the other, in list order. The
        edge normal need not be square to the fretboard's, so this is not quite the line where they meet."""
        for role in ("FRETBOARD_PLANE", "FRETBOARD_EDGE"):
            origin, normal = found[role]
            point = point - normal * (point - origin).dot(normal)
        return point

    def check_align(self, unit):
        obj, root = setup_scene(unit)
        settings = bpy.context.scene.gtr
        settings.mode = 'ALIGN'
        magnets_only(settings)
        found, pivot, direction = self.pose_left(obj, root, 0.04, 0.03)
        mounted = root.matrix_world.copy()
        before = palm_point(obj)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(bpy.context.scene)
        self.assertIsNotNone(result)
        self.assertTrue(result.converged)
        after = palm_point(obj)
        tolerance = TOLERANCE * unit
        # The palm point slid onto the fretboard edge line, keeping its place along the neck.
        self.assertLess((after - self.expected_align(before, found)).length, tolerance)
        self.assertLess((after - self.expected_on_line(before, pivot, direction)).length, 0.001 * unit)
        self.assertGreater((after - before).length, 0.02 * unit)
        barrier, normal = found["NECK_BODY_BARRIER"]
        self.assertGreater((wrist(obj, 'L') - barrier).dot(normal), 0.0)
        # The guitar sits on its mount.
        for got, expected in zip(root.matrix_world, mounted):
            self.assertLess((Vector(got) - Vector(expected)).length, 1e-5 * unit)
        weights = {settings.magnets[i].preset_id: hit.weight for i, hit in result.sides['L'].hits}
        self.assertEqual((weights["FRETBOARD_PLANE"], weights["FRETBOARD_EDGE"]), (1.0, 1.0))

    def test_align(self):
        self.check_align(1.0)

    def test_align_in_centimetres(self):
        self.check_align(100.0)

    def test_follow_edge_is_a_barrier(self):
        obj, root = setup_scene()
        settings = bpy.context.scene.gtr
        self.assertEqual(settings.mode, 'FOLLOW')
        magnets_only(settings)
        # Below the edge plane: clamped onto it, like ALIGN.
        found, pivot, direction = self.pose_left(obj, root, 0.04, -0.12)
        before = palm_point(obj)
        edge_point, edge = found["FRETBOARD_EDGE"]
        self.assertLess((before - edge_point).dot(edge), 0.0)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        after = palm_point(obj)
        self.assertLess((after - self.expected_align(before, found)).length, TOLERANCE)
        # Above it: onto the fretboard plane only; the edge barrier does not act.
        assert bpy.ops.gtr.clear_solve() == {'FINISHED'}
        found, pivot, direction = self.pose_left(obj, root, 0.04, 0.10)
        before = palm_point(obj)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        after = palm_point(obj)
        fret_point, fret = found["FRETBOARD_PLANE"]
        self.assertLess((after - (before - fret * (before - fret_point).dot(fret))).length, TOLERANCE)
        self.assertGreater((after - edge_point).dot(edge), 0.05)

    def test_barrier_holds_the_wrist(self):
        """A wrist on the body side of the neck/body barrier is put on the barrier plane."""
        obj, root = setup_scene()
        bpy.context.scene.gtr.mode = 'ALIGN'
        magnets_only(bpy.context.scene.gtr)
        found, _, _ = self.pose_left(obj, root, 0.03, 0.02, along=0.0)
        barrier, normal = found["NECK_BODY_BARRIER"]
        self.assertLess((wrist(obj, 'L') - barrier).dot(normal), -0.05)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertLess(abs((wrist(obj, 'L') - barrier).dot(normal)), TOLERANCE)

    def test_nut_barrier_holds_the_wrist(self):
        """The ukulele preset's nut barrier (SAO magnet 6): a wrist past it toward the headstock is put on it."""
        obj, root = setup_scene(preset='ukulele')
        bpy.context.scene.gtr.mode = 'ALIGN'
        magnets_only(bpy.context.scene.gtr)
        found, pivot, direction = self.pose_left(obj, root, 0.03, 0.02)
        barrier, normal = found["NUT_BARRIER"]
        along = (barrier - pivot).dot(direction) + 0.04
        self.pose_left(obj, root, 0.03, 0.02, along=along)
        self.assertLess((wrist(obj, 'L') - barrier).dot(normal), -0.03)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertLess(abs((wrist(obj, 'L') - barrier).dot(normal)), TOLERANCE)
        result = solver.shown_result(bpy.context.scene)
        weights = {bpy.context.scene.gtr.magnets[i].preset_id: hit.weight for i, hit in result.sides['L'].hits}
        self.assertEqual(weights["NUT_BARRIER"], 1.0)

    def test_offset_hand_converges(self):
        """A hand that does not start at the forearm tail: the IK goal is corrected over the iterations."""
        reset_scene()
        obj = rigs.vroid()
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        hand = obj.data.edit_bones["J_Bip_L_Hand"]
        hand.use_connect = False
        hand.head += Vector((0.0, -0.02, 0.015))
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.name = "VRoid Offset"
        assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
        assert bpy.ops.gtr.calibrate() == {'FINISHED'}
        objects, _ = guitars.build(matrix=guitars.world_placement())
        root = normalize(objects)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        bpy.context.view_layer.objects.active = obj
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        bpy.context.scene.gtr.mode = 'ALIGN'
        magnets_only(bpy.context.scene.gtr)
        found, pivot, direction = self.pose_left(obj, root, 0.04, 0.03)
        before = palm_point(obj)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        result = solver.shown_result(bpy.context.scene)
        self.assertTrue(result.converged)
        self.assertGreater(result.iterations, 1)
        self.assertLess((palm_point(obj) - self.expected_align(before, found)).length, 1e-4)


class StrumTest(unittest.TestCase):
    """The picking hand against the strum line, the strum position plane and the string barrier (SAO 0-2),
    recomputed here from the landmark empties with SAO's formulas."""

    def test_right_hand(self):
        obj, root = setup_scene()
        settings = bpy.context.scene.gtr
        magnets_only(settings)
        found = mounted_landmarks(root)
        a, b = found["STRUM_A"][0], found["STRUM_B"][0]
        string_point, string_normal = found["STRING_PLANE"]
        start = (a + b) * 0.5 + string_normal * 0.06 + (b - a).normalized() * 0.03
        rigs.reach(obj, *chain(obj, 'R'), start, Vector((0.0, 0.5, -1.0)))
        fk = wrist(obj, 'R')

        ratio = obj.gtr_char.calibration.ratio_arm
        reach = {m.preset_id: m.effective_distance_m * ratio for m in settings.magnets}
        f = fk.copy()
        ab = b - a
        t = min(max((f - a).dot(ab) / ab.length_squared, 0.0), 1.0)
        n = a + ab * t
        d = (f - n).length
        self.assertLess(d, reach["STRUM_LINE"])
        f = f + (n - f) * (1.0 - d / reach["STRUM_LINE"])
        plane_point, plane_normal = found["STRUM_X_PLANE"]
        s = (f - plane_point).dot(plane_normal)
        if abs(s) < reach["STRUM_POSITION"]:
            f = f - plane_normal * s * (1.0 - abs(s) / reach["STRUM_POSITION"])
        s = (f - string_point).dot(string_normal)
        if s < 0.0:
            f = f - string_normal * s

        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertLess((wrist(obj, 'R') - f).length, TOLERANCE)
        self.assertGreater((f - fk).length, 0.01)

    def test_string_barrier_at_any_distance(self):
        obj, root = setup_scene()
        settings = bpy.context.scene.gtr
        magnets_only(settings)
        found = mounted_landmarks(root)
        string_point, string_normal = found["STRING_PLANE"]
        for item in settings.magnets:
            item.enabled = item.preset_id == "STRING_BARRIER"
        a, b = found["STRUM_A"][0], found["STRUM_B"][0]
        start = (a + b) * 0.5 - string_normal * 0.45
        rigs.reach(obj, *chain(obj, 'R'), start, Vector((0.0, 0.5, -1.0)))
        barrier = next(item for item in settings.magnets if item.preset_id == "STRING_BARRIER")
        beyond = barrier.effective_distance_m * obj.gtr_char.calibration.ratio_arm
        self.assertLess((wrist(obj, 'R') - string_point).dot(string_normal), -beyond)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertLess(abs((wrist(obj, 'R') - string_point).dot(string_normal)), TOLERANCE)
        settings.barriers_ignore_distance = False
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertLess((wrist(obj, 'R') - string_point).dot(string_normal), -beyond)


class SolveTest(unittest.TestCase):
    def setUp(self):
        self.obj, self.root = setup_scene()
        self.settings = bpy.context.scene.gtr

    def test_no_magnets_keep_the_mocap(self):
        """With every magnet and the wrist blend off, the solved arms are the FK arms, bone for bone, though the
        neck is aimed."""
        self.settings.wrist_blend = 0.0
        for item in self.settings.magnets:
            item.enabled = False
        mapping = self.obj.gtr_char.bone_map
        names = [getattr(mapping, key) for key in ("upper_arm_L", "forearm_L", "hand_L", "upper_arm_R",
                                                   "forearm_R", "hand_R", "index_distal_L", "ring_distal_R")]
        bpy.context.view_layer.update()
        before = rigs.pose_arrays(self.obj, names)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertTrue(build.find(self.settings).ik['L'].influence == 1.0)
        after = rigs.pose_arrays(self.obj, names)
        for name in names:
            self.assertLess(abs(after[name] - before[name]).max(), 1e-5, name)

    def test_polls_and_state(self):
        scene = bpy.context.scene
        self.assertFalse(bpy.ops.gtr.clear_solve.poll())
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        self.assertTrue(self.settings.solve_active)
        self.assertEqual(self.settings.solve_frame, scene.frame_current)
        self.assertIsNotNone(solver.shown_result(scene))
        # An undone solve is not shown as current.
        self.settings.solve_serial -= 1
        self.assertIsNone(solver.shown_result(scene))
        self.settings.solve_serial += 1
        # Moving to another frame switches the rig off.
        scene.frame_set(scene.frame_current + 3)
        self.assertFalse(self.settings.solve_active)
        self.assertEqual(build.find(self.settings).ik['R'].influence, 0.0)
        self.assertIsNone(solver.shown_result(scene))
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        assert bpy.ops.gtr.clear_solve() == {'FINISHED'}
        self.assertEqual(build.find(self.settings).wrist['L'].influence, 0.0)
        # No rig, no solve.
        assert bpy.ops.gtr.clean_rig() == {'FINISHED'}
        self.assertFalse(bpy.ops.gtr.solve_frame.poll())
        assert bpy.ops.gtr.build_rig() == {'FINISHED'}
        self.settings.mount_source = 'NONE'
        self.assertFalse(bpy.ops.gtr.solve_frame.poll())

    def test_missing_landmark_skips_the_magnet(self):
        self.settings.magnets[0].landmark_b = None
        result = solver.solve(bpy.context, build.find(self.settings))
        self.assertTrue(any("Strum Line" in text for level, text in result.messages if level == 'WARNING'))
        self.assertNotIn(0, [i for i, _ in result.sides['R'].hits])

    def test_mode_switch(self):
        edge = next(item for item in self.settings.magnets if item.preset_id == "FRETBOARD_EDGE")
        self.assertEqual((edge.power, edge.filter, self.settings.aim_enabled), (-99.0, 'ROTATION_BASED', True))
        self.settings.mode = 'ALIGN'
        self.assertEqual((edge.power, edge.filter, self.settings.aim_enabled), (1.0, 'NONE', False))
        edge.power = 0.5                            # the fields stay editable
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        edge = next(item for item in self.settings.magnets if item.preset_id == "FRETBOARD_EDGE")
        self.assertEqual(edge.power, 1.0)           # a preset loads in the current mode
        self.settings.mode = 'FOLLOW'
        self.assertEqual((edge.power, edge.filter), (-99.0, 'ROTATION_BASED'))

    def test_autoscale_policy_scales_the_reach(self):
        cal = self.obj.gtr_char.calibration
        self.assertAlmostEqual(solver.reach_scale(self.settings, cal), cal.ratio_arm, places=6)
        self.settings.autoscale_policy = 'NONE'
        self.assertAlmostEqual(solver.reach_scale(self.settings, cal), 1.0)


class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.obj, self.root = setup_scene()
        self.settings = bpy.context.scene.gtr

    def draw_panels(self):
        labels = []
        for cls in panels.CLASSES:
            poll = getattr(cls, "poll", None)
            if poll is None or poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        return labels

    def test_overlay(self):
        self.settings.active_magnet_index = 0       # the strum line: its reach is a cylinder
        self.settings.show_magnets = False
        lines, _, _, _ = overlay.build_geometry(bpy.context)
        self.settings.show_magnets = True
        with_magnets, colors, dots, _ = overlay.build_geometry(bpy.context)
        # A line (1) and its reach (2 circles, 4 lines), 2 crossable planes (square and normal) and 3 barriers
        # (square, cross and normal).
        self.assertEqual(len(with_magnets) - len(lines), 2 * (1 + 2 * overlay.CIRCLE_SEGMENTS + 4 + 2 * 5 + 3 * 7))
        self.assertEqual(len(colors), len(with_magnets))
        self.assertEqual(overlay.build_labels(bpy.context), [])
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        solved, _, solved_dots, _ = overlay.build_geometry(bpy.context)
        self.assertGreater(len(solved), len(with_magnets))
        self.assertGreater(len(solved_dots), len(dots))
        labels = overlay.build_labels(bpy.context)
        self.assertTrue(labels)
        self.assertTrue(all(text.split(": ")[0] in self.settings.magnets for _, _, text, _ in labels))

    def test_panels(self):
        labels = self.draw_panels()
        self.assertIn("Options", labels)
        assert bpy.ops.gtr.solve_frame() == {'FINISHED'}
        labels = self.draw_panels()
        self.assertIn("Left wrist", labels)
        self.assertIn("Right wrist", labels)
        self.assertTrue(any(label.startswith("Reach") for label in labels))
        assert bpy.ops.gtr.clean_rig() == {'FINISHED'}
        self.assertTrue(any("Build Rig adds" in label for label in self.draw_panels()))

    def test_magnet_list_operators(self):
        items = self.settings.magnets
        names = [item.name for item in items]
        self.settings.active_magnet_index = 1
        assert bpy.ops.gtr.magnet_add() == {'FINISHED'}
        self.assertEqual(len(items), 7)
        self.assertEqual(self.settings.active_magnet_index, 2)
        self.assertEqual(items[2].name, "Magnet")
        assert bpy.ops.gtr.magnet_add() == {'FINISHED'}
        self.assertEqual(items[3].name, "Magnet 2")
        assert bpy.ops.gtr.magnet_move(direction='UP') == {'FINISHED'}
        self.assertEqual((items[2].name, self.settings.active_magnet_index), ("Magnet 2", 2))
        assert bpy.ops.gtr.magnet_remove() == {'FINISHED'}
        assert bpy.ops.gtr.magnet_remove() == {'FINISHED'}
        self.assertEqual([item.name for item in items], names)
        self.settings.active_magnet_index = 0
        self.assertEqual(bpy.ops.gtr.magnet_move(direction='UP'), {'CANCELLED'})     # already first
        # A new magnet without landmarks is skipped by the solver, with a warning.
        assert bpy.ops.gtr.magnet_add() == {'FINISHED'}
        result = solver.solve(bpy.context, build.find(self.settings))
        self.assertTrue(any("Magnet" in text for _, text in result.messages))
