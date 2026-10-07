"""Per-frame solve (§7): the guitar on its chest mount, aimed at the fretting hand; the wrist blend on the fretting
hand; the chest collider, the magnets, fingertips and reach clamp on both wrist targets; Blender's IK through the
helper rig (rig/build.py).

The FK pose is read with the rig's constraints at influence 0, and every pass starts from it, so nothing drifts.
A pass, with the guitar at rotation q (the mount rotation at first):
  1. the fretting wrist's rotation is blended toward the guitar (wrist.py); the other hand keeps its FK rotation;
  2. the chest collider pushes each wrist out of the torso (collider.py), and the magnets move each wrist target,
     with hand offsets and fingertips turned by the solved hand;
  3. the IK puts the arms there (one depsgraph update);
  4. in FOLLOW, the neck is aimed at the solved fretting hand from the mount rotation (aim.py), and q moves
     `relax` of the way to it.
Each frame is solved in its mode (modes.py): the scene's settings, or a range override's switch of the neck aim and
the fretboard-edge magnet, with the aim weight cross-faded where the mode changes.
SAO runs this loop once per frame and feeds the result into the next; offline it repeats until the aim and the
wrists settle, with at most `iterations` aims and one pass after the last, so the hands always match the guitar
they were solved for. The passes also refine the IK goal: the IK puts the IK forearm's tail on its goal, and
where a rig's hand does not start at that tail, the goal is corrected by the hand offset turned with the solved
forearm.

A bake (baker.py) solves frame after frame and carries a SolveState from one to the next: the filters (filters.py)
and the snap magnets that held each hand (their hysteresis). The filters act where SAO's do:
- the fingertip shift of fingertip magnets, and a magnet's pull when its Filter is set: One Euro filters the pull
  w (target - P) as a vector, Rotation filters the angle that P's offset from the magnet subtends at the guitar
  origin, asin(d / R), and puts P that far from the magnet: when the magnet does not act (w = 0) the offset is P's
  own, so P's height above the fretboard edge lags; when it clamps (w = 1) the offset shrinks to nothing (SAO's
  1/9999), so P settles onto the plane smoothly (min.js, Tt, reference_point_filter);
- the fretting wrist rotation after the blend (It, hand_rot_filter), here relative to the chest, so the body's
  own turns are not delayed;
and, off by default, where SAO does not: each wrist target's correction (the target less the FK wrist, so the
mocap's own motion is never smoothed), and the neck aim's swing. Lengths are filtered in SAO's arm space.
Solve Frame solves the current frame like the first frame of a bake: the filters have no history to smooth.

Pass-through (mocap prep §6.2): a snap or linear magnet shrinks a wrist's distance d from it to about d² / R, so it
would take back most of a stroke. On the Pass-Through hands the wrist's motion relative to the chest is split into
a slow base (low-passed at the pass-through cutoff, zero phase) and the quick detail; the collider and the magnets
act on the base, the detail (times the gain) is added back, and the barriers and the collider push the result out
again. The magnets still decide where the hand hovers, and the strokes ride on top. The bake samples the FK wrists
of all its frames first; Solve Frame samples 2 s each side of its frame, within the bake range.

The last Solve Frame result, with what each magnet did, is kept for the overlay and the panels while the rig
shows it, which is until the frame changes. Meanwhile a bake's tracks are muted (keys.mute_for_solve): the IK
then starts from the mocap, as in the bake, and Blender's IK result depends on the pose it starts from (the
upper arm's twist turns the pole alignment).
"""

import math
from dataclasses import dataclass, field

import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

from . import aim, calibrate, collider, filters, ik, keys, landmarks, magnets, modes, mount, wrist
from .bonemap import SIDES
from .mathx import rotation_angle

TOLERANCE_M = 1e-4          # a wrist this close to its target, in metres, has converged
TOLERANCE_ANGLE = math.radians(0.05)    # an aim that turns the guitar less than this has converged
CHECK_TOLERANCE_M = 1e-3    # the rig check passes when the IK reproduces the FK elbows and wrists this closely
SIDE_NAMES = {'L': "left", 'R': "right"}
FRET_SIDE = 'L'             # the fretting hand: the neck aims at it and its wrist follows the guitar
SAO_UNITS_PER_M = 11.0      # MMD units per metre: SAO's lengths, in the arm space of its reference avatar
CLAMPED_OFFSET_SAO = 1.0 / 9999.0   # SAO's offset of a clamped hand for the rotation filter, in its units
PASSTHROUGH_WINDOW_S = 2.0  # Solve Frame samples this many seconds each side of its frame for the pass-through

_results = {}               # scene session_uid -> FrameResult of the last solve


class SolveError(ValueError):
    """The scene is not ready to solve."""


