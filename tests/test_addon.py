import math
import unittest
from types import SimpleNamespace

import bpy
from mathutils import Euler, Quaternion, Vector

import rigs
from guitar_rig.core import bonemap, calibrate
from guitar_rig.core.mathx import auto_scale_factor, rotation_angle
from guitar_rig.ui import overlay, panels


def auto_map_and_calibrate(obj):
    bpy.context.view_layer.objects.active = obj
    assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
    assert bpy.ops.gtr.calibrate() == {'FINISHED'}


class OperatorTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_auto_map_and_calibrate(self):
        obj = rigs.rigify()
        auto_map_and_calibrate(obj)
        self.assertIs(bpy.context.scene.gtr.armature, obj)
        bone_map = obj.gtr_char.bone_map
        self.assertEqual(bone_map.chain_forearm_L, "forearm_fk.L")
        self.assertEqual(bone_map.chain_count_L, 2)
        self.assertEqual(bone_map.source, "Rigify (generated rig)")
        cal = obj.gtr_char.calibration
        self.assertTrue(cal.is_valid)
        self.assertAlmostEqual(cal.arm_len, rigs.ARM_LEN, places=5)
        self.assertEqual(len(cal.fingertips), 6)

    def test_chain_count_follows_edits(self):
        obj = rigs.mmd()
        auto_map_and_calibrate(obj)
        bone_map = obj.gtr_char.bone_map
        self.assertEqual(bone_map.chain_count_L, 3)
        bone_map.chain_upper_arm_L = "左肩"
        self.assertEqual(bone_map.chain_count_L, 4)
        bone_map.chain_upper_arm_L = "右腕"
        self.assertEqual(bone_map.chain_count_L, 0)

    def test_calibrate_refuses_an_incomplete_map(self):
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        obj.gtr_char.bone_map.hand_L = ""
        with self.assertRaises(RuntimeError):
            bpy.ops.gtr.calibrate()
        self.assertFalse(obj.gtr_char.calibration.is_valid)

    def test_polls(self):
        self.assertFalse(bpy.ops.gtr.auto_map_bones.poll())
        obj = rigs.vroid()
        bpy.context.view_layer.objects.active = obj
        self.assertTrue(bpy.ops.gtr.auto_map_bones.poll())
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            self.assertFalse(bpy.ops.gtr.calibrate.poll())
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

    def test_calibration_inputs_recalibrate(self):
        obj = rigs.mmd(a_pose=math.radians(35.0))
        auto_map_and_calibrate(obj)
        cal = obj.gtr_char.calibration
        before = Quaternion(cal.char_frame)
        self.assertGreater(rotation_angle(Quaternion(cal.axis_rot_L), Quaternion()), 0.5)
        cal.flip_facing = True
        self.assertAlmostEqual(rotation_angle(before, Quaternion(cal.char_frame)), math.pi, places=4)
        cal.flip_facing = False
        cal.axis_rot_ref_angle = math.radians(35.0)
        self.assertLess(rotation_angle(Quaternion(cal.axis_rot_L), Quaternion()), 1e-4)
        mapping = bonemap.mapping_from(obj.gtr_char.bone_map)
        self.assertEqual(calibrate.fingerprint(obj, mapping, False, cal.axis_rot_ref_angle, 1.0), cal.fingerprint)


class FakeLayout:
    """Stands in for UILayout: records labels, and checks that drawn properties and operators exist."""

    def __init__(self, test, labels=None):
        self.test = test
        self.labels = [] if labels is None else labels

    def _child(self, *args, **kwargs):
        return FakeLayout(self.test, self.labels)

    row = column = box = split = _child

    def panel(self, idname, default_closed=False):
        return self._child(), self._child()

    def label(self, text="", icon='NONE', **kwargs):
        self.labels.append(text)

    def prop(self, data, name, **kwargs):
        self.test.assertIn(name, data.bl_rna.properties.keys(), name)

    def prop_search(self, data, name, search_data, search_name, **kwargs):
        self.test.assertIn(name, data.bl_rna.properties.keys(), name)
        self.test.assertIn(search_name, search_data.bl_rna.properties.keys(), search_name)

    def operator(self, idname, **kwargs):
        module, _, name = idname.partition(".")
        getattr(getattr(bpy.ops, module), name).get_rna_type()


class PanelTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def draw(self):
        labels = []
        for cls in panels.CLASSES:
            poll = getattr(cls, "poll", None)
            if poll is None or poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        return labels

    def test_without_character(self):
        self.assertIn("Pick the retargeted character", self.draw())

    def test_before_and_after_calibration(self):
        obj = rigs.vroid()
        bpy.context.scene.gtr.armature = obj
        self.assertIn("Not calibrated", self.draw())
        auto_map_and_calibrate(obj)
        labels = self.draw()
        self.assertIn("Matched: VRoid / VRM (J_Bip)", labels)
        self.assertIn("1.750 m", labels)
        self.assertNotIn("The rig or bone map changed: calibrate again", labels)
        obj.gtr_char.bone_map.neck = ""
        self.assertIn("The rig or bone map changed: calibrate again", self.draw())

    def test_messages_are_wrapped(self):
        obj = rigs.vroid(skip=("Chest",))
        auto_map_and_calibrate(obj)
        obj.gtr_char.bone_map.hand_L = ""
        labels = self.draw()
        self.assertIn("Left Hand is not mapped.", labels)
        self.assertTrue(all(len(label) < 60 for label in labels))


class OverlayTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def test_geometry(self):
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        lines, line_colors, dots, dot_colors = overlay.build_geometry(bpy.context)
        self.assertEqual(len(lines), 4 * 3 * 2 + 2)       # four tripods and the aim line
        self.assertEqual(len(line_colors), len(lines))
        self.assertEqual(len(dots), 6 + 1)                 # fingertips and the aim point
        # The hips tripod: X toward the character's left (+X), Z forward (-Y).
        self.assertAlmostEqual((lines[1] - lines[0]).normalized().dot(Vector((1, 0, 0))), 1.0, places=5)
        self.assertAlmostEqual((lines[5] - lines[4]).normalized().dot(Vector((0, -1, 0))), 1.0, places=5)

    def test_aim_point(self):
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        cal = obj.gtr_char.calibration
        hand = obj.pose.bones["J_Bip_L_Hand"]
        offset = Vector(bpy.context.scene.gtr.aim_hand_offset) * auto_scale_factor(cal.ratio_palm)
        # At rest in T-pose the offset is in the character frame: along the arm and down.
        expected = hand.head + Vector((offset.x, -offset.z, offset.y))
        self.assertLess((overlay.aim_point(obj, bpy.context.scene.gtr, cal, hand) - expected).length, 1e-6)
        # The point turns with the hand.
        frame = calibrate.char_frame_world(Quaternion(cal.char_frame), obj.matrix_world)
        turn = frame @ Euler((0.0, 0.0, 0.8)).to_quaternion() @ frame.inverted()
        rigs.rotate_bone(obj, "J_Bip_L_Hand", turn)
        turned = hand.head + turn @ Vector((offset.x, -offset.z, offset.y))
        self.assertLess((overlay.aim_point(obj, bpy.context.scene.gtr, cal, hand) - turned).length, 1e-6)

    def test_nothing_to_draw(self):
        self.assertIsNone(overlay.build_geometry(bpy.context))
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        bpy.context.scene.gtr.show_overlay = False
        try:
            self.assertIsNone(overlay.build_geometry(bpy.context))
        finally:
            bpy.context.scene.gtr.show_overlay = True

    def test_draws_offscreen(self):
        """The draw handler's shaders and GPU state calls work (front view of the calibrated rig)."""
        import gpu
        import numpy as np
        from mathutils import Matrix
        try:
            if hasattr(gpu, "init"):
                gpu.init()  # Blender 5: GPU drawing in background mode needs this
            offscreen = gpu.types.GPUOffScreen(200, 200)
        except Exception as exc:
            self.skipTest(f"no GPU drawing here: {exc}")
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        view = Matrix(((1, 0, 0, 0), (0, 0, 1, -0.9), (0, -1, 0, 0), (0, 0, 0, 1)))
        try:
            with offscreen.bind():
                fb = gpu.state.active_framebuffer_get()
                fb.clear(color=(0.0, 0.0, 0.0, 0.0))
                with gpu.matrix.push_pop(), gpu.matrix.push_pop_projection():
                    gpu.matrix.load_matrix(view)
                    gpu.matrix.load_projection_matrix(Matrix.Diagonal((1.0, 1.0, -0.1, 1.0)))
                    overlay._draw()
                pixels = np.array(fb.read_color(0, 0, 200, 200, 4, 0, 'FLOAT').to_list())
        finally:
            offscreen.free()
        lit = pixels[..., 3] > 0.0
        self.assertGreater(int(lit.sum()), 100)
        red = lit & (pixels[..., 0] > 0.8) & (pixels[..., 1] < 0.4) & (pixels[..., 2] < 0.4)
        self.assertGreater(int(red.sum()), 10)
