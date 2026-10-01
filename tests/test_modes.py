import unittest
from types import SimpleNamespace

import bpy

from guitar_rig.core import modes, solver
from guitar_rig.rig import build
from test_addon import FakeLayout
from test_baker import BakeTest, animate, plain, played


def settings_with(ranges=(), mode='FOLLOW', aim_enabled=True, aim_weight=1.0):
    items = [SimpleNamespace(enabled=enabled, frame_start=start, frame_end=end, mode=m)
             for start, end, m, enabled in ((*r, True) if len(r) == 3 else r for r in ranges)]
    return SimpleNamespace(mode=mode, aim_enabled=aim_enabled, aim_weight=aim_weight, range_overrides=items)


class ScheduleTest(unittest.TestCase):
    def test_without_ranges(self):
        schedule = modes.Schedule(settings_with(mode='ALIGN', aim_enabled=False))
        frame_mode = schedule.at(7)
        self.assertEqual((frame_mode.mode, frame_mode.override, frame_mode.aim_weight, frame_mode.run_start),
                         ('ALIGN', modes.SCENE, 0.0, False))
        self.assertEqual(modes.Schedule(settings_with(aim_weight=0.7)).at(3).aim_weight, 0.7)

    def test_fade(self):
        schedule = modes.Schedule(settings_with([(10, 20, 'ALIGN')]))
        weights = {f: schedule.at(f).aim_weight for f in range(5, 30)}
        self.assertEqual(weights[9], 1.0)
        for frame, weight in ((10, 0.8), (11, 0.6), (13, 0.2), (14, 0.0), (20, 0.0), (21, 0.2), (24, 0.8),
                              (25, 1.0)):
            self.assertAlmostEqual(weights[frame], weight, msg=frame)
        self.assertEqual([f for f in range(5, 30) if schedule.at(f).run_start], [10, 21])
        self.assertEqual((schedule.at(15).mode, schedule.at(15).override), ('ALIGN', 0))
        self.assertEqual((schedule.at(21).mode, schedule.at(21).override), ('FOLLOW', modes.SCENE))

    def test_short_ranges_do_not_jump(self):
        """Runs shorter than the fade start from wherever the weight was: it never steps more than one fade
        step per frame."""
        schedule = modes.Schedule(settings_with([(10, 11, 'ALIGN'), (13, 13, 'ALIGN'), (15, 40, 'ALIGN')]))
        weights = {f: schedule.at(f).aim_weight for f in range(5, 45)}
        steps = [abs(weights[f + 1] - weights[f]) for f in range(5, 44)]
        self.assertLessEqual(max(steps), 1.0 / modes.FADE_FRAMES + 1e-9)
        self.assertEqual(weights[40], 0.0)
        self.assertAlmostEqual(weights[44], 0.8)

    def test_overlaps_and_disabled_ranges(self):
        schedule = modes.Schedule(settings_with([(1, 100, 'ALIGN'), (40, 60, 'FOLLOW'), (50, 55, 'ALIGN', False),
                                                 (70, 60, 'FOLLOW')]))
        self.assertEqual(schedule.at(45).override, 1)       # the lower range wins
        self.assertEqual(schedule.at(52).mode, 'FOLLOW')    # the disabled one does not count
        self.assertEqual(schedule.at(65).override, 0)       # the inverted one is ignored
        runs = schedule.runs(30, 70)
        self.assertEqual([(first, last, m.mode) for first, last, m in runs],
                         [(30, 39, 'ALIGN'), (40, 60, 'FOLLOW'), (61, 70, 'ALIGN')])

    def test_magnet_switch(self):
        """A range switches the fretboard-edge magnet like the mode buttons; the scene's frames keep whatever the
        magnets were set to."""
        edge = SimpleNamespace(preset_id="FRETBOARD_EDGE", power=-50.0, filter='ONE_EURO')
        other = SimpleNamespace(preset_id="FRETBOARD_PLANE", power=1.0, filter='NONE')
        schedule = modes.Schedule(settings_with([(10, 20, 'ALIGN'), (30, 40, 'FOLLOW')]))
        inside, follow, outside = schedule.at(15), schedule.at(35), schedule.at(5)
        self.assertEqual((inside.magnet(edge, "power"), inside.magnet(edge, "filter")), (1.0, 'NONE'))
        self.assertEqual((follow.magnet(edge, "power"), follow.magnet(edge, "filter")), (-99.0, 'ROTATION_BASED'))
        self.assertEqual((outside.magnet(edge, "power"), outside.magnet(edge, "filter")), (-50.0, 'ONE_EURO'))
        self.assertEqual(inside.magnet(other, "power"), 1.0)


