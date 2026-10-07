"""Apply Prep, Remove Prep and Show Original (mocap_prep_plan §4, §5.8, §7): the scene side of prep.py.

PrepJob samples the evaluated pose frame by frame, as the bake does (frame_set, meshes hidden), with every track of
the add-on muted, the prep's own included: a prep always starts from the raw mocap, so strengths never compound.
It keeps the armature-space poses of the chest, both arm chains and the picking hand's pick-point bones, and the
basis rotations of the finger joints. The frames are the bake range plus 1.5 s of context on each side, clipped to
the scene; only the bake range is keyed. Nothing is keyed until the last frame is sampled, so cancelling leaves
the scene as it was.

Then, in this order (§5.8):
  1. the picking hand: Range and stroke Snap on its turn relative to the forearm, D_rel = D_forearm⁻¹ D_hand,
     with D_b = R_b(pose) R_b(rest)⁻¹ a bone's turn from rest in armature space;
  2. Swing: the upper arm and the elbow turn so that the wrist follows the pick point's strum;
  3. Roll, on both hands: the twist of D_rel about the forearm axis moves onto the twist bone (MMD 手捩), and the
     hand keeps its pose (the axis is taken from the twist bone's head to the hand's, at rest, so the hand does
     not move either);
  4. the fretting fingers: Snap driven by each finger's total bend, then Range per joint, then the joint clamp;
  5. with Picking Fingers, Snap on the picking hand's fingers.
The arm bones' new poses become basis values (bake.pose_to_basis) and the fingers' basis rotations are written as
they are. The GuitarPrep action keys, one per frame, only the channels that changed, in each bone's rotation mode;
keys.place_prep puts it into the NLA under the bake. The bones it keys have their static values recorded first
(keys.record_static): MMD's 手捩, which the mocap does not animate, gets its value back when the layer is muted.

Bones are found by their MMD Japanese names: mmd_tools' name_j, the bone's own name, or mmd_tools' renaming
("手首.R") undone. The arm chains are the bone map's. The fretting hand is the left one (solver.FRET_SIDE).
"""

import math
import re
import time
from dataclasses import dataclass, field

import bpy
import numpy as np

from . import bake, baker, bonemap, calibrate, keys, prep, solver
from .bonemap import SIDES

CONTEXT_S = 1.5             # seconds of mocap sampled beyond each end of the bake range, but not keyed
REPORT_CUTOFF = 1.0         # Hz: the report measures the motion above this
SETTINGS_PROP = "gtr_prep_settings"     # on the prep action: the settings it was made with
RANGE_PROP = "gtr_prep_range"           # on the prep action: [first, last] keyed frame
FRET_SIDE = solver.FRET_SIDE
PICK_SIDE = 'R' if FRET_SIDE == 'L' else 'L'
SIDE_PREFIX = {'L': "左", 'R': "右"}
# (finger id, MMD name, joint digits), thumb first. MMD's thumb has 親指０ (on newer models) to 親指２.
FINGERS = (('THUMB', "親指", "０１２"), ('INDEX', "人指", "１２３"), ('MIDDLE', "中指", "１２３"),
           ('RING', "薬指", "１２３"), ('LITTLE', "小指", "１２３"))
FRET_FINGERS = ('INDEX', 'MIDDLE', 'RING', 'LITTLE')    # the fretting thumb holds the neck: no snap
PICK_TIPS = ('THUMB', 'INDEX')          # the pick point is midway between these fingertips
TWIST_NAME = "手捩"
LOCATION_TOLERANCE = 1e-6               # armature units: a bone moved less than this is not keyed
SETTING_NAMES = ("intensity", "range_wrist", "range_fingers", "range_cutoff", "snap_strokes", "snap_fingers",
                 "snap_picking", "snap_picking_fingers", "stroke_min", "finger_min", "swing", "swing_lead",
                 "swing_elbow_share", "roll_to_twist", "joint_margin")
NOT_MMD = "Prep supports MMD models (MMD Tools) in this version"


class PrepError(baker.BakeError):
    """The scene is not ready for the prep."""


# Bones ---------------------------------------------------------------------------------------------------------

_SUFFIX = re.compile(r"^(.+)[._]([LR])$")


