import math
import unittest

from mathutils import Quaternion, Vector

from guitar_rig.core import mathx


class AutoScaleTest(unittest.TestCase):
    def test_dead_band(self):
        for ratio in (0.9, 0.95, 1.0, 1.05, 1.1, 1.111):
            self.assertAlmostEqual(mathx.auto_scale_factor(ratio), 1.0, msg=ratio)

    def test_outside_dead_band(self):
        self.assertAlmostEqual(mathx.auto_scale_factor(1.2), 1.08)
        self.assertAlmostEqual(mathx.auto_scale_factor(0.8), 0.8 / 0.9)

    def test_weight(self):
        self.assertAlmostEqual(mathx.auto_scale_factor(1.5, 0.9), 1.0 + 0.35 * 0.9)
        self.assertAlmostEqual(mathx.auto_scale_factor(1.5, 0.0), 1.0)
        self.assertAlmostEqual(mathx.auto_scale_factor(0.5, 1.0), 0.5 / 0.9)

    def test_vector(self):
        v = mathx.auto_scale(Vector((1.0, 2.0, 3.0)), 2.0)
        self.assertLess((v - Vector((1.8, 3.6, 5.4))).length, 1e-6)


class FrameTest(unittest.TestCase):
    def test_frame_quaternion(self):
        q = mathx.frame_quaternion(Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)))
        self.assertLess((q @ Vector((0, 1, 0)) - Vector((0, 0, 1))).length, 1e-6)
        self.assertLess((q @ Vector((0, 0, 1)) - Vector((0, -1, 0))).length, 1e-6)

    def test_rotation_angle_ignores_sign(self):
        a = Quaternion((0.0, 0.0, 1.0), 0.3)
        b = Quaternion((0.0, 0.0, 1.0), 0.5)
        self.assertAlmostEqual(mathx.rotation_angle(a, b), 0.2, places=6)
        self.assertAlmostEqual(mathx.rotation_angle(a, -b), 0.2, places=6)
        self.assertAlmostEqual(mathx.rotation_angle(a, Quaternion((1.0, 0.0, 0.0), math.pi) @ a), math.pi, places=6)
        self.assertAlmostEqual(mathx.rotation_angle(Quaternion(), Quaternion((0.0, 1.0, 0.0), 5.0)),
                               2.0 * math.pi - 5.0, places=6)

    def test_rotation_angle_precision(self):
        """Tiny angles stay accurate with float32 quaternions (2·acos(a·b) reads about 7e-4 rad here)."""
        q = Quaternion((0.7071, -0.4056, 0.0, 0.5792)).normalized()
        self.assertLess(mathx.rotation_angle(q, q.copy()), 1e-6)
        self.assertAlmostEqual(mathx.rotation_angle(q, Quaternion((1.0, 0.0, 0.0), 1e-4) @ q), 1e-4, delta=2e-6)