class RangeBakeTest(BakeTest):
    def add_range(self, start, end, mode='ALIGN'):
        self.scene.frame_set(start)
        self.assertEqual(bpy.ops.gtr.range_add(), {'FINISHED'})
        item = self.settings.range_overrides[-1]
        item.frame_start, item.frame_end, item.mode = start, end, mode
        return item

    def test_solve_frame_follows_the_range(self):
        animate(self.obj, self.root)
        self.add_range(3, 5)
        self.scene.frame_set(4)
        result = solver.solve(bpy.context, self.rig)
        self.assertEqual((result.mode, result.frame_mode.override), ('ALIGN', 0))
        self.assertAlmostEqual(result.frame_mode.aim_weight, 0.6)
        self.assertIsNotNone(result.neck)
        edge = next(i for i, m in enumerate(self.settings.magnets) if m.preset_id == "FRETBOARD_EDGE")
        hit = result.hit(edge)
        self.assertTrue(hit is not None and hit.weight == 1.0 and not hit.barrier)     # snaps, as in ALIGN
        self.scene.frame_set(7)
        self.assertEqual(solver.solve(bpy.context, self.rig).mode, 'FOLLOW')
        build.deactivate(self.settings)
        # The scene's own settings did not change.
        self.assertEqual((self.settings.mode, self.settings.magnets[edge].power), ('FOLLOW', -99.0))

    def test_bake_plays_the_solve(self):
        animate(self.obj, self.root)
        plain(self.settings)
        self.add_range(3, 5)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.assertIn("Modes: 1-2 Follow, 3-5 Align*, 6-8 Follow", self.settings.bake_report)
        self.assert_matches_solve()

    def test_filters_restart_at_a_change(self):
        """With the filters on, the first frame of a run is baked unfiltered, like the first frame of a bake."""
        animate(self.obj, self.root)
        for item in self.settings.magnets:
            item.hysteresis = 1.0
        self.add_range(4, 8)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        arms, _ = played(self.obj, self.root, self.rig, 4)
        result = solver.solve(bpy.context, self.rig)
        build.deactivate(self.settings)
        for side in arms:
            self.assertLess((arms[side][0] - result.sides[side].wrist).length, 1e-4)
        arms, _ = played(self.obj, self.root, self.rig, 5)
        result = solver.solve(bpy.context, self.rig)
        build.deactivate(self.settings)
        self.assertGreater(max((arms[side][0] - result.sides[side].wrist).length for side in arms), 1e-4)

    def test_operators_and_panel(self):
        from guitar_rig.ui import lists, panels
        self.scene.frame_set(12)
        self.assertFalse(bpy.ops.gtr.range_remove.poll())
        self.assertEqual(bpy.ops.gtr.range_add(), {'FINISHED'})
        item = self.settings.range_overrides[0]
        self.assertEqual((item.frame_start, item.mode), (12, 'ALIGN'))
        self.assertGreaterEqual(item.frame_end, item.frame_start)
        labels = []
        for cls in panels.CLASSES:
            poll = getattr(cls, "poll", None)
            if poll is None or poll(bpy.context):
                cls.draw(SimpleNamespace(layout=FakeLayout(self, labels)), bpy.context)
        self.assertIn("Frame 12: Align (range 1), neck aim fading (0.80)", labels)
        lists.GTR_UL_ranges.draw_item(None, bpy.context, FakeLayout(self), self.settings, item, 0, self.settings,
                                      "active_range_index")
        self.assertEqual(bpy.ops.gtr.range_remove(), {'FINISHED'})
        self.assertEqual(len(self.settings.range_overrides), 0)
