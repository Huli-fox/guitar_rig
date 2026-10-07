import math
import os
import unittest

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

import guitars
import rigs
import sao
from guitar_rig.core import guitar_frame, landmarks, mount, presets
from guitar_rig.core.mathx import auto_scale_factor, rotation_angle

HERE = os.path.dirname(os.path.abspath(__file__))
SAO_UNIT = 0.088 / 11.0         # metres per GLB unit of the acoustic prop
TMP_DIR = os.path.join(os.path.dirname(HERE), ".tmp")


def reset_scene():
    rigs.clear_scene()
    guitars.clear()
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
    settings = bpy.context.scene.gtr
    for group in (settings, settings.prep):
        for key in group.bl_rna.properties.keys():
            if key not in {"rna_type", "name", "prep"}:
                group.property_unset(key)
    settings.magnets.clear()


def detect_in(objects, matrix):
    """Detection of the objects' guitar, in the frame given by `matrix` (world -> that frame)."""
    geometry = guitar_frame.gather(objects, bpy.context.evaluated_depsgraph_get(), np.array(matrix))
    return guitar_frame.detect(guitar_frame.sample_surface(geometry), geometry)


def normalize(objects, **kwargs):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    assert bpy.ops.gtr.normalize_frame(**kwargs) == {'FINISHED'}
    return bpy.context.scene.gtr.guitar_root


def axis_angle(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b))))))


def root_frame_in_guitar(root, placement):
    """GTR_ROOT's axes in the synthetic guitar's own frame, as columns."""
    return np.array((placement.inverted().to_3x3() @ root.matrix_world.to_3x3().normalized()))


# Pure maths ----------------------------------------------------------------------------------------------------

