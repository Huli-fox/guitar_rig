import math
import unittest
from types import SimpleNamespace

from mathutils import Quaternion, Vector

from guitar_rig.core import magnets
from guitar_rig.core.mathx import auto_scale_factor

PLANE = magnets.Feature('PLANE', Vector((0.0, 0.0, 1.0)), normal=Vector((0.0, 0.0, 1.0)))
LINE = magnets.Feature('LINE', Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0)))


def assert_vector(test, actual, expected, places=6):
    test.assertLess((Vector(actual) - Vector(expected)).length, 10.0 ** -places, f"{tuple(actual)} != {expected}")


class FalloffTest(unittest.TestCase):
    """SAO: w = 1 - |d - peak| / (D - peak) within D, then w^(1 - power) for powers above -9, else 0."""

    def test_linear(self):
        for d, w in ((0.0, 1.0), (0.25, 0.75), (0.5, 0.5), (0.99, 0.01), (1.0, 0.0), (3.0, 0.0)):
            self.assertAlmostEqual(magnets.falloff(d, 1.0), w, msg=d)

    def test_snap(self):
        for d in (0.0, 0.3, 0.999):
            self.assertEqual(magnets.falloff(d, 1.0, power=1.0), 1.0)
        self.assertEqual(magnets.falloff(1.0, 1.0, power=1.0), 0.0)

    def test_barrier_power(self):
        for power in (-9.0, -99.0):
            self.assertEqual(magnets.falloff(0.1, 1.0, power=power), 0.0)
        self.assertAlmostEqual(magnets.falloff(0.5, 1.0, power=-8.0), 0.5 ** 9.0)

    def test_other_powers(self):
        self.assertAlmostEqual(magnets.falloff(0.5, 1.0, power=0.5), math.sqrt(0.5))
        self.assertAlmostEqual(magnets.falloff(0.5, 1.0, power=-1.0), 0.25)
        self.assertEqual(magnets.falloff(0.5, 1.0, power=2.0), 1.0)     # SAO overshoots here (w = 2)

    def test_peak(self):
        self.assertAlmostEqual(magnets.falloff(0.2, 1.0, peak=0.2), 1.0)
        self.assertAlmostEqual(magnets.falloff(0.6, 1.0, peak=0.2), 0.5)
        self.assertAlmostEqual(magnets.falloff(0.1, 1.0, peak=0.2), 0.875)
        # Far below a large peak SAO's w goes negative (a NaN power in JS); it is clamped to 0.
        self.assertEqual(magnets.falloff(0.0, 1.0, peak=0.7), 0.0)
        self.assertEqual(magnets.falloff(0.0, 1.0, peak=0.7, power=0.5), 0.0)


class NearestTest(unittest.TestCase):
    def test_line_is_clamped_to_the_segment(self):
        for point, nearest in (((0.5, 2.0, 0.0), (0.5, 0.0, 0.0)), ((-1.0, 1.0, 0.0), (0.0, 0.0, 0.0)),
                               ((3.0, 0.0, 4.0), (1.0, 0.0, 0.0))):
            n, d, s = magnets.nearest_point(LINE, Vector(point))
            assert_vector(self, n, nearest)
            self.assertAlmostEqual(d, (Vector(point) - Vector(nearest)).length, places=6)
            self.assertEqual(d, s)
        degenerate = magnets.Feature('LINE', Vector((1.0, 1.0, 1.0)), Vector((1.0, 1.0, 1.0)))
        n, d, _ = magnets.nearest_point(degenerate, Vector((1.0, 1.0, 3.0)))
        assert_vector(self, n, (1.0, 1.0, 1.0))
        self.assertAlmostEqual(d, 2.0)

    def test_plane_signed_distance(self):
        n, d, s = magnets.nearest_point(PLANE, Vector((0.3, -0.2, 0.4)))
        assert_vector(self, n, (0.3, -0.2, 1.0))
        self.assertAlmostEqual(d, 0.6)
        self.assertAlmostEqual(s, -0.6)