@dataclass
class Arm:
    """One arm in the FK pose, in world space."""
    shoulder: Vector            # IK chain root head
    elbow: Vector               # IK forearm head
    tip: Vector                 # IK forearm tail: what the IK constraint puts on its goal
    wrist: Vector               # IK hand head: the point the magnets move
    up: Vector                  # the chain root's up axis for its pole angle (ik.up_axis)
    upper_frame: Quaternion     # rest-aligned frame of the chain root
    forearm: Quaternion         # IK forearm world rotation
    hand: Quaternion            # IK hand world rotation
    hand_frame: Quaternion      # rest-aligned hand frame Q_hand
    hand_offset: Quaternion     # hand world rotation @ this = its rest-aligned frame
    tips: dict = field(default_factory=dict)    # finger ('INDEX', ...) -> world vector from the wrist to its tip

    @property
    def length(self):
        """Reach of the wrist: shoulder to elbow plus elbow to wrist."""
        return (self.elbow - self.shoulder).length + (self.wrist - self.elbow).length


def sample_arm(obj, chain, char_frame, pole_angle, fingertips=()):
    """The arm of `chain` (rig/build.py) in the armature's current evaluated pose. `fingertips` are the
    calibrate.Fingertip entries of this side: re-sampled from the current finger pose, as SAO does each frame."""
    mw = obj.matrix_world
    pose = obj.pose.bones
    root, forearm, hand = pose[chain.upper], pose[chain.forearm], pose[chain.hand]
    root_world, forearm_world, hand_world = mw @ root.matrix, mw @ forearm.matrix, mw @ hand.matrix
    axes = root_world.to_3x3().normalized()
    root_rotation, hand_rotation = root_world.to_quaternion(), hand_world.to_quaternion()
    hand_offset = calibrate.rest_aligned_offset(hand.bone, char_frame)
    tips = {}
    for tip in fingertips:
        distal = pose.get(tip.bone)
        if distal is not None:
            tips[tip.finger.upper()] = mw @ (distal.matrix @ Vector(tip.tip_local)) - hand_world.translation
    return Arm(
        shoulder=root_world.translation, elbow=forearm_world.translation, tip=mw @ forearm.tail,
        wrist=hand_world.translation, up=ik.up_axis(axes.col[0], axes.col[2], pole_angle),
        upper_frame=calibrate.rest_aligned(root_rotation, calibrate.rest_aligned_offset(root.bone, char_frame)),
        forearm=forearm_world.to_quaternion(), hand=hand_rotation,
        hand_frame=calibrate.rest_aligned(hand_rotation, hand_offset), hand_offset=hand_offset, tips=tips,
    )


def root_bias(settings, side, arm):
    """SAO's right-arm root_rotation as a world rotation about the shoulder, or None when it is off.

    SAO turns the right upper arm by it, in the upper arm's own frame, before its IK (min.js, jt): an elbow hint,
    not a move of the wrist target. The pole target does the same here (ik.pole_position).
    """
    if side != 'R' or not settings.use_right_root_bias:
        return None
    turn = Euler(settings.right_root_bias, 'XYZ').to_quaternion()
    return arm.upper_frame @ turn @ arm.upper_frame.inverted()


# Magnets -------------------------------------------------------------------------------------------------------

def magnet_shapes(root, items):
    """({magnet index: magnets.Shape}, messages) for the enabled magnets, from their landmarks relative to
    GTR_ROOT. Magnets that miss a landmark are left out with a warning."""
    shapes, messages = {}, []
    for index, item in enumerate(items):
        if not item.enabled:
            continue
        a, b = item.landmark_a, item.landmark_b
        if a is None or (item.kind == 'LINE' and b is None):
            messages.append(('WARNING', f"Magnet {item.name} is missing a landmark and was skipped."))
        elif item.kind == 'LINE':
            shapes[index] = magnets.Shape('LINE', landmarks.local_position(root, a),
                                          landmarks.local_position(root, b))
        else:
            shapes[index] = magnets.Shape('PLANE', landmarks.local_position(root, a),
                                          normal=landmarks.local_normal(root, a))
    return shapes, messages


def reach_scale(settings, cal):
    """Scene units per metre of a magnet distance (reach and peak) on this character."""
    return magnets.distance_scale(settings.autoscale_policy, cal.ratio_arm) / cal.metres_per_bu


def sao_unit(settings, cal):
    """Scene units per unit of SAO's arm space, the unit its length filters work in."""
    return reach_scale(settings, cal) / SAO_UNITS_PER_M


