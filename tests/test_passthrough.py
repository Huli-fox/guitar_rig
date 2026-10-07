"""Magnet pass-through of quick wrist motion (mocap prep §6.2) and Smooth on the correction (§6.4)."""

import math
import unittest

import bpy
import numpy as np
from mathutils import Vector

import rigs
from guitar_rig.core import diagnostics, keys, landmarks, prep, solver
from guitar_rig.rig import build
from test_baker import BakeTest, animate, plain
from test_solve import chain

FRAMES = range(1, 61)
FPS = 30.0


def strum(obj, root, frames=FRAMES, amplitude=0.03, frequency=3.0):
    """The bake test's performance, with the right wrist moving `amplitude` metres up and down at `frequency` Hz
    about a point near the strum line."""
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = int(FPS), 1.0
    animate(obj, root, frames=frames)
    unit = 1.0 / scene.unit_settings.scale_length
    found = landmarks.find(root)
    names = chain(obj, 'R')
    for f in frames:
        scene.frame_set(f)
        strum_a = found["STRUM_A"].matrix_world.translation.copy()
        t = (f - frames[0]) / FPS
        offset = Vector((0.0, -0.05, amplitude * math.sin(2.0 * math.pi * frequency * t))) * unit
        rigs.reach(obj, *names, strum_a + offset, Vector((0.0, 0.5, -1.0)))
        for name in names:
            pbone = obj.pose.bones[name]
            pbone.keyframe_insert("rotation_quaternion" if pbone.rotation_mode == 'QUATERNION' else
                                  "rotation_euler")
    scene.frame_set(frames[0])


def wrist_track(obj, side='R', frames=FRAMES):
    """The wrist's path in the chest bone's space (n, 3), as played."""
    scene = bpy.context.scene
    chest_name = obj.gtr_char.bone_map.chest
    points = []
    for f in frames:
        scene.frame_set(f)
        chest = obj.matrix_world @ obj.pose.bones[chest_name].matrix
        points.append(np.array(chest.inverted() @ (obj.matrix_world @ obj.pose.bones[chain(obj, side)[2]].head)))
    return np.array(points)


class DetailTest(unittest.TestCase):
    def test_details(self):
        settings = bpy.context.scene.gtr
        n = 90
        t = np.arange(n) / FPS
        chest = np.tile(np.eye(4), (n, 1, 1))
        chest[:, 0, 3] = 0.3 * t                    # the body walks along x, and turns about z
        turn = 0.2 * t
        chest[:, 0, 0], chest[:, 0, 1], chest[:, 1, 0], chest[:, 1, 1] = (np.cos(turn), -np.sin(turn), np.sin(turn),
                                                                          np.cos(turn))
        local = np.stack((np.full(n, 0.3), 0.01 * np.sin(2.0 * math.pi * 3.0 * t), np.full(n, 0.2)), -1)
        world = np.einsum("nij,nj->ni", chest[:, :3, :3], local) + chest[:, :3, 3]
        settings.passthrough_hands, settings.passthrough_gain = {'R'}, 1.0
        details = solver.passthrough_details(settings, {'L': world, 'R': world}, chest, FPS)
        self.assertEqual(set(details), {'R'})
        expected = np.einsum("nij,nj->ni", chest[:, :3, :3], local - (0.3, 0.0, 0.2))
        np.testing.assert_allclose(details['R'][20:-20], expected[20:-20], atol=1.5e-3)
        # A wrist carried by the body has nothing to pass through, however the body moves.
        still = np.einsum("nij,j->ni", chest[:, :3, :3], (0.3, 0.0, 0.2)) + chest[:, :3, 3]
        self.assertLess(np.abs(solver.passthrough_details(settings, {'R': still}, chest, FPS)['R']).max(), 1e-9)
        settings.passthrough_gain = 0.0
        self.assertEqual(solver.passthrough_details(settings, {'R': world}, chest, FPS), {})
        settings.property_unset("passthrough_gain")

    def test_window(self):
        scene = bpy.context.scene
        scene.frame_start, scene.frame_end = 1, 300
        scene.gtr.use_scene_frame_range = True
        self.assertEqual(solver.passthrough_window(scene, 100, 30.0), list(range(40, 161)))
        self.assertEqual(solver.passthrough_window(scene, 10, 30.0), list(range(1, 71)))
        self.assertEqual(solver.passthrough_window(scene, 400, 30.0)[-1], 400)


class PassThroughBakeTest(BakeTest):
    def travel(self):
        return prep.travel(wrist_track(self.obj), 1.0, FPS)[0]

    def test_strokes_pass_through_the_magnets(self):
        strum(self.obj, self.root)
        plain(self.settings)
        fk = self.travel()
        self.assertGreater(fk, 0.015)
        travel = {}
        for gain in (0.0, 1.0):
            self.settings.passthrough_gain = gain
            self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
            travel[gain] = self.travel()
        self.assertLess(travel[0.0], 0.6 * fk)              # the strum-line magnet takes the stroke back
        self.assertAlmostEqual(travel[1.0], fk, delta=0.2 * fk)
        # The bake plays what Solve Frame shows, and the strokes stay out of the barriers.
        self.assert_matches_solve(frames=(1, 17, 40, 60))
        result = solver.solve(bpy.context, self.rig)
        self.assertIsNotNone(result.sides['R'].passthrough)
        self.assertIsNone(result.sides['L'].passthrough)
        build.deactivate(self.settings)
        self.assertEqual(bpy.ops.gtr.reclamp(), {'FINISHED'})
        self.assertIn("No frame", self.settings.bake_report)
        found = diagnostics.read(diagnostics.find(self.settings))
        self.assertIn("R pass-through (cm)", found[1])
        self.assertGreater(np.nanmax(found[1]["R pass-through (cm)"][1]), 1.0)

    def test_smooth_keeps_the_strokes(self):
        strum(self.obj, self.root)
        plain(self.settings)
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        baked = self.travel()
        action = keys.bake_strips(self.obj)[keys.ARM][1].action
        before = {(c.data_path, c.array_index): keys.read(c)[1] for c in keys.fcurves(action)}
        self.settings.smooth_cutoff_arms = 2.0
        self.assertEqual(bpy.ops.gtr.smooth_bake(), {'FINISHED'})
        self.assertIn("correction", self.settings.bake_report)
        after = {(c.data_path, c.array_index): keys.read(c)[1] for c in keys.fcurves(action)}
        self.assertTrue(any(np.abs(after[key] - values).max() > 1e-5 for key, values in before.items()))
        self.assertAlmostEqual(self.travel(), baked, delta=0.1 * baked)
        self.assertFalse(any(track.mute for track in self.obj.animation_data.nla_tracks))
        # Smoothing the keys themselves takes the strokes out.
        self.assertEqual(bpy.ops.gtr.bake(), {'FINISHED'})
        self.settings.smooth_mode = 'KEYS'
        self.assertEqual(bpy.ops.gtr.smooth_bake(), {'FINISHED'})
        self.assertLess(self.travel(), 0.5 * baked)
