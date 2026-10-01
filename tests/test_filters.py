import math
import unittest
from types import SimpleNamespace

import numpy as np
from mathutils import Quaternion, Vector

from guitar_rig.core import collider, filters, magnets, solver
from guitar_rig.core.mathx import rotation_angle


class OneEuroTest(unittest.TestCase):
    def test_first_sample_passes(self):
        filt = filters.OneEuro('SCALAR', (1.0, 0.0, 1.0), 30.0)
        self.assertEqual(filt(5.0), 5.0)
        self.assertEqual(filt(5.0), 5.0)

    def test_without_beta_it_is_a_first_order_low_pass(self):
        fs, cutoff = 30.0, 2.0
        filt = filters.OneEuro('SCALAR', (cutoff, 0.0, 1.0), fs)
        filt(0.0)
        a = filters.alpha(cutoff, fs)
        y = 0.0
        for _ in range(5):
            y += a * (1.0 - y)
            self.assertAlmostEqual(filt(1.0), y, places=12)

    def test_speed_raises_the_cutoff(self):
        """A fast move is followed more closely with beta than without."""
        outputs = {}
        for beta in (0.0, 1.0):
            filt = filters.OneEuro('VECTOR', (0.5, beta, 1.0), 30.0)
            for i in range(10):
                y = filt(Vector((i * 0.5, 0.0, 0.0)))
            outputs[beta] = y.x
        self.assertGreater(outputs[1.0], outputs[0.0])
        self.assertLess(outputs[1.0], 4.5)

    def test_quaternions_slerp_and_stay_unit(self):
        filt = filters.OneEuro('QUATERNION', (1.0, 0.5, 1.0), 30.0)
        start, end = Quaternion(), Quaternion((0.0, 0.0, 1.0), 1.0)
        filt(start)
        previous = 0.0
        for _ in range(20):
            y = filt(-end)          # the other sign of the same rotation
            self.assertAlmostEqual(y.magnitude, 1.0, places=6)    # mathutils is single precision
            angle = rotation_angle(start, y)
            self.assertGreater(angle, previous)
            previous = angle
        self.assertLess(rotation_angle(y, end), 0.1)

    def test_bank_passes_start_from_the_committed_state(self):
        bank = filters.FilterBank(30.0)
        params = (1.0, 0.0, 1.0)
        bank.apply("x", 'SCALAR', params, 0.0)
        bank.commit()
        first = bank.apply("x", 'SCALAR', params, 1.0)
        again = bank.apply("x", 'SCALAR', params, 1.0)
        self.assertEqual(first, again)
        bank.discard()
        self.assertEqual(bank.apply("x", 'SCALAR', params, 1.0), first)
        bank.commit()
        self.assertGreater(bank.apply("x", 'SCALAR', params, 1.0), first)


class ButterworthTest(unittest.TestCase):
    def test_unit_dc_gain(self):
        b, a = filters.butterworth(3.0, 30.0)
        self.assertAlmostEqual(sum(b) / sum(a), 1.0, places=12)

    def test_constant_and_linear_signals_pass(self):
        t = np.arange(50, dtype=np.float64)
        for signal in (np.full(50, 2.5), 0.3 * t - 4.0):
            np.testing.assert_allclose(filters.filtfilt(signal, 3.0, 30.0), signal, atol=1e-5)

    def test_zero_phase_and_attenuation(self):
        fs = 30.0
        t = np.arange(300) / fs
        slow = np.sin(2.0 * math.pi * 0.5 * t)
        fast = 0.5 * np.sin(2.0 * math.pi * 12.0 * t)
        out = filters.filtfilt(np.stack((slow + fast, fast), axis=1), 3.0, fs)
        middle = slice(60, 240)
        self.assertLess(np.abs(out[middle, 0] - slow[middle]).max(), 0.01)    # no lag on the slow wave
        self.assertLess(np.abs(out[middle, 1]).max(), 0.02)                  # the fast one is gone

    def test_cutoff_above_nyquist_changes_nothing(self):
        signal = np.random.default_rng(1).normal(size=20)
        self.assertFalse(filters.can_filter(20.0, 30.0))
        np.testing.assert_array_equal(filters.filtfilt(signal, 20.0, 30.0), signal)

    def test_quaternion_signs(self):
        q = np.array([tuple(Quaternion((0.0, 0.0, 1.0), 0.02 * i)) for i in range(40)])
        q[1::2] *= -1.0
        out = filters.smooth_quaternions(q, 3.0, 30.0)
        np.testing.assert_allclose(np.linalg.norm(out, axis=1), 1.0, atol=1e-12)
        for i in range(40):
            expected = Quaternion((0.0, 0.0, 1.0), 0.02 * i)
            self.assertLess(rotation_angle(Quaternion(out[i]), expected), 1e-3)


