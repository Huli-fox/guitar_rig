"""Per-frame solve (§7): the guitar on its chest mount, the magnets and the reach clamp on both wrist targets,
then Blender's IK through the helper rig (rig/build.py).

The FK pose is read with the rig's constraints at influence 0, and the magnets always start from it, so nothing
drifts. The guitar stays on its mount in both modes for now; the modes differ only in their magnet settings
(magnets.MODE_PRESETS), so the magnets give the wrist targets in one pass. The iterations then only refine the IK
goal: the IK puts the IK forearm's tail on its goal, and where a rig's hand does not start at that tail, the goal
is corrected by the hand offset turned with the solved forearm. On connected arms the first iteration is exact.

The hands keep their FK world rotation: the wrist empties copy it. The last result, with what each magnet did,
is kept for the overlay and the panels while the rig shows it, which is until the frame changes.
"""

from dataclasses import dataclass, field

from mathutils import Euler, Matrix, Quaternion, Vector

from . import calibrate, ik, landmarks, magnets, mount
from .bonemap import SIDES

TOLERANCE_M = 1e-4          # a wrist this close to its target, in metres, has converged
CHECK_TOLERANCE_M = 1e-3    # the rig check passes when the IK reproduces the FK elbows and wrists this closely
SIDE_NAMES = {'L': "left", 'R': "right"}

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

    @property
    def length(self):
        """Reach of the wrist: shoulder to elbow plus elbow to wrist."""
        return (self.elbow - self.shoulder).length + (self.wrist - self.elbow).length


