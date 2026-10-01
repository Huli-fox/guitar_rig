import math
import unittest

import bpy
import numpy as np
from mathutils import Vector

import guitars
import sao
from guitar_rig.core import autoland, guitar_frame, landmarks, presets
from test_guitar import normalize, reset_scene


def world_point(root, role):
    return landmarks.find(root)[role].matrix_world.translation.copy()


def world_normal(root, role):
    m = landmarks.find(root)[role].matrix_world
    return (m.to_3x3().inverted().transposed() @ Vector((0.0, 0.0, 1.0))).normalized()


def line_distance(point, a, b):
    d = (b - a).normalized()
    v = point - a
    return (v - d * v.dot(d)).length


def setup_prop(key):
    """SAO's prop of scene `key`, normalised, with the acoustic preset loaded. Returns (Prop, empty, GTR_ROOT)."""
    reset_scene()
    prop = sao.Prop(key)
    empty, meshes = prop.load()
    root = normalize(meshes)
    bpy.context.scene.gtr.preset = 'acoustic'
    assert bpy.ops.gtr.load_preset() == {'FINISHED'}
    return prop, empty, root


def compare(prop, empty, root):
    """How far the landmarks are from SAO's own points for the prop (metres): {measure: distance}."""
    def world(p):
        return prop.to_world(empty, p)

    out = {}
    pivot, nut = world_point(root, "NECK_PIVOT"), world_point(root, "NUT")
    sao_pivot, sao_nut = world(prop.points["aim_origin"]), world(prop.points["aim_point"])
    out["neck line at SAO pivot"] = line_distance(sao_pivot, pivot, nut)
    out["neck line at SAO nut"] = line_distance(sao_nut, pivot, nut)
    out["nut"] = (nut - sao_nut).length
    for role, normal in (("FRETBOARD_PLANE", (0, 0, 1)), ("FRETBOARD_EDGE", (0, 1, 0))):
        magnet = prop.magnet("left", "plane", normal)
        out[role.lower() + " height"] = abs((world(magnet["point"]) - world_point(root, role)).dot(
            world_normal(root, role)))
    magnet = prop.magnet("left", "plane", (1, 0, 0))
    out["barrier"] = abs((world(magnet["point"]) - world_point(root, "NECK_BODY_BARRIER")).dot(
        world_normal(root, "NECK_BODY_BARRIER")))
    line = prop.magnet("right", "line")
    middle = (world(line["point"]) + world(line["end"])) * 0.5
    out["strum middle"] = (middle - (world_point(root, "STRUM_A") + world_point(root, "STRUM_B")) * 0.5).length
    return out


class HeelTest(unittest.TestCase):
    """Neck.heel_x and fret_slope on synthetic guitars (in their own frame)."""

    def setUp(self):
        reset_scene()

    def measure(self, **kwargs):
        objects, _ = guitars.build(**kwargs)
        geometry = guitar_frame.gather(objects, bpy.context.evaluated_depsgraph_get())
        return guitar_frame.measure_geometry(geometry).neck

    def test_plain_body(self):
        neck = self.measure()
        self.assertAlmostEqual(neck.heel_x, 0.0, delta=0.012)
        self.assertAlmostEqual(neck.joint_x, 0.0, delta=0.012)
        self.assertAlmostEqual(neck.fret_slope, 0.0, delta=0.002)

    def test_cutaway(self):
        """Horns beside the neck move where the neck narrows toward the headstock, not the heel."""
        neck = self.measure(horns=True)
        self.assertAlmostEqual(neck.heel_x, 0.0, delta=0.012)
        self.assertGreater(neck.joint_x, guitars.HORN_END_X - 0.012)

    def test_tilted_neck(self):
        neck = self.measure(neck_tilt=math.radians(2.0))
        self.assertAlmostEqual(math.degrees(math.atan(neck.fret_slope)), 2.0, delta=0.15)
        self.assertAlmostEqual(neck.top_at(guitars.NUT_X), guitars.FRET_Z + math.tan(math.radians(2.0)) * guitars.NUT_X,
                               delta=0.002)

    def test_round_trip(self):
        """Measurements saved in a preset keep the heel and the tilt; older presets have neither."""
        neck = self.measure(neck_tilt=math.radians(1.0))
        again = guitar_frame.Measurements.from_dict(
            guitar_frame.Measurements(np.zeros(3), np.ones(3), neck).scaled(2.0).as_dict()).neck
        self.assertAlmostEqual(again.heel_x, 2.0 * neck.heel_x, places=6)
        self.assertAlmostEqual(again.fret_slope, neck.fret_slope, places=9)
        old = {key: value for key, value in neck.as_dict().items() if key not in ("heel_x", "top_joint", "top_nut")}
        older = guitar_frame.Neck(**old)
        self.assertIsNone(older.heel_x)
        self.assertEqual(older.fret_slope, 0.0)
        self.assertEqual(older.top_at(0.3), older.fret_z)


