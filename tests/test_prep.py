"""Mocap prep maths (core/prep.py) on synthetic signals."""

import math
import unittest

import numpy as np
from mathutils import Quaternion

from guitar_rig.core import prep

FS = 30.0


def about(axis, angle):
    """Quaternions (n, 4) of rotations by `angle` (n,) about the unit `axis`."""
    return prep.qexp(np.outer(angle, prep.normalize(axis)))


def wave(frequency, seconds=20.0, amplitude=1.0, phase=0.0):
    t = np.arange(int(seconds * FS)) / FS
    return amplitude * np.sin(2.0 * math.pi * frequency * t + phase)


def smooth_step(n, start, frames, low=0.0, high=1.0):
    """A move from `low` to `high` over about `frames` frames starting at `start`, as a raised cosine."""
    x = np.clip((np.arange(n) - start) / frames, 0.0, 1.0)
    return low + (high - low) * (0.5 - 0.5 * np.cos(math.pi * x))


def rise_time(x):
    """10-90 % time of a monotonic rise, in frames (interpolated)."""
    lo, hi = x.min(), x.max()
    p = (x - lo) / (hi - lo)
    index = np.arange(len(x), dtype=np.float64)
    return np.interp(0.9, p, index) - np.interp(0.1, p, index)


class QuaternionTest(unittest.TestCase):
    def test_matrices_round_trip(self):
        rng = np.random.default_rng(1)
        q = prep.continuous(prep.normalize(rng.normal(size=(200, 4))))
        q = np.where(q[:, :1] < 0.0, -q, q)
        np.testing.assert_allclose(prep.from_matrices(prep.to_matrices(q)), q, atol=1e-12)
        for value in q[:5]:
            expected = np.array(Quaternion(value).to_matrix())
            np.testing.assert_allclose(prep.to_matrices(value[None])[0], expected, atol=1e-6)

    def test_log_exp_and_slerp(self):
        r = np.array(((0.0, 0.0, 0.0), (0.3, -0.2, 0.1), (0.0, 3.0, 0.0)))
        np.testing.assert_allclose(prep.qlog(prep.qexp(r)), r, atol=1e-12)
        a, b = about((0.0, 0.0, 1.0), np.zeros(1)), about((0.0, 0.0, 1.0), np.full(1, 1.0))
        np.testing.assert_allclose(prep.angles(prep.slerp(a, -b, np.full(1, 0.25))), 0.25, atol=1e-12)


class SplitTest(unittest.TestCase):
    axis = (0.3, 1.0, -0.2)

    def test_slow_motion_and_posture_stay(self):
        for angle in (np.full(600, 0.7), 0.4 + wave(0.2, amplitude=0.3)):
            q = about(self.axis, angle)
            out = prep.scale_detail(q, 2.0, 1.0, FS)
            self.assertLess(prep.angles(prep.qmul(prep.qinv(q), out)).max(), 1e-3)

    def test_detail_scales_and_keeps_its_timing(self):
        motion = wave(3.0, amplitude=0.1, phase=math.pi / 2.0)     # peaks on frames
        q = about(self.axis, 0.4 + motion)
        out = prep.scale_detail(q, 2.0, 1.0, FS)
        result = prep.twist_angles(out, self.axis) - 0.4
        middle = slice(90, -90)
        ratio = np.sqrt((result[middle] ** 2).mean() / (motion[middle] ** 2).mean())
        self.assertAlmostEqual(ratio, 2.0, delta=0.1)
        peaks = [i for i in range(100, 500) if motion[i] > motion[i - 1] and motion[i] >= motion[i + 1]]
        for i in peaks:
            window = slice(i - 4, i + 5)
            self.assertEqual(np.argmax(result[window]), np.argmax(motion[window]), i)

    def test_gain_one_is_the_identity(self):
        q = about(self.axis, wave(2.0))
        np.testing.assert_allclose(prep.scale_detail(q, 1.0, 1.0, FS), q, atol=1e-12)


