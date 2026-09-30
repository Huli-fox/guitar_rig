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


def aim_shift(normal_local, shift_world, scale):
    """How far the neck axis ends move in GTR_ROOT space for a fingertip shift of `shift_world` (scene units,
    along the magnet's unit plane normal `normal_local` in GTR_ROOT space; SAO: reference_point[axis] += e)."""
    n = Vector(normal_local).normalized()
    return Vector([n[i] * shift_world / scale[i] for i in range(3)])