def mmd_names(obj):
    """{normalised MMD Japanese name: bone name} for the armature `obj`."""
    names_j = bonemap.read_mmd_names(obj)
    index = {}
    for bone in obj.data.bones:
        match = _SUFFIX.match(bone.name)
        unsuffixed = SIDE_PREFIX[match.group(2)] + match.group(1) if match else None
        for name in (names_j.get(bone.name), bone.name, unsuffixed):
            if name:
                index.setdefault(bonemap.normalize(name), bone.name)
    return index


@dataclass
class Arm:
    path: list                  # bone names from the upper arm down to the hand, parents first
    twist: str = None           # the twist bone between the forearm and the hand, or None

    @property
    def upper(self):
        return self.path[0]

    @property
    def hand(self):
        return self.path[-1]


@dataclass
class Bones:
    """What the prep works on, by bone name."""
    chest: str
    forearm: dict               # side -> the forearm bone of the bone map
    arms: dict                  # side -> Arm
    fingers: dict               # side -> {finger id: [joint bone names], proximal first}
    tips: dict                  # side -> {finger id: (bone name, point in the bone's space)}
    messages: list = field(default_factory=list)


def _path(bones, upper, hand):
    names, bone = [], bones.get(hand)
    while bone is not None:
        names.append(bone.name)
        if bone.name == upper:
            return names[::-1]
        bone = bone.parent
    return None


def find_bones(obj):
    """The Bones of the armature `obj`; raises PrepError if they are not there."""
    bone_map = obj.gtr_char.bone_map
    bones = obj.data.bones
    index = mmd_names(obj)
    messages = []

    def mmd(side, name):
        return index.get(bonemap.normalize(SIDE_PREFIX[side] + name))

    if not bone_map.chest or bones.get(bone_map.chest) is None:
        raise PrepError("The chest bone is not mapped, or not in the armature.")
    arms, forearms, fingers, tips = {}, {}, {}, {}
    for side in SIDES:
        upper, forearm, hand = (getattr(bone_map, f"{kind}_{side}") for kind in ("upper_arm", "forearm", "hand"))
        path = _path(bones, upper, hand) if upper and hand else None
        if path is None or forearm not in path:
            raise PrepError(f"The {solver.SIDE_NAMES[side]} arm's bones are not mapped as a chain: check the bone "
                            "map.")
        between = path[path.index(forearm) + 1:-1]
        named = mmd(side, TWIST_NAME)
        twist = named if named in between else (between[-1] if between else None)
        arms[side], forearms[side] = Arm(path, twist), forearm
        found = {}
        for finger, name, digits in FINGERS:
            joints = [mmd(side, name + digit) for digit in digits]
            joints = [joint for joint in joints if joint is not None]
            if len(joints) >= 2:
                found[finger] = joints
        fingers[side] = found
        side_tips = {}
        for finger in PICK_TIPS:
            tip = mmd(side, FINGERS[[f for f, _, _ in FINGERS].index(finger)][1] + "先")
            if tip is not None:
                side_tips[finger] = (tip, (0.0, 0.0, 0.0))
            elif finger in found:
                distal = bones[found[finger][-1]]
                side_tips[finger] = (distal.name, (0.0, distal.length, 0.0))
        tips[side] = side_tips
    if not any(finger in fingers[FRET_SIDE] for finger in FRET_FINGERS):
        raise PrepError(f"{NOT_MMD}: no MMD finger bones (人指１…) were found on the "
                        f"{solver.SIDE_NAMES[FRET_SIDE]} hand.")
    for side in SIDES:
        if arms[side].twist is None:
            messages.append(('WARNING', f"No twist bone between the {solver.SIDE_NAMES[side]} forearm and hand: "
                                        "Roll is off there."))
    if len(tips[PICK_SIDE]) < len(PICK_TIPS):
        messages.append(('WARNING', f"The {solver.SIDE_NAMES[PICK_SIDE]} thumb or index finger is missing: Swing "
                                    "is off."))
    return Bones(bone_map.chest, forearms, arms, fingers, tips, messages)


# Settings ------------------------------------------------------------------------------------------------------