class ColliderTest(unittest.TestCase):
    def setUp(self):
        self.body = collider.Capsule(Vector((0.0, 0.0, 0.0)), Quaternion(), -0.3, 0.2, 0.12)

    def test_push_to_the_front_surface(self):
        self.assertAlmostEqual(self.body.push(Vector((0.0, 0.0, 0.05))), 0.07)
        self.assertAlmostEqual(self.body.push(Vector((0.0, 0.25, 0.0))), math.sqrt(0.12 ** 2 - 0.05 ** 2))
        self.assertEqual(self.body.push(Vector((0.2, 0.0, 0.05))), 0.0)        # beside it
        self.assertEqual(self.body.push(Vector((0.0, 0.0, -0.05))), 0.0)       # behind the axis
        self.assertEqual(self.body.push(Vector((0.0, -0.5, 0.05))), 0.0)       # below it

    def test_fingertips(self):
        wrist = Vector((0.0, 0.0, 0.2))
        tip = Vector((0.0, 0.0, 0.05))
        moved, contact = collider.push(self.body, wrist, [tip])
        self.assertAlmostEqual(moved.z, 0.27)
        self.assertEqual(contact.weight, 1.0)
        self.assertEqual(contact.deepest, tip)
        same, contact = collider.push(self.body, wrist)
        self.assertEqual(same, wrist)
        self.assertEqual(contact.weight, 0.0)

    def test_scene_capsule(self):
        settings = SimpleNamespace(collider_enabled=False, autoscale_policy='NONE', collider_bottom_m=-0.3,
                                   collider_top_m=0.2, collider_depth_m=0.05, collider_radius_m=0.12)
        cal = SimpleNamespace(ratio_spine=1.0, metres_per_bu=0.01)
        rotation = Quaternion((0.0, 0.0, 1.0), math.pi / 2.0)
        self.assertIsNone(collider.capsule(settings, cal, Vector(), rotation))
        settings.collider_enabled = True
        body = collider.capsule(settings, cal, Vector((1.0, 2.0, 3.0)), rotation)
        self.assertAlmostEqual(body.radius, 12.0)
        self.assertAlmostEqual((body.origin - Vector((1.0, 2.0, 8.0))).length, 0.0)
        self.assertAlmostEqual((body.forward - Vector((0.0, 0.0, 1.0))).length, 0.0)


class ClampOutTest(unittest.TestCase):
    def entry(self, tips=None, crossable=False):
        feature = magnets.Feature('PLANE', Vector((0.0, 0.0, 1.0)), normal=Vector((0.0, 0.0, 1.0)))
        return magnets.Entry(0, feature, magnets.Params(0.1, crossable=crossable), Vector((0.0, 0.0, -0.1)), tips)

    def test_only_pushes_out(self):
        entry = self.entry()
        self.assertTrue(magnets.is_barrier(entry))
        self.assertFalse(magnets.is_barrier(self.entry(crossable=True)))
        wrist, push = magnets.clamp_out(Vector((0.0, 0.0, 1.05)), entry)      # hand point 5 cm behind
        self.assertAlmostEqual(push, 0.05, places=6)
        self.assertAlmostEqual(wrist.z, 1.1, places=6)
        wrist = Vector((0.0, 0.0, 1.3))
        self.assertEqual(magnets.clamp_out(wrist, entry), (wrist, 0.0))

    def test_fingertip_margin(self):
        tips = magnets.Fingertips([Vector((0.0, 0.0, -0.2))], 0.01)
        wrist, push = magnets.clamp_out(Vector((0.0, 0.0, 1.15)), self.entry(tips))
        self.assertAlmostEqual(push, 0.06, places=6)
        self.assertAlmostEqual(wrist.z - 0.2, 1.01, places=6)


