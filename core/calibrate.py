"""Rest-pose calibration (§3.4): character frame, rest-aligned frames, ratios, axis_rot and fingertips.

Frames
------
C_char is the character frame. Its columns, in armature space, are
    X: right shoulder -> left shoulder (screen right in Blender's Front view; SAO/MMD +X),
    Y: up (hips -> head),
    Z: X × Y, the direction the character faces.
The plan's "right" is screen right: the character's own right would make the frame left-handed. At rest,
SAO's MMD/VRM bones have exactly these axes (three.js, after SAO's Z negation), so offsets and rotations
from SAO scene files apply in this frame unchanged.

The rest-aligned frame of bone b is Q_b(t) = q_b(t) @ Rrest[b]⁻¹ @ C_char, where q_b(t) is the bone's world
rotation. Rrest and C_char are kept in armature space: in the world-space form the object rotation at
calibration time cancels out, and armature space keeps the calibration valid when the object moves. At
rest every Q_b equals the world character frame, whatever the bone's roll or axis convention.
"""

import hashlib
import math
from dataclasses import dataclass, field

from mathutils import Quaternion, Vector

from . import bonemap
from .bonemap import SIDES
from .mathx import frame_quaternion

# SAO reference measurements (auto_scale_property in SA_system_emulation.min.js), MMD units / 11 = metres.
REF_ARM_LEN = 5.153592238246502 / 11.0      # |leftUpperArm - leftHand|
REF_PALM_LEN = 0.9020481908808872 / 11.0    # |leftHand - leftMiddleProximal|
REF_SPINE_LEN = 4.97462 / 11.0              # height of the neck above leftUpperLeg

HEIGHT_RANGE = (0.5, 2.5)                   # metres; outside it the units are probably wrong
TAIL_RATIO_RANGE = (0.25, 2.5)              # distal bone length / intermediate segment for a usable tail
TAIL_MAX_ANGLE = math.radians(60.0)         # maximum bend between the distal bone and the finger
FLIP = Quaternion((0.0, 1.0, 0.0), math.pi)  # half turn about the character's up axis


class CalibrationError(ValueError):
    """The bone map is incomplete or the rest pose is degenerate."""


@dataclass
class Fingertip:
    side: str           # 'L' or 'R'
    finger: str         # 'index', 'middle' or 'ring'
    bone: str           # distal bone
    tip_local: Vector   # the tip in the distal bone's rest space (armature units)
    source: str         # 'TAIL' or 'ESTIMATE'


@dataclass
class Calibration:
    char_frame: Quaternion      # C_char, armature space
    metres_per_bu: float        # scene unit scale at calibration time
    height: float               # metres, like all lengths below
    arm_len: float              # |left upper arm head - left hand head|, as SAO measures it
    palm_len: float             # |left hand head - left middle proximal head|
    spine_len: float            # height of the neck head above the left upper-leg head
    chain_len: dict             # side -> upper arm + forearm length (joint to joint)
    axis_rot: dict              # side -> Quaternion in character-frame coordinates
    fingertips: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    fingerprint: str = ""

    @property
    def ratio_arm(self):
        return self.arm_len / REF_ARM_LEN

    @property
    def ratio_palm(self):
        return self.palm_len / REF_PALM_LEN

    @property
    def ratio_spine(self):
        return self.spine_len / REF_SPINE_LEN


def character_frame(hips, head, upper_arm_l, upper_arm_r):
    """C_char from rest joint positions: up = hips -> head, X = right -> left shoulder made orthogonal to up."""
    up = head - hips
    across = upper_arm_l - upper_arm_r
    if up.length < 1e-9 or across.length < 1e-9:
        raise CalibrationError("The hips and head, or the two upper arms, are at the same place in rest pose.")
    up.normalize()
    x = across - up * across.dot(up)
    if x.length < 1e-6 * across.length:
        raise CalibrationError("The shoulder line is parallel to the hips-to-head line in rest pose.")
    x.normalize()
    return frame_quaternion(x, up, x.cross(up))