@dataclass
class Strengths:
    """The settings with Intensity applied: gains and snap exponents toward 1, the swing toward 0."""
    range_wrist: float
    range_fingers: float
    snap_strokes: float
    snap_fingers: float
    snap_picking: float         # 1 when Picking Fingers is off
    swing: float

    @classmethod
    def of(cls, options):
        def toward(value):
            return 1.0 + options.intensity * (value - 1.0)
        return cls(toward(options.range_wrist), toward(options.range_fingers), toward(options.snap_strokes),
                   toward(options.snap_fingers),
                   toward(options.snap_picking_fingers) if options.snap_picking else 1.0,
                   options.intensity * options.swing)

    def neutral(self, roll):
        return (not roll and self.swing == 0.0
                and all(v == 1.0 for v in (self.range_wrist, self.range_fingers, self.snap_strokes,
                                           self.snap_fingers, self.snap_picking)))


def snapshot(options):
    return {name: getattr(options, name) for name in SETTING_NAMES}


# Status --------------------------------------------------------------------------------------------------------

def prep_action(obj):
    found = keys.bake_strips(obj).get(keys.PREP) if obj is not None else None
    return found[1].action if found is not None else None


def is_muted(obj):
    found = keys.bake_strips(obj).get(keys.PREP) if obj is not None else None
    return found is not None and found[0].mute


def status(settings):
    """Messages on the prep layer of the scene's character: settings changed since it was applied, the bake is
    older than it, the layer is muted."""
    obj = settings.armature
    action = prep_action(obj)
    messages = []
    if action is not None:
        stored = action.get(SETTINGS_PROP)
        stored = stored.to_dict() if stored is not None else {}
        current = snapshot(settings.prep)
        if any(name not in stored or abs(float(stored[name]) - float(value)) > 1e-6
               for name, value in current.items()):
            messages.append(('INFO', "The settings changed since the prep was applied: Apply Prep again."))
        first, last = action.get(RANGE_PROP, (0, -1))
        start, end = baker.frame_range(settings.id_data)
        if start < first or end > last:
            messages.append(('WARNING', f"The prep covers frames {first}-{last} only, and the bake range is "
                                        f"{start}-{end}: Apply Prep again."))
        if is_muted(obj):
            messages.append(('INFO', "Showing the original mocap: the GuitarPrep layer is muted."))
    found = keys.bake_strips(obj).get(keys.ARM) if obj is not None else None
    if found is not None and int(found[1].action.get(keys.PREP_SERIAL_PROP, 0)) != keys.prep_serial(obj):
        text = ("The bake was made before this prep: bake again." if action is not None else
                "The bake was made from a prep that has been removed: bake again.")
        messages.append(('WARNING', text))
    return messages


# Apply ---------------------------------------------------------------------------------------------------------

def _rest(bones, name):
    """The bone's rest rotation in armature space, as a quaternion (4,)."""
    m = np.array(bones[name].matrix_local, dtype=np.float64)[:3, :3]
    return prep.from_matrices(m / np.linalg.norm(m, axis=0))


def _rotations(matrices):
    """Quaternions (n, 4) of the rotation part of matrices (n, 4, 4), scale removed."""
    _, rot, _ = bake.decompose(matrices)
    return prep.continuous(prep.from_matrices(rot))


def _turn(bones, matrices, name):
    """D_b = R_b(pose) R_b(rest)⁻¹ (n, 4)."""
    return prep.continuous(prep.qmul(_rotations(matrices), prep.qinv(_rest(bones, name))))


def _with_rotation(matrices, q):
    """Matrices (n, 4, 4) with their rotation replaced by q (n, 4), keeping their translation and scale."""
    out = np.array(matrices, dtype=np.float64)
    scale = np.linalg.norm(out[:, :3, :3], axis=1)
    out[:, :3, :3] = prep.to_matrices(q) * scale[:, None, :]
    return out


def _points(matrices, local):
    """Armature-space points (n, 3) of a point given in a bone's space."""
    return np.einsum("nij,j->ni", matrices[:, :3, :3], np.asarray(local, dtype=np.float64)) + matrices[:, :3, 3]


def _in_chest(chest, points):
    inverse = np.linalg.inv(chest)
    return np.einsum("nij,nj->ni", inverse[:, :3, :3], points) + inverse[:, :3, 3]


