"""Bake, Smooth, Re-clamp and Remove Bake (§6 to §9).

The bake solves the frames one after the other and keeps the results in NumPy buffers; nothing is keyed until
the last frame is solved, so cancelling leaves the scene as it was. The plan's passes 1 and 2 are one loop: each
frame's FK pose is read from the same frame_set that the frame is then solved on. Per frame:
  - the rig is switched off and the frame set, with the add-on's tracks muted, so the character plays the mocap;
  - the FK pose is solved (solver.solve_pose) with the SolveState of the previous frame: the one-euro filters
    and the snap magnets that held each hand;
  - the armature-space poses of the arm chains (IK upper arm down to IK hand), of their parents and of the chest
    bone, the armature's world matrix and the solved guitar are stored.
Then (pass 3, §8) the poses become matrix_basis values (bake.py) and keys, one per frame, in two new actions: the
arm chains on the armature, GTR_ROOT's transform on GTR_ROOT. Of the chain bones, the three mapped ones always get
rotation keys and the bones between them only if the solve turned them (twist bones keep playing the mocap);
location and scale are keyed only where the solve changed them. The guitar is keyed relative to the chest bone's
tail, with GTR_ROOT parented to that bone, or in world space (Guitar Keys). keys.py puts both actions into the
NLA. A few frames are then played back and compared with the solve.

Smooth (§9) low-passes the bake actions with the zero-phase Butterworth filter, at the arm and guitar cutoffs.
Rotations are smoothed as quaternions and written back in the channels' rotation mode, nearest the old values.

Re-clamp (§9) plays the bake back and, on the frames where a hand has gone into a barrier or the chest collider
(after Smooth, or through a filter's lag), pushes the wrist back out (magnets.clamp_out, collider.push) and solves
that arm again from the baked pose, keeping the baked hand rotation; only those frames' keys change. The user's
GuitarRefine layer on the armature is muted meanwhile, as the keys go into the bake strip under it.

Remove Bake takes the add-on's tracks and actions away and puts back what the bake changed: the pushed-down
actions and the static values (keys.py), and GTR_ROOT's parent. It removes the bake's diagnostics as well.

A bake also records what the solve did on each frame (diagnostics.py) and keys it on the GTR_Diagnostics empty.
Range overrides (modes.py) choose each frame's mode; where the mode changes, the bake starts its SolveState afresh.
"""

import math
import time
from dataclasses import dataclass, field

import bpy
import numpy as np
from mathutils import Euler, Matrix, Quaternion, Vector

from . import bake, calibrate, collider, diagnostics, filters, keys, magnets, modes, solver
from .bonemap import SIDES

ROOT_PARENT_PROP = "gtr_bake_parent"    # on GTR_ROOT: its parent before the first bake
VERIFY_FRAMES = 5
VERIFY_TOLERANCE_M = 5e-4       # how far the played-back bake may be from the solve (keys are 32-bit floats)
ROTATION_TOLERANCE = 1e-6       # in rotation matrix entries: a chain bone turned less than this is not keyed
SCALE_TOLERANCE = 1e-6
LOCATION_TOLERANCE_M = 1e-6
RECLAMP_PASSES = 4
TRANSFORM_GROUP = "Object Transforms"


class BakeError(ValueError):
    """The scene is not ready for the bake or its post-processing."""


def frame_range(scene):
    settings = scene.gtr
    if settings.use_scene_frame_range:
        return scene.frame_start, scene.frame_end
    return settings.frame_start, settings.frame_end


def rotation_path(mode):
    return {'QUATERNION': "rotation_quaternion", 'AXIS_ANGLE': "rotation_axis_angle"}.get(mode, "rotation_euler")


def chain_path(obj, chain):
    """Names of the pose bones from the IK upper arm down to the IK hand, parents first."""
    names, pbone = [], obj.pose.bones[chain.hand]
    while pbone is not None:
        names.append(pbone.name)
        if pbone.name == chain.upper:
            break
        pbone = pbone.parent
    return names[::-1]


def _driven(owner, prefix):
    """Whether a driver of `owner` drives a transform property of the struct at `prefix` ('' for the owner)."""
    data = owner.animation_data
    for fcurve in (data.drivers if data is not None else ()):
        head, _, prop = fcurve.data_path.rpartition(".")
        if head == prefix and prop in keys.TRANSFORM_PROPS:
            return True
    return False