class SnapTest(unittest.TestCase):
    def test_moves(self):
        x = np.array((0.0, 1.0, 5.0, 9.0, 8.0, 3.0, 2.5, 4.0, 3.0, 10.0))
        self.assertEqual(prep.moves(x, 4.0), [(0, 3), (3, 6), (6, 9)])
        self.assertEqual(prep.moves(x, 20.0), [])

    def test_identity_at_a_of_one(self):
        x = smooth_step(60, 10, 12, high=30.0)
        times, count = prep.snap_times(x, 1.0, 8.0)
        np.testing.assert_array_equal(times, np.arange(60.0))
        self.assertEqual(count, 0)

    def test_steeper_moves_with_fixed_holds_and_midpoints(self):
        n = 120
        x = smooth_step(n, 10, 12, high=30.0) - smooth_step(n, 60, 9, high=30.0)
        for a in (2.0, 3.0):
            times, count = prep.snap_times(x, a, 8.0)
            self.assertEqual(count, 2)
            self.assertTrue((np.diff(times) >= -1e-9).all())
            snapped = np.interp(times, np.arange(n), x)
            self.assertLess(rise_time(snapped[:50]), 0.75 * rise_time(x[:50]))
            self.assertLess(rise_time(-snapped[50:]), 0.75 * rise_time(-x[50:]))
            for held in (0, 5, 30, 40, 80, 119):
                self.assertAlmostEqual(snapped[held], x[held], places=6)
            # The moment each move crosses half way stays.
            for move in (slice(0, 50), slice(50, n)):
                index = np.arange(n, dtype=np.float64)[move]
                half = lambda y: np.interp(15.0, np.sort(y[move]), index[np.argsort(y[move])])  # noqa: E731
                self.assertAlmostEqual(half(snapped), half(x), delta=0.05)

    def test_small_moves_are_untouched(self):
        x = smooth_step(60, 10, 12, high=5.0)
        times, count = prep.snap_times(x, 3.0, 8.0)
        self.assertEqual(count, 0)
        np.testing.assert_array_equal(times, np.arange(60.0))

    def test_finger_shares_the_retiming_and_clamps(self):
        n = 90
        flex = smooth_step(n, 20, 10, high=0.8) - smooth_step(n, 55, 10, high=0.8)
        axis = (1.0, 0.0, 0.1)
        joints = [about(axis, flex * share) for share in (0.5, 0.8, 0.6)]
        out, clamped, count = prep.finger(joints, 3.0, 1.0, 8.0, 1.0, FS, margin=math.radians(5.0))
        self.assertEqual(count, 2)
        before = [prep.twist_angles(q, axis) for q in joints]
        after = [prep.twist_angles(q, axis) for q in out]
        rises = [rise_time(a[:50]) / rise_time(b[:50]) for a, b in zip(after, before)]
        self.assertLess(max(rises), 0.75)
        self.assertAlmostEqual(min(rises), max(rises), delta=0.05)
        self.assertFalse(clamped.any())
        # Range overshoots; the clamp keeps every joint within its own range plus the margin.
        out, clamped, _ = prep.finger(joints, 3.0, 3.0, 8.0, 1.0, FS, margin=math.radians(5.0))
        self.assertTrue(clamped.any())
        for q, source in zip(out, joints):
            along, along0 = prep.twist_angles(q, axis), prep.twist_angles(source, axis)
            self.assertLessEqual(along.max(), along0.max() + math.radians(5.0) + 1e-6)
            self.assertGreaterEqual(along.min(), along0.min() - math.radians(5.0) - 1e-6)

    def test_strokes(self):
        motion = wave(2.0, amplitude=0.15) + wave(0.3, amplitude=0.4)
        q = about((0.2, 1.0, 0.0), motion)
        out, info = prep.strokes(q, 1.5, 2.0, 4.0, 1.0, FS)
        self.assertGreater(info["share"], 0.99)
        self.assertGreater(info["moves"], 70)
        self.assertGreater(np.percentile(prep.speeds(out, FS), 95), 1.5 * np.percentile(prep.speeds(q, FS), 95))
        same, _ = prep.strokes(q, 1.0, 1.0, 4.0, 1.0, FS)
        self.assertLess(prep.angles(prep.qmul(prep.qinv(q), same)).max(), 1e-9)


class RollTest(unittest.TestCase):
    def test_twist_split(self):
        rng = np.random.default_rng(2)
        axis = prep.normalize(np.array((-0.83, -0.005, -0.557)))
        hand = prep.continuous(prep.normalize(rng.normal(size=(100, 4))))
        t = prep.twist(hand, axis)
        swing = prep.qmul(prep.qinv(t), hand)
        np.testing.assert_allclose(prep.angles(prep.qmul(prep.qinv(hand), prep.qmul(t, swing))), 0.0, atol=1e-6)
        # The twist turns about the axis only, and none of it is left on the hand.
        self.assertLess(np.abs(np.cross(prep.qlog(t), axis)).max(), 1e-9)
        self.assertLess(np.abs(prep.twist_angles(swing, axis)).max(), 1e-9)
        np.testing.assert_allclose(prep.twist(about(axis, np.full(3, 0.4)), axis), about(axis, np.full(3, 0.4)),
                                   atol=1e-12)