class HelpersTest(unittest.TestCase):
    def test_loose_parts(self):
        edges = np.array(((0, 1), (1, 2), (3, 4), (6, 5)))
        labels = guitar_frame.loose_parts(7, edges)
        self.assertEqual(len(set(labels)), 3)
        self.assertEqual(labels[0], labels[2])
        self.assertEqual(labels[5], labels[6])
        self.assertNotEqual(labels[0], labels[3])

    def test_find_neck(self):
        """A body, a tapering neck with a heel bump, and a wider headstock."""
        x = np.linspace(0.0, 1.0, 20001)
        width = np.where(x < 0.45, 0.4, 0.056 - 0.012 * (x - 0.45) / 0.35)
        width = np.where((x > 0.45) & (x < 0.47), 0.09, width)           # heel
        width = np.where(x > 0.8, 0.085, width)                           # headstock
        coords = np.column_stack((x, width * np.where(np.arange(len(x)) % 2, 0.5, -0.5), np.zeros_like(x)))
        prof = guitar_frame.profile(coords)
        first, last = guitar_frame.find_neck(prof)
        self.assertAlmostEqual(prof.x_of(first), 0.47, delta=0.011)
        self.assertAlmostEqual(prof.x_of(last + 1), 0.80, delta=0.011)
        self.assertIsNone(guitar_frame.find_neck(guitar_frame.profile(coords * (1, 0, 1) + (0, 0.1, 0))))

    def test_sao_mount(self):
        """The mount rotation matches three.js: Euler(-rx, -ry, rz, 'YXZ') is Ry·Rx·Rz."""
        offset, rotation = presets.sao_mount((-1.3, -0.2, -1.8), (10.0, 15.0, 5.0))
        self.assertLess((offset - Vector((-1.3, -0.2, 1.8)) / 11.0).length, 1e-9)

        def about(axis, degrees):
            return Quaternion(axis, math.radians(degrees))
        expected = about((0, 1, 0), -15.0) @ about((1, 0, 0), -10.0) @ about((0, 0, 1), 5.0)
        self.assertLess(rotation_angle(rotation, expected), 1e-6)
        # three.js 'XYZ' (the wrist offset) is Rx·Ry·Rz.
        expected = about((1, 0, 0), 60.0) @ about((0, 1, 0), 180.0)
        self.assertLess(rotation_angle(presets.sao_euler_xyz((60.0, 180.0, 0.0)), expected), 1e-6)

    def test_fit(self):
        reference = guitar_frame.Measurements(
            np.array((-0.5, -0.2, -0.1)), np.array((0.6, 0.2, 0.02)),
            guitar_frame.Neck(0.0, 0.4, 0.056, 0.044, 0.0, 0.01, -0.02))
        same = presets.fit(reference, reference)
        self.assertEqual(same.method, 'NECK')
        np.testing.assert_allclose(same.scale, 1.0)
        np.testing.assert_allclose(same.origin, 0.0, atol=1e-12)
        # The target is twice as long, 1.5 times as wide, in centimetres, and shifted.
        neck = guitar_frame.Neck(10.0, 90.0, 8.4, 6.6, 3.0, 5.0, -1.0)
        target = guitar_frame.Measurements(np.array((-90.0, -30.0, -10.0)), np.array((120.0, 36.0, 5.0)), neck)
        fitted = presets.fit(reference, target)
        np.testing.assert_allclose(fitted.scale, (200.0, 150.0, 200.0))
        np.testing.assert_allclose(fitted.origin, (10.0, 3.0, 3.0))
        # The fretboard edge at the joint lands on the target's.
        edge = fitted.origin + np.array(fitted.point((0.0, -0.028, 0.01)))
        np.testing.assert_allclose(edge, (10.0, 3.0 - 4.2, 5.0), atol=1e-5)   # Vectors are float32
        normal = fitted.normal((1.0, 1.0, 0.0))
        self.assertAlmostEqual(normal.x / normal.y, 150.0 / 200.0)
        without_neck = presets.fit(reference, guitar_frame.Measurements(target.bounds_min, target.bounds_max))
        self.assertEqual(without_neck.method, 'BOUNDS')
        self.assertTrue(without_neck.messages)

    def test_rebase(self):
        """Moving GTR_ROOT against the guitar keeps a mount that places the guitar where it was."""
        chest_pos, chest_frame = Vector((0.1, -0.2, 1.3)), Quaternion((1.0, 0.2, -0.3, 0.1)).normalized()
        mount_t, mount_q = Vector((-0.12, -0.02, 0.16)), Quaternion((0.9, 0.1, 0.3, -0.2)).normalized()
        scale, factor = Vector((0.5, 0.5, 0.5)), 1.2
        old = mount.mount_matrix(chest_pos, chest_frame, mount_t, mount_q, factor, scale)
        change = Matrix.LocRotScale((0.3, -0.1, 0.05), Euler((math.pi, 0.0, 0.4)), None)
        new = old @ change
        t2, q2 = mount.rebase(mount_t, mount_q, old, new, factor)
        placed = mount.mount_matrix(chest_pos, chest_frame, t2, q2, factor, scale)
        self.assertLess((placed.translation - new.translation).length, 1e-6)
        self.assertLess(rotation_angle(placed.to_quaternion(), new.to_quaternion()), 1e-6)

    def test_capture_round_trip(self):
        chest_pos, chest_frame = Vector((0.1, -0.2, 1.3)), Quaternion((1.0, 0.2, -0.3, 0.1)).normalized()
        target = Matrix.LocRotScale((0.0, -0.4, 1.1), Euler((0.3, -1.2, 2.0)), (0.9, 0.9, 0.9))
        for factor in (1.0, 1.25):
            t, q = mount.capture(chest_pos, chest_frame, target, factor, metres_per_bu=0.01)
            placed = mount.mount_matrix(chest_pos, chest_frame, t, q, factor, target.to_scale(), 0.01)
            for a, b in zip(placed, target):
                self.assertLess((Vector(a) - Vector(b)).length, 1e-5)


