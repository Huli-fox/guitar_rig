"""Apply Prep, Remove Prep and Show Original (core/prepjob.py) on the MMD test rig, and how the prep layer sits with
the bake. The optional MMDPartTest runs the prep on a real model and motion (see its notes)."""

import math
import os
import re
import unittest
from types import SimpleNamespace

import bpy
import numpy as np
from mathutils import Matrix, Quaternion

import rigs
from guitar_rig.core import baker, keys, prep, prepjob, solver
from guitar_rig.rig import build
from guitar_rig.ui import panels
from test_addon import FakeLayout, auto_map_and_calibrate
from test_baker import animate, plain
from test_guitar import reset_scene
from test_solve import setup_scene

FPS = 30.0
FRAMES = range(1, 61)
FINGER_JOINTS = [f"左{finger}{digit}" for finger in ("人指", "中指", "薬指", "小指") for digit in "１２３"]


def presses(frames, rise=8, hold=12):
    """A finger's bend (0 to 1) pressing and releasing over `rise` frames, holding `hold` frames in between."""
    period = 2 * (rise + hold)
    out = []
    for f in frames:
        phase = (f - frames[0]) % period
        if phase < rise:
            value = 0.5 - 0.5 * math.cos(math.pi * phase / rise)
        elif phase < rise + hold:
            value = 1.0
        elif phase < 2 * rise + hold:
            value = 0.5 + 0.5 * math.cos(math.pi * (phase - rise - hold) / rise)
        else:
            value = 0.0
        out.append(value)
    return out


def perform(obj, frames=FRAMES, strum=True, fingers=True, elbow=1.0):
    """Key a strum on the right hand (a 2 Hz roll of the wrist about the forearm, with a slower turn, the elbow
    bent by `elbow` radians more) and presses on the left fingers, on top of whatever the bones already play."""
    scene = bpy.context.scene
    bend = presses(frames)
    names = ["右手首", "右ひじ"] + FINGER_JOINTS
    for name in names:
        obj.pose.bones[name].rotation_mode = 'QUATERNION'
    base = {}
    for f in frames:
        scene.frame_set(f)
        base[f] = {name: obj.pose.bones[name].rotation_quaternion.copy() for name in names}
    for i, f in enumerate(frames):
        t = (f - frames[0]) / FPS
        turns = {}
        if strum:
            turns["右手首"] = (Quaternion((1.0, 0.0, 0.0), 0.15 * math.sin(2.0 * math.pi * 0.4 * t))
                              @ Quaternion((0.0, 1.0, 0.0), 0.35 * math.sin(2.0 * math.pi * 2.0 * t)))
            turns["右ひじ"] = Quaternion((1.0, 0.0, 0.0), elbow + 0.02 * math.sin(2.0 * math.pi * 2.0 * t))
        if fingers:
            for k, name in enumerate(FINGER_JOINTS):
                turns[name] = Quaternion((1.0, 0.0, 0.0), (0.6 + 0.1 * (k % 3)) * bend[i])
        for name, turn in turns.items():
            pbone = obj.pose.bones[name]
            pbone.rotation_quaternion = base[f][name] @ turn
            pbone.keyframe_insert("rotation_quaternion", frame=f)
    scene.frame_start, scene.frame_end = frames[0], frames[-1]
    scene.frame_set(frames[0])


def world(obj, name):
    return obj.matrix_world @ obj.pose.bones[name].matrix


def tracks(obj):
    return [track.name for track in obj.animation_data.nla_tracks]


def only(options, **values):
    """Every tool neutral except `values`."""
    options.range_wrist = options.range_fingers = 1.0
    options.snap_strokes = options.snap_fingers = 1.0
    options.swing = 0.0
    options.roll_to_twist = options.snap_picking = False
    for name, value in values.items():
        setattr(options, name, value)