def magnet_entries(settings, cal, side, arm, guitar, shapes, hand=None, hooks=None, frame_mode=None):
    """The magnets of `side` as magnets.Entry, in scene units, for the guitar placed at `guitar`. `hand` is the
    hand's solved world rotation (default: FK): hand offsets and fingertips turn with it. `hooks` (Hooks) adds the
    bake's filters. `frame_mode` (modes.FrameMode) switches the settings a range override changes."""
    distance = reach_scale(settings, cal)
    offset_scale = magnets.offset_scale(settings.autoscale_policy, cal.ratio_arm, cal.ratio_palm) / cal.metres_per_bu
    hand = arm.hand if hand is None else hand
    hand_frame = hand @ arm.hand_offset
    turn = hand @ arm.hand.inverted()
    value = getattr if frame_mode is None else frame_mode.magnet
    entries = []
    for index, item in enumerate(settings.magnets):
        shape = shapes.get(index)
        if shape is None or item.hand != side:
            continue
        params = magnets.Params(item.effective_distance_m * distance, item.peak * distance, value(item, "power"),
                                item.crossable, item.hysteresis)
        offset = Vector()
        if item.hand_offset_mode != 'NONE':
            local = settings.aim_hand_offset if item.hand_offset_mode == 'PARENT_BONE' else item.hand_offset
            offset = magnets.hand_offset(local, hand_frame, offset_scale,
                                         cal.axis_rot[side] if item.apply_axis_rot else None)
        fingertips = None
        if item.kind == 'PLANE' and item.fingertip_mode == 'V2':
            vectors = [turn @ arm.tips[finger] for finger in sorted(item.fingers) if finger in arm.tips]
            margin = settings.palm_margin_m * distance
            if vectors:
                margin += item.fingertip_offset_m * guitar.scale[0]
            else:
                vectors = [offset]      # no finger bones: the hand point itself keeps the palm margin (§13)
            fingertips = magnets.Fingertips(vectors, margin, item.push_only)
        tip_filter = pull_filter = None
        if hooks is not None:
            tip_filter = hooks.tip(side, index) if fingertips is not None else None
            pull_filter = hooks.pull(side, index, value(item, "filter"))
        entries.append(magnets.Entry(index, shape.world(guitar, item.use_default_rotation), params, offset,
                                     fingertips, tip_filter, pull_filter))
    return entries


def mount_from_chest(chest_pos, chest_frame, cal, settings, scale):
    """The guitar on its chest mount for a chest pose (P_chest, Q_chest), as a magnets.GuitarPose."""
    matrix = mount.mount_matrix(chest_pos, chest_frame, settings.mount_t, settings.mount_q,
                                mount.spine_factor(cal, settings.autoscale_policy), scale, cal.metres_per_bu)
    location, rotation, _ = matrix.decompose()
    return magnets.GuitarPose(location, rotation, rotation.copy(), Vector(scale))


def mount_pose(obj, cal, settings, root):
    """The guitar on its chest mount in the armature's current pose, as a magnets.GuitarPose."""
    chest_pos, chest_frame = mount.chest_pose(obj, cal, obj.gtr_char.bone_map.chest)
    return mount_from_chest(chest_pos, chest_frame, cal, settings, mount.root_scale(root))


# Filters -------------------------------------------------------------------------------------------------------

class Hooks:
    """The bake's filters (filters.py) for one solve pass, as hooks for the solve: each returns its input where
    its filter is off. `unit` is the scene length of one unit of SAO's arm space; `origin` the guitar origin."""

    def __init__(self, settings, bank, unit, origin):
        self.settings, self.bank, self.unit, self.origin = settings, bank, unit, origin
        self.on = bank is not None and settings.use_filters

    def tip(self, side, index):
        """The fingertip shift filter of magnet `index`, or None."""
        if not (self.on and self.settings.use_filter_fingertips):
            return None
        bank, unit, key, params = self.bank, self.unit, ('TIP', side, index), tuple(self.settings.filter_fingertip)
        return lambda shift: bank.apply(key, 'SCALAR', params, shift / unit) * unit

    def pull(self, side, index, kind):
        """The pull filter of magnet `index` for its Filter setting, or None (see the module notes)."""
        if not self.on or kind not in {'ONE_EURO', 'ROTATION_BASED'}:
            return None
        bank, unit, key = self.bank, self.unit, ('PULL', side, index)
        zero = Vector((0.0, 0.0, 0.0))
        if kind == 'ONE_EURO':
            params = tuple(self.settings.filter_pull)

            def vector(point, target, weight):
                moved = bank.apply(key, 'VECTOR', params, (target - point) * (weight / unit) if weight > 0.0 else zero)
                return moved * unit if weight > 0.0 else zero.copy()
            return vector

        params, origin = tuple(self.settings.filter_rotation), self.origin

        def rotation(point, target, weight):
            radius = max((point - origin).length, 1e-9)
            if weight >= 1.0:
                base, offset = target, target - point
                offset = offset.normalized() * (CLAMPED_OFFSET_SAO * unit) if offset.length > 1e-12 else zero
            elif weight > 0.0:
                base, offset = point, (target - point) * weight
            else:
                base, offset = target, point - target
            length = offset.length
            angle = bank.apply(key, 'SCALAR', params, math.asin(min(length / radius, 1.0)))
            if length <= 1e-12:
                return base - point
            return base + offset * (math.sin(angle) * radius / length) - point
        return rotation

    def wrist(self, side, hand, chest_frame):
        """The fretting wrist's world rotation after its filter, which runs relative to the chest."""
        if not (self.on and self.settings.use_filter_wrist):
            return hand
        chest_frame = Quaternion(chest_frame)
        relative = self.bank.apply(('WRIST', side), 'QUATERNION', tuple(self.settings.filter_wrist),
                                   chest_frame.inverted() @ hand)
        return (chest_frame @ relative).normalized()

    def target(self, side, fk_wrist, point):
        """A wrist target after its correction filter: the target less the FK wrist is filtered."""
        if not (self.on and self.settings.use_filter_targets):
            return point
        moved = self.bank.apply(('TARGET', side), 'VECTOR', tuple(self.settings.filter_target),
                                (point - fk_wrist) / self.unit)
        return fk_wrist + moved * self.unit

    def guitar(self, rotation, default_rotation):
        """An aimed guitar rotation after its filter, which runs on the swing away from the mount rotation."""
        if not (self.on and self.settings.use_filter_guitar):
            return rotation
        swing = self.bank.apply(('GUITAR',), 'QUATERNION', tuple(self.settings.filter_guitar),
                                rotation @ default_rotation.inverted())
        return (swing @ default_rotation).normalized()