def chain_messages(rig, paths):
    """Warnings for what would act on top of the chain bones' keys: their own constraints, and drivers."""
    obj = rig.armature
    ours = {con.name for side in SIDES for con in (rig.ik[side], rig.bend[side], rig.wrist[side])}
    messages = []
    for side in SIDES:
        for name in paths[side]:
            pbone = obj.pose.bones[name]
            names = [con.name for con in pbone.constraints
                     if con.name not in ours and not con.mute and con.influence > 0.0]
            if names:
                messages.append(('WARNING', f"{name} has constraints ({', '.join(names)}) that act on top of the "
                                            "baked keys: the baked arm will differ from the solve. Mute them, or "
                                            "bake the rig's FK controls."))
            if _driven(obj, pbone.path_from_id()):
                messages.append(('WARNING', f"Drivers on {name} override its baked keys."))
    return messages


def root_messages(root):
    """Warnings for GTR_ROOT; raises BakeError if its keys could not hold the solved guitar."""
    deltas = (any(abs(v) > 1e-9 for v in root.delta_location)
              or any(abs(v) > 1e-9 for v in root.delta_rotation_euler)
              or any(abs(a - b) > 1e-9 for a, b in zip(root.delta_rotation_quaternion, (1.0, 0.0, 0.0, 0.0)))
              or any(abs(v - 1.0) > 1e-9 for v in root.delta_scale))
    if deltas:
        raise BakeError("GTR_ROOT has delta transforms: clear them (Object properties > Transform > Delta "
                        "Transform) before baking.")
    messages = []
    if any(not con.mute and con.influence > 0.0 for con in root.constraints):
        messages.append(('WARNING', "GTR_ROOT has constraints, which act on top of its baked keys."))
    if _driven(root, ""):
        messages.append(('WARNING', "Drivers on GTR_ROOT override its baked keys."))
    return messages


def set_root_parent(root, armature, bone):
    """Parent GTR_ROOT to `bone` of `armature` (None: no parent) with an identity parent inverse, so that its keys
    are relative to the bone's tail. The first time, its own parent is remembered for Remove Bake."""
    if ROOT_PARENT_PROP not in root:
        root[ROOT_PARENT_PROP] = {
            "object": root.parent.name if root.parent is not None else "",
            "type": root.parent_type, "bone": root.parent_bone,
            "inverse": [v for row in root.matrix_parent_inverse for v in row]}
    root.parent = armature
    if armature is not None:
        root.parent_type = 'BONE'
        root.parent_bone = bone
    else:
        root.parent_type = 'OBJECT'
    root.matrix_parent_inverse = Matrix.Identity(4)


def restore_root_parent(root):
    """Put back the parent GTR_ROOT had before the first bake."""
    info = root.get(ROOT_PARENT_PROP)
    if info is None:
        return
    parent = bpy.data.objects.get(info["object"]) if info["object"] else None
    root.parent = parent
    root.parent_type = info["type"]
    if parent is not None and info["bone"]:
        root.parent_bone = info["bone"]
    root.matrix_parent_inverse = Matrix(np.array(info["inverse"], dtype=np.float64).reshape(4, 4).tolist())
    del root[ROOT_PARENT_PROP]


def write_channels(channels, data_path, values, frames, group, interpolation):
    """Key `values` (frames, components) on the F-curves of `data_path`, one per component."""
    for index in range(values.shape[1]):
        keys.write(channels.new(data_path, index, group), frames, values[:, index], interpolation)


def channels_near(rot, mode, reference):
    """Rotation channel values (n, k) for `mode` of the rotation matrices `rot` (n, 3, 3), each frame's values
    nearest that frame's `reference` values: the same quaternion sign, the nearest Euler solution, axis-angle with
    the same axis direction and angle turn."""
    reference = np.asarray(reference, dtype=np.float64)
    out = np.empty_like(reference)
    for i, m in enumerate(np.asarray(rot, dtype=np.float64)):
        mat = Matrix(m.tolist())
        ref = reference[i]
        if mode in bake.EULER_ORDERS:
            out[i] = mat.to_euler(mode, Euler(ref, mode))
            continue
        q = mat.to_quaternion()
        if mode == 'QUATERNION':
            if np.dot(tuple(q), ref) < 0.0:
                q.negate()
            out[i] = tuple(q)
            continue
        axis, angle = q.to_axis_angle()
        ref_axis = Vector(ref[1:])
        if abs(angle) < 1e-7:
            axis = ref_axis.normalized() if ref_axis.length > 1e-9 else axis
        elif axis.dot(ref_axis) < 0.0:
            axis.negate()
            angle = -angle
        angle += 2.0 * math.pi * round((ref[0] - angle) / (2.0 * math.pi))
        out[i] = (angle, *axis)
    return out


def channel_quaternions(values, mode):
    """Quaternions (n, 4) of rotation channel values (n, k) in `mode`."""
    if mode == 'QUATERNION':
        return np.asarray(values, dtype=np.float64)
    if mode == 'AXIS_ANGLE':
        return np.array([tuple(Quaternion(Vector(v[1:]), v[0])) for v in values])
    return np.array([tuple(Euler(v, mode).to_quaternion()) for v in values])