class SwingTest(unittest.TestCase):
    def arm(self, n, bend=1.0):
        shoulder = np.zeros((n, 3))
        elbow = np.tile((0.28, 0.0, 0.0), (n, 1))
        wrist = elbow + 0.25 * np.stack((np.cos(np.full(n, bend)), np.zeros(n), np.sin(np.full(n, bend))), -1)
        return shoulder, elbow, wrist

    def test_reaches_the_target_on_a_bent_arm(self):
        n = 50
        shoulder, elbow, wrist = self.arm(n)
        offset = 0.03 * np.stack((np.sin(np.arange(n) * 0.4), np.cos(np.arange(n) * 0.3), np.zeros(n)), -1)
        a_upper, a_forearm, straight = prep.swing_ik(shoulder, elbow, wrist, wrist + offset, 0.7)
        reached = prep._moved(a_forearm, wrist)
        self.assertLess(np.linalg.norm(reached - wrist - offset, axis=1).max(), 1e-3)
        self.assertFalse(straight.any())
        # The shoulder stays; the forearm turns relative to the upper arm about the hinge only.
        np.testing.assert_allclose(prep._moved(a_upper, shoulder), shoulder, atol=1e-12)
        np.testing.assert_allclose(prep._moved(a_forearm, elbow), prep._moved(a_upper, elbow), atol=1e-12)
        relative = prep.from_matrices(np.linalg.inv(a_upper) @ a_forearm)
        hinge = prep.normalize(np.cross(elbow - shoulder, wrist - elbow))
        self.assertLess(np.abs(np.cross(prep.qlog(relative), hinge)).max(), 1e-9)
        self.assertGreater(np.abs(prep.qlog(relative)).max(), 1e-3)

    def test_no_swing_is_the_identity(self):
        shoulder, elbow, wrist = self.arm(10)
        a_upper, a_forearm, _ = prep.swing_ik(shoulder, elbow, wrist, wrist, 0.7)
        np.testing.assert_allclose(a_upper, np.tile(np.eye(4), (10, 1, 1)), atol=1e-12)
        np.testing.assert_allclose(a_forearm, np.tile(np.eye(4), (10, 1, 1)), atol=1e-12)

    def test_straight_arm_turns_at_the_shoulder(self):
        shoulder, elbow, wrist = self.arm(5, bend=0.0)
        a_upper, a_forearm, straight = prep.swing_ik(shoulder, elbow, wrist, wrist + (0.0, 0.02, 0.0), 0.7)
        self.assertTrue(straight.all())
        np.testing.assert_allclose(a_forearm, a_upper, atol=1e-12)
        self.assertLess(np.linalg.norm(prep._moved(a_forearm, wrist) - wrist - (0.0, 0.02, 0.0), axis=1).max(), 1e-3)

    def test_strum_direction(self):
        t = np.arange(600) / FS
        u = prep.normalize(np.array((0.2, 1.0, 0.1)))
        pick = np.outer(0.01 * np.sin(2.0 * math.pi * 2.0 * t), u) + np.outer(0.05 * t / t[-1], (1.0, 0.0, 0.0))
        s, direction, share = prep.strum(pick, 1.0, FS, 1.0)
        self.assertGreater(abs(direction @ u), 0.999)
        self.assertGreater(share, 0.99)
        expected = 0.01 * np.sin(2.0 * math.pi * 2.0 * (t + 1.0 / FS)) * np.sign(direction @ u)
        self.assertLess(np.abs(s - expected)[60:-60].max(), 1e-3)


class MeasureTest(unittest.TestCase):
    def test_transitions_and_travel(self):
        n = 200
        flex = smooth_step(n, 20, 10, high=60.0) - smooth_step(n, 100, 4, high=60.0)
        self.assertEqual(prep.transitions(flex), [5, 3])     # a raised cosine rises 10-90 % in 59 % of its length
        points = np.zeros((600, 3))
        points[:, 0] = wave(3.0, amplitude=0.01, phase=math.pi / 2.0)
        rms, p99 = prep.travel(points, 1.0, FS)
        self.assertAlmostEqual(rms, 0.01 / math.sqrt(2.0), delta=5e-4)
        self.assertAlmostEqual(p99, 0.01, delta=5e-4)