@dataclass
class SolveState:
    """What a bake carries from one frame to the next: the filters and, per side, the magnets that held the hand
    (their hysteresis). A new state (Solve Frame) has neither, so the filters pass the frame through."""
    bank: filters.FilterBank
    holding: dict = field(default_factory=lambda: {side: frozenset() for side in SIDES})

    @classmethod
    def new(cls, fps):
        return cls(filters.FilterBank(fps))

    def commit(self, result):
        """Keep what the solved frame `result` leaves for the next one."""
        self.bank.commit()
        self.holding = {side: frozenset(index for index, hit in side_result.hits if hit.holds)
                        for side, side_result in result.sides.items()}


# Results -------------------------------------------------------------------------------------------------------

@dataclass
class SideResult:
    fk_wrist: Vector
    target: Vector              # the wrist target after the collider, the magnets and the reach clamp
    hits: list                  # [(magnet index, magnets.Hit)] in list order
    clamped: bool               # the reach clamp moved the target
    wrist: Vector = None        # the solved wrist
    elbow: Vector = None        # the solved elbow
    collider: object = None     # collider.Contact: what the chest collider did, or None when it is off
    passthrough: Vector = None  # the quick wrist motion that passed through the magnets, or None when it is off

    @property
    def error(self):
        return (self.wrist - self.target).length


@dataclass
class FrameResult:
    frame: int
    serial: int                 # settings.solve_serial when it was solved
    mode: str
    guitar: magnets.GuitarPose
    sides: dict                 # side -> SideResult
    iterations: int             # passes: wrists, magnets and IK, one depsgraph update each
    converged: bool
    metres_per_bu: float
    messages: list = field(default_factory=list)
    neck: aim.Aim = None        # the last neck aim (FOLLOW), or None
    wrist_turn: float = 0.0     # radians the fretting wrist turned away from the mocap
    wrist_constrained: bool = False     # the wrist yaw was turned the constrained way
    frame_mode: modes.FrameMode = None  # the mode the frame was solved in

    @property
    def swing(self):
        """Angle between the mount rotation and the solved guitar rotation, in radians."""
        return rotation_angle(self.guitar.rotation, self.guitar.default_rotation)

    def hit(self, index):
        """The magnets.Hit of magnet `index`, or None if it did not act."""
        for side in self.sides.values():
            for i, hit in side.hits:
                if i == index:
                    return hit
        return None


def shown_result(scene):
    """The last solve if the rig still shows it (the constraints are on at its frame), otherwise None."""
    result = _results.get(scene.session_uid)
    settings = scene.gtr
    if (result is None or not settings.solve_active or result.serial != settings.solve_serial
            or result.frame != settings.solve_frame or result.frame != scene.frame_current):
        return None
    return result


def summary(result, items):
    """One line on how far each wrist moved and which magnets acted."""
    parts = []
    for side in SIDES:
        side_result = result.sides[side]
        moved = (side_result.target - side_result.fk_wrist).length * result.metres_per_bu * 100.0
        acting = [f"{items[i].name} {'clamp' if hit.barrier else format(hit.weight, '.2f')}"
                  for i, hit in side_result.hits if hit.weight > 0.0 and i < len(items)]
        contact = side_result.collider
        if contact is not None and contact.weight > 0.0:
            acting.insert(0, f"chest collider {contact.moved.length * result.metres_per_bu * 100.0:.1f} cm")
        text = f"{SIDE_NAMES[side]} wrist moved {moved:.1f} cm"
        parts.append(text + (f" ({', '.join(acting)})" if acting else ""))
    if result.neck is not None:
        parts.append(f"neck swung {math.degrees(result.swing):.1f}°")
    if result.wrist_turn > 0.0:
        parts.append(f"{SIDE_NAMES[FRET_SIDE]} wrist turned {math.degrees(result.wrist_turn):.1f}°")
    return f"Frame {result.frame}: " + "; ".join(parts) + "."