def quaternion_matrices(q):
    """Rotation matrices (n, 3, 3) of quaternions (n, 4)."""
    return np.array([np.array(Quaternion(v).normalized().to_matrix()) for v in q])


class Temp:
    """What a job changes in the scene while it runs, and puts back: the frame, muted tracks, hidden meshes."""

    def __init__(self, context, owners, roles, hide_meshes):
        scene = context.scene
        self.scene = scene
        self.frame = (scene.frame_current, scene.frame_subframe)
        self.muted = keys.mute(owners, roles)
        self.hidden = []
        if hide_meshes:
            for obj in scene.objects:
                if obj.type == 'MESH' and not obj.hide_viewport:
                    obj.hide_viewport = True
                    self.hidden.append(obj.name)

    def unmute(self):
        keys.unmute(self.muted)
        self.muted = []

    def restore(self):
        self.unmute()
        for name in self.hidden:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.hide_viewport = False
        self.hidden = []
        self.scene.frame_set(self.frame[0], subframe=self.frame[1])


class Job:
    """Frames processed one `step` at a time, so that a modal operator can show progress and be cancelled;
    `finish` writes the result and returns a report, `cancel` leaves the scene as it was."""

    frames = ()
    index = 0

    @property
    def done(self):
        return self.index >= len(self.frames)

    @property
    def progress(self):
        return self.index / max(len(self.frames), 1)

    @property
    def frame(self):
        return self.frames[min(self.index, len(self.frames) - 1)] if self.frames else 0

    def run(self, context):
        """Every step, then finish. Cancels on an error."""
        try:
            while not self.done:
                self.step(context)
        except Exception:
            self.cancel(context)
            raise
        return self.finish(context)

    def step(self, context):
        raise NotImplementedError

    def finish(self, context):
        raise NotImplementedError

    def cancel(self, context):
        raise NotImplementedError


def _check_tweak(owners):
    for owner in owners:
        data = owner.animation_data if owner is not None else None
        if data is not None and data.use_tweak_mode:
            raise BakeError(f"{owner.name} is in NLA tweak mode: leave it in the NLA editor first.")


def _parent_names(obj, paths):
    names = set()
    for path in paths.values():
        parent = obj.pose.bones[path[0]].parent
        if parent is not None:
            names.add(parent.name)
    return names


def _fmt_frames(frames, limit=8):
    text = ", ".join(str(f) for f in frames[:limit])
    return text + (f" and {len(frames) - limit} more" if len(frames) > limit else "")


# Bake ----------------------------------------------------------------------------------------------------------

@dataclass
class Stats:
    """What the solve did over a bake, for its report."""
    unconverged: list = field(default_factory=list)
    misses: list = field(default_factory=list)      # frames where an IK missed its target
    clamped: int = 0            # frames where the reach clamp acted
    collider: int = 0           # frames where the chest collider pushed a hand
    aim_limited: int = 0        # frames where the neck aim hit Max Swing
    largest: float = 0.0        # the largest wrist correction, in metres
    largest_frame: int = None

    def note(self, frame, result, metres_per_bu):
        tolerance = solver.TOLERANCE_M / metres_per_bu
        sides = result.sides.values()
        if not result.converged:
            self.unconverged.append(frame)
        if any(side.error >= tolerance for side in sides):
            self.misses.append(frame)
        self.clamped += any(side.clamped for side in sides)
        self.collider += any(side.collider is not None and side.collider.weight > 0.0 for side in sides)
        self.aim_limited += result.neck is not None and result.neck.clamped
        for side in sides:
            moved = (side.target - side.fk_wrist).length * metres_per_bu
            if moved > self.largest:
                self.largest, self.largest_frame = moved, frame