def rest_rotation(bone):
    """Rrest[b]: the bone's rest rotation in armature space."""
    return bone.matrix_local.to_quaternion()


def rest_aligned_offset(bone, char_frame):
    """Rrest[b]⁻¹ @ C_char: multiply the bone's world rotation by this to get its rest-aligned frame."""
    return rest_rotation(bone).inverted() @ char_frame


def rest_aligned(q_world, offset):
    """Q_b(t) = q_b(t) @ Rrest[b]⁻¹ @ C_char, from the bone's world rotation and its rest_aligned_offset."""
    return q_world @ offset


def char_frame_world(char_frame, matrix_world):
    """The character frame in world space for the armature object's world matrix."""
    return matrix_world.to_quaternion() @ char_frame


def axis_rot_from(rest_dir, side, ref_angle=0.0):
    """Rotation (character-frame coordinates) taking SAO's reference arm direction onto the rig's rest forearm.

    `rest_dir` points from the forearm head to the hand head at rest, in character coordinates. The reference
    direction is (±cos a, -sin a, 0) with `a` = `ref_angle`, the arm angle below horizontal of the avatar the
    SAO offsets were authored for. The guitar scenes target T-pose VRM avatars, whose arm axis_rot SAO sets
    to identity (MMD_SA.js get_bone_axis_rotation, THREEX branch), hence the default of 0. The aim offset is
    applied as Q_hand @ axis_rot @ offset, so it follows the rest forearm whatever the rig's rest pose.
    """
    sign = 1.0 if side == 'L' else -1.0
    reference = Vector((sign * math.cos(ref_angle), -math.sin(ref_angle), 0.0))
    return reference.rotation_difference(rest_dir.normalized())


def fingertip_local(distal, intermediate=None):
    """(tip in the distal bone's rest space, source).

    The distal bone's tail is used unless it looks unreliable (much shorter or longer than the intermediate
    segment, or bent away from the finger). Then the tip is SAO's estimate: the distal head plus half the
    intermediate segment, continued along the finger.
    """
    head, tail = distal.head_local, distal.tail_local
    tip, source = tail, 'TAIL'
    if intermediate is not None:
        segment = head - intermediate.head_local
        direction = tail - head
        if segment.length > 1e-9:
            ratio = direction.length / segment.length
            bent = direction.angle(segment, math.pi) > TAIL_MAX_ANGLE
            if bent or not TAIL_RATIO_RANGE[0] <= ratio <= TAIL_RATIO_RANGE[1]:
                tip, source = head + 0.5 * segment, 'ESTIMATE'
    return distal.matrix_local.inverted() @ tip, source


def _first(*items):
    return next((item for item in items if item is not None), None)