# Solving -------------------------------------------------------------------------------------------------------

def _load(obj):
    cal = calibrate.load(obj.gtr_char.calibration)
    if cal is None:
        raise SolveError("Calibrate the character first.")
    return cal


def scene_fps(scene):
    return scene.render.fps / (scene.render.fps_base or 1.0)


def frame_range(scene):
    """The bake's frame range (first, last)."""
    settings = scene.gtr
    if settings.use_scene_frame_range:
        return scene.frame_start, scene.frame_end
    return settings.frame_start, settings.frame_end


# Pass-through --------------------------------------------------------------------------------------------------

def passthrough_sides(settings):
    """The hands whose quick motion passes through the magnets."""
    if settings.passthrough_gain <= 0.0:
        return ()
    return tuple(side for side in SIDES if side in settings.passthrough_hands)


def read_wrists(obj, chains, chest):
    """({side: the IK hand's head}, the chest bone's matrix), world space, in the current evaluated pose, as
    NumPy arrays."""
    mw = obj.matrix_world
    wrists = {side: np.array(mw @ obj.pose.bones[chain.hand].head) for side, chain in chains.items()}
    return wrists, np.array(mw @ obj.pose.bones[chest].matrix)


def passthrough_details(settings, wrists, chest, fps):
    """{side: (n, 3)} the world vectors that pass through the magnets on each frame: the wrist's motion relative to
    the chest above the cutoff, times the gain. `wrists`: {side: (n, 3) world points}; `chest`: (n, 4, 4) world
    matrices of the chest bone."""
    chest = np.asarray(chest, dtype=np.float64)
    inverse = np.linalg.inv(chest)
    out = {}
    for side in passthrough_sides(settings):
        local = np.einsum("nij,nj->ni", inverse[:, :3, :3], wrists[side]) + inverse[:, :3, 3]
        detail = local - filters.filtfilt(local, settings.passthrough_cutoff, fps)
        out[side] = np.einsum("nij,nj->ni", chest[:, :3, :3], detail) * settings.passthrough_gain
    return out


def passthrough_window(scene, frame, fps):
    """The frames Solve Frame samples for the pass-through: 2 s each side of `frame`, within the bake range (the
    scene range for a frame outside it)."""
    start, end = frame_range(scene)
    if not start <= frame <= end:
        start, end = scene.frame_start, scene.frame_end
    reach = int(round(PASSTHROUGH_WINDOW_S * fps))
    return list(range(min(frame, max(start, frame - reach)), max(frame, min(end, frame + reach)) + 1))


def sample_passthrough(context, rig, setup):
    """{side: world vector} that passes through the magnets on the current frame, from the FK wrists of the frames
    around it (passthrough_window). The rig is off and the add-on's bake tracks muted while they are sampled, the
    scene's meshes hidden if the bake hides them; the frame is set back afterwards."""
    scene = context.scene
    settings = scene.gtr
    if not passthrough_sides(settings):
        return {}
    obj = rig.armature
    current = (scene.frame_current, scene.frame_subframe)
    frames = passthrough_window(scene, current[0], setup.fps)
    hidden = []
    if settings.bake_hide_meshes:
        for item in scene.objects:
            if item.type == 'MESH' and not item.hide_viewport:
                item.hide_viewport = True
                hidden.append(item.name)
    wrists = {side: np.empty((len(frames), 3)) for side in SIDES}
    chest = np.empty((len(frames), 4, 4))
    try:
        with keys.muted((obj,)):
            rig.set_active(False)
            for i, frame in enumerate(frames):
                scene.frame_set(frame)
                found, chest[i] = read_wrists(obj, rig.chains, obj.gtr_char.bone_map.chest)
                for side in SIDES:
                    wrists[side][i] = found[side]
    finally:
        for name in hidden:
            item = scene.objects.get(name)
            if item is not None:
                item.hide_viewport = False
        scene.frame_set(current[0], subframe=current[1])
    index = frames.index(current[0])
    return {side: Vector(values[index]) for side, values in passthrough_details(settings, wrists, chest,
                                                                                setup.fps).items()}


def keep_out(settings, body, wrist, tips, entries):
    """(wrist, push) with the wrist pushed out of the chest collider `body` (or None) and of the barrier magnets
    among `entries`, as Re-clamp does; `tips` are world vectors from the wrist to the fingertips the collider
    keeps out."""
    start = wrist
    if body is not None:
        wrist, _ = collider.push(body, wrist, [wrist + v for v in tips])
    for entry in entries:
        if not magnets.is_barrier(entry):
            continue
        if not settings.barriers_ignore_distance:
            depth = -(wrist + entry.offset - entry.feature.a).dot(entry.feature.normal)
            if depth >= entry.params.reach:
                continue
        wrist, _ = magnets.clamp_out(wrist, entry)
    return wrist, (wrist - start).length