class BakeJob(Job):
    """Bake the frame range (see the module notes). Raises BakeError or solver.SolveError when the scene is not
    ready; from then on the scene is in the job's hands until `finish` or `cancel`."""

    def __init__(self, context, rig):
        scene = context.scene
        settings = scene.gtr
        obj = rig.armature
        self.rig = rig
        self.start, self.end = frame_range(scene)
        if self.end < self.start:
            raise BakeError("The frame range is empty.")
        _check_tweak((obj, settings.guitar_root))
        settings.solve_active = False
        rig.set_active(False)
        keys.unmute_after_solve(obj)
        self.setup = setup = solver.prepare(context, rig)
        self.messages = list(setup.messages) + root_messages(setup.root)
        self.paths = {side: chain_path(obj, rig.chains[side]) for side in SIDES}
        self.messages += chain_messages(rig, self.paths)
        self.chest = obj.gtr_char.bone_map.chest
        solved = [name for side in SIDES for name in self.paths[side]]
        self.frames = list(range(self.start, self.end + 1))
        count = len(self.frames)
        self.fk = {name: np.empty((count, 4, 4))
                   for name in set(solved) | _parent_names(obj, self.paths) | {self.chest}}
        self.solved = {name: np.empty((count, 4, 4)) for name in solved}
        self.object_world = np.empty((count, 4, 4))
        self.guitar = np.empty((count, 4, 4))
        self.wrists = {side: np.empty((count, 3)) for side in SIDES}
        self.state = solver.SolveState.new(setup.fps)
        self.stats = Stats()
        self.diagnostics = diagnostics.Recorder(self.frames, settings.magnets)
        self.index = 0
        self.started = time.perf_counter()
        keys.record_static(obj, solved)
        keys.record_static(setup.root, transform=True)
        self.temp = Temp(context, (obj, setup.root), keys.ROLES, settings.bake_hide_meshes)

    def step(self, context):
        i, frame = self.index, self.frames[self.index]
        rig, setup = self.rig, self.setup
        bones = rig.armature.pose.bones
        if i > 0 and setup.schedule.at(frame).run_start:
            self.state = solver.SolveState.new(setup.fps)       # another mode's magnets: no history (modes.py)
        rig.set_active(False)
        context.scene.frame_set(frame)
        pose = solver.sample_pose(context, rig, setup, update=False)
        for name, buffer in self.fk.items():
            buffer[i] = bones[name].matrix
        self.object_world[i] = rig.armature.matrix_world
        result = solver.solve_pose(context, rig, setup, pose, self.state, show_guitar=False)
        self.state.commit(result)
        for name, buffer in self.solved.items():
            buffer[i] = bones[name].matrix
        self.guitar[i] = result.guitar.matrix()
        for side, side_result in result.sides.items():
            self.wrists[side][i] = side_result.wrist
        rig.set_active(False)
        self.stats.note(frame, result, setup.cal.metres_per_bu)
        self.diagnostics.note(i, result)
        self.index += 1

    def finish(self, context):
        settings = context.scene.gtr
        obj, root = self.rig.armature, self.setup.root
        frames = np.array(self.frames, dtype=np.float64)
        interpolation = settings.bake_interpolation
        self.rig.set_active(False)

        arm_action = keys.new_action(f"{obj.name}_GuitarBake", keys.ARM)
        arm_channels = keys.Channels(arm_action, obj)
        keyed = self._key_arms(obj, arm_channels, frames, interpolation)
        guitar_action = keys.new_action(f"{root.name}_GuitarBake", keys.GUITAR)
        guitar_channels = keys.Channels(guitar_action, root)
        self._key_guitar(obj, root, settings.guitar_space, guitar_channels, frames, interpolation)

        self.temp.unmute()
        for owner, role, action, channels in ((obj, keys.ARM, arm_action, arm_channels),
                                              (root, keys.GUITAR, guitar_action, guitar_channels)):
            self.messages += place(owner, role, action, channels.slot, self.start, self.end)
        diagnostics.write(settings, self.diagnostics, root.users_collection or (context.scene.collection,))
        error, error_frame = self._verify(context)
        self.temp.restore()

        elapsed = max(time.perf_counter() - self.started, 1e-9)
        report = self._report(len(keyed), error, error_frame, elapsed)
        report += self.messages
        settings.bake_report = calibrate.format_messages(report)
        return report

    def cancel(self, context):
        try:
            self.rig.set_active(False)
        except ReferenceError:
            pass
        self.temp.restore()

    def _key_arms(self, obj, channels, frames, interpolation):
        """Key the chain bones the solve changed; returns their names."""
        bones = obj.data.bones
        basis = bake.pose_to_basis(bones, self.solved, self.fk)
        fk_basis = bake.pose_to_basis(bones, {name: self.fk[name] for name in self.solved}, self.fk)
        location_tolerance = LOCATION_TOLERANCE_M / self.setup.cal.metres_per_bu
        mapped = {name for chain in self.rig.chains.values() for name in (chain.upper, chain.forearm, chain.hand)}
        keyed = []
        for name in self.solved:
            pbone = obj.pose.bones[name]
            loc, rot, scale = bake.decompose(basis[name])
            fk_loc, fk_rot, fk_scale = bake.decompose(fk_basis[name])
            changed = False
            if name in mapped or np.abs(rot - fk_rot).max() > ROTATION_TOLERANCE:
                mode = pbone.rotation_mode
                write_channels(channels, pbone.path_from_id(rotation_path(mode)), bake.rotation_channels(rot, mode),
                               frames, name, interpolation)
                changed = True
            if np.abs(loc - fk_loc).max() > location_tolerance:
                write_channels(channels, pbone.path_from_id("location"), loc, frames, name, interpolation)
                changed = True
            if np.abs(scale - fk_scale).max() > SCALE_TOLERANCE:
                write_channels(channels, pbone.path_from_id("scale"), scale, frames, name, interpolation)
                changed = True
            if changed:
                keyed.append(name)
        return keyed

    def _key_guitar(self, obj, root, space, channels, frames, interpolation):
        """Key GTR_ROOT's transform relative to the chest bone's tail (parenting it there), or in world space."""
        local = self.guitar
        if space == 'CHEST':
            tail = np.array(Matrix.Translation((0.0, obj.data.bones[self.chest].length, 0.0)))
            local = np.linalg.inv(self.object_world @ self.fk[self.chest] @ tail) @ self.guitar
        set_root_parent(root, obj if space == 'CHEST' else None, self.chest)
        loc, rot, scale = bake.decompose(local)
        mode = root.rotation_mode
        write_channels(channels, "location", loc, frames, TRANSFORM_GROUP, interpolation)
        write_channels(channels, rotation_path(mode), bake.rotation_channels(rot, mode), frames, TRANSFORM_GROUP,
                       interpolation)
        write_channels(channels, "scale", scale, frames, TRANSFORM_GROUP, interpolation)

    def _verify(self, context):
        """(distance in metres, frame): the largest distance between the played-back bake and the solve, over a
        few frames, of the wrists and the guitar origin. The refine layers are muted meanwhile."""
        obj, root = self.rig.armature, self.setup.root
        count = len(self.frames)
        picks = sorted({int(round(v)) for v in np.linspace(0, count - 1, min(VERIFY_FRAMES, count))})
        worst, worst_frame = 0.0, None
        with keys.muted((obj, root), roles=(keys.REFINE,)):
            for i in picks:
                context.scene.frame_set(self.frames[i])
                errors = [(root.matrix_world.translation - Vector(self.guitar[i][:3, 3])).length]
                for side in SIDES:
                    hand = obj.matrix_world @ obj.pose.bones[self.rig.chains[side].hand].head
                    errors.append((hand - Vector(self.wrists[side][i])).length)
                if max(errors) > worst:
                    worst, worst_frame = max(errors), self.frames[i]
        return worst * self.setup.cal.metres_per_bu, worst_frame

    def _report(self, keyed, error, error_frame, elapsed):
        stats, count = self.stats, len(self.frames)
        lines = [('INFO', f"Baked frames {self.start}-{self.end} ({count} frames) in {elapsed:.1f} s "
                          f"({count / elapsed:.1f} frames/s): {keyed} arm bones and the guitar.")]
        parts = []
        if stats.largest_frame is not None:
            parts.append(f"the largest wrist correction was {stats.largest * 100.0:.1f} cm (frame "
                         f"{stats.largest_frame})")
        for number, text in ((stats.collider, "the chest collider"), (stats.clamped, "the reach clamp"),
                             (stats.aim_limited, "the Max Swing limit")):
            if number:
                parts.append(f"{text} acted on {number} frames")
        if parts:
            lines.append(('INFO', "; ".join(parts).capitalize() + "."))
        runs = self.setup.schedule.runs(self.start, self.end)
        if len(runs) > 1 or runs[0][2].override != modes.SCENE:
            text = ", ".join(f"{first}-{last} {mode.mode.title()}" + ("" if mode.override == modes.SCENE else "*")
                             for first, last, mode in runs)
            lines.append(('INFO', f"Modes: {text} (* range override). The filters restarted at the {len(runs) - 1} "
                                  f"changes, where the neck aim fades over {modes.FADE_FRAMES} frames."))
        if stats.unconverged:
            lines.append(('INFO', f"The neck aim did not settle on {len(stats.unconverged)} frames "
                                  f"({_fmt_frames(stats.unconverged)}): raise Iterations or lower Relax."))
        if stats.misses:
            lines.append(('WARNING', f"The IK missed its target on {len(stats.misses)} frames "
                                     f"({_fmt_frames(stats.misses)}): check the arm bones for IK locks, limits or "
                                     "stretch."))
        if error > VERIFY_TOLERANCE_M:
            lines.append(('WARNING', f"Played back, the bake is {error * 1000.0:.1f} mm from the solve at frame "
                                     f"{error_frame}: something acts on top of the keys (constraints, drivers, "
                                     "other NLA tracks above the bake)."))
        else:
            lines.append(('INFO', f"Played back within {error * 1000.0:.2f} mm of the solve."))
        return lines


