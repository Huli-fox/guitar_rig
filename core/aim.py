"""Neck aim (§5.4): swing the guitar about its origin so that its neck points at the fretting hand.

SAO does this in jThree/index.js (align_with_external_point, L676-840), each frame from the chest-mount rotation:

    pivot       = a + m·t, m = p - a, t = -(a·m)/|m|²     the foot of the perpendicular from the guitar origin
                                                          onto the neck axis a (NECK_PIVOT) -> p (NUT)
    axis_origin = O + q_def @ pivot                       O: the guitar origin, q_def: the mount rotation
    ext         = target - axis_origin, L = |ext|
    ref         = q_def @ normalize(p - pivot) · L + axis_origin - O
    swing       = the shortest rotation taking ref onto target - O
    q           = swing @ q_def

So the point of the neck axis as far from the pivot as the target is swung about the guitar origin onto the line
from the origin to the target. The swing has no twist about that line. The target is the fretting wrist plus the
aim hand offset in its rest-aligned frame, turned by axis_rot (index.js applies it for every avatar; it is the
identity for T-pose ones). `max_swing` and `weight` are the add-on's own limits; SAO has neither. Points are
scaled before the rotation, which for the uniform scale SAO's props have is its order too.

When a fingertip magnet on the fretting hand acts (min.js, Tt), SAO moves `a` and `p` along that magnet's plane
normal by -E·w, where E is the magnet's fingertip shift and w its weight: the aimed axis then runs at the
height the fingertips hold the hand point above the fretboard. `aim_shift` gives that move in GTR_ROOT space.

The aim leaves the target a little off the line through `a` and `p` (the swung neck point is as far from the pivot
as the target is, not from the guitar origin), and `max_swing` leaves it further off. `axis_foot` measures that
distance for any rotation of the guitar, `limit_gap` how much of it is the limit's doing, and `limit_move` is the
move across the neck that covers that much: what the solver has the arm do (solver.py, neck contact).
"""

import math
from dataclasses import dataclass

from mathutils import Quaternion, Vector

from .mathx import auto_scale_factor


@dataclass
class Aim:
    """One neck aim: the rotation and what it was computed from, all in world space."""
    rotation: Quaternion        # the aimed guitar rotation
    swing: float                # angle of the swing applied, in radians
    clamped: bool               # the swing was limited to max_swing
    axis_origin: Vector         # the pivot on the mounted guitar
    target: Vector              # the aim point on the fretting hand


def pivot(a, p):
    """The foot of the perpendicular from the origin onto the line a -> p."""
    a, p = Vector(a), Vector(p)
    m = p - a
    if m.length_squared < 1e-24:
        return a.copy()
    return a + m * (-a.dot(m) / m.length_squared)


def offset_scale(policy, ratio_palm):
    """World metres per metre of the aim hand offset: index.js scales it with the palm (auto_scale 手首, f = 1)."""
    return 1.0 if policy == 'NONE' else auto_scale_factor(ratio_palm, 1.0)


def target_point(wrist, hand_frame, offset, scale=1.0, axis_rot=None):
    """The aim point: the wrist plus `offset` (rest-aligned hand frame, times `scale`) turned by axis_rot."""
    v = Vector(offset) * scale
    if axis_rot is not None:
        v = axis_rot @ v
    return wrist + hand_frame @ v


def swing_rotation(ref, ext, max_swing=None, weight=1.0):
    """(swing, angle, clamped): the shortest rotation taking direction `ref` onto `ext`, limited to `max_swing`
    radians and scaled by `weight`."""
    if ref.length < 1e-12 or ext.length < 1e-12:
        return Quaternion(), 0.0, False
    axis, angle = ref.normalized().rotation_difference(ext.normalized()).to_axis_angle()
    if angle > math.pi:
        angle, axis = 2.0 * math.pi - angle, -axis
    clamped = max_swing is not None and angle > max_swing
    if clamped:
        angle = max_swing
    angle *= weight
    return Quaternion(axis, angle), angle, clamped


def aim(guitar, a, p, target, max_swing=None, weight=1.0):
    """The guitar aimed at `target` from its mount pose `guitar` (a magnets.GuitarPose; its default rotation is
    used). `a` and `p` are the neck axis ends in GTR_ROOT space. Returns an Aim."""
    q_def = guitar.default_rotation
    a, p = Vector(a) * guitar.scale, Vector(p) * guitar.scale
    foot = pivot(a, p)
    origin = guitar.location
    axis_origin = origin + q_def @ foot
    direction = q_def @ (p - foot)
    if direction.length < 1e-12:
        return Aim(q_def.copy(), 0.0, False, axis_origin, target.copy())
    ref = direction.normalized() * (target - axis_origin).length + axis_origin - origin
    swing, angle, clamped = swing_rotation(ref, target - origin, max_swing, weight)
    return Aim((swing @ q_def).normalized(), angle, clamped, axis_origin, target.copy())


def axis_foot(guitar, rotation, a, p, point):
    """(foot, distance): the point nearest the world point `point` on the line through the neck axis ends `a` and
    `p` (GTR_ROOT space) of `guitar` turned to `rotation`, and how far from `point` it is. The line goes on past
    its ends, as the aim's does: a hand beyond the nut is aimed at as well."""
    start = guitar.location + rotation @ (Vector(a) * guitar.scale)
    along = rotation @ ((Vector(p) - Vector(a)) * guitar.scale)
    if along.length_squared < 1e-24:
        return start, (point - start).length
    foot = start + along * ((point - start).dot(along) / along.length_squared)
    return foot, (point - foot).length


def limit_gap(guitar, a, p, target, max_swing, weight=1.0):
    """How much further from the aimed neck axis `max_swing` leaves `target`: its distance from the axis of the
    guitar aimed with the limit, less its distance aimed without (0 if that is not less). Both aims have `weight`,
    so this is 0 up to the limit and at weight 0, and grows from there without a step."""
    limited = aim(guitar, a, p, target, max_swing, weight)
    free = aim(guitar, a, p, target, None, weight)
    return max(axis_foot(guitar, limited.rotation, a, p, target)[1]
               - axis_foot(guitar, free.rotation, a, p, target)[1], 0.0)


def limit_move(guitar, rotation, a, p, target, max_swing, weight=1.0):
    """The move that takes `target` straight toward the neck axis of `guitar` turned to `rotation` (the guitar as
    it is shown) by what `max_swing` left between them (limit_gap), at most onto that axis. It is square to the
    axis, so the target keeps its place along the neck."""
    foot, gap = axis_foot(guitar, rotation, a, p, target)
    extra = min(limit_gap(guitar, a, p, target, max_swing, weight), gap)
    if extra <= 0.0:
        return Vector((0.0, 0.0, 0.0))
    return (foot - target) * (extra / gap)


def aim_shift(normal_local, shift_world, scale):
    """How far the neck axis ends move in GTR_ROOT space for a fingertip shift of `shift_world` (scene units,
    along the magnet's unit plane normal `normal_local` in GTR_ROOT space; SAO: reference_point[axis] += e)."""
    n = Vector(normal_local).normalized()
    return Vector([n[i] * shift_world / scale[i] for i in range(3)])