class AutoLandmarkTest(unittest.TestCase):
    def setUp(self):
        reset_scene()
        self.placement = guitars.world_placement()

    def build(self, **kwargs):
        objects, _ = guitars.build(matrix=self.placement, **kwargs)
        root = normalize(objects)
        assert bpy.ops.gtr.load_preset() == {'FINISHED'}
        return root

    def local(self, root, role):
        """A landmark's position in the synthetic guitar's own frame."""
        return self.placement.inverted() @ world_point(root, role)

    def test_neck_landmarks(self):
        root = self.build()
        names = sorted(obj.name for obj in landmarks.find(root).values())
        root_matrix = root.matrix_world.copy()
        assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
        info = root.gtr_guitar
        self.assertEqual((info.landmark_source, info.landmark_confidence), ('AUTO', 'HIGH'))
        self.assertEqual(sorted(obj.name for obj in landmarks.find(root).values()), names)   # moved, not added
        self.assertEqual(root.matrix_world, root_matrix)
        nut = self.local(root, "NUT")
        self.assertAlmostEqual(nut.x, guitars.NUT_X, delta=0.01)
        self.assertAlmostEqual(nut.z, guitars.FRET_Z, delta=0.002)
        # SAO's nut point is a little inside the fretboard's edge; that offset scales with the neck width.
        preset = presets.load("acoustic")
        spec = preset.landmarks["NUT"].position
        inside = (spec.y - preset.reference.neck.edge_at(spec.x)) * info.fit_scale[1]
        self.assertGreater(inside, 0.003)
        self.assertAlmostEqual(nut.y, -0.5 * guitars.NECK_WIDTH[1] + inside, delta=0.002)
        pivot = self.local(root, "NECK_PIVOT")
        self.assertAlmostEqual(pivot.z, guitars.FRET_Z, delta=0.002)
        self.assertAlmostEqual(self.local(root, "NECK_BODY_BARRIER").x, 0.0, delta=0.015)

    def test_string_plane_keeps_the_fingertip_offset(self):
        """The string barrier's fingertip offset cancels the string plane's height above the fretboard, as in
        SAO's scene and as Load Preset leaves them."""
        root = self.build()
        settings = bpy.context.scene.gtr
        item = next(m for m in settings.magnets if m.preset_id == "STRING_BARRIER")

        def gap():
            height = (world_point(root, "STRING_PLANE") - world_point(root, "FRETBOARD_PLANE")).dot(
                world_normal(root, "FRETBOARD_PLANE"))
            return height / root.matrix_world.to_scale().x + item.fingertip_offset_m

        loaded = gap()
        assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
        self.assertAlmostEqual(gap(), loaded, delta=1e-4)
        self.assertLess(abs(gap()), 0.002)

    def test_cutaway_barrier(self):
        """On a guitar with horns, the barrier goes to the heel; the preset fit puts it where the neck narrows."""
        root = self.build(horns=True)
        fitted = self.local(root, "NECK_BODY_BARRIER").x
        self.assertGreater(fitted, 0.05)
        assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
        self.assertAlmostEqual(self.local(root, "NECK_BODY_BARRIER").x, 0.0, delta=0.015)
        self.assertIn("past where the neck narrows (cutaways)", root.gtr_guitar.landmark_messages)
        strum = (self.local(root, "STRUM_A") + self.local(root, "STRUM_B")) * 0.5
        self.assertTrue(guitars.BODY_X[0] < strum.x < 0.0)

    def test_tilted_fretboard(self):
        """The fretboard plane turns with the fretboard: at the joint and at the nut it is as far from the
        fretboard top on a tilted neck as on a straight one (SAO's plane is not quite parallel to its own
        fretboard). The preset fit keeps the reference guitar's tilt, so on the tilted neck it moves away from the
        fretboard at one end."""
        gaps = {}
        for tilt in (0.0, math.radians(2.0)):
            reset_scene()
            root = self.build(neck_tilt=tilt)
            tops = [Vector((x, 0.0, guitars.FRET_Z + math.tan(tilt) * x)) for x in (0.0, guitars.NUT_X)]
            to_guitar = self.placement.inverted().to_3x3()

            def gap():
                normal = to_guitar @ world_normal(root, "FRETBOARD_PLANE")
                return np.array([(top - self.local(root, "FRETBOARD_PLANE")).dot(normal) for top in tops])

            fitted = gap()
            assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
            gaps[tilt] = (fitted, gap())
            self.assertAlmostEqual(self.local(root, "NUT").z, tops[1].z, delta=0.002)
        (fit_straight, auto_straight), (fit_tilted, auto_tilted) = gaps.values()
        self.assertGreater(np.abs(fit_tilted - fit_straight).max(), 0.005)
        self.assertLess(np.abs(auto_tilted - auto_straight).max(), 0.0015)

    def test_without_preset_landmarks(self):
        """Auto-Place creates the landmarks the preset has, also when none were placed yet."""
        objects, _ = guitars.build(matrix=self.placement)
        root = normalize(objects)
        for obj in list(landmarks.find(root).values()):
            bpy.data.objects.remove(obj)
        assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
        self.assertFalse(landmarks.missing(root))

    def test_no_neck(self):
        reference = presets.load("acoustic").reference
        target = guitar_frame.Measurements(np.array((-0.5, -0.2, -0.1)), np.array((0.5, 0.2, 0.05)))
        with self.assertRaises(autoland.AutoError):
            autoland.place(presets.load("acoustic"), target)
        # A neck without a heel: placed from where it narrows, with a warning.
        neck = guitar_frame.Neck(**{**reference.neck.as_dict(), "heel_x": None})
        placement = autoland.place(presets.load("acoustic"),
                                   guitar_frame.Measurements(reference.bounds_min, reference.bounds_max, neck))
        self.assertEqual(placement.confidence, 'MEDIUM')
        self.assertTrue(any("No body was found under the neck" in text for _, text in placement.messages))

    def test_format_2_preset(self):
        """A preset saved before the heel and the top line were measured places from where the neck narrows,
        with a level reference fretboard, and says so."""
        preset = presets.load("acoustic")
        raw = dict(preset.raw, format=2)
        raw["reference"] = dict(raw["reference"], neck={key: value for key, value in raw["reference"]["neck"].items()
                                                         if key not in ("heel_x", "top_joint", "top_nut")})
        old = presets.parse(raw, "old")
        self.assertIsNone(old.reference.neck.heel_x)
        placement = autoland.place(old, preset.reference)
        self.assertEqual(placement.confidence, 'MEDIUM')
        self.assertTrue(any("saved without its guitar's heel" in text for _, text in placement.messages))
        # The reference fretboard is nearly level: the landmarks move only by the difference between the old
        # reference's fretboard height (fret_z) and the top line, 1.3 mm at the nut.
        for role, spec in preset.landmarks.items():
            self.assertLess((placement.landmarks[role][0] - spec.position).length, 0.002, role)

    def test_reference_reproduces_the_preset(self):
        """On measurements equal to the preset's reference, the landmarks are the preset's own."""
        preset = presets.load("acoustic")
        placement = autoland.place(preset, preset.reference)
        for role, spec in preset.landmarks.items():
            position, normal = placement.landmarks[role]
            self.assertLess((position - spec.position).length, 1e-9, role)
            if spec.normal is not None:
                self.assertLess((normal - spec.normal).length, 1e-6, role)

    def test_flip_goes_back_to_the_preset_fit(self):
        root = self.build()
        assert bpy.ops.gtr.auto_landmarks() == {'FINISHED'}
        assert bpy.ops.gtr.flip_frame(axis='Z') == {'FINISHED'}
        self.assertEqual(root.gtr_guitar.landmark_source, 'PRESET')