class PrepJob(baker.Job):
    """Apply Prep to the scene's character (see the module notes). Raises PrepError when the scene is not ready;
    from then on the scene is in the job's hands until `finish` or `cancel`."""

    def __init__(self, context, rig=None):
        scene = context.scene
        settings = scene.gtr
        obj = settings.armature
        if obj is None:
            raise PrepError("Pick the character first.")
        if calibrate.load(obj.gtr_char.calibration) is None:
            raise PrepError("Calibrate the character first.")
        options = settings.prep
        self.strengths = Strengths.of(options)
        if self.strengths.neutral(options.roll_to_twist):
            raise PrepError("Every tool is off (Intensity 0, or each strength neutral): there is nothing to apply.")
        baker._check_tweak((obj,))
        settings.solve_active = False
        if rig is not None:
            rig.set_active(False)
        keys.unmute_after_solve(obj)
        self.obj = obj
        self.bones = found = find_bones(obj)
        self.messages = list(found.messages)
        self.start, self.end = baker.frame_range(scene)
        if self.end < self.start:
            raise PrepError("The frame range is empty.")
        self.fps = solver.scene_fps(scene)
        margin = int(round(CONTEXT_S * self.fps))
        first = min(self.start, max(scene.frame_start, self.start - margin))
        last = max(self.end, min(scene.frame_end, self.end + margin))
        self.frames = list(range(first, last + 1))
        self.keyed = slice(self.start - first, self.end - first + 1)
        count = len(self.frames)
        posed = {found.chest} | {name for arm in found.arms.values() for name in arm.path}
        posed |= {pbone.parent.name for side in SIDES
                  for pbone in (obj.pose.bones[found.arms[side].upper],) if pbone.parent is not None}
        posed |= {bone for bone, _ in found.tips[PICK_SIDE].values()}
        sides = [FRET_SIDE] + ([PICK_SIDE] if options.snap_picking else [])
        based = {name for side in sides for finger, joints in found.fingers[side].items()
                 if side == PICK_SIDE or finger in FRET_FINGERS for name in joints}
        self.poses = {name: np.empty((count, 4, 4)) for name in posed}
        self.basis = {name: np.empty((count, 4, 4)) for name in based}
        self.index = 0
        self.started = time.perf_counter()
        self.temp = baker.Temp(context, (obj,), keys.ALL_ROLES, settings.bake_hide_meshes)

    def step(self, context):
        i = self.index
        context.scene.frame_set(self.frames[i])
        bones = self.obj.pose.bones
        for name, buffer in self.poses.items():
            buffer[i] = bones[name].matrix
        for name, buffer in self.basis.items():
            buffer[i] = bones[name].matrix_basis
        self.index += 1

    def cancel(self, context):
        self.temp.restore()

    # Processing ----------------------------------------------------------------------------------------------

    def finish(self, context):
        scene = context.scene
        settings = scene.gtr
        options = settings.prep
        obj = self.obj
        found = self.bones
        strengths = self.strengths
        cutoff, fps = options.range_cutoff, self.fps
        stats = {}

        # The arms: new armature-space poses of the chain bones.
        arm_poses = {side: {name: self.poses[name].copy() for name in found.arms[side].path} for side in SIDES}
        self._picking_hand(arm_poses[PICK_SIDE], options, strengths, stats)
        if strengths.swing > 0.0 and len(found.tips[PICK_SIDE]) == len(PICK_TIPS):
            self._swing(arm_poses[PICK_SIDE], options, strengths, stats)
        if options.roll_to_twist:
            for side in SIDES:
                self._roll(side, arm_poses[side], stats)
        rotations, locations = {}, {}
        for side in SIDES:
            self._arm_keys(side, arm_poses[side], rotations, locations)

        # The fingers: basis rotations.
        finger_quats = {}
        clamped = np.zeros(len(self.frames), dtype=bool)
        moves = {}
        for side in (FRET_SIDE, PICK_SIDE):
            a, gain, margin = ((strengths.snap_fingers, strengths.range_fingers, options.joint_margin)
                               if side == FRET_SIDE else (strengths.snap_picking, 1.0, None))
            if (a == 1.0 and gain == 1.0) or (side == PICK_SIDE and not options.snap_picking):
                continue
            moves[side] = 0
            for finger, joints in found.fingers[side].items():
                if side == FRET_SIDE and finger not in FRET_FINGERS:
                    continue
                source = [_rotations(self.basis[name]) for name in joints]
                out, hit, count = prep.finger(source, a, gain, math.degrees(options.finger_min), cutoff, fps, margin)
                clamped |= hit
                moves[side] += count
                finger_quats.update((name, pair) for name, pair in zip(joints, zip(source, out)))
        for name, (_, q) in finger_quats.items():
            rotations[name] = prep.to_matrices(q[self.keyed])

        report = self._report(context, arm_poses, finger_quats, clamped, moves, stats)
        self._write(context, rotations, locations)
        self.temp.restore()
        elapsed = max(time.perf_counter() - self.started, 1e-9)
        count = len(range(self.start, self.end + 1))
        lines = [('INFO', f"Prepped frames {self.start}-{self.end} ({count} frames) in {elapsed:.1f} s: "
                          f"{len(set(rotations) | set(locations))} bones keyed on the GuitarPrep layer.")]
        lines += report + self.messages
        if keys.has_bake(obj):
            lines.append(('WARNING', "The bake still holds the arms solved from the mocap before this prep: bake "
                                     "again."))
        options.report = calibrate.format_messages(lines)
        return lines

    def _picking_hand(self, poses, options, strengths, stats):
        """Range and stroke Snap on the picking hand's turn relative to its forearm."""
        if strengths.range_wrist == 1.0 and strengths.snap_strokes == 1.0:
            return
        bones = self.obj.data.bones
        forearm, hand = self.bones.forearm[PICK_SIDE], self.bones.arms[PICK_SIDE].hand
        d_forearm = _turn(bones, poses[forearm], forearm)
        relative = prep.qmul(prep.qinv(d_forearm), _turn(bones, poses[hand], hand))
        new, info = prep.strokes(relative, strengths.range_wrist, strengths.snap_strokes,
                                 math.degrees(options.stroke_min), options.range_cutoff, self.fps)
        stats["strokes"] = info
        poses[hand] = _with_rotation(poses[hand], prep.qmul(prep.qmul(d_forearm, new), _rest(bones, hand)))

    def _pick_points(self, poses):
        """The pick point (n, 3), armature space: midway between the picking thumb and index tips, carried with
        the hand from its sampled pose to `poses`' hand pose."""
        hand = self.bones.arms[PICK_SIDE].hand
        carry = poses[hand] @ np.linalg.inv(self.poses[hand])
        points = [_points(carry @ self.poses[bone], local) for bone, local in self.bones.tips[PICK_SIDE].values()]
        return 0.5 * (points[0] + points[1])

    def _swing(self, poses, options, strengths, stats):
        """Turn the picking upper arm and elbow so that the wrist follows the pick point's strum (§5.5)."""
        found = self.bones
        arm = found.arms[PICK_SIDE]
        chest = self.poses[found.chest]
        s, u, share = prep.strum(_in_chest(chest, self._pick_points(poses)), options.range_cutoff, self.fps,
                                 options.swing_lead)
        forearm = found.forearm[PICK_SIDE]
        shoulder, elbow, wrist = (poses[name][:, :3, 3] for name in (arm.upper, forearm, arm.hand))
        direction = np.einsum("nij,j->ni", chest[:, :3, :3], u)
        target = wrist + strengths.swing * s[:, None] * direction
        a_upper, a_forearm, straight = prep.swing_ik(shoulder, elbow, wrist, target, options.swing_elbow_share)
        below = arm.path.index(forearm)
        for i, name in enumerate(arm.path):
            poses[name] = (a_forearm if i >= below else a_upper) @ poses[name]
        stats["swing"] = {"share": share, "straight": np.nonzero(straight[self.keyed])[0] + self.start}

    def _roll(self, side, poses, stats):
        """Move the twist of the hand's turn relative to the forearm onto the twist bone (§5.6)."""
        arm = self.bones.arms[side]
        if arm.twist is None:
            return
        bones = self.obj.data.bones
        forearm = self.bones.forearm[side]
        d_forearm = _turn(bones, poses[forearm], forearm)
        relative = prep.qmul(prep.qinv(d_forearm), _turn(bones, poses[arm.hand], arm.hand))
        axis = prep.normalize(np.array(bones[arm.hand].head_local - bones[arm.twist].head_local))
        twist = prep.twist(relative, axis)
        poses[arm.twist] = _with_rotation(poses[arm.twist],
                                          prep.qmul(prep.qmul(d_forearm, twist), _rest(bones, arm.twist)))
        stats.setdefault("roll", {})[side] = np.degrees(prep.twist_angles(twist, axis)[self.keyed])
        self._check_axis(side, axis)

    def _check_axis(self, side, axis):
        """Cross-check the roll axis with mmd_tools' fixed axis of the twist bone (stored in MMD space)."""
        mmd = getattr(self.obj.pose.bones[self.bones.arms[side].twist], "mmd_bone", None)
        if mmd is None or not getattr(mmd, "enabled_fixed_axis", False):
            return
        x, y, z = mmd.fixed_axis
        fixed = np.array((x, z, y), dtype=np.float64)
        if np.linalg.norm(fixed) < 1e-9:
            return
        angle = math.degrees(math.acos(min(abs(prep.normalize(fixed) @ axis), 1.0)))
        if angle > 2.0:
            self.messages.append(('INFO', f"The {solver.SIDE_NAMES[side]} twist bone's fixed axis is {angle:.0f}° "
                                          "off the forearm: Roll turns it about the forearm."))

    def _arm_keys(self, side, poses, rotations, locations):
        """Basis rotations (and locations, if they moved) of the arm bones whose pose changed."""
        bones = self.obj.data.bones
        new = bake.pose_to_basis(bones, poses, self.poses)
        old = bake.pose_to_basis(bones, {name: self.poses[name] for name in poses}, self.poses)
        for name in poses:
            loc, rot, _ = bake.decompose(new[name])
            old_loc, old_rot, _ = bake.decompose(old[name])
            if np.abs(rot - old_rot).max() > baker.ROTATION_TOLERANCE:
                rotations[name] = rot[self.keyed]
            if np.abs(loc - old_loc).max() > LOCATION_TOLERANCE:
                locations[name] = loc[self.keyed]

    # Writing -------------------------------------------------------------------------------------------------

    def _write(self, context, rotations, locations):
        """Key the GuitarPrep action and put it into the NLA."""
        settings = context.scene.gtr
        obj = self.obj
        frames = np.arange(self.start, self.end + 1, dtype=np.float64)
        interpolation = settings.bake_interpolation
        action = keys.new_action(f"{obj.name}_GuitarPrep", keys.PREP)
        channels = keys.Channels(action, obj)
        for name in bake.parent_first(obj.data.bones, set(rotations) | set(locations)):
            pbone = obj.pose.bones[name]
            if name in rotations:
                mode = pbone.rotation_mode
                baker.write_channels(channels, pbone.path_from_id(baker.rotation_path(mode)),
                                     bake.rotation_channels(rotations[name], mode), frames, name, interpolation)
            if name in locations:
                baker.write_channels(channels, pbone.path_from_id("location"), locations[name], frames, name,
                                     interpolation)
        settings.prep.serial += 1
        action[keys.PREP_SERIAL_PROP] = settings.prep.serial
        action[SETTINGS_PROP] = snapshot(settings.prep)
        action[RANGE_PROP] = [self.start, self.end]
        keys.record_static(obj, set(rotations) | set(locations))
        self.temp.unmute()
        strip, old = keys.place_prep(obj, action, channels.slot, self.start)
        for item in old:
            if item.users == 0:
                bpy.data.actions.remove(item)
        action.name = f"{obj.name}_GuitarPrep"
        strip.name = action.name

    # Report --------------------------------------------------------------------------------------------------

    def _report(self, context, arm_poses, finger_quats, clamped, moves, stats):
        obj = self.obj
        found = self.bones
        cutoff, fps, keyed = REPORT_CUTOFF, self.fps, self.keyed
        cm = 100.0 * context.scene.unit_settings.scale_length * float(np.mean(obj.matrix_world.to_scale()))
        lines = []
        arm, poses = found.arms[PICK_SIDE], arm_poses[PICK_SIDE]
        chest = self.poses[found.chest][keyed]
        name = solver.SIDE_NAMES[PICK_SIDE]
        before = prep.travel(_in_chest(chest, self.poses[arm.hand][keyed, :3, 3]), cutoff, fps)
        after = prep.travel(_in_chest(chest, poses[arm.hand][keyed, :3, 3]), cutoff, fps)
        text = (f"The {name} wrist's travel above {cutoff:g} Hz: {before[0] * cm:.1f} → {after[0] * cm:.1f} cm RMS "
                f"(99th percentile {before[1] * cm:.1f} → {after[1] * cm:.1f} cm)")
        if len(found.tips[PICK_SIDE]) == len(PICK_TIPS):
            pick_before = self._pick_points(self.poses)[keyed]
            pick_after = self._pick_points(poses)[keyed]
            b, a = prep.travel(_in_chest(chest, pick_before), cutoff, fps), prep.travel(_in_chest(chest, pick_after),
                                                                                         cutoff, fps)
            text += f"; the pick point's {b[0] * cm:.1f} → {a[0] * cm:.1f} cm RMS"
        lines.append(('INFO', text + "."))
        chest_q = _rotations(chest)
        hands = [prep.qmul(prep.qinv(chest_q), _rotations(p[arm.hand][keyed])) for p in (self.poses, poses)]
        rms = [math.degrees(prep.detail_rms(q, cutoff, fps)) for q in hands]
        speed = [math.degrees(np.percentile(prep.speeds(q, fps), 95)) if len(q) > 1 else 0.0 for q in hands]
        text = (f"The {name} hand's turns above {cutoff:g} Hz: {rms[0]:.1f}° → {rms[1]:.1f}° RMS, speed "
                f"{speed[0]:.0f} → {speed[1]:.0f}°/s (95th percentile)")
        if "strokes" in stats:
            text += f"; {stats['strokes']['moves']} strokes snapped"
        lines.append(('INFO', text + "."))
        swing = stats.get("swing")
        if swing is not None and len(swing["straight"]):
            lines.append(('INFO', f"The {name} elbow was too straight to swing on {len(swing['straight'])} frames "
                                  f"({baker._fmt_frames(list(swing['straight']))}): only the shoulder turned."))
        for side, roll in stats.get("roll", {}).items():
            if len(roll):
                lines.append(('INFO', f"Roll: the {solver.SIDE_NAMES[side]} twist bone turns "
                                      f"{np.percentile(roll, 1):.0f}° to {np.percentile(roll, 99):.0f}° (1st to 99th "
                                      "percentile); the hand keeps its pose."))
        fret = [(finger, joints) for finger, joints in found.fingers[FRET_SIDE].items()
                if finger in FRET_FINGERS and joints[0] in finger_quats]
        if fret:
            times = {0: [], 1: []}
            for _, joints in fret:
                for k in (0, 1):
                    times[k] += prep.transitions(prep.bend([finger_quats[j][k][keyed] for j in joints]))
            if times[0]:
                lines.append(('INFO', f"The {solver.SIDE_NAMES[FRET_SIDE]} fingers' presses and releases: "
                                      f"{np.median(times[0]):.0f} → {np.median(times[1]):.0f} frames from 10 % to "
                                      f"90 % (median of {len(times[0])}); {moves.get(FRET_SIDE, 0)} moves snapped."))
        if PICK_SIDE in moves:
            lines.append(('INFO', f"The {name} fingers: {moves[PICK_SIDE]} moves snapped."))
        hit = np.nonzero(clamped[keyed])[0] + self.start
        if len(hit):
            lines.append(('INFO', f"The joint clamp held the {solver.SIDE_NAMES[FRET_SIDE]} fingers on {len(hit)} "
                                  f"frames ({baker._fmt_frames([int(f) for f in hit])})."))
        return lines


# Remove and show -----------------------------------------------------------------------------------------------

def remove(context):
    """Remove the prep layer from the scene's character; the bake stays. Returns messages."""
    scene = context.scene
    settings = scene.gtr
    obj = settings.armature
    removed = 0
    for action in keys.remove_prep(obj):
        if action.users == 0:
            bpy.data.actions.remove(action)
            removed += 1
    scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
    messages = [('INFO', f"Removed the prep ({removed} action{'s' if removed != 1 else ''}).")]
    found = keys.bake_strips(obj).get(keys.ARM)
    if found is not None and found[1].action.get(keys.PREP_SERIAL_PROP, 0):
        messages.append(('WARNING', "The bake was made from a prep: bake again."))
    settings.prep.report = calibrate.format_messages(messages)
    return messages


def show_original(context, original):
    """Mute (`original`) or unmute the prep layer, for a before and after view."""
    scene = context.scene
    obj = scene.gtr.armature
    if original:
        keys.mute((obj,), (keys.PREP,))
    else:
        found = keys.bake_strips(obj).get(keys.PREP)
        if found is not None:
            found[0].mute = False
    scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