def sample_arms(context, rig, cal):
    """The FK pose of both arms: the rig's constraints are switched off and the scene is evaluated."""
    rig.set_active(False)
    context.view_layer.update()
    return _arms(rig, cal)


def _arms(rig, cal):
    return {side: sample_arm(rig.armature, rig.chains[side], cal.char_frame, rig.ik[side].pole_angle,
                             [tip for tip in cal.fingertips if tip.side == side])
            for side in SIDES}


def aim_axis(root):
    """(NECK_PIVOT, NUT) in GTR_ROOT space, or None if either landmark is missing."""
    found = landmarks.find(root)
    if "NECK_PIVOT" not in found or "NUT" not in found:
        return None
    return landmarks.local_position(root, found["NECK_PIVOT"]), landmarks.local_position(root, found["NUT"])


def aim_axis_shift(settings, shapes, hits, scale):
    """How far the fretting hand's fingertip magnets move the aimed neck axis, in GTR_ROOT space (aim.py). The
    last one in list order wins, as in SAO."""
    shift = Vector()
    for index, hit in hits:
        item = settings.magnets[index]
        if item.kind == 'PLANE' and item.fingertip_mode == 'V2' and hit.tip is not None:
            shift = aim.aim_shift(shapes[index].normal, -hit.shift * hit.weight, scale)
    return shift


def aim_target(obj, chain, arm, settings, cal):
    """The aim point on the solved fretting hand (world)."""
    hand = obj.matrix_world @ obj.pose.bones[chain.hand].matrix
    frame = hand.to_quaternion() @ arm.hand_offset
    scale = aim.offset_scale(settings.autoscale_policy, cal.ratio_palm) / cal.metres_per_bu
    return aim.target_point(hand.translation, frame, settings.aim_hand_offset, scale, cal.axis_rot[FRET_SIDE])


def place_goal(rig, side, arm, goal, cal, bias=None):
    """Put the IK goal of `side` on `goal`, its pole where the IK swings the FK arm there (ik.pole_position), and
    its bend on the seed a straight FK arm needs to reach it (ik.seed_bend)."""
    rig.helper("IKT", side).matrix_world = Matrix.Translation(goal)
    pole = ik.pole_position(arm.shoulder, arm.elbow, arm.tip, arm.up, goal,
                            ik.pole_distance(arm.length, cal.metres_per_bu), bias)
    rig.helper("POLE", side).matrix_world = Matrix.Translation(pole)
    bend = ik.seed_bend(arm.shoulder, arm.elbow, arm.tip, arm.up, arm.forearm, goal)
    rig.helper("BEND", side).matrix_world = Matrix.LocRotScale(arm.elbow, bend, None)


@dataclass
class Setup:
    """What a solve reads once; a bake reads it once for all its frames."""
    armature: object
    root: object                # GTR_ROOT
    cal: calibrate.Calibration
    shapes: dict                # magnet index -> magnets.Shape
    axis: tuple                 # (NECK_PIVOT, NUT) in GTR_ROOT space, or None: no neck aim
    scale: Vector               # GTR_ROOT's world scale
    fps: float                  # the scene's frame rate, for the filters
    schedule: modes.Schedule    # the mode of each frame
    messages: list = field(default_factory=list)


def prepare(context, rig):
    """The Setup of a solve for the scene's settings; raises SolveError when the scene is not ready."""
    scene = context.scene
    settings = scene.gtr
    obj, root = rig.armature, settings.guitar_root
    cal = _load(obj)
    if root is None:
        raise SolveError("Normalise the guitar first.")
    if settings.mount_source == 'NONE':
        raise SolveError("Load a preset or capture the mount first.")
    chest = obj.gtr_char.bone_map.chest
    if not chest or obj.pose.bones.get(chest) is None:
        raise SolveError("The chest bone is not mapped, or not in the armature.")
    try:
        scale = mount.root_scale(root)
    except mount.MountError as exc:
        raise SolveError(str(exc)) from exc
    shapes, messages = magnet_shapes(root, settings.magnets)
    schedule = modes.Schedule(settings)
    axis = aim_axis(root)
    aims = settings.aim_enabled or any(mode == 'FOLLOW' for *_range, mode in schedule.ranges)
    if aims and axis is None:
        messages.append(('WARNING', "The neck is not aimed: the Neck Pivot or Nut landmark is missing."))
    return Setup(obj, root, cal, shapes, axis, scale, scene_fps(scene), schedule, messages)