class PullTest(unittest.TestCase):
    def test_linear_pull_toward_a_line(self):
        point, hit = magnets.pull(Vector((0.5, 0.3, 0.4)), LINE, magnets.Params(1.0))
        self.assertAlmostEqual(hit.distance, 0.5)
        self.assertAlmostEqual(hit.weight, 0.5)
        assert_vector(self, point, (0.5, 0.15, 0.2))
        assert_vector(self, hit.moved, (0.0, -0.15, -0.2))
        self.assertFalse(hit.barrier)

    def test_out_of_reach(self):
        point, hit = magnets.pull(Vector((0.5, 3.0, 0.0)), LINE, magnets.Params(1.0, power=1.0))
        assert_vector(self, point, (0.5, 3.0, 0.0))
        self.assertEqual(hit.weight, 0.0)
        self.assertFalse(hit.holds)

    def test_barrier_clamps_at_any_distance(self):
        """SAO clamps a point behind a plane that is not crossable whatever the distance (min.js, Tt)."""
        barrier = magnets.Params(0.1, power=-99.0, crossable=False)
        point, hit = magnets.pull(Vector((0.2, 0.3, -4.0)), PLANE, barrier)
        assert_vector(self, point, (0.2, 0.3, 1.0))
        self.assertTrue(hit.barrier)
        self.assertEqual(hit.weight, 1.0)
        # In front of it nothing happens, near or far.
        for z in (1.05, 3.0):
            point, hit = magnets.pull(Vector((0.2, 0.3, z)), PLANE, barrier)
            assert_vector(self, point, (0.2, 0.3, z))
            self.assertEqual(hit.weight, 0.0)
        # With the distance check, a barrier beyond its reach lets the point be.
        point, hit = magnets.pull(Vector((0.2, 0.3, -4.0)), PLANE, barrier, barriers_ignore_distance=False)
        assert_vector(self, point, (0.2, 0.3, -4.0))
        point, hit = magnets.pull(Vector((0.2, 0.3, 0.95)), PLANE, barrier, barriers_ignore_distance=False)
        assert_vector(self, point, (0.2, 0.3, 1.0))

    def test_crossable_plane_pulls_from_both_sides(self):
        params = magnets.Params(1.0, power=1.0, crossable=True)
        for z in (0.2, 1.7):
            point, hit = magnets.pull(Vector((0.0, 0.0, z)), PLANE, params)
            assert_vector(self, point, (0.0, 0.0, 1.0))
            self.assertFalse(hit.barrier)

    def test_snap_plane_that_is_a_barrier(self):
        """ALIGN makes the fretboard-edge barrier snap: onto the plane from both sides."""
        params = magnets.Params(0.5, power=1.0, crossable=False)
        for z in (0.7, 1.3, -10.0):
            point, _ = magnets.pull(Vector((0.1, 0.1, z)), PLANE, params)
            assert_vector(self, point, (0.1, 0.1, 1.0))

    def test_peak_target(self):
        """With a peak, SAO pulls toward the point `peak` off the feature, toward the hand point."""
        params = magnets.Params(1.0, peak=0.2, power=1.0)
        point, hit = magnets.pull(Vector((0.5, 0.0, 0.6)), LINE, params)
        assert_vector(self, hit.target, (0.5, 0.0, 0.2))
        assert_vector(self, point, (0.5, 0.0, 0.2))
        # A barrier clamp goes onto the plane itself.
        barrier = magnets.Params(1.0, peak=0.2, crossable=False)
        point, _ = magnets.pull(Vector((0.0, 0.0, 0.5)), PLANE, barrier)
        assert_vector(self, point, (0.0, 0.0, 1.0))

    def test_hysteresis(self):
        snap = magnets.Params(1.0, power=1.0, hysteresis=1.15)
        far = Vector((0.0, 0.0, 2.1))       # 1.1 from the plane
        self.assertEqual(magnets.pull(far, PLANE, snap)[1].weight, 0.0)
        point, hit = magnets.pull(far, PLANE, snap, holding=True)
        self.assertEqual(hit.weight, 1.0)
        self.assertAlmostEqual(hit.reach, 1.15)
        assert_vector(self, point, (0.0, 0.0, 1.0))
        # Only snap magnets get it.
        linear = magnets.Params(1.0, power=0.0, hysteresis=1.15)
        self.assertEqual(magnets.pull(far, PLANE, linear, holding=True)[1].weight, 0.0)


class ApplyTest(unittest.TestCase):
    def test_order_and_hand_offset(self):
        """Each magnet acts on the hand point wrist + offset, in list order, on the wrist the last one left."""
        offset = Vector((0.0, 0.0, 0.3))
        snap_plane = magnets.Entry(0, PLANE, magnets.Params(5.0, power=1.0), offset)
        wall = magnets.Feature('PLANE', Vector((0.5, 0.0, 0.0)), normal=Vector((1.0, 0.0, 0.0)))
        barrier = magnets.Entry(1, wall, magnets.Params(0.1, power=-99.0, crossable=False), Vector())
        wrist, hits = magnets.apply(Vector((0.2, 0.4, 0.0)), [snap_plane, barrier])
        assert_vector(self, wrist, (0.5, 0.4, 0.7))
        self.assertEqual([index for index, _ in hits], [0, 1])
        assert_vector(self, hits[0][1].point, (0.2, 0.4, 0.3))
        self.assertTrue(hits[1][1].barrier)
        # The other order: the barrier first sees the wrist, then the plane snaps.
        wrist, _ = magnets.apply(Vector((0.2, 0.4, 0.0)), [barrier, snap_plane])
        assert_vector(self, wrist, (0.5, 0.4, 0.7))

    def test_holding(self):
        entry = magnets.Entry(3, PLANE, magnets.Params(1.0, power=1.0, hysteresis=1.5), Vector())
        start = Vector((0.0, 0.0, 2.2))
        self.assertAlmostEqual(magnets.apply(start, [entry])[0].z, 2.2)
        self.assertAlmostEqual(magnets.apply(start, [entry], holding={3})[0].z, 1.0)