class PrepTest(unittest.TestCase):
    """The MMD rig alone: Prep needs only the calibrated character."""

    def setUp(self):
        reset_scene()
        bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = 30, 1.0
        self.obj = rigs.mmd()
        auto_map_and_calibrate(self.obj)
        self.scene = bpy.context.scene
        self.settings = self.scene.gtr
        self.options = self.settings.prep

    def sample(self, names, frames=FRAMES, basis=False):
        out = {name: [] for name in names}
        for f in frames:
            self.scene.frame_set(f)
            for name in names:
                pbone = self.obj.pose.bones[name]
                out[name].append(np.array(pbone.matrix_basis if basis else world(self.obj, name)))
        return {name: np.array(values) for name, values in out.items()}

    def test_finds_mmd_bones(self):
        found = prepjob.find_bones(self.obj)
        self.assertEqual(found.arms['R'].twist, "右手捩")
        self.assertEqual(found.arms['L'].path, ["左腕", "左腕捩", "左ひじ", "左手捩", "左手首"])
        self.assertEqual(found.fingers['L']['THUMB'], ["左親指０", "左親指１", "左親指２"])
        self.assertEqual(found.fingers['R']['LITTLE'], ["右小指１", "右小指２", "右小指３"])
        self.assertEqual(found.tips['R']['INDEX'], ("右人指先", (0.0, 0.0, 0.0)))
        self.assertEqual(found.messages, [])
        rigs.clear_scene()
        obj = rigs.mmd(suffix=True)
        auto_map_and_calibrate(obj)
        self.assertEqual(prepjob.find_bones(obj).arms['R'].twist, "手捩.R")
        self.assertEqual(prepjob.find_bones(obj).fingers['L']['INDEX'], ["人指１.L", "人指２.L", "人指３.L"])

    def test_other_rigs_are_refused(self):
        rigs.clear_scene()
        obj = rigs.vroid()
        auto_map_and_calibrate(obj)
        self.assertFalse(bpy.ops.gtr.apply_prep.poll())
        with self.assertRaisesRegex(prepjob.PrepError, "MMD"):
            prepjob.find_bones(obj)

    def test_layer_and_static_values(self):
        perform(self.obj)
        source = self.obj.animation_data.action
        twist = self.obj.pose.bones["右手捩"]
        twist.rotation_quaternion = Quaternion((0.0, 1.0, 0.0), 0.2)     # not animated: a static value
        static = tuple(twist.rotation_quaternion)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        data = self.obj.animation_data
        self.assertIsNone(data.action)
        self.assertEqual(tracks(self.obj), [source.name, "GuitarPrep"])
        strip = data.nla_tracks["GuitarPrep"].strips[0]
        self.assertEqual((strip.blend_type, strip.extrapolation), ('REPLACE', 'NOTHING'))
        self.assertEqual(strip.action.name, "MMD_GuitarPrep")
        self.assertEqual(strip.action[keys.TAG], keys.PREP)
        self.assertEqual((strip.frame_start, strip.frame_end), (1.0, 60.0))
        keyed = {c.data_path.split('"')[1] for c in keys.fcurves(strip.action)}
        self.assertIn("右手首", keyed)
        self.assertIn("右手捩", keyed)
        self.assertTrue(set(FINGER_JOINTS) <= keyed)
        self.assertTrue({"右腕", "右ひじ"} <= keyed)            # the swing
        self.assertNotIn("too straight", self.options.report)
        self.assertFalse({"左腕", "左ひじ", "右人指１"} & keyed)
        self.assertTrue(all(len(c.keyframe_points) == len(FRAMES) for c in keys.fcurves(strip.action)))
        self.assertIn("Prepped frames 1-60", self.options.report)
        self.assertFalse(keys.has_bake(self.obj))
        self.assertFalse(baker.has_bake(self.settings))
        # Show Original mutes the layer, and the twist bone gets its own value back.
        self.scene.frame_set(20)
        self.assertGreater(abs(Quaternion(twist.rotation_quaternion).rotation_difference(
            Quaternion(static)).angle), 1e-3)
        self.assertEqual(bpy.ops.gtr.toggle_prep(original=True), {'FINISHED'})
        self.assertTrue(prepjob.is_muted(self.obj))
        self.scene.frame_set(21)
        np.testing.assert_allclose(tuple(twist.rotation_quaternion), static, atol=1e-6)
        self.assertEqual(bpy.ops.gtr.toggle_prep(original=False), {'FINISHED'})
        self.assertFalse(prepjob.is_muted(self.obj))
        # Re-prep replaces the action; Remove Prep puts everything back.
        actions = set(bpy.data.actions.keys())
        self.options.range_wrist = 2.0
        self.assertTrue(any("settings changed" in text for _, text in prepjob.status(self.settings)))
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.assertEqual(set(bpy.data.actions.keys()), actions)
        self.assertEqual(tracks(self.obj), [source.name, "GuitarPrep"])
        self.assertEqual(prepjob.status(self.settings), [])
        self.assertEqual(bpy.ops.gtr.remove_prep(), {'FINISHED'})
        self.assertEqual(self.obj.animation_data.action, source)
        self.assertEqual(len(self.obj.animation_data.nla_tracks), 0)
        self.assertNotIn(keys.STATIC_PROP, self.obj)
        self.scene.frame_set(20)
        np.testing.assert_allclose(tuple(twist.rotation_quaternion), static, atol=1e-6)
        self.assertNotIn("MMD_GuitarPrep", bpy.data.actions)

    def test_reads_the_original_mocap(self):
        """Applying again reads the mocap without the prep: the strengths do not compound."""
        perform(self.obj)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        first = self.sample(["右手首", "左人指２"])
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        second = self.sample(["右手首", "左人指２"])
        for name in first:
            np.testing.assert_allclose(second[name], first[name], atol=1e-5)

    def test_roll_keeps_the_hands(self):
        perform(self.obj)
        only(self.options, roll_to_twist=True)
        names = ["右手首", "左手首", "右人指先", "左小指先"]
        before = self.sample(names)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        after = self.sample(names + ["右ひじ", "右手捩"])
        for name in names:
            np.testing.assert_allclose(after[name], before[name], atol=1e-5)
        # The twist bone took the roll about the forearm: none of it is left between it and the hand.
        bones = self.obj.data.bones
        axis = np.array(bones["右手首"].head_local - bones["右手捩"].head_local)
        hand = prep.from_matrices(after["右手首"][:, :3, :3])
        twist = prep.from_matrices(after["右手捩"][:, :3, :3])
        rest = [prep.from_matrices(np.array(self.obj.data.bones[n].matrix_local)[None, :3, :3])[0]
                for n in ("右手首", "右手捩")]
        relative = prep.qmul(prep.qinv(prep.qmul(twist, prep.qinv(rest[1]))), prep.qmul(hand, prep.qinv(rest[0])))
        self.assertLess(np.abs(prep.twist_angles(relative, axis)).max(), 1e-3)
        roll = self.sample(["右手捩"], basis=True)["右手捩"]
        self.assertGreater(prep.angles(prep.from_matrices(roll[:, :3, :3])).max(), math.radians(15.0))

    def test_strokes_and_fingers(self):
        perform(self.obj)
        before = self.sample(["右手首", "右ひじ"] + FINGER_JOINTS, basis=False)
        basis_before = self.sample(FINGER_JOINTS, basis=True)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        after = self.sample(["右手首", "右ひじ"] + FINGER_JOINTS, basis=False)
        basis_after = self.sample(FINGER_JOINTS, basis=True)

        def relative(poses):
            return prep.qmul(prep.qinv(prep.from_matrices(poses["右ひじ"][:, :3, :3])),
                             prep.from_matrices(poses["右手首"][:, :3, :3]))
        rms = [prep.detail_rms(relative(p), 1.0, FPS) for p in (before, after)]
        self.assertGreater(rms[1], 1.3 * rms[0])
        speed = [np.percentile(prep.speeds(relative(p), FPS), 95) for p in (before, after)]
        self.assertGreater(speed[1], 1.3 * speed[0])
        # The swing moved the right wrist and elbow along the strum.
        self.assertGreater(np.abs(after["右手首"][:, :3, 3] - before["右手首"][:, :3, 3]).max(), 1e-3)
        # Fretting fingers: quicker presses, within their range plus the margin.
        for name in ("左人指", "左薬指"):
            joints = [name + digit for digit in "１２３"]
            bends = [prep.bend([prep.from_matrices(basis[j][:, :3, :3]) for j in joints])
                     for basis in (basis_before, basis_after)]
            self.assertLess(np.median(prep.transitions(bends[1])), np.median(prep.transitions(bends[0])))
        for name in FINGER_JOINTS:
            a0 = prep.angles(prep.from_matrices(basis_before[name][:, :3, :3]))
            a1 = prep.angles(prep.from_matrices(basis_after[name][:, :3, :3]))
            self.assertLessEqual(a1.max(), a0.max() + self.options.joint_margin + 1e-4)
        self.assertIn("presses and releases", self.options.report)

    def test_picking_fingers(self):
        perform(self.obj, strum=False, fingers=False)
        names = [f"右{finger}{digit}" for finger in ("人指", "中指") for digit in "１２３"]
        bend = presses(FRAMES, rise=6)
        for i, f in enumerate(FRAMES):
            self.scene.frame_set(f)
            for name in names:
                pbone = self.obj.pose.bones[name]
                pbone.rotation_quaternion = Quaternion((1.0, 0.0, 0.0), 0.5 * bend[i])
                pbone.keyframe_insert("rotation_quaternion")
        only(self.options, snap_fingers=2.0)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        keyed = {c.data_path.split('"')[1] for c in keys.fcurves(prepjob.prep_action(self.obj))}
        self.assertFalse(keyed & set(names))
        self.options.snap_picking = True
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        keyed = {c.data_path.split('"')[1] for c in keys.fcurves(prepjob.prep_action(self.obj))}
        self.assertTrue(set(names) <= keyed)
        self.assertIn("right fingers", self.options.report)

    def test_intensity_scales_toward_neutral(self):
        perform(self.obj)
        self.options.intensity = 0.0
        self.options.roll_to_twist = False
        self.assertFalse(prepjob.Strengths.of(self.options).neutral(True))
        with self.assertRaisesRegex(RuntimeError, "nothing to apply"):
            bpy.ops.gtr.apply_prep()
        self.options.intensity = 0.5
        strengths = prepjob.Strengths.of(self.options)
        self.assertAlmostEqual(strengths.range_wrist, 1.25)
        self.assertAlmostEqual(strengths.snap_strokes, 1.5)
        self.assertAlmostEqual(strengths.swing, 0.5)

    def test_cancel_changes_nothing(self):
        perform(self.obj)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.scene.frame_set(7)
        before = set(bpy.data.actions.keys()), tracks(self.obj), self.sample(["右手首"], frames=(7,))
        job = prepjob.PrepJob(bpy.context)
        job.step(bpy.context)
        job.step(bpy.context)
        self.assertTrue(all(track.mute for track in self.obj.animation_data.nla_tracks if track.name == "GuitarPrep"))
        job.cancel(bpy.context)
        self.assertEqual(self.scene.frame_current, 7)
        self.assertFalse(any(track.mute for track in self.obj.animation_data.nla_tracks))
        after = set(bpy.data.actions.keys()), tracks(self.obj), self.sample(["右手首"], frames=(7,))
        self.assertEqual(after[:2], before[:2])
        np.testing.assert_allclose(after[2]["右手首"], before[2]["右手首"], atol=1e-6)

    def test_context_frames(self):
        perform(self.obj, frames=range(1, 121))
        self.settings.use_scene_frame_range = False
        self.settings.frame_start, self.settings.frame_end = 50, 70
        job = prepjob.PrepJob(bpy.context)
        self.assertEqual((job.frames[0], job.frames[-1]), (5, 115))
        job.run(bpy.context)
        strip = self.obj.animation_data.nla_tracks["GuitarPrep"].strips[0]
        self.assertEqual((strip.frame_start, strip.frame_end), (50.0, 70.0))
        self.settings.frame_end = 80
        self.assertTrue(any("covers frames 50-70" in text for _, text in prepjob.status(self.settings)))

    def test_panel(self):
        perform(self.obj)
        labels = []

        def draw():
            labels.clear()
            for cls in panels.CLASSES:
                poll = getattr(cls, "poll", None)
                if poll is None or poll(bpy.context):
                    cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
            return labels

        self.assertTrue(any("Apply Prep touches up" in label for label in draw()))
        self.assertTrue(bpy.ops.gtr.apply_prep.poll())
        self.assertFalse(bpy.ops.gtr.remove_prep.poll())
        self.assertFalse(bpy.ops.gtr.toggle_prep.poll())
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.assertTrue(bpy.ops.gtr.remove_prep.poll())
        self.assertTrue(any(label.startswith("Prepped frames") for label in draw()))
        self.assertFalse(bpy.ops.gtr.remove_bake.poll())