def sample_arm(obj, chain, char_frame, pole_angle):
    """The arm of `chain` (rig/build.py) in the armature's current evaluated pose."""
    mw = obj.matrix_world
    pose = obj.pose.bones
    root, forearm, hand = pose[chain.upper], pose[chain.forearm], pose[chain.hand]
    root_world, forearm_world, hand_world = mw @ root.matrix, mw @ forearm.matrix, mw @ hand.matrix
    axes = root_world.to_3x3().normalized()
    root_rotation, hand_rotation = root_world.to_quaternion(), hand_world.to_quaternion()
    return Arm(
        shoulder=root_world.translation, elbow=forearm_world.translation, tip=mw @ forearm.tail,
        wrist=hand_world.translation, up=ik.up_axis(axes.col[0], axes.col[2], pole_angle),
        upper_frame=calibrate.rest_aligned(root_rotation, calibrate.rest_aligned_offset(root.bone, char_frame)),
        forearm=forearm_world.to_quaternion(), hand=hand_rotation,
        hand_frame=calibrate.rest_aligned(hand_rotation, calibrate.rest_aligned_offset(hand.bone, char_frame)),
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


def magnet_entries(settings, cal, side, arm, guitar, shapes):
    """The magnets of `side` as magnets.Entry, in scene units, for the guitar placed at `guitar`."""
    distance = reach_scale(settings, cal)
    offset_scale = magnets.offset_scale(settings.autoscale_policy, cal.ratio_arm, cal.ratio_palm) / cal.metres_per_bu
    entries = []
    for index, item in enumerate(settings.magnets):
        shape = shapes.get(index)
        if shape is None or item.hand != side:
            continue
        params = magnets.Params(item.effective_distance_m * distance, item.peak * distance, item.power,
                                item.crossable, item.hysteresis)
        offset = Vector()
        if item.hand_offset_mode != 'NONE':
            local = settings.aim_hand_offset if item.hand_offset_mode == 'PARENT_BONE' else item.hand_offset
            offset = magnets.hand_offset(local, arm.hand_frame, offset_scale,
                                         cal.axis_rot[side] if item.apply_axis_rot else None)
        entries.append(magnets.Entry(index, shape.world(guitar, item.use_default_rotation), params, offset))
    return entries


def mount_pose(obj, cal, settings, root):
    """The guitar on its chest mount in the armature's current pose, as a magnets.GuitarPose."""
    chest_pos, chest_frame = mount.chest_pose(obj, cal, obj.gtr_char.bone_map.chest)
    scale = mount.root_scale(root)
    matrix = mount.mount_matrix(chest_pos, chest_frame, settings.mount_t, settings.mount_q,
                                mount.spine_factor(cal, settings.autoscale_policy), scale, cal.metres_per_bu)
    location, rotation, _ = matrix.decompose()
    return magnets.GuitarPose(location, rotation, rotation.copy(), scale)


# Results -------------------------------------------------------------------------------------------------------

@dataclass
class SideResult:
    fk_wrist: Vector
    target: Vector              # the wrist target after the magnets and the reach clamp
    hits: list                  # [(magnet index, magnets.Hit)] in list order
    clamped: bool               # the reach clamp moved the target
    wrist: Vector = None        # the solved wrist
    elbow: Vector = None        # the solved elbow

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
    iterations: int
    converged: bool
    metres_per_bu: float
    messages: list = field(default_factory=list)

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
        text = f"{SIDE_NAMES[side]} wrist moved {moved:.1f} cm"
        parts.append(text + (f" ({', '.join(acting)})" if acting else ""))
    return f"Frame {result.frame}: " + "; ".join(parts) + "."


# Solving -------------------------------------------------------------------------------------------------------

def _load(obj):
    cal = calibrate.load(obj.gtr_char.calibration)
    if cal is None:
        raise SolveError("Calibrate the character first.")
    return cal


def sample_arms(context, rig, cal):
    """The FK pose of both arms: the rig's constraints are switched off and the scene is evaluated."""
    rig.set_active(False)
    context.view_layer.update()
    return {side: sample_arm(rig.armature, rig.chains[side], cal.char_frame, rig.ik[side].pole_angle)
            for side in SIDES}


def place_goal(rig, side, arm, goal, cal, bias=None):
    """Put the IK goal of `side` on `goal`, its pole where the IK swings the FK arm there (ik.pole_position), and
    its bend on the seed a straight FK arm needs to reach it (ik.seed_bend)."""
    rig.helper("IKT", side).matrix_world = Matrix.Translation(goal)
    pole = ik.pole_position(arm.shoulder, arm.elbow, arm.tip, arm.up, goal,
                            ik.pole_distance(arm.length, cal.metres_per_bu), bias)
    rig.helper("POLE", side).matrix_world = Matrix.Translation(pole)
    bend = ik.seed_bend(arm.shoulder, arm.elbow, arm.tip, arm.up, arm.forearm, goal)
    rig.helper("BEND", side).matrix_world = Matrix.LocRotScale(arm.elbow, bend, None)


def solve(context, rig, iterations=None):
    """Solve the current frame and leave the rig showing it (§7). Returns a FrameResult; raises SolveError."""
    scene = context.scene
    settings = scene.gtr
    obj, root = rig.armature, settings.guitar_root
    settings.solve_active = False
    cal = _load(obj)
    if root is None:
        raise SolveError("Normalise the guitar first.")
    if settings.mount_source == 'NONE':
        raise SolveError("Load a preset or capture the mount first.")

    arms = sample_arms(context, rig, cal)
    shapes, messages = magnet_shapes(root, settings.magnets)
    try:
        guitar = mount_pose(obj, cal, settings, root)
    except mount.MountError as exc:
        raise SolveError(str(exc)) from exc
    root.matrix_world = guitar.matrix()

    sides = {}
    for side, arm in arms.items():
        entries = magnet_entries(settings, cal, side, arm, guitar, shapes)
        wrist, hits = magnets.apply(arm.wrist, entries, barriers_ignore_distance=settings.barriers_ignore_distance)
        target, clamped = ik.reach_clamp(wrist, arm.shoulder, settings.reach_clamp * arm.length,
                                         (arm.wrist - arm.shoulder).length)
        sides[side] = SideResult(arm.wrist.copy(), target, hits, clamped)
        rig.helper("WRIST_ROT", side).matrix_world = Matrix.LocRotScale(target, arm.hand, None)

    tolerance = TOLERANCE_M / cal.metres_per_bu
    turns = {side: Quaternion() for side in SIDES}     # solved forearm rotation relative to the FK one
    count, converged = 0, False
    rig.set_active(True)
    try:
        for count in range(1, max(1, iterations or settings.iterations) + 1):
            for side, arm in arms.items():
                goal = sides[side].target - turns[side] @ (arm.wrist - arm.tip)
                place_goal(rig, side, arm, goal, cal, root_bias(settings, side, arm))
            context.view_layer.update()
            for side, arm in arms.items():
                chain = rig.chains[side]
                forearm = obj.matrix_world @ obj.pose.bones[chain.forearm].matrix
                sides[side].elbow = forearm.translation
                sides[side].wrist = obj.matrix_world @ obj.pose.bones[chain.hand].head
                turns[side] = forearm.to_quaternion() @ arm.forearm.inverted()
            converged = all(result.error < tolerance for result in sides.values())
            if converged:
                break
    except Exception:
        rig.set_active(False)
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
    settings.solve_serial += 1
    settings.solve_frame = scene.frame_current
    settings.solve_active = True
    result = FrameResult(scene.frame_current, settings.solve_serial, settings.mode, guitar, sides, count, converged,
                         cal.metres_per_bu, messages)
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
            wrist = obj.matrix_world @ obj.pose.bones[chain.hand].head
            errors[side] = ((elbow - arm.elbow).length * cal.metres_per_bu,
                            (wrist - arm.wrist).length * cal.metres_per_bu)
    finally:
        rig.set_active(False)
        context.view_layer.update()
    return errors


def check_messages(errors):
    """Warnings for the sides whose IK does not reproduce the FK pose (see check_rig)."""
    messages = []
    for side, (elbow, wrist) in errors.items():
        if max(elbow, wrist) > CHECK_TOLERANCE_M:
            messages.append(('WARNING', f"The {SIDE_NAMES[side]} IK does not reproduce the current pose: the elbow "
                                        f"is {elbow * 1000.0:.1f} mm and the wrist {wrist * 1000.0:.1f} mm off. Check "
                                        "the arm bones for IK locks, limits or stretch."))
    return messages