class ScalingTest(unittest.TestCase):
    def test_distance(self):
        self.assertAlmostEqual(magnets.distance_scale('INDEX_JS', 1.2), 1.2)
        self.assertAlmostEqual(magnets.distance_scale('MIN_JS', 0.8), 0.8)
        self.assertEqual(magnets.distance_scale('NONE', 1.2), 1.0)

    def test_offset(self):
        self.assertAlmostEqual(magnets.offset_scale('INDEX_JS', 1.3, 1.2), auto_scale_factor(1.2))
        self.assertAlmostEqual(magnets.offset_scale('MIN_JS', 1.3, 1.2), 1.3)
        self.assertEqual(magnets.offset_scale('NONE', 1.3, 1.2), 1.0)

    def test_hand_offset(self):
        frame = Quaternion((0.0, 0.0, 1.0), math.pi / 2.0)
        assert_vector(self, magnets.hand_offset((0.1, 0.0, 0.0), frame, 2.0), (0.0, 0.2, 0.0))
        axis_rot = Quaternion((0.0, 0.0, 1.0), -math.pi / 2.0)
        assert_vector(self, magnets.hand_offset((0.1, 0.0, 0.0), frame, 1.0, axis_rot), (0.1, 0.0, 0.0))


class GuitarPoseTest(unittest.TestCase):
    def test_points_and_normals(self):
        rotation = Quaternion((1.0, 0.0, 0.0), 0.5)
        pose = magnets.GuitarPose(Vector((1.0, 2.0, 3.0)), rotation, Quaternion(), Vector((2.0, 1.0, 0.5)))
        assert_vector(self, pose.point((1.0, 1.0, 1.0)), Vector((1.0, 2.0, 3.0)) + rotation @ Vector((2.0, 1.0, 0.5)))
        assert_vector(self, pose.point((1.0, 1.0, 1.0), default=True), (3.0, 3.0, 3.5))
        # Under a non-uniform scale a plane's normal stays square to the plane.
        normal = Vector((1.0, 1.0, 0.0)).normalized()
        in_plane = Vector((1.0, -1.0, 0.0))
        world_normal = pose.normal(normal)
        world_in_plane = pose.point(in_plane) - pose.point((0.0, 0.0, 0.0))
        self.assertAlmostEqual(world_normal.length, 1.0, places=6)
        self.assertAlmostEqual(world_normal.dot(world_in_plane), 0.0, places=6)

    def test_shape(self):
        pose = magnets.GuitarPose(Vector((0.0, 0.0, 1.0)), Quaternion(), Quaternion(), Vector((2.0, 2.0, 2.0)))
        line = magnets.Shape('LINE', Vector((0.0, 0.0, 0.0)), Vector((1.0, 0.0, 0.0))).world(pose)
        assert_vector(self, line.b, (2.0, 0.0, 1.0))
        plane = magnets.Shape('PLANE', Vector((0.0, 0.0, 1.0)), normal=Vector((0.0, 0.0, 1.0))).world(pose)
        assert_vector(self, plane.a, (0.0, 0.0, 3.0))
        assert_vector(self, plane.normal, (0.0, 0.0, 1.0))


class ModeTest(unittest.TestCase):
    def test_apply_mode(self):
        edge = SimpleNamespace(preset_id="FRETBOARD_EDGE", power=-99.0, filter='ROTATION_BASED')
        other = SimpleNamespace(preset_id="FRETBOARD_PLANE", power=1.0, filter='NONE')
        settings = SimpleNamespace(aim_enabled=True, magnets=[edge, other])
        magnets.apply_mode(settings, 'ALIGN')
        self.assertEqual((settings.aim_enabled, edge.power, edge.filter), (False, 1.0, 'NONE'))
        self.assertEqual((other.power, other.filter), (1.0, 'NONE'))
        magnets.apply_mode(settings, 'FOLLOW')
        self.assertEqual((settings.aim_enabled, edge.power, edge.filter), (True, -99.0, 'ROTATION_BASED'))