class PrepBakeTest(unittest.TestCase):
    """The prep layer with the bake: NLA order, and the solve reading the prep."""

    def setUp(self):
        self.obj, self.root = setup_scene(build_rig=rigs.mmd)
        self.scene = bpy.context.scene
        self.scene.render.fps, self.scene.render.fps_base = 30, 1.0
        self.settings = self.scene.gtr
        self.rig = build.find(self.settings)
        frames = range(1, 31)
        animate(self.obj, self.root, frames=frames)
        perform(self.obj, frames=frames, elbow=0.0)
        plain(self.settings)
        self.source = self.obj.animation_data.action

    def test_layers(self):
        source = self.source.name
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarPrep", "GuitarBake", "GuitarRefine"])
        bake_action = keys.bake_strips(self.obj)[keys.ARM][1].action
        self.assertEqual(bake_action[keys.PREP_SERIAL_PROP], keys.prep_serial(self.obj))
        self.assertEqual(prepjob.status(self.settings), [])
        # Re-prep after the bake: under the bake, and the bake is now older.
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarPrep", "GuitarBake", "GuitarRefine"])
        self.assertIn("bake again", self.settings.prep.report)
        self.assertTrue(any("bake again" in text for _, text in prepjob.status(self.settings)))
        # A re-bake keeps the prep, and so does Remove Bake.
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarPrep", "GuitarBake", "GuitarRefine"])
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarPrep"])
        self.assertIsNone(self.obj.animation_data.action)
        # Bake then prep, then Remove Prep keeps the bake; the source comes back once both are gone.
        self.assertEqual(bpy.ops.gtr.remove_prep(), {'FINISHED'})
        self.assertEqual(self.obj.animation_data.action, self.source)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarPrep", "GuitarBake", "GuitarRefine"])
        self.assertEqual(bpy.ops.gtr.remove_prep(), {'FINISHED'})
        self.assertEqual(tracks(self.obj), [source, "GuitarBake", "GuitarRefine"])
        self.assertEqual(prepjob.status(self.settings), [])     # the bake was made before the prep
        self.assertIsNone(self.obj.animation_data.action)
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertEqual(self.obj.animation_data.action, self.source)
        self.assertEqual(len(self.obj.animation_data.nla_tracks), 0)

    def test_solve_and_bake_read_the_prep(self):
        frame = 12
        self.scene.frame_set(frame)
        raw = solver.solve(bpy.context, self.rig).sides['R'].fk_wrist.copy()
        build.deactivate(self.settings)
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        self.scene.frame_set(frame)
        prepped = world(self.obj, "右手首")
        self.assertGreater((prepped.translation - raw).length, 1e-4)     # the swing moved the wrist
        result = solver.solve(bpy.context, self.rig)
        self.assertLess((result.sides['R'].fk_wrist - prepped.translation).length, 1e-6)
        build.deactivate(self.settings)
        job = baker.BakeJob(bpy.context, self.rig)
        while job.pre_index < len(job.prepass):
            job.step(bpy.context)
        while job.frame < frame:
            job.step(bpy.context)
        job.step(bpy.context)
        sampled = self.obj.matrix_world @ Matrix(job.fk["右手首"][frame - 1].tolist())
        job.cancel(bpy.context)
        np.testing.assert_allclose(np.array(sampled), np.array(prepped), atol=1e-6)
        # Muted (Show Original), the prep is not read, and the bake says so.
        self.assertEqual(bpy.ops.gtr.toggle_prep(original=True), {'FINISHED'})
        self.scene.frame_set(frame)
        self.assertLess((solver.solve(bpy.context, self.rig).sides['R'].fk_wrist - raw).length, 1e-6)
        build.deactivate(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertIn("without the prep", self.settings.bake_report)
        self.assertTrue(any("bake again" in text for _, text in prepjob.status(self.settings)))

    def test_bake_keeps_the_prepped_strokes(self):
        """The bake keys the picking hand from the prep's world rotation, and leaves the twist bone to the prep."""
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        prepped = {}
        for f in (5, 15, 25):
            self.scene.frame_set(f)
            prepped[f] = world(self.obj, "右手首").to_quaternion()
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        bake_action = keys.bake_strips(self.obj)[keys.ARM][1].action
        self.assertNotIn("右手捩", {c.data_path.split('"')[1] for c in keys.fcurves(bake_action)})
        for f, q in prepped.items():
            self.scene.frame_set(f)
            self.assertLess(world(self.obj, "右手首").to_quaternion().rotation_difference(q).angle, 1e-3)


@unittest.skipUnless(os.environ.get("GTR_TEST_PMX") and os.environ.get("GTR_TEST_VMD"),
                     "set GTR_TEST_PMX and GTR_TEST_VMD to run the prep on a real MMD model and motion")
class MMDPartTest(unittest.TestCase):
    """Apply Prep on a real model and motion imported with mmd_tools, compared with the prototype's results on
    example.pmx and part1.vmd (mocap_prep_plan §11). Needs the mmd_tools extension; GTR_TEST_PMX and
    GTR_TEST_VMD point at the files."""

    def setUp(self):
        import addon_utils
        name = next((m.__name__ for m in addon_utils.modules() if m.__name__.endswith("mmd_tools")), None)
        if name is None:
            self.skipTest("mmd_tools is not installed")
        addon_utils.enable(name, default_set=True)
        rigs.clear_scene()
        bpy.ops.mmd_tools.import_model(filepath=os.environ["GTR_TEST_PMX"], types={'ARMATURE'}, scale=0.08,
                                       log_level='WARNING')
        root = bpy.context.view_layer.objects.active
        self.obj = next(o for o in [root, *root.children_recursive] if o.type == 'ARMATURE')
        for other in bpy.context.selected_objects:
            other.select_set(False)
        self.obj.select_set(True)
        bpy.context.view_layer.objects.active = self.obj
        bpy.ops.mmd_tools.import_vmd(filepath=os.environ["GTR_TEST_VMD"], scale=0.08, margin=0, log_level='WARNING')
        auto_map_and_calibrate(self.obj)

    def test_matches_the_prototype(self):
        """Within 5 % of the prototype's numbers (mocap_prep_plan §11), with its finger snap of 3."""
        options = bpy.context.scene.gtr.prep
        options.snap_fingers = 3.0
        self.assertEqual(bpy.ops.gtr.apply_prep(), {'FINISHED'})
        report = options.report
        print(report)
        numbers = {
            r"wrist's travel above 1 Hz: ([\d.]+) → ([\d.]+) cm RMS \(99th percentile ([\d.]+) → ([\d.]+)": (
                0.3, 1.3, 1.2, 3.4),
            r"pick point's ([\d.]+) → ([\d.]+) cm RMS": (0.9, 2.7),
            r"turns above 1 Hz: ([\d.]+)° → ([\d.]+)° RMS, speed (\d+) → (\d+)": (10.1, 17.3, 315.0, 718.0),
            r"presses and releases: (\d+) → (\d+) frames": (5.0, 2.0),
        }
        for pattern, expected in numbers.items():
            found = re.search(pattern, report)
            self.assertIsNotNone(found, pattern)
            for got, want in zip(found.groups(), expected):
                self.assertAlmostEqual(float(got), want, delta=max(0.05 * want, 0.051), msg=pattern)
