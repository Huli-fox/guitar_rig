"""Small maths helpers shared by the solver modules."""

import math

from mathutils import Matrix, Quaternion

# Dead band of SAO's auto_scale_property (SA_system_emulation.min.js): ratios within ±10 % give 1.
AUTO_SCALE_BAND = 0.9


def auto_scale_factor(ratio, f=1.0):
    """Factor SAO's auto_scale_property applies for a rig/reference length `ratio`.

    The ratio is damped by a ±10 % dead band, then blended toward 1 by `f` (0: no scaling, 1: full).
    """
    if ratio > 1.0:
        s = max(ratio * AUTO_SCALE_BAND, 1.0)
    else:
        s = min(ratio / AUTO_SCALE_BAND, 1.0)
    return 1.0 + (s - 1.0) * f


def auto_scale(v, ratio, f=1.0):
    """Scale `v` (a number, Vector or array) the way SAO's auto_scale_property does."""
    return v * auto_scale_factor(ratio, f)


def frame_quaternion(x, y, z):
    """Rotation whose columns are the orthonormal axes `x`, `y` and `z`."""
    return Matrix((x, y, z)).transposed().to_quaternion()


def rotation_angle(a, b):
    """Angle in radians between two rotations, ignoring the quaternion sign.

    Uses 4·atan2(|a-b|, |a+b|) rather than 2·acos(a·b): with float32 quaternions the acos form reads up to
    7e-4 rad for identical rotations, which is as large as the solver's convergence threshold.
    """
    a, b = Quaternion(a).normalized(), Quaternion(b).normalized()
    diff = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    total = math.sqrt(sum((x + y) ** 2 for x, y in zip(a, b)))
    return 4.0 * math.atan2(min(diff, total), max(diff, total))