@dataclass
class Pose:
    """The FK pose of one frame, as the solve reads it (world space)."""
    arms: dict                  # side -> Arm
    mounted: magnets.GuitarPose
    chest: tuple                # (P_chest, Q_chest): the chest bone head and its rest-aligned frame
    char_world: Quaternion      # the character frame
    passthrough: dict = field(default_factory=dict)     # side -> world vector passing through the magnets


def sample_pose(context, rig, setup, update=True):
    """The FK pose of the current frame. With `update` the rig is switched off and the scene evaluated first, with
    the add-on's bake tracks muted, so a previous bake is not taken for the mocap. Without, the caller has just
    evaluated the frame that way (the bake)."""
    obj, cal = setup.armature, setup.cal
    if update:
        with keys.muted((obj,)):
            arms = sample_arms(context, rig, cal)
            chest = mount.chest_pose(obj, cal, obj.gtr_char.bone_map.chest)
    else:
        arms = _arms(rig, cal)
        chest = mount.chest_pose(obj, cal, obj.gtr_char.bone_map.chest)
    mounted = mount_from_chest(*chest, cal, context.scene.gtr, setup.scale)
    return Pose(arms, mounted, chest, calibrate.char_frame_world(cal.char_frame, obj.matrix_world))


def solve_pose(context, rig, setup, pose, state, iterations=None, show_guitar=True):
    """Solve the FK pose `pose` (sample_pose) of the current frame, filtering from `state` (SolveState), and leave
    the rig showing it. The filters' new state is left pending in `state.bank`: SolveState.commit keeps it.
    `show_guitar` puts GTR_ROOT on the solved guitar. Returns a FrameResult."""
    scene = context.scene
    settings = scene.gtr
    obj, root, cal, shapes = setup.armature, setup.root, setup.cal, setup.shapes
    frame_mode = setup.schedule.at(scene.frame_current)
    axis = setup.axis if frame_mode.aim_weight > 0.0 else None
    arms, mounted = pose.arms, pose.mounted
    messages = list(setup.messages)
    direction = wrist.DIRECTIONS[settings.wrist_direction]
    tolerance = TOLERANCE_M / cal.metres_per_bu
    unit = sao_unit(settings, cal)
    body = collider.capsule(settings, cal, *pose.chest)
    turns = {side: Quaternion() for side in SIDES}     # solved forearm rotation relative to the FK one
    rotation = mounted.rotation.copy()
    passes = max(1, iterations or settings.iterations) + (1 if axis is not None else 0)
    count, converged, aimed, constrained = 0, False, None, False
    rig.set_active(True)
    try:
        for count in range(1, passes + 1):
            guitar = magnets.GuitarPose(mounted.location, rotation, mounted.default_rotation, mounted.scale)
            if show_guitar:
                root.matrix_world = guitar.matrix()
            hooks = Hooks(settings, state.bank, unit, guitar.location)
            sides, hands = {}, {}
            for side, arm in arms.items():
                hand = arm.hand
                if side == FRET_SIDE and settings.wrist_blend > 0.0:
                    frame, constrained = wrist.blend(arm.hand_frame, rotation, settings.wrist_offset,
                                                     settings.wrist_blend, pose.char_world, side, direction,
                                                     cal.axis_rot[side])
                    hand = hooks.wrist(side, (frame @ arm.hand_offset.inverted()).normalized(), pose.chest[1])
                hands[side] = hand
                detail = pose.passthrough.get(side)
                start, contact = arm.wrist if detail is None else arm.wrist - detail, None
                collide = body is not None and side in settings.collider_hands
                turn = hand @ arm.hand.inverted()
                tips = [turn @ v for v in arm.tips.values()] if collide and settings.collider_fingertips else []
                if collide:
                    start, contact = collider.push(body, start, [start + v for v in tips])
                entries = magnet_entries(settings, cal, side, arm, guitar, shapes, hand, hooks, frame_mode)
                point, hits = magnets.apply(start, entries, barriers_ignore_distance=settings.barriers_ignore_distance,
                                            holding=state.holding.get(side, frozenset()))
                if detail is not None:
                    point, _ = keep_out(settings, body if collide else None, point + detail, tips, entries)
                point = hooks.target(side, arm.wrist, point)
                target, clamped = ik.reach_clamp(point, arm.shoulder, settings.reach_clamp * arm.length,
                                                 (arm.wrist - arm.shoulder).length)
                sides[side] = SideResult(arm.wrist.copy(), target, hits, clamped, collider=contact,
                                         passthrough=None if detail is None else detail.copy())
                rig.helper("WRIST_ROT", side).matrix_world = Matrix.LocRotScale(target, hand, None)
                goal = target - turns[side] @ (arm.wrist - arm.tip)
                place_goal(rig, side, arm, goal, cal, root_bias(settings, side, arm))
            context.view_layer.update()
            for side, arm in arms.items():
                chain = rig.chains[side]
                forearm = obj.matrix_world @ obj.pose.bones[chain.forearm].matrix
                sides[side].elbow = forearm.translation
                sides[side].wrist = obj.matrix_world @ obj.pose.bones[chain.hand].head
                turns[side] = forearm.to_quaternion() @ arm.forearm.inverted()
            settled = all(result.error < tolerance for result in sides.values())
            if axis is not None:
                shift = aim_axis_shift(settings, shapes, sides[FRET_SIDE].hits, mounted.scale)
                aim_point = aim_target(obj, rig.chains[FRET_SIDE], arms[FRET_SIDE], settings, cal)
                aimed = aim.aim(mounted, axis[0] + shift, axis[1] + shift, aim_point,
                                settings.aim_max_swing, frame_mode.aim_weight)
                wanted = hooks.guitar(aimed.rotation, mounted.default_rotation)
                following = rotation.slerp(wanted, settings.relax).normalized()
                settled = settled and rotation_angle(rotation, following) < TOLERANCE_ANGLE
            if settled:
                converged = True
                break
            if axis is not None and count < passes:
                rotation = following
    except Exception:
        rig.set_active(False)
        state.bank.discard()
        raise

    for side, side_result in sides.items():
        name = SIDE_NAMES[side]
        if side_result.clamped:
            messages.append(('INFO', f"The {name} wrist target was out of reach: it was kept within "
                                     f"{settings.reach_clamp:.1%} of the arm length, or the mocap wrist's "
                                     "distance if that is further."))
        if side_result.error >= tolerance:
            messages.append(('WARNING', f"The {name} IK misses its target by "
                                        f"{side_result.error * cal.metres_per_bu * 1000.0:.1f} mm: check the arm "
                                        "bones for IK locks, limits or stretch."))
    if aimed is not None and aimed.clamped:
        messages.append(('INFO', f"The neck aim was limited to {math.degrees(settings.aim_max_swing):.0f}° (Max "
                                 "Swing): the fretting hand is far from the neck."))
    if axis is not None and not converged and all(r.error < tolerance for r in sides.values()):
        messages.append(('INFO', f"The neck aim had not settled after {count - 1} iterations: raise Iterations, "
                                 "or lower Relax if the guitar oscillates."))
    return FrameResult(scene.frame_current, settings.solve_serial, frame_mode.mode, guitar, sides, count, converged,
                       cal.metres_per_bu, messages, aimed, rotation_angle(hands[FRET_SIDE], arms[FRET_SIDE].hand),
                       constrained, frame_mode)


