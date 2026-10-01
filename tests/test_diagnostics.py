import unittest
from types import SimpleNamespace

import bpy
import numpy as np

from guitar_rig.core import diagnostics, keys, solver
from guitar_rig.rig import build
from guitar_rig.ui import panels
from test_addon import FakeLayout
from test_baker import FRAMES, BakeTest, animate, plain


class ScoresTest(unittest.TestCase):
    def test_scores(self):
        frames = np.array((1.0, 2.0, 3.0))
        nan = np.nan
        curves = {
            "L wrist correction (cm)": ({"kind": 'CORRECTION', "side": 'L', "barrier": 0}, np.array((1.0, 5.0, 2.0))),
            "R wrist correction (cm)": ({"kind": 'CORRECTION', "side": 'R', "barrier": 0}, np.array((4.0, nan, 1.0))),
            "L Edge d (cm)": ({"kind": 'DISTANCE', "side": 'L', "barrier": 1}, np.array((2.0, -3.0, -0.5))),
            "L Plane d (cm)": ({"kind": 'DISTANCE', "side": 'L', "barrier": 0}, np.array((-9.0, -9.0, -9.0))),
            "solve passes": ({"kind": 'PASSES', "side": "", "barrier": 0}, np.array((2.0, 5.0, 5.0))),
            "settled": ({"kind": 'SETTLED', "side": "", "barrier": 0}, np.array((1.0, 0.0, 1.0))),
        }
        np.testing.assert_allclose(diagnostics.scores(frames, curves, 'CORRECTION'), (4.0, 5.0, 2.0))
        np.testing.assert_allclose(diagnostics.scores(frames, curves, 'BARRIER'), (0.0, 3.0, 0.5))    # barriers only
        np.testing.assert_allclose(diagnostics.scores(frames, curves, 'UNSETTLED'), (0.0, 5.0, 0.0))
        self.assertTrue(np.isnan(diagnostics.scores(frames, curves, 'SWING')).all())
        self.assertEqual(diagnostics.format_value('CORRECTION', 3.14159), "3.1 cm")
        self.assertEqual(diagnostics.format_value('SWING', 12.0), "12.0°")

    def test_labels(self):
        items = [SimpleNamespace(name='Strum "Line"', kind='LINE', crossable=True),
                 SimpleNamespace(name="Edge", kind='PLANE', crossable=False),
                 SimpleNamespace(name="Edge", kind='PLANE', crossable=True)]
        recorder = diagnostics.Recorder((1, 2), items)
        self.assertEqual(recorder.labels, {0: "Strum 'Line'", 1: "Edge #2", 2: "Edge #3"})
        self.assertEqual(recorder.barriers, {1})