class HooksTest(unittest.TestCase):
    """The solver's filter hooks: the first frame passes unchanged, later ones lag."""

    def settings(self, **kwargs):
        values = dict(use_filters=True, use_filter_fingertips=True, filter_fingertip=filters.SAO_FINGERTIP,
                      filter_pull=filters.SAO_PULL, filter_rotation=filters.SAO_ROTATION, use_filter_wrist=True,
                      filter_wrist=filters.SAO_WRIST, use_filter_targets=True, filter_target=filters.SAO_TARGET,
                      use_filter_guitar=True, filter_guitar=filters.SAO_WRIST)
        values.update(kwargs)
        return SimpleNamespace(**values)

    def test_off_without_a_bank(self):
        hooks = solver.Hooks(self.settings(), None, 0.1, Vector())
        self.assertIsNone(hooks.pull('L', 0, 'ROTATION_BASED'))
        self.assertIsNone(hooks.tip('L', 0))
        q = Quaternion((1.0, 0.0, 0.0), 0.3)
        self.assertEqual(hooks.wrist('L', q, Quaternion()), q)
        hooks = solver.Hooks(self.settings(use_filters=False), filters.FilterBank(30.0), 0.1, Vector())
        self.assertIsNone(hooks.pull('L', 0, 'ONE_EURO'))

    def test_rotation_pull_first_frame(self):
        origin = Vector((0.0, 0.0, 0.0))
        point, target = Vector((0.5, 0.1, 0.0)), Vector((0.5, 0.0, 0.0))
        for weight, expected in ((0.0, Vector()), (0.4, (target - point) * 0.4), (1.0, target - point)):
            bank = filters.FilterBank(30.0)
            pull = solver.Hooks(self.settings(), bank, 0.1, origin).pull('L', 5, 'ROTATION_BASED')
            self.assertLess((pull(point, target, weight) - expected).length, 1e-4)

    def test_rotation_pull_lags(self):
        bank = filters.FilterBank(30.0)
        hooks = solver.Hooks(self.settings(), bank, 0.1, Vector())
        target = Vector((0.5, 0.0, 0.0))
        pull = hooks.pull('L', 5, 'ROTATION_BASED')
        pull(Vector((0.5, 0.1, 0.0)), target, 0.0)          # the hand is 10 cm in front of a barrier (normal +Y)
        bank.commit()
        pull = hooks.pull('L', 5, 'ROTATION_BASED')
        point = Vector((0.5, -0.05, 0.0))                   # then behind it: the clamp brings it back in front,
        moved = pull(point, Vector((0.5, 0.0, 0.0)), 1.0)   # from where it settles onto the plane
        after = point + moved
        self.assertLess(abs(after.x - 0.5) + abs(after.z), 1e-9)
        self.assertGreater(after.y, 0.05)
        self.assertLess(after.y, 0.1)

    def test_one_euro_pull_and_tip(self):
        bank = filters.FilterBank(30.0)
        hooks = solver.Hooks(self.settings(), bank, 0.1, Vector())
        pull, tip = hooks.pull('R', 0, 'ONE_EURO'), hooks.tip('R', 2)
        self.assertAlmostEqual((pull(Vector(), Vector((0.1, 0.0, 0.0)), 0.5) - Vector((0.05, 0.0, 0.0))).length, 0.0)
        self.assertAlmostEqual(tip(0.02), 0.02)
        bank.commit()
        hooks = solver.Hooks(self.settings(), bank, 0.1, Vector())
        self.assertLess(hooks.tip('R', 2)(0.0), 0.02)
        self.assertGreater(hooks.tip('R', 2)(0.0), 0.0)

    def test_wrist_runs_relative_to_the_chest(self):
        """A body turn that carries the hand along is not delayed."""
        bank = filters.FilterBank(30.0)
        hooks = solver.Hooks(self.settings(), bank, 0.1, Vector())
        hand = Quaternion((1.0, 0.0, 0.0), 0.3)
        hooks.wrist('L', hand, Quaternion())
        bank.commit()
        turn = Quaternion((0.0, 0.0, 1.0), 0.5)
        self.assertLess(rotation_angle(hooks.wrist('L', turn @ hand, turn), turn @ hand), 1e-6)