def place(owner, role, action, slot, start, end):
    """Put a bake action into the owner's NLA (keys.place_bake), delete the actions of the bake it replaces, and
    give the new one their name. Returns messages."""
    strip, _, old, messages = keys.place_bake(owner, role, action, slot, start, (start, end))
    for item in old:
        if item.users == 0:
            bpy.data.actions.remove(item)
    action.name = f"{owner.name}_GuitarBake"
    strip.name = action.name
    return messages


def bake_owners(settings):
    """The objects a bake keys: the character and GTR_ROOT (and the armature the rig was built on, if it is
    another)."""
    owners = []
    for owner in (settings.armature, settings.rig_armature, settings.guitar_root):
        if owner is not None and owner not in owners:
            owners.append(owner)
    return owners


def has_bake(settings):
    return any(keys.bake_strips(owner) or ROOT_PARENT_PROP in owner for owner in bake_owners(settings))


# Smooth --------------------------------------------------------------------------------------------------------

def _euler_order(owner, data_path):
    """The rotation mode of the struct of `owner` that `data_path` animates, if it is an Euler order."""
    head = data_path.rpartition(".")[0]
    try:
        struct = owner.path_resolve(head) if head else owner
    except ValueError:
        struct = None
    mode = getattr(struct, "rotation_mode", 'XYZ')
    return mode if mode in bake.EULER_ORDERS else 'XYZ'