class DiagnosticsBakeTest(BakeTest):
    def curves(self):
        obj = diagnostics.find(self.settings)
        return {fc.data_path[2:-2]: keys.read(fc) for fc in keys.fcurves(diagnostics.action_of(obj))}

    def test_curves_record_the_solve(self):
        animate(self.obj, self.root)
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        obj = diagnostics.find(self.settings)
        self.assertEqual(obj.name, diagnostics.OBJECT_NAME)
        curves = self.curves()
        for side in "LR":
            for name in (f"{side} wrist correction (cm)", f"{side} IK miss (mm)"):
                self.assertIn(name, curves)
        for name, (frames, _values) in curves.items():
            np.testing.assert_array_equal(frames, np.array(FRAMES, dtype=float), name)
        # The values are the solve's: Solve Frame gives the same on a bake without filters.
        frame, i = 5, list(FRAMES).index(5)
        self.scene.frame_set(frame)
        result = solver.solve(bpy.context, self.rig)
        build.deactivate(self.settings)
        cm = 100.0 * result.metres_per_bu
        for side, side_result in result.sides.items():
            moved = (side_result.target - side_result.fk_wrist).length * cm
            self.assertAlmostEqual(curves[f"{side} wrist correction (cm)"][1][i], moved, places=3)
            for index, hit in side_result.hits:
                label = self.settings.magnets[index].name
                self.assertAlmostEqual(curves[f"{side} {label} d (cm)"][1][i], hit.signed * cm, places=3)
                self.assertAlmostEqual(curves[f"{side} {label} w"][1][i], hit.weight, places=5)
        self.assertAlmostEqual(curves["neck swing (°)"][1][i], np.degrees(result.swing), places=3)
        # The curves animate the empty's custom properties.
        self.scene.frame_set(frame)
        self.assertAlmostEqual(obj["L wrist correction (cm)"], curves["L wrist correction (cm)"][1][i], places=4)

    def test_jump_to_worst_frame(self):
        animate(self.obj, self.root)
        self.assertFalse(bpy.ops.gtr.jump_worst_frame.poll())
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        curves = self.curves()
        correction = np.maximum(curves["L wrist correction (cm)"][1], curves["R wrist correction (cm)"][1])
        order = np.argsort(-correction)
        self.assertEqual(bpy.ops.gtr.jump_worst_frame(metric='CORRECTION'), {'FINISHED'})
        self.assertEqual(self.scene.frame_current, FRAMES[order[0]])
        self.assertEqual(bpy.ops.gtr.jump_worst_frame(metric='CORRECTION', rank=2), {'FINISHED'})
        self.assertEqual(self.scene.frame_current, FRAMES[order[1]])
        ranked = diagnostics.ranking(diagnostics.find(self.settings), 'CORRECTION')
        self.assertEqual([frame for frame, _ in ranked], [FRAMES[i] for i in order[:diagnostics.RANK_COUNT]])
        self.assertAlmostEqual(ranked[0][1], correction[order[0]], places=4)
        # A measure nothing scores in: nothing to jump to.
        self.assertEqual(bpy.ops.gtr.jump_worst_frame(metric='COLLIDER'), {'CANCELLED'})

    def test_rebake_and_remove(self):
        animate(self.obj, self.root)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        obj = diagnostics.find(self.settings)
        first = diagnostics.action_of(obj)
        before = diagnostics.ranking(obj, 'CORRECTION')
        actions = len(bpy.data.actions)
        self.settings.magnets[0].enabled = False     # the strum line: the right hand moves less
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertIs(diagnostics.find(self.settings), obj)
        self.assertEqual(len(bpy.data.actions), actions)
        second = diagnostics.action_of(obj)
        self.assertEqual(second[diagnostics.SERIAL_PROP], 2)
        self.assertNotIn(f"R {self.settings.magnets[0].name} w", obj.keys())
        self.assertNotEqual(diagnostics.ranking(obj, 'CORRECTION'), before)     # the cache follows the bake
        self.assertNotIn(first, list(bpy.data.actions))
        self.assertEqual(bpy.ops.gtr.remove_bake(), {'FINISHED'})
        self.assertIsNone(diagnostics.find(self.settings))
        self.assertNotIn(diagnostics.OBJECT_NAME, bpy.data.objects)
        self.assertNotIn(diagnostics.OBJECT_NAME, bpy.data.actions)

    def test_panel_and_select(self):
        def draw():
            labels = []
            for cls in panels.CLASSES:
                poll = getattr(cls, "poll", None)
                if poll is None or poll(bpy.context):
                    cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
            return labels

        animate(self.obj, self.root)
        self.assertTrue(any(label.startswith("Bake to record") for label in draw()))
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertTrue(any("curves hold every frame" in label for label in draw()))
        self.settings.diagnostics_metric = 'COLLIDER'
        self.assertIn("No frame has any chest collider", draw())
        self.assertEqual(bpy.ops.gtr.show_diagnostics(), {'FINISHED'})
        self.assertIs(bpy.context.view_layer.objects.active, diagnostics.find(self.settings))