@unittest.skipUnless(sao.available(), "the SAO guitar collection is not next to the add-on")
class SaoAutoLandmarkTest(unittest.TestCase):
    """Auto-placed landmarks with the acoustic preset against SAO's own points on each of its guitar scenes."""

    # (measure, limit in metres) for every scene. SAO's own neck points scatter by up to 2 cm around the mesh
    # (the electric's nut); its strum lines are wrist lines, 9 to 26 cm long, tuned per instrument.
    LIMITS = (("neck line at SAO pivot", 0.012), ("neck line at SAO nut", 0.012), ("nut", 0.02),
              ("fretboard_plane height", 0.006), ("fretboard_edge height", 0.005), ("strum middle", 0.08))
    BARRIER_LIMIT = 0.02

    def test_scenes(self):
        totals = {"fit": {"barrier": 0.0, "strum middle": 0.0}, "auto": {"barrier": 0.0, "strum middle": 0.0}}
        for key in sao.SCENES:
            with self.subTest(key):
                prop, empty, root = setup_prop(key)
                fitted = compare(prop, empty, root)
                self.assertEqual(bpy.ops.gtr.auto_landmarks(), {'FINISHED'})
                self.assertNotEqual(root.gtr_guitar.landmark_confidence, 'LOW')
                if key in sao.COPIED:
                    continue
                auto = compare(prop, empty, root)
                for name, limit in self.LIMITS:
                    self.assertLess(auto[name], limit, name)
                self.assertLess(auto["barrier"], self.BARRIER_LIMIT)
                for name in totals["fit"]:
                    totals["fit"][name] += fitted[name]
                    totals["auto"][name] += auto[name]
                if key == "acoustic":       # the preset's own prop
                    for name, distance in auto.items():
                        self.assertLess(distance, 0.002, name)
        # Over the scenes, auto-placing is much closer to SAO than the preset fit at the barrier, and closer at the
        # strum line.
        self.assertLess(totals["auto"]["barrier"], 0.2 * totals["fit"]["barrier"])
        self.assertLess(totals["auto"]["strum middle"], totals["fit"]["strum middle"])