def smooth_action(action, owner, cutoff, fps):
    """Low-pass every F-curve of `action`, a bake of `owner`, at `cutoff` Hz (filters.filtfilt); rotations as
    quaternions. Curves need evenly spaced keys. Returns (smoothed curves, skipped curves)."""
    groups = {}
    for fcurve in keys.fcurves(action):
        groups.setdefault(fcurve.data_path, {})[fcurve.array_index] = fcurve
    smoothed = skipped = 0
    for path, curves in groups.items():
        indices = sorted(curves)
        data = [keys.read(curves[i]) for i in indices]
        frames = data[0][0]
        steps = np.diff(frames)
        if (len(frames) < 3 or any(len(d[0]) != len(frames) or not np.allclose(d[0], frames) for d in data)
                or not np.allclose(steps, steps[0]) or steps[0] <= 0.0):
            skipped += len(indices)
            continue
        fs = fps / steps[0]
        if not filters.can_filter(cutoff, fs):
            continue
        values = np.stack([d[1] for d in data], axis=1)
        prop = path.rpartition(".")[2]
        mode = {"rotation_quaternion": 'QUATERNION', "rotation_axis_angle": 'AXIS_ANGLE'}.get(prop)
        if prop == "rotation_euler":
            mode = _euler_order(owner, path)
        if mode is not None and indices == list(range(values.shape[1])):
            q = filters.smooth_quaternions(channel_quaternions(values, mode), cutoff, fs)
            values = channels_near(quaternion_matrices(q), mode, values)
        else:
            values = filters.filtfilt(values, cutoff, fs)
        for column, i in enumerate(indices):
            keys.set_values(curves[i], values[:, column])
        smoothed += len(indices)
    return smoothed, skipped


def smooth(context):
    """Smooth the bake actions of the scene's character and guitar. Returns messages."""
    scene = context.scene
    settings = scene.gtr
    fps = solver.scene_fps(scene)
    lines, total = [], 0
    for owner, role, cutoff in ((settings.armature, keys.ARM, settings.smooth_cutoff_arms),
                                (settings.guitar_root, keys.GUITAR, settings.smooth_cutoff_guitar)):
        found = keys.bake_strips(owner).get(role) if owner is not None else None
        if found is None:
            continue
        smoothed, skipped = smooth_action(found[1].action, owner, cutoff, fps)
        total += smoothed
        name = "arm" if role == keys.ARM else "guitar"
        text = f"Smoothed {smoothed} {name} curves at {cutoff:g} Hz"
        if not filters.can_filter(cutoff, fps):
            text = f"The {name} cutoff, {cutoff:g} Hz, is above what {fps:g} frames/s can show: nothing changed"
        if skipped:
            text += f"; skipped {skipped} whose keys are not one per frame"
        lines.append(text + ".")
    if not lines:
        raise BakeError("There is no bake to smooth.")
    scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
    messages = [('INFO', text) for text in lines]
    messages.append(('INFO', "Re-clamp restores the contacts that smoothing loosened."))
    settings.bake_report = calibrate.format_messages(messages)
    return messages


# Re-clamp ------------------------------------------------------------------------------------------------------