def compute(arm_obj, mapping, *, flip=False, ref_angle=0.0, metres_per_bu=1.0):
    """Calibrate the armature object `arm_obj` with the bone map `mapping` ({slot key: bone name}).

    `flip` turns the character frame half a turn about up (the user's fix for a wrong facing); `ref_angle` is
    the axis_rot reference angle; `metres_per_bu` is the scene unit scale (unit_settings.scale_length).
    Raises CalibrationError if a required bone is missing or the rest pose is degenerate.
    """
    bones = arm_obj.data.bones
    messages = []

    def bone(key, required=True):
        name = mapping.get(key, "")
        found = bones.get(name) if name else None
        if found is None and required:
            raise CalibrationError(f"{bonemap.SLOT_BY_KEY[key].title} is not mapped to a bone.")
        return found

    mw = arm_obj.matrix_world
    scale = mw.to_scale()
    if mw.to_3x3().determinant() < 0.0:
        messages.append(('WARNING', "The armature object has a mirroring (negative) scale; rotations may be wrong."))
    elif max(scale) > 1.001 * min(scale):
        messages.append(('WARNING', "The armature object has a non-uniform scale; apply it for reliable rotations."))

    hips, head = bone("hips"), bone("head")
    bone("chest")
    upper_arm = {side: bone(f"upper_arm_{side}") for side in SIDES}
    forearm = {side: bone(f"forearm_{side}") for side in SIDES}
    hand = {side: bone(f"hand_{side}") for side in SIDES}

    char_frame = character_frame(hips.head_local, head.head_local,
                                 upper_arm['L'].head_local, upper_arm['R'].head_local)
    if flip:
        char_frame = char_frame @ FLIP
    up_world = (mw.to_3x3() @ (char_frame @ Vector((0.0, 1.0, 0.0)))).normalized()
    forward = char_frame @ Vector((0.0, 0.0, 1.0))

    # Sign check: in T- and A-poses the index finger sits in front of the ring finger.
    votes = []
    for side in SIDES:
        index = _first(bone(f"index_proximal_{side}", False), bone(f"index_intermediate_{side}", False))
        ring = _first(bone(f"ring_proximal_{side}", False), bone(f"ring_intermediate_{side}", False))
        if index is not None and ring is not None:
            across = index.head_local - ring.head_local
            if across.length > 1e-9:
                votes.append(across.normalized().dot(forward))
    if votes and max(votes) < -0.3:
        messages.append(('WARNING', "The index fingers sit behind the ring fingers relative to the detected facing "
                                    "(Z): left and right may be swapped in the bone map. Check the overlay, and use "
                                    "Flip Facing if the frame is wrong."))

    def metres(a, b):
        return (mw @ a - mw @ b).length * metres_per_bu

    arm_len = metres(upper_arm['L'].head_local, hand['L'].head_local)
    chain_len = {side: metres(upper_arm[side].head_local, forearm[side].head_local)
                 + metres(forearm[side].head_local, hand[side].head_local) for side in SIDES}

    middle = bone("middle_proximal_L", False)
    if middle is not None:
        palm_len = metres(hand['L'].head_local, middle.head_local)
    else:
        palm_len = metres(hand['L'].head_local, hand['L'].tail_local)
        messages.append(('WARNING', "No left middle-finger proximal bone: the palm length is taken from the hand "
                                    "bone."))

    neck = bone("neck", False)
    if neck is None:
        neck = head
        messages.append(('WARNING', "No neck bone: the spine length is measured up to the head instead."))
    thigh = bone("thigh_L", False)
    if thigh is None:
        thigh = hips
        messages.append(('WARNING', "No left upper-leg bone: the spine length is measured from the hips instead."))
    spine_len = (mw @ neck.head_local - mw @ thigh.head_local).dot(up_world) * metres_per_bu

    if min(arm_len, palm_len, spine_len, *chain_len.values()) <= 1e-6:
        raise CalibrationError("An arm, palm or spine length is zero or negative; check the bone map.")

    heights = [(mw @ p).dot(up_world) for b in bones for p in (b.head_local, b.tail_local)]
    height = (max(heights) - min(heights)) * metres_per_bu
    if not HEIGHT_RANGE[0] <= height <= HEIGHT_RANGE[1]:
        messages.append(('WARNING', f"The character is {height:.2f} m tall. GuitarRig works in metres: check the "
                                    "object scale and the scene's unit scale."))

    char_inv = char_frame.inverted()
    axis_rot = {}
    for side in SIDES:
        rest_dir = char_inv @ (hand[side].head_local - forearm[side].head_local)
        if rest_dir.length < 1e-9:
            raise CalibrationError(f"The {side} forearm and hand start at the same place in rest pose.")
        axis_rot[side] = axis_rot_from(rest_dir, side, ref_angle)

    tips = []
    for side in SIDES:
        side_tips = []
        for finger in bonemap.FINGERS:
            distal = bone(f"{finger}_distal_{side}", False)
            if distal is not None:
                tip, source = fingertip_local(distal, bone(f"{finger}_intermediate_{side}", False))
                side_tips.append(Fingertip(side, finger, distal.name, tip, source))
        if not side_tips:
            hand_name = "left" if side == 'L' else "right"
            messages.append(('INFO', f"No finger bones on the {hand_name} hand: fingertip v2 is off there and only "
                                     "the palm margin applies."))
        tips += side_tips
    estimated = sum(1 for tip in tips if tip.source == 'ESTIMATE')
    if estimated:
        messages.append(('INFO', f"{estimated} fingertip(s) estimated from the finger joints because the bone tails "
                                 "look unreliable."))

    return Calibration(
        char_frame=char_frame, metres_per_bu=metres_per_bu, height=height,
        arm_len=arm_len, palm_len=palm_len, spine_len=spine_len, chain_len=chain_len,
        axis_rot=axis_rot, fingertips=tips, messages=messages,
        fingerprint=fingerprint(arm_obj, mapping, flip, ref_angle, metres_per_bu),
    )