class PresetFileTest(unittest.TestCase):
    def test_builtin_presets_parse(self):
        ids = presets.builtin_ids()
        self.assertIn("acoustic", ids)
        self.assertNotIn("bone_maps", ids)
        for preset_id in ids:
            with self.subTest(preset_id):
                preset = presets.load(preset_id)
                required = {role.id for role in landmarks.ROLES if role.required}
                self.assertLessEqual(required, set(preset.landmarks))
                for spec in preset.magnets:
                    self.assertTrue(set(spec) - {"a", "b"} <= set(presets.MAGNET_FIELDS), spec)
                    for key in ("a", "b"):
                        if key in spec:
                            self.assertIn(spec[key], preset.landmarks)

    def test_acoustic_values(self):
        preset = presets.load("acoustic")
        self.assertTrue(preset.verified)
        frame = Quaternion(preset.raw["frame"])
        self.assertLess(math.degrees(rotation_angle(frame, Quaternion())), 2.0)
        nut = frame.inverted() @ preset.landmarks["NUT"].position / SAO_UNIT
        self.assertLess((nut - Vector((64.4079, -1.828405, 7.2436))).length, 1e-4)
        magnets = {m["preset_id"]: m for m in preset.magnets}
        self.assertAlmostEqual(magnets["FRETBOARD_PLANE"]["effective_distance_m"], 6.0 / 11.0)
        self.assertAlmostEqual(magnets["STRING_BARRIER"]["fingertip_offset_m"], -5.0 * SAO_UNIT)
        self.assertEqual(magnets["FRETBOARD_EDGE"]["power"], -99)
        self.assertLess((preset.aim_hand_offset - Vector((0.6, -0.25, 0.0)) / 11.0).length, 1e-9)
        self.assertEqual(preset.wrist_blend, 0.5)

    def test_malformed(self):
        with self.assertRaises(presets.PresetError):
            presets.load(os.path.join(HERE, "no_such_preset.json"))
        os.makedirs(TMP_DIR, exist_ok=True)
        path = os.path.join(TMP_DIR, "broken_preset.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"name": "Broken", "landmarks": {}}')
        with self.assertRaises(presets.PresetError):
            presets.load(path)


# Frame detection -----------------------------------------------------------------------------------------------

class DetectTest(unittest.TestCase):
    def setUp(self):
        reset_scene()

    def assert_frame(self, detection, expected=np.identity(3), tolerance=0.5):
        for i in range(3):
            self.assertLess(axis_angle(detection.axes[:, i], expected[:, i]), tolerance, f"axis {i}")

    def test_variants(self):
        placement = guitars.world_placement()
        for kwargs in (dict(), dict(strings=False), dict(joined=True), dict(parent_scale=0.01)):
            with self.subTest(**kwargs):
                guitars.clear()
                objects, _ = guitars.build(matrix=placement, **kwargs)
                detection = detect_in(objects, placement.inverted())
                self.assertEqual(detection.confidence, 'HIGH')
                self.assert_frame(detection)
                neck = detection.measurements.neck
                self.assertAlmostEqual(neck.joint_x, 0.0, delta=0.01)
                self.assertAlmostEqual(neck.nut_x, guitars.NUT_X, delta=0.01)
                self.assertAlmostEqual(neck.fret_z, guitars.FRET_Z, delta=0.002)   # strings left out
                self.assertAlmostEqual(detection.measurements.length, guitars.LENGTH, delta=0.005)

    def test_any_orientation(self):
        """Half turns and odd rotations of the input give the same frame."""
        objects, _ = guitars.build()
        for rotation in (Euler((0.0, 0.0, math.pi)), Euler((math.pi, 0.0, 0.0)), Euler((0.0, math.pi, 0.0)),
                         Euler((1.1, 2.3, -0.4)), Euler((-2.8, 0.6, 1.9))):
            with self.subTest(rotation=tuple(rotation)):
                turned = rotation.to_matrix().to_4x4()
                geometry = guitar_frame.transformed(
                    guitar_frame.gather(objects, bpy.context.evaluated_depsgraph_get()), turned)
                detection = guitar_frame.detect(guitar_frame.sample_surface(geometry), geometry)
                self.assert_frame(detection, np.array(turned.to_3x3()))

    def test_degenerate(self):
        bm_objects, _ = guitars.build()
        geometry = guitar_frame.gather(bm_objects, bpy.context.evaluated_depsgraph_get())
        flat = guitar_frame.transformed(geometry, Matrix.Diagonal((1.0, 1.0, 0.0, 1.0)))
        with self.assertRaises(guitar_frame.FrameError):
            guitar_frame.detect(guitar_frame.sample_surface(flat), flat)
        empty = guitar_frame.Geometry(np.zeros((0, 3, 3)), np.zeros(0, int), np.zeros((0, 3)), np.zeros(0, int))
        with self.assertRaises(guitar_frame.FrameError):
            guitar_frame.detect(guitar_frame.sample_surface(empty), empty)

    def test_low_poly_strings_are_kept(self):
        """When every neck face is a loose part, the neck's faces look like strings; the neck must survive."""
        objects, _ = guitars.build(low_poly=True)
        geometry = guitar_frame.gather(objects, bpy.context.evaluated_depsgraph_get())
        stats = guitar_frame.part_stats(geometry)
        self.assertGreater(len(guitar_frame.string_parts(geometry, stats)), 12)   # strings and neck faces
        detection = detect_in(objects, Matrix.Identity(4))
        self.assertIsNotNone(detection.measurements.neck)
        self.assert_frame(detection)


# Operators -----------------------------------------------------------------------------------------------------

class GuitarOperatorTest(unittest.TestCase):
    def setUp(self):
        reset_scene()
        self.placement = guitars.world_placement()
        self.objects, self.parent = guitars.build(matrix=self.placement, parent_scale=0.01)

    def test_normalize(self):
        root = normalize(self.objects)
        self.assertEqual(root.name, "GTR_ROOT")
        self.assertIs(self.parent.parent, root)
        frame = root_frame_in_guitar(root, self.placement)
        for i in range(3):
            self.assertLess(axis_angle(frame[:, i], np.identity(3)[:, i]), 0.5)
        info = root.gtr_guitar
        self.assertEqual(info.confidence, 'HIGH')
        self.assertAlmostEqual(info.length_m, guitars.LENGTH, delta=0.005)
        self.assertEqual(info.fit_method, 'NECK')
        # The meshes did not move.
        bpy.context.view_layer.update()
        vertex = self.objects[0].matrix_world @ self.objects[0].data.vertices[0].co
        guitars.clear()
        objects, _ = guitars.build(matrix=self.placement, parent_scale=0.01)
        self.assertLess((vertex - objects[0].matrix_world @ objects[0].data.vertices[0].co).length, 1e-6)

    def test_real_length(self):
        root = normalize(self.objects, real_length=2.0 * guitars.LENGTH)
        self.assertAlmostEqual(root.gtr_guitar.length_m, 2.0 * guitars.LENGTH, delta=0.01)
        self.assertAlmostEqual(root.matrix_world.to_scale().x, 2.0, delta=0.01)

    def test_flip(self):
        root = normalize(self.objects)
        before = root.matrix_world.to_quaternion()
        assert bpy.ops.gtr.flip_frame(axis='X') == {'FINISHED'}
        x = root.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        self.assertAlmostEqual(x.dot(before @ Vector((1, 0, 0))), -1.0, places=5)
        assert bpy.ops.gtr.flip_frame(axis='Z') == {'FINISHED'}
        z = root.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        self.assertAlmostEqual(z.dot(before @ Vector((0, 0, 1))), -1.0, places=5)
        assert bpy.ops.gtr.flip_frame(axis='X') == {'FINISHED'}
        assert bpy.ops.gtr.flip_frame(axis='Z') == {'FINISHED'}
        self.assertLess(rotation_angle(root.matrix_world.to_quaternion(), before), 1e-4)

    def test_load_preset(self):
        root = normalize(self.objects)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        found = landmarks.find(root)
        self.assertFalse(landmarks.missing(root))
        self.assertEqual(len(settings.magnets), 6)
        for magnet in settings.magnets:
            self.assertIsNotNone(magnet.landmark_a, magnet.name)
        self.assertEqual(settings.mount_source, 'PRESET')
        # Landmarks on the neck land on the synthetic neck: the pivot near the joint at the fretboard's lower
        # edge and surface, the nut at the nut.
        to_guitar = self.placement.inverted()
        pivot = to_guitar @ found["NECK_PIVOT"].matrix_world.translation
        nut = to_guitar @ found["NUT"].matrix_world.translation
        self.assertAlmostEqual(nut.x, guitars.NUT_X, delta=0.012)
        self.assertAlmostEqual(nut.z, guitars.FRET_Z, delta=0.004)
        self.assertAlmostEqual(pivot.z, guitars.FRET_Z, delta=0.004)
        self.assertLess(pivot.y, -0.015)
        self.assertGreater(pivot.y, -0.5 * guitars.NECK_WIDTH[0] - 0.01)
        barrier = to_guitar @ found["NECK_BODY_BARRIER"].matrix_world.translation
        self.assertAlmostEqual(barrier.x, 0.0, delta=0.03)
        normal = to_guitar.to_3x3() @ (found["FRETBOARD_EDGE"].matrix_world.to_3x3() @ Vector((0, 0, 1)))
        self.assertGreater(normal.normalized().y, 0.99)
        # A second load re-places the same objects.
        names = sorted(obj.name for obj in found.values())
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        self.assertEqual(sorted(obj.name for obj in landmarks.find(root).values()), names)

    def test_switch_presets(self):
        """The ukulele preset adds its Nut Barrier and the magnet on it; another preset takes both away again,
        unless the magnets are kept."""
        root = normalize(self.objects)
        settings = bpy.context.scene.gtr
        settings.preset = 'ukulele'
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        found = landmarks.find(root)
        self.assertEqual(len(settings.magnets), 7)
        self.assertEqual(settings.magnets[6].preset_id, "NUT_BARRIER")
        self.assertIs(settings.magnets[6].landmark_a, found["NUT_BARRIER"])
        to_guitar = self.placement.inverted()
        barrier = to_guitar @ found["NUT_BARRIER"].matrix_world.translation
        self.assertTrue(0.0 < barrier.x < guitars.NUT_X)
        normal = to_guitar.to_3x3() @ (found["NUT_BARRIER"].matrix_world.to_3x3() @ Vector((0, 0, 1)))
        self.assertLess(normal.normalized().x, -0.99)
        settings.preset = 'acoustic'
        assert bpy.ops.gtr.load_preset(magnets=False) == {'FINISHED'}
        self.assertIn("NUT_BARRIER", landmarks.find(root))
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        self.assertNotIn("NUT_BARRIER", landmarks.find(root))
        self.assertEqual(len(settings.magnets), 6)
        self.assertFalse(landmarks.missing(root))

    def test_load_keeps_a_captured_mount(self):
        normalize(self.objects)
        settings = bpy.context.scene.gtr
        settings.mount_source = 'CAPTURE'
        settings.mount_t = (0.1, 0.2, 0.3)
        assert bpy.ops.gtr.load_preset('INVOKE_DEFAULT') == {'FINISHED'}
        self.assertEqual(settings.mount_source, 'CAPTURE')

    def test_save_and_load_file(self):
        root = normalize(self.objects)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        found = landmarks.find(root)
        found["NUT"].location.x -= 0.02            # a hand-tuned landmark
        bpy.context.scene.gtr.magnets[0].power = 0.5
        bpy.context.view_layer.update()
        expected = {role: obj.matrix_world.translation.copy() for role, obj in found.items()}
        os.makedirs(TMP_DIR, exist_ok=True)
        path = os.path.join(TMP_DIR, "saved_preset.json")
        assert bpy.ops.gtr.save_preset(filepath=path, name="Saved") == {'FINISHED'}
        bpy.context.scene.gtr.magnets[0].power = 0.0
        found["NUT"].location.x += 0.05
        assert bpy.ops.gtr.load_preset_file(filepath=path) == {'FINISHED'}
        self.assertEqual(bpy.context.scene.gtr.magnets[0].power, 0.5)
        for role, obj in landmarks.find(root).items():
            self.assertLess((obj.matrix_world.translation - expected[role]).length, 1e-4, role)

    def test_select_landmark(self):
        root = normalize(self.objects)
        bpy.context.scene.cursor.location = (1.0, 2.0, 3.0)
        assert bpy.ops.gtr.select_landmark(role='NUT_BARRIER') == {'FINISHED'}
        obj = landmarks.find(root)["NUT_BARRIER"]
        self.assertIs(bpy.context.view_layer.objects.active, obj)
        self.assertLess((obj.matrix_world.translation - Vector((1.0, 2.0, 3.0))).length, 1e-5)

    def test_polls(self):
        self.assertFalse(bpy.ops.gtr.load_preset.poll())
        self.assertFalse(bpy.ops.gtr.capture_mount.poll())
        bpy.ops.object.select_all(action='DESELECT')
        self.assertFalse(bpy.ops.gtr.normalize_frame.poll())


class MountOperatorTest(unittest.TestCase):
    def setUp(self):
        reset_scene()
        self.rig = rigs.vroid()
        bpy.context.view_layer.objects.active = self.rig
        assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
        assert bpy.ops.gtr.calibrate() == {'FINISHED'}
        self.objects, _ = guitars.build(matrix=guitars.world_placement())
        self.root = normalize(self.objects)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        bpy.context.view_layer.objects.active = self.root

    def chest(self):
        return self.rig.pose.bones["J_Bip_C_Chest"]

    def test_place_preset_mount(self):
        """At rest in T-pose, the SAO mount puts the guitar at chest + (x, y, -z)/11 in the character frame."""
        assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        cal = self.rig.gtr_char.calibration
        char = rigs.BLENDER_AXES.to_quaternion()
        factor = auto_scale_factor(cal.ratio_spine)
        expected = self.chest().head + char @ (Vector((-1.3, -0.2, 1.8)) / 11.0 * factor)
        self.assertLess((self.root.matrix_world.translation - expected).length, 1e-6)
        rotation = char @ Quaternion(settings.mount_q)
        self.assertLess(rotation_angle(self.root.matrix_world.to_quaternion(), rotation), 1e-5)

    def test_capture_follows_the_chest(self):
        target = Matrix.LocRotScale((0.05, -0.25, 1.15), Euler((0.4, -1.3, 2.2)), None)
        self.root.matrix_world = target
        assert bpy.ops.gtr.capture_mount() == {'FINISHED'}
        settings = bpy.context.scene.gtr
        self.assertEqual(settings.mount_source, 'CAPTURE')
        # Capture then place gives back the pose.
        self.root.matrix_world = Matrix.Identity(4)
        assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
        self.assertLess((self.root.matrix_world.translation - target.translation).length, 1e-5)
        # The guitar follows the chest rigidly.
        chest_world = self.rig.matrix_world @ self.chest().matrix
        relative = chest_world.inverted() @ self.root.matrix_world
        rigs.rotate_bone(self.rig, "J_Bip_C_Chest", Quaternion((0.3, 0.8, 0.2), 0.6))
        assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
        moved = (self.rig.matrix_world @ self.chest().matrix).inverted() @ self.root.matrix_world
        for a, b in zip(relative, moved):
            self.assertLess((Vector(a) - Vector(b)).length, 1e-5)

    def test_flip_keeps_the_captured_guitar(self):
        target = Matrix.LocRotScale((0.05, -0.25, 1.15), Euler((0.4, -1.3, 2.2)), None)
        self.root.matrix_world = target
        bpy.context.view_layer.update()
        mesh = self.objects[0]
        vertex = mesh.matrix_world @ mesh.data.vertices[0].co
        assert bpy.ops.gtr.capture_mount() == {'FINISHED'}
        assert bpy.ops.gtr.flip_frame(axis='Z') == {'FINISHED'}
        self.root.matrix_world = Matrix.Identity(4)
        assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
        bpy.context.view_layer.update()
        self.assertLess((mesh.matrix_world @ mesh.data.vertices[0].co - vertex).length, 1e-5)

    def test_needs_a_mount(self):
        bpy.context.scene.gtr.mount_source = 'NONE'
        self.assertFalse(bpy.ops.gtr.place_on_mount.poll())
        self.assertTrue(bpy.ops.gtr.capture_mount.poll())


# SAO equivalence -----------------------------------------------------------------------------------------------

SAO_PRESETS = ("acoustic", "bass", "strat", "ukulele")     # built-in presets made from sao.SCENES[id]
SAO_ROLES = {0: ("STRUM_A", "STRUM_B"), 1: ("STRUM_X_PLANE",), 2: ("STRING_PLANE",), 3: ("FRETBOARD_PLANE",),
             4: ("NECK_BODY_BARRIER",), 5: ("FRETBOARD_EDGE",), 6: ("NUT_BARRIER",)}    # SAO magnet -> its points
SAO_FINGERS = {"人": "INDEX", "中": "MIDDLE", "薬": "RING"}


def xyz(d):
    return [d["x"], d["y"], d["z"]]


@unittest.skipUnless(sao.available(), "the SAO guitar collection is not next to the add-on")
class SaoPresetFileTest(unittest.TestCase):
    """Each SAO preset file holds the numbers of its scene file."""

    def test_presets_match_their_scenes(self):
        for preset_id in SAO_PRESETS:
            with self.subTest(preset_id):
                data = sao.scene(preset_id)
                para = data["object3D_list"][0]["model_para"]
                bone = para["parent_bone"]
                aim = bone["rotation"]["align_with_external_point"]
                tracking = next(iter(data["on"]["gesture"].values()))["left|horns"]["action"]["motion_tracking"]
                raw = presets.load(preset_id).raw
                self.assertTrue(raw["verified"])
                self.assertEqual(raw["sao_placement_scale"], para["placement"]["scale"])
                self.assertEqual(raw["mount"], {"sao_bone": bone["name"], "sao_position": xyz(bone["position"]),
                                                "sao_rotation": xyz(bone["rotation"])})
                self.assertEqual(raw["aim"], {"sao_offset": xyz(aim["external_point"]["offset"])})
                wrist = tracking["hand_tracking"]["rotation_reference"]["left"]
                self.assertEqual(raw["wrist"], {"sao_offset": xyz(wrist["offset"]), "weight": wrist["weight"]})
                points = raw["landmarks"]
                self.assertEqual(points["NECK_PIVOT"]["position"], xyz(aim["reference_origin"]))
                self.assertEqual(points["NUT"]["position"], xyz(aim["reference_point"]))
                scene_magnets = tracking["arm_tracking"]["transformation"]["position"]["magnet"]
                self.assertEqual([entry["sao_index"] for entry in raw["magnets"]], list(range(len(scene_magnets))))
                for entry, magnet in zip(raw["magnets"], scene_magnets):
                    self.check_magnet(entry, magnet, points)

    def check_magnet(self, entry, magnet, points):
        (hand, options), = magnet["hand_affected"].items()
        self.assertEqual(entry["hand"], hand[0].upper())
        self.assertEqual(entry["kind"], magnet["magnet_type"].upper())
        self.assertEqual(entry["effective_distance"], magnet["effective_distance"])
        self.assertEqual(entry["power"], magnet["power"])
        self.assertEqual(entry.get("crossable", False), magnet.get("plane_crossable", False))
        self.assertEqual(entry.get("use_default_rotation", False), magnet.get("use_default_rotation", False))
        self.assertEqual(entry.get("hand_offset_mode") == "PARENT_BONE", options.get("offset") == "parent_bone")
        self.assertEqual(entry.get("filter") == "ROTATION_BASED", "reference_point_filter" in magnet)
        fingertips = options.get("offset_fingertip_v2") or options.get("offset_fingertip")
        if fingertips is None:
            self.assertNotIn("fingertip_mode", entry)
        else:
            self.assertEqual(entry["fingertip_mode"], "V2")
            self.assertEqual(entry["fingers"], [SAO_FINGERS[finger] for finger in fingertips["finger_list"]])
            self.assertEqual(entry.get("fingertip_offset", 0), fingertips.get("reference_point_offset_distance", 0))
            self.assertEqual(entry.get("push_only", False), fingertips.get("push_only", False))
        roles = SAO_ROLES[entry["sao_index"]]
        self.assertEqual(entry["a"], roles[0])
        self.assertEqual(points[roles[0]]["position"], xyz(magnet["reference_point"]))
        if "line_end" in magnet:
            self.assertEqual(entry["b"], roles[1])
            self.assertEqual(points[roles[1]]["position"], xyz(magnet["line_end"]))
        if "plane_normal" in magnet:
            self.assertEqual(points[roles[0]]["normal"], xyz(magnet["plane_normal"]))


@unittest.skipUnless(sao.available(), "the SAO guitar collection is not next to the add-on")
class SaoPresetTest(unittest.TestCase):
    """Each SAO preset on its own prop reproduces its scene file."""

    def load(self, preset_id):
        """The calibrated VRoid character, and SAO's prop for the preset normalised with the preset loaded.
        Returns (sao.Prop, the prop's empty, GTR_ROOT)."""
        reset_scene()
        self.rig = rigs.vroid()
        bpy.context.view_layer.objects.active = self.rig
        assert bpy.ops.gtr.auto_map_bones() == {'FINISHED'}
        assert bpy.ops.gtr.calibrate() == {'FINISHED'}
        prop = sao.Prop(preset_id)
        empty, meshes = prop.load()
        root = normalize(meshes)
        bpy.context.scene.gtr.preset = preset_id
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        return prop, empty, root

    def test_landmarks_match_the_scenes(self):
        for preset_id in SAO_PRESETS:
            with self.subTest(preset_id):
                prop, empty, root = self.load(preset_id)
                self.assertEqual(root.gtr_guitar.fit_method, 'NECK')
                # The reference is stored to the micrometre: up to 1e-4 of the 2 to 4 cm neck thickness.
                np.testing.assert_allclose(root.gtr_guitar.fit_scale, 1.0, atol=1e-4)
                found = landmarks.find(root)
                preset = presets.load(preset_id)
                self.assertEqual(set(found), set(preset.landmarks))
                self.assertEqual(len(bpy.context.scene.gtr.magnets), len(preset.magnets))
                for role, entry in preset.raw["landmarks"].items():
                    obj = found[role]
                    expected = prop.to_world(empty, entry["position"])
                    self.assertLess((obj.matrix_world.translation - expected).length, 1e-5, role)
                    if "normal" in entry:
                        normal = obj.matrix_world.to_3x3().normalized() @ Vector((0, 0, 1))
                        self.assertGreater(normal.dot(prop.direction_to_world(empty, entry["normal"])), 1.0 - 1e-6)
                # The GLB origin is the preset origin.
                self.assertLess((root.matrix_world.translation - prop.to_world(empty, (0, 0, 0))).length, 5e-6)

    def test_mount_matches_index_js(self):
        """index.js: obj.pos = chest + rot·auto_scale([x, y, -z]); obj.q = rot·Euler(-rx, -ry, rz, 'YXZ'),
        in three.js coordinates, which are the character frame for SAO's avatars."""
        def about(axis, degrees):
            return Quaternion(axis, math.radians(degrees))

        for preset_id in SAO_PRESETS:
            with self.subTest(preset_id):
                prop, _, root = self.load(preset_id)
                chest_bone = self.rig.pose.bones["J_Bip_C_Chest"]
                rigs.rotate_bone(self.rig, "J_Bip_C_Chest", Quaternion((0.2, -0.5, 0.1), 0.4))
                assert bpy.ops.gtr.place_on_mount() == {'FINISHED'}
                bpy.context.view_layer.update()

                char_world = rigs.BLENDER_AXES.to_quaternion()       # three.js axes -> Blender world
                chest_rot = (self.rig.matrix_world @ chest_bone.matrix).to_quaternion()
                rot = (char_world.inverted() @ chest_rot @ chest_bone.bone.matrix_local.to_quaternion().inverted()
                       @ char_world)
                raw = presets.load(preset_id).raw
                (x, y, z), (rx, ry, rz) = raw["mount"]["sao_position"], raw["mount"]["sao_rotation"]
                obj_q = rot @ about((0, 1, 0), -ry) @ about((1, 0, 0), -rx) @ about((0, 0, 1), rz)
                cal = self.rig.gtr_char.calibration
                obj_pos = rot @ (Vector((x, y, -z)) * auto_scale_factor(cal.ratio_spine) / 11.0)

                chest = self.rig.matrix_world @ chest_bone.head
                for role, entry in raw["landmarks"].items():
                    glb = Vector(entry["position"]) * prop.unit       # placement.scale of MMD units: metres
                    expected = chest + char_world @ (obj_pos + obj_q @ glb)
                    actual = landmarks.find(root)[role].matrix_world.translation
                    self.assertLess((actual - expected).length, 1e-5, role)


class LandmarkPanelTest(unittest.TestCase):
    def setUp(self):
        reset_scene()

    def test_panels_and_overlay(self):
        from test_addon import FakeLayout
        from types import SimpleNamespace
        from guitar_rig.ui import overlay, panels

        def draw():
            labels = []
            for cls in panels.CLASSES:
                poll = getattr(cls, "poll", None)
                if poll is None or poll(bpy.context):
                    cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
            return labels

        self.assertTrue(any(label.startswith("Select the guitar meshes") for label in draw()))
        rig = rigs.vroid()
        bpy.context.view_layer.objects.active = rig
        bpy.ops.gtr.auto_map_bones()
        bpy.ops.gtr.calibrate()
        objects, _ = guitars.build(matrix=guitars.world_placement())
        normalize(objects)
        before = overlay.build_geometry(bpy.context)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        labels = draw()
        self.assertIn("Landmarks", labels)
        self.assertTrue(any(label.startswith("Preset estimate") for label in labels))
        bpy.context.scene.gtr.show_magnets = False     # the magnets have their own overlay tests
        lines, colors, _, _ = overlay.build_geometry(bpy.context)
        self.assertEqual(len(lines), len(before[0]) + 2 * 2 + 3 * 2)    # neck and strum lines, mount tripod
        self.assertEqual(len(colors), len(lines))