def clamp_targets(settings, setup, pose, guitar, frame_mode=None):
    """{side: (wrist, push)}: each FK wrist of `pose` pushed out of the chest collider and of the barriers, with
    the distance it moved. `frame_mode`: the frame's modes.FrameMode."""
    cal = setup.cal
    body = collider.capsule(settings, cal, *pose.chest)
    out = {}
    for side, arm in pose.arms.items():
        wrist = arm.wrist
        if body is not None and side in settings.collider_hands:
            tips = [arm.wrist + v for v in arm.tips.values()] if settings.collider_fingertips else ()
            wrist, _ = collider.push(body, wrist, tips)
        for entry in solver.magnet_entries(settings, cal, side, arm, guitar, setup.shapes, frame_mode=frame_mode):
            if not magnets.is_barrier(entry):
                continue
            if not settings.barriers_ignore_distance:
                depth = -(wrist + entry.offset - entry.feature.a).dot(entry.feature.normal)
                if depth >= entry.params.reach:
                    continue
            wrist, _ = magnets.clamp_out(wrist, entry)
        out[side] = (wrist, (wrist - arm.wrist).length)
    return out


class ReclampJob(Job):
    """Re-clamp the bake of the scene's character (see the module notes)."""

    def __init__(self, context, rig):
        scene = context.scene
        settings = scene.gtr
        obj = rig.armature
        self.rig = rig
        found = keys.bake_strips(obj).get(keys.ARM)
        if found is None:
            raise BakeError("Bake first: the character has no GuitarBake strip.")
        _check_tweak((obj,))
        strip = found[1]
        self.action, self.slot = strip.action, getattr(strip, "action_slot", None)
        settings.solve_active = False
        rig.set_active(False)
        keys.unmute_after_solve(obj)
        self.setup = solver.prepare(context, rig)
        self.paths = {side: chain_path(obj, rig.chains[side]) for side in SIDES}
        self.frames = list(range(math.ceil(strip.frame_start - 1e-6), math.floor(strip.frame_end + 1e-6) + 1))
        count = len(self.frames)
        names = {name for path in self.paths.values() for name in path} | _parent_names(obj, self.paths)
        self.poses = {name: np.empty((count, 4, 4)) for name in names}     # the played-back poses
        self.solved = {side: {} for side in SIDES}      # side -> {frame index: {bone: re-solved pose}}
        self.pushes = {side: {} for side in SIDES}      # side -> {frame index: how far the wrist was pushed}
        self.tolerance = settings.reclamp_tolerance_m / self.setup.cal.metres_per_bu
        self.index = 0
        self.temp = Temp(context, (obj,), (keys.REFINE,), settings.bake_hide_meshes)

    def step(self, context):
        i, frame = self.index, self.frames[self.index]
        rig, setup = self.rig, self.setup
        bones = rig.armature.pose.bones
        rig.set_active(False)
        context.scene.frame_set(frame)
        pose = solver.sample_pose(context, rig, setup, update=False)
        for name, buffer in self.poses.items():
            buffer[i] = bones[name].matrix
        location, rotation, scale = setup.root.matrix_world.decompose()
        guitar = magnets.GuitarPose(location, rotation, pose.mounted.default_rotation, scale)
        targets = {}
        for side, (wrist, push) in clamp_targets(context.scene.gtr, setup, pose, guitar,
                                                 setup.schedule.at(frame)).items():
            if push > self.tolerance:
                targets[side] = wrist
                self.pushes[side][i] = push
        if targets:
            self._solve(context, pose, targets, i)
        self.index += 1

    def _solve(self, context, pose, targets, i):
        """Solve the arms of `targets` from the played-back pose so that the wrists reach them, keeping the hand
        rotations. The other arm's goals are put on its own pose."""
        rig, cal = self.rig, self.setup.cal
        obj = rig.armature
        tolerance = solver.TOLERANCE_M / cal.metres_per_bu
        turns = {side: Quaternion() for side in targets}
        for side, arm in pose.arms.items():
            rig.helper("WRIST_ROT", side).matrix_world = Matrix.LocRotScale(targets.get(side, arm.wrist), arm.hand,
                                                                            None)
        rig.set_active(True)
        try:
            for _ in range(RECLAMP_PASSES):
                for side, arm in pose.arms.items():
                    target = targets.get(side)
                    goal = arm.tip if target is None else target - turns[side] @ (arm.wrist - arm.tip)
                    solver.place_goal(rig, side, arm, goal, cal)
                context.view_layer.update()
                settled = True
                for side, target in targets.items():
                    chain = rig.chains[side]
                    forearm = obj.matrix_world @ obj.pose.bones[chain.forearm].matrix
                    turns[side] = forearm.to_quaternion() @ pose.arms[side].forearm.inverted()
                    wrist = obj.matrix_world @ obj.pose.bones[chain.hand].head
                    settled = settled and (wrist - target).length < tolerance
                if settled:
                    break
            for side in targets:
                self.solved[side][i] = {name: np.array(obj.pose.bones[name].matrix) for name in self.paths[side]}
        finally:
            rig.set_active(False)

    def finish(self, context):
        settings = context.scene.gtr
        obj = self.rig.armature
        bones = obj.data.bones
        frames = np.array(self.frames, dtype=np.float64)
        channels = keys.Channels(self.action, obj, self.slot)
        for side in SIDES:
            solved = self.solved[side]
            if not solved:
                continue
            indices = sorted(solved)
            path = self.paths[side]
            parent = obj.pose.bones[path[0]].parent
            parents_now = {parent.name: self.poses[parent.name][indices]} if parent is not None else {}
            parents_all = {parent.name: self.poses[parent.name]} if parent is not None else {}
            new = bake.pose_to_basis(bones, {name: np.array([solved[i][name] for i in indices]) for name in path},
                                     parents_now)
            old = bake.pose_to_basis(bones, {name: self.poses[name] for name in path}, parents_all)
            for name in path:
                self._write_bone(channels, obj.pose.bones[name], frames, indices, new[name], old[name],
                                 settings.bake_interpolation)
        self.temp.restore()
        report = self._report()
        settings.bake_report = calibrate.format_messages(report)
        return report

    def cancel(self, context):
        try:
            self.rig.set_active(False)
        except ReferenceError:
            pass
        self.temp.restore()

    def _write_bone(self, channels, pbone, frames, indices, new, old, interpolation):
        """Write the re-solved basis `new` of a bone at frames[indices]; `old` is its played-back basis on every
        frame, for the curves that have to be created."""
        loc, rot, scale = bake.decompose(new)
        old_loc, old_rot, old_scale = bake.decompose(old)
        location_tolerance = LOCATION_TOLERANCE_M / self.setup.cal.metres_per_bu
        mode = pbone.rotation_mode
        for prop, values, before, tolerance in (
                (rotation_path(mode), rot, old_rot, ROTATION_TOLERANCE), ("location", loc, old_loc, location_tolerance),
                ("scale", scale, old_scale, SCALE_TOLERANCE)):
            if np.abs(values - before[indices]).max() <= tolerance:
                continue
            path = pbone.path_from_id(prop)
            rotation = prop == rotation_path(mode)
            size = (3 if mode in bake.EULER_ORDERS else 4) if rotation else 3
            curves = [channels.find(path, k) for k in range(size)]
            if all(curve is not None for curve in curves):
                if rotation:
                    reference = [[curve.evaluate(frames[i]) for curve in curves] for i in indices]
                    values = channels_near(values, mode, reference)
                for k, curve in enumerate(curves):
                    keys.set_at(curve, frames[indices], values[:, k])
                continue
            full = before.copy()
            full[indices] = values
            if rotation:
                full = bake.rotation_channels(full, mode)
            for k, curve in enumerate(curves):
                keys.write(curve or channels.new(path, k, pbone.name), frames, full[:, k], interpolation)

    def _report(self):
        metres = self.setup.cal.metres_per_bu
        counts = {side: len(self.solved[side]) for side in SIDES}
        frames = sorted({i for side in SIDES for i in self.solved[side]})
        if not frames:
            text = (f"No frame of {self.frames[0]}-{self.frames[-1]} needed a re-clamp (tolerance "
                    f"{self.tolerance * metres * 1000.0:.1f} mm).") if self.frames else "No frames to re-clamp."
            return [('INFO', text)]
        deepest, side, index = max((push, side, i) for side in SIDES for i, push in self.pushes[side].items())
        return [('INFO', f"Re-clamped {len(frames)} frames: the left hand on {counts['L']}, the right hand on "
                         f"{counts['R']}. The deepest was {deepest * metres * 1000.0:.1f} mm "
                         f"({solver.SIDE_NAMES[side]} hand, frame {self.frames[index]}).")]


# Remove --------------------------------------------------------------------------------------------------------

def remove_bake(context):
    """Remove the bake from the scene's character and guitar (see the module notes). Returns messages."""
    scene = context.scene
    settings = scene.gtr
    removed, kept = 0, []
    for owner in bake_owners(settings):
        if ROOT_PARENT_PROP in owner:
            restore_root_parent(owner)
        actions, refine = keys.remove_bake(owner)
        for action in actions:
            if action.users == 0:
                bpy.data.actions.remove(action)
                removed += 1
        for action in refine:
            action.use_fake_user = True
            kept.append(action.name)
    diagnostics.remove(settings)
    scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
    messages = [('INFO', f"Removed the bake ({removed} actions).")]
    if kept:
        messages.append(('INFO', f"Kept the refine actions with your keys ({', '.join(kept)}) with a fake user."))
    settings.bake_report = calibrate.format_messages(messages)
    return messages
