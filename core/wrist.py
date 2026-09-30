"""Fretting-wrist rotation (§5.7): blend the mocap wrist toward a rotation fixed to the guitar.

SAO (SA_system_emulation.min.js, It and rotation_reference) blends in its hand-tracking frame g, whose relation
to the wrist bone is fixed per side: the bone's rotation from rest is g · w · axis_rot⁻¹ (rot_hand_adjust), with
w = three.js Euler(0, -90°, 90°, 'YZX') for the left hand and axis_rot the arm's rest-pose correction
(calibrate.py; the identity for T-pose rigs). In the rest-aligned frame Q_hand of calibrate.py, seen in the
character frame, g = Q_hand @ axis_rot @ w⁻¹. The guitar rotation times the scene's rotation_reference offset is
a target for g, so with wrist_offset = offset @ w (presets.sao_wrist):

    Q_target = q_gtr @ wrist_offset @ axis_rot⁻¹
    g_new    = g.slerp(q_gtr @ offset, weight), with SAO's constrained yaw below
    Q_new    = g_new @ w @ axis_rot⁻¹

wrist_offset is thus the hand's T-pose-aligned frame, Q_hand @ axis_rot, relative to the guitar. That frame's X
runs along the rest forearm on any rig, so an offset from a preset or a capture means the same hand pose on
every character.

Constrained direction (the scenes' constrained_direction: -1): with both rotations as three.js Euler 'YXZ'
(yaw about the character's up axis first), when the yaws differ by more than 120° and the mocap wrist is pitched
and rolled less than 60°, pitch and roll are blended at zero yaw, and the yaw turns from the mocap's toward the
target's in the given direction (-1: decreasing) instead of the shorter way. This stops the blend from flipping
the hand over the back when the mocap wrist faces away from the target.
"""

import math

from mathutils import Euler, Quaternion

# SAO's hand-tracking frame for each hand, relative to the rest-aligned hand frame (rot_hand_adjust_base, w).
# three.js order 'YZX' is the matrix Ry·Rz·Rx, which is Blender's order 'XZY'.
HAND_FRAME = {
    'L': Euler((0.0, -math.pi / 2.0, math.pi / 2.0), 'XZY').to_quaternion(),
    'R': Euler((0.0, math.pi / 2.0, -math.pi / 2.0), 'XZY').to_quaternion(),
}
YAW_LIMIT = 2.0 * math.pi / 3.0     # yaw difference above which the constrained direction applies
TILT_LIMIT = math.pi / 3.0          # ...while the mocap wrist's pitch and roll stay below this
DIRECTIONS = {'NEGATIVE': -1, 'POSITIVE': 1, 'NONE': 0}


def _axis_rot(axis_rot):
    return Quaternion() if axis_rot is None else Quaternion(axis_rot)


def target_frame(guitar_rotation, wrist_offset, axis_rot=None):
    """Q_target: the rest-aligned hand frame (world) that `wrist_offset` puts on the guitar."""
    target = Quaternion(guitar_rotation) @ Quaternion(wrist_offset) @ _axis_rot(axis_rot).inverted()
    return target.normalized()


def capture(guitar_rotation, hand_frame, axis_rot=None):
    """The wrist offset that makes the rest-aligned hand frame `hand_frame` the target (Capture Wrist Offset)."""
    offset = Quaternion(guitar_rotation).normalized().inverted() @ Quaternion(hand_frame) @ _axis_rot(axis_rot)
    return offset.normalized()


def _yxz(q):
    """three.js Euler 'YXZ' angles (x, y, z) of `q`: the matrix Ry·Rx·Rz, Blender's order 'ZXY'."""
    return q.to_euler('ZXY')


def _from_yxz(x, y, z):
    return Euler((x, y, z), 'ZXY').to_quaternion()


def constrained_blend(g, d, weight, direction):
    """(rotation, constrained): SAO's blend of `g` toward `d`, both in character-frame coordinates.

    `direction` is -1, 1 or 0 (off). `constrained` tells whether the yaw was turned the given way.
    """
    if direction:
        k, x = _yxz(g), _yxz(d)
        difference = abs(k.y - x.y)
        if difference > math.pi:
            difference = 2.0 * math.pi - difference
        if difference > YAW_LIMIT and abs(k.x) < TILT_LIMIT and abs(k.z) < TILT_LIMIT:
            tilt = _from_yxz(k.x, 0.0, k.z).slerp(_from_yxz(x.x, 0.0, x.z), weight)
            if direction > 0:
                turn = x.y + (2.0 * math.pi if k.y > x.y else 0.0) - k.y
            else:
                turn = -(k.y + (2.0 * math.pi if k.y < x.y else 0.0) - x.y)
            return (_from_yxz(0.0, k.y + turn * weight, 0.0) @ tilt).normalized(), True
    return g.slerp(d, weight).normalized(), False


def blend(hand_frame, guitar_rotation, wrist_offset, weight, char_world, side='L', direction=-1, axis_rot=None):
    """(new rest-aligned hand frame, constrained) for the mocap frame `hand_frame` (world).

    `char_world` is the character frame in world space (calibrate.char_frame_world), whose Y is the up axis the
    constrained yaw turns about; `axis_rot` is the side's calibrated axis_rot (character-frame coordinates).
    """
    if weight <= 0.0:
        return Quaternion(hand_frame).normalized(), False
    to_hand = HAND_FRAME[side] @ _axis_rot(axis_rot).inverted()     # g -> rest-aligned frame, char. coordinates
    char_world = Quaternion(char_world)
    to_char = char_world.inverted()
    g = to_char @ Quaternion(hand_frame) @ to_hand.inverted()
    d = to_char @ target_frame(guitar_rotation, wrist_offset, axis_rot) @ to_hand.inverted()
    g_new, constrained = constrained_blend(g, d, min(weight, 1.0), direction)
    return (char_world @ g_new @ to_hand).normalized(), constrained