def fingerprint(arm_obj, mapping, flip, ref_angle, metres_per_bu):
    """Hash of everything the calibration depends on, to tell when it is out of date."""
    h = hashlib.sha1()
    bones = arm_obj.data.bones
    for key in sorted(mapping):
        name = mapping[key]
        h.update(f"{key}={name};".encode())
        b = bones.get(name) if name else None
        if b is not None:
            h.update(_digits(v for row in b.matrix_local for v in row))
            h.update(_digits(b.tail_local))
    h.update(_digits(arm_obj.matrix_world.to_scale()))
    h.update(_digits((float(flip), ref_angle, metres_per_bu)))
    return h.hexdigest()[:16]


def _digits(values):
    return ",".join(f"{v:.5g}" for v in values).encode()


def format_messages(messages):
    return "\n".join(f"{level}\t{text}" for level, text in messages)


def parse_messages(text):
    messages = []
    for line in text.splitlines():
        level, _, message = line.partition("\t")
        if message:
            messages.append((level, message))
    return messages


def store(cal, pg):
    """Write a Calibration into a GTR_Calibration property group."""
    pg.char_frame = cal.char_frame
    pg.metres_per_bu = cal.metres_per_bu
    pg.height = cal.height
    pg.arm_len = cal.arm_len
    pg.palm_len = cal.palm_len
    pg.spine_len = cal.spine_len
    pg.chain_len_L, pg.chain_len_R = cal.chain_len['L'], cal.chain_len['R']
    pg.ratio_arm, pg.ratio_palm, pg.ratio_spine = cal.ratio_arm, cal.ratio_palm, cal.ratio_spine
    pg.axis_rot_L, pg.axis_rot_R = cal.axis_rot['L'], cal.axis_rot['R']
    pg.fingertips.clear()
    for tip in cal.fingertips:
        item = pg.fingertips.add()
        item.side, item.finger, item.bone = tip.side, tip.finger.upper(), tip.bone
        item.tip_local, item.source = tip.tip_local, tip.source
    pg.messages = format_messages(cal.messages)
    pg.fingerprint = cal.fingerprint
    pg.is_valid = True


def load(pg):
    """Calibration from a GTR_Calibration property group, or None if the armature is not calibrated."""
    if not pg.is_valid:
        return None
    return Calibration(
        char_frame=Quaternion(pg.char_frame), metres_per_bu=pg.metres_per_bu, height=pg.height,
        arm_len=pg.arm_len, palm_len=pg.palm_len, spine_len=pg.spine_len,
        chain_len={'L': pg.chain_len_L, 'R': pg.chain_len_R},
        axis_rot={'L': Quaternion(pg.axis_rot_L), 'R': Quaternion(pg.axis_rot_R)},
        fingertips=[Fingertip(t.side, t.finger.lower(), t.bone, Vector(t.tip_local), t.source)
                    for t in pg.fingertips],
        messages=parse_messages(pg.messages), fingerprint=pg.fingerprint,
    )