def solve(context, rig, iterations=None):
    """Solve the current frame and leave the rig showing it (§7), as the first frame of a bake would be. Returns a
    FrameResult; raises SolveError."""
    scene = context.scene
    settings = scene.gtr
    settings.solve_active = False
    setup = prepare(context, rig)
    keys.mute_for_solve(rig.armature)
    try:
        passthrough = sample_passthrough(context, rig, setup)
        pose = sample_pose(context, rig, setup)
        pose.passthrough = passthrough
        result = solve_pose(context, rig, setup, pose, SolveState.new(setup.fps), iterations)
    except Exception:
        keys.unmute_after_solve(rig.armature)
        raise
    settings.solve_serial += 1
    settings.solve_frame = scene.frame_current
    settings.solve_active = True
    result.serial = settings.solve_serial
    _results[scene.session_uid] = result
    return result


def check_rig(context, rig):
    """{side: (elbow error, wrist error)} in metres with the IK goals on the FK pose: zero when the IK reproduces
    the mocap. IK locks, limits or stretch on the arm bones show up here. Leaves the rig off."""
    obj = rig.armature
    cal = _load(obj)
    arms = sample_arms(context, rig, cal)
    for side, arm in arms.items():
        place_goal(rig, side, arm, arm.tip, cal)
        rig.helper("WRIST_ROT", side).matrix_world = Matrix.LocRotScale(arm.wrist, arm.hand, None)
    rig.set_active(True)
    try:
        context.view_layer.update()
        errors = {}
        for side, arm in arms.items():
            chain = rig.chains[side]
            elbow = obj.matrix_world @ obj.pose.bones[chain.forearm].head
            hand = obj.matrix_world @ obj.pose.bones[chain.hand].head
            errors[side] = ((elbow - arm.elbow).length * cal.metres_per_bu,
                            (hand - arm.wrist).length * cal.metres_per_bu)
    finally:
        rig.set_active(False)
        context.view_layer.update()
    return errors


def check_messages(errors):
    """Warnings for the sides whose IK does not reproduce the FK pose (see check_rig)."""
    messages = []
    for side, (elbow, hand) in errors.items():
        if max(elbow, hand) > CHECK_TOLERANCE_M:
            messages.append(('WARNING', f"The {SIDE_NAMES[side]} IK does not reproduce the current pose: the elbow "
                                        f"is {elbow * 1000.0:.1f} mm and the wrist {hand * 1000.0:.1f} mm off. Check "
                                        "the arm bones for IK locks, limits or stretch."))
    return messages
