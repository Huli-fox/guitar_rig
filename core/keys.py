"""Keyframes and NLA tracks for the bake (§8).

Actions: Blender 4.4 introduced slotted actions (layers, keyframe strips, channelbags per slot) and 5.0 removed
the legacy `Action.fcurves`. `Channels` writes F-curves through whichever API the running Blender has; keys are
written densely, one per frame, with `foreach_set`.

NLA: the add-on's actions carry a `gtr_bake` custom property with their role (ARM, GUITAR, REFINE, PREP). On each
owner (the armature, GTR_ROOT) a bake leaves, from the bottom up:
    the user's tracks, then the owner's active action pushed down into a track of its own,
    "GuitarPrep" (armature only, from Apply Prep, prepjob.py): the touched-up mocap, blend Replace,
    "GuitarBake": the solved channels, blend Replace, nothing outside the bake range,
    "GuitarRefine": an empty action, blend Combine, for the user's corrections (§17).
The active action is evaluated above every NLA track, so a Replace strip below it would be overridden: the bake
and the prep push it down first, as the NLA editor's Push Down does, and it is put back once neither is left. A
re-bake replaces the bake track right under the refine track, which it leaves as it is: it holds the user's work.
The prep track always sits right above the pushed-down action, so the bake goes above it.

To read the mocap again (a re-bake, Solve Frame), the add-on's bake tracks are muted (ROLES); the prep track plays
on, as it is the mocap the solve reads. Apply Prep reads the raw mocap, with every track muted (ALL_ROLES). A
channel the mocap does not animate would then keep the last value that played, so the bake and the prep remember
such static values first (record_static) and muting puts them back.
"""

import math
from contextlib import contextmanager

import bpy
import numpy as np

TAG = "gtr_bake"                    # custom property on the add-on's actions: their role
ARM, GUITAR, REFINE, PREP = 'ARM', 'GUITAR', 'REFINE', 'PREP'
ROLES = (ARM, GUITAR, REFINE)       # the tracks muted to read the mocap
BAKED = (ARM, GUITAR)
ALL_ROLES = ROLES + (PREP,)
TRACK_NAMES = {ARM: "GuitarBake", GUITAR: "GuitarBake", REFINE: "GuitarRefine", PREP: "GuitarPrep"}
SOURCE_PROP = "gtr_bake_source"     # on an owner whose active action a bake pushed down: [track, action]
INTERPOLATION = {'CONSTANT': 0, 'LINEAR': 1, 'BEZIER': 2}


def slotted():
    """Whether this Blender has slotted actions (4.4 and later)."""
    return "slots" in bpy.types.Action.bl_rna.properties


def is_ours(action):
    return action is not None and action.get(TAG) in ALL_ROLES


def new_action(name, role):
    action = bpy.data.actions.new(name)
    action[TAG] = role
    return action


class Channels:
    """The F-curves of one owner (an Object) in an action: on slotted actions, those of `slot`, or of a new slot
    for the owner."""

    def __init__(self, action, owner, slot=None):
        self.action = action
        self.slot = None
        self.channelbag = None
        if slotted():
            self.slot = slot or action.slots.new(id_type=owner.id_type, name=owner.name)
            layer = action.layers[0] if len(action.layers) else action.layers.new("Layer")
            strip = layer.strips[0] if len(layer.strips) else layer.strips.new(type='KEYFRAME')
            self.channelbag = strip.channelbag(self.slot, ensure=True)

    def new(self, data_path, index, group):
        if self.channelbag is None:
            return self.action.fcurves.new(data_path, index=index, action_group=group)
        fcurves = self.channelbag.fcurves
        try:
            return fcurves.new(data_path, index=index, group_name=group)
        except TypeError:       # group_name came after 4.4
            fcurve = fcurves.new(data_path, index=index)
            groups = self.channelbag.groups
            fcurve.group = groups.get(group) or groups.new(group)
            return fcurve

    def find(self, data_path, index):
        if self.channelbag is None:
            return self.action.fcurves.find(data_path, index=index)
        return self.channelbag.fcurves.find(data_path, index=index)


def fcurves(action):
    """Every F-curve of an action, whichever API."""
    if action is None:
        return []
    if not slotted():
        return list(action.fcurves)
    found = []
    for layer in action.layers:
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", ()):
                found.extend(bag.fcurves)
    return found


def write(fcurve, frames, values, interpolation='LINEAR'):
    """Replace the keys of `fcurve` by one per frame."""
    count = len(frames)
    points = fcurve.keyframe_points
    if len(points):
        points.clear()
    points.add(count)
    co = np.empty(2 * count, dtype=np.float32)
    co[0::2] = frames
    co[1::2] = values
    points.foreach_set("co", co)
    points.foreach_set("interpolation", np.full(count, INTERPOLATION[interpolation], dtype=np.int32))
    fcurve.update()


def read(fcurve):
    """(frames, values) of the keys of `fcurve` as float64 arrays."""
    count = len(fcurve.keyframe_points)
    co = np.empty(2 * count, dtype=np.float32)
    fcurve.keyframe_points.foreach_get("co", co)
    return co[0::2].astype(np.float64), co[1::2].astype(np.float64)


def set_values(fcurve, values):
    """Change the values of the keys of `fcurve`, keeping their frames."""
    frames, _ = read(fcurve)
    co = np.empty(2 * len(frames), dtype=np.float32)
    co[0::2] = frames
    co[1::2] = values
    fcurve.keyframe_points.foreach_set("co", co)
    fcurve.update()


def set_at(fcurve, frames, values):
    """Set the values of `fcurve` at `frames`, adding a key where there is none."""
    keyed, current = read(fcurve)
    missing = []
    for frame, value in zip(frames, values):
        index = int(np.searchsorted(keyed, frame - 1e-3))
        if index < len(keyed) and abs(keyed[index] - frame) < 1e-3:
            current[index] = value
        else:
            missing.append((frame, value))
    co = np.empty(2 * len(keyed), dtype=np.float32)
    co[0::2] = keyed
    co[1::2] = current
    fcurve.keyframe_points.foreach_set("co", co)
    for frame, value in missing:
        fcurve.keyframe_points.insert(frame, value, options={'FAST'})
    fcurve.update()


# Static values -------------------------------------------------------------------------------------------------

STATIC_PROP = "gtr_bake_static"     # on an owner: {"object": {prop: values}, "bones": {name: {prop: values}}}
TRANSFORM_PROPS = ("location", "rotation_quaternion", "rotation_euler", "rotation_axis_angle", "scale")


def record_static(owner, bones=(), transform=False):
    """Remember the transform values of the pose bones `bones` (and of the owner itself with `transform`) as
    they are before they are first baked, unless they are remembered already.

    Animation writes the values it evaluates into the properties, and a property nothing animates keeps the last
    one. So once a bake has played, a channel that the mocap does not animate holds a baked value: muting or
    removing the bake would leave it there. `apply_static` puts the remembered values back."""
    stored = owner.get(STATIC_PROP)
    data = stored.to_dict() if stored else {}
    data.setdefault("object", {})
    data.setdefault("bones", {})
    if transform and not data["object"]:
        data["object"] = {prop: list(getattr(owner, prop)) for prop in TRANSFORM_PROPS}
    for name in bones:
        pbone = owner.pose.bones.get(name)
        if pbone is not None and name not in data["bones"]:
            data["bones"][name] = {prop: list(getattr(pbone, prop)) for prop in TRANSFORM_PROPS}
    owner[STATIC_PROP] = data


def apply_static(owner, forget=False):
    """Put back the values `record_static` remembered; with `forget`, also forget them."""
    stored = owner.get(STATIC_PROP)
    if not stored:
        return
    for prop, values in stored["object"].items():
        setattr(owner, prop, values)
    for name, props in stored["bones"].items():
        pbone = owner.pose.bones.get(name) if owner.pose is not None else None
        for prop, values in (props.items() if pbone is not None else ()):
            setattr(pbone, prop, values)
    if forget:
        del owner[STATIC_PROP]


# NLA -----------------------------------------------------------------------------------------------------------

def _our_tracks(owner):
    """[(track, roles of the add-on's strips in it)] on `owner`, bottom up."""
    data = owner.animation_data if owner is not None else None
    found = []
    for track in (data.nla_tracks if data is not None else ()):
        roles = {strip.action[TAG] for strip in track.strips if is_ours(strip.action)}
        if roles:
            found.append((track, roles))
    return found


def bake_strips(owner):
    """{role: (track, strip)} of the add-on's strips on `owner`, the lowest of each role."""
    found = {}
    for track, _ in _our_tracks(owner):
        for strip in track.strips:
            if is_ours(strip.action) and strip.action[TAG] not in found:
                found[strip.action[TAG]] = (track, strip)
    return found


def has_bake(owner):
    return any(role in BAKED for role in bake_strips(owner))


def has_prep(owner):
    return owner is not None and PREP in bake_strips(owner)


PREP_SERIAL_PROP = "gtr_prep_serial"    # on a prep action: its serial; on a bake action: the prep it was baked from


def prep_serial(owner, playing=False):
    """The serial of the owner's prep action, 0 if there is none (or, with `playing`, if its track is muted)."""
    found = bake_strips(owner).get(PREP) if owner is not None else None
    if found is None or (playing and found[0].mute):
        return 0
    return int(found[1].action.get(PREP_SERIAL_PROP, 0))


def mute(owners, roles=ROLES):
    """Mute the add-on's tracks with strips of `roles` on `owners`; returns what `unmute` needs. Muting a bake or
    prep track also puts back the static values (record_static), so that the scene plays the source animation.
    Only then: muting a track has the animation evaluated again, which overrides the static values of the
    channels something still animates (a prep layer that plays on, the mocap)."""
    saved = []
    for owner in owners:
        muted = False
        for track, found in _our_tracks(owner):
            if found & set(roles):
                saved.append((owner.name, track.name, track.mute))
                track.mute = True
                muted = muted or bool(found & {ARM, GUITAR, PREP})
        if muted:
            apply_static(owner)
    return saved


def unmute(saved):
    """Undo `mute`. Tracks are found again by name: one may have been removed since."""
    for owner_name, track_name, value in saved:
        owner = bpy.data.objects.get(owner_name)
        data = owner.animation_data if owner is not None else None
        track = data.nla_tracks.get(track_name) if data is not None else None
        if track is not None:
            track.mute = value


@contextmanager
def muted(owners, roles=ROLES):
    """`mute` for the duration."""
    saved = mute(owners, roles)
    try:
        yield
    finally:
        unmute(saved)


SOLVE_MUTED_PROP = "gtr_solve_muted"    # on an owner: the tracks Solve Frame muted while the rig shows its solve


def mute_for_solve(owner):
    """Mute the add-on's tracks on `owner` until `unmute_after_solve`: the solve the rig shows starts its IK from
    the mocap, as a bake does, and Blender's IK result depends on the pose it starts from."""
    names = [track for _, track, was_muted in mute((owner,)) if not was_muted]
    if names:
        owner[SOLVE_MUTED_PROP] = list(set(names) | set(owner.get(SOLVE_MUTED_PROP, ())))


def unmute_after_solve(owner):
    names = owner.get(SOLVE_MUTED_PROP)
    if names is None:
        return
    data = owner.animation_data
    for name in names:
        track = data.nla_tracks.get(name) if data is not None else None
        if track is not None:
            track.mute = False
    del owner[SOLVE_MUTED_PROP]


def push_down(owner, after=None):
    """Move the owner's active action into a new NLA track right above the track `after` (on top when None),
    keeping how it blends; returns the track, or None when there was nothing to push down."""
    data = owner.animation_data
    action = data.action if data is not None else None
    if action is None or is_ours(action):
        return None
    slot = getattr(data, "action_slot", None)
    blend, extrapolation, influence = data.action_blend_type, data.action_extrapolation, data.action_influence
    start = action.frame_range[0]
    track = data.nla_tracks.new(prev=after)
    track.name = action.name
    strip = track.strips.new(action.name, int(math.floor(start)), action)
    if start != math.floor(start):
        strip.frame_start_ui = start
    if slot is not None:
        strip.action_slot = slot
    strip.blend_type = blend
    strip.extrapolation = extrapolation
    if influence < 1.0:
        strip.use_animated_influence = True
        strip.influence = influence
    data.action = None
    owner[SOURCE_PROP] = [track.name, action.name]
    return track


def restore_pushed(owner):
    """Put back the active action `push_down` moved into the NLA, if its track is still as the bake left it."""
    info = owner.get(SOURCE_PROP)
    data = owner.animation_data
    if not info or data is None:
        return None
    del owner[SOURCE_PROP]
    track = data.nla_tracks.get(info[0])
    if track is None or len(track.strips) != 1 or data.action is not None:
        return None
    strip = track.strips[0]
    action = strip.action
    if action is None or action.name != info[1]:
        return None
    slot = getattr(strip, "action_slot", None)
    blend, extrapolation = strip.blend_type, strip.extrapolation
    influence = strip.influence if strip.use_animated_influence else 1.0
    data.nla_tracks.remove(track)
    data.action = action
    if slot is not None:
        data.action_slot = slot
    data.action_blend_type = blend
    data.action_extrapolation = extrapolation
    data.action_influence = influence
    return action


def _track_below(data, track):
    """The track right under `track` in the stack, or None."""
    tracks = list(data.nla_tracks)
    index = next(i for i, t in enumerate(tracks) if t == track)     # new wrappers each time: compare, not `is`
    return tracks[index - 1] if index > 0 else None


STRIP_PROPS = ("action_frame_start", "action_frame_end", "scale", "repeat", "blend_type", "extrapolation",
               "blend_in", "blend_out", "use_auto_blend", "use_reverse", "use_sync_length", "use_animated_influence",
               "influence", "mute")


def _move_to_top(data, track):
    """Recreate `track` with its strips on top of the stack (the API only adds tracks above another one)."""
    top = data.nla_tracks.new()
    top.mute, top.lock = track.mute, track.lock
    for strip in track.strips:
        copy = top.strips.new(strip.name, int(math.floor(strip.frame_start)), strip.action)
        if getattr(strip, "action_slot", None) is not None:
            copy.action_slot = strip.action_slot
        for prop in STRIP_PROPS:
            setattr(copy, prop, getattr(strip, prop))
        copy.frame_start_ui = strip.frame_start
    name = track.name
    data.nla_tracks.remove(track)
    top.name = name
    return top


def place_bake(owner, role, action, slot, start, refine_range):
    """Put the bake `action` (role ARM or GUITAR) into the owner's NLA stack as described in the module notes.

    The old bake track is removed, the active action is pushed down, and the new bake track goes right under the
    refine track, which is created on top, with a new empty action spanning `refine_range`, if there is none.
    Returns (bake strip, pushed-down track or None, the old bake actions for the caller to delete, messages).
    """
    data = owner.animation_data or owner.animation_data_create()
    old_actions, messages = [], []
    for track, roles in _our_tracks(owner):
        if roles & set(BAKED):
            old_actions += [strip.action for strip in track.strips if is_ours(strip.action)
                            and strip.action[TAG] in BAKED]
            data.nla_tracks.remove(track)
    found = bake_strips(owner)
    refine = found.get(REFINE)
    below, lift = None, False
    if refine is not None:
        below = _track_below(data, refine[0])
        lift = below is None        # nothing goes under the bottom track: the refine track moves up instead
    elif PREP in found:
        below = found[PREP][0]
    pushed = push_down(owner, None if lift else below)
    track = data.nla_tracks.new(prev=pushed if pushed is not None else below)
    track.name = TRACK_NAMES[role]
    strip = track.strips.new(action.name, int(math.floor(start)), action)
    if slot is not None:
        strip.action_slot = slot
    strip.blend_type = 'REPLACE'
    strip.extrapolation = 'NOTHING'
    if lift:
        _move_to_top(data, refine[0])
    if refine is None:
        empty = new_action(f"{owner.name}_GuitarRefine", REFINE)
        empty.use_frame_range = True
        empty.frame_start, empty.frame_end = refine_range
        refine_track = data.nla_tracks.new()
        refine_track.name = TRACK_NAMES[REFINE]
        refine_strip = refine_track.strips.new(empty.name, int(math.floor(refine_range[0])), empty)
        refine_strip.blend_type = 'COMBINE'
        refine_strip.extrapolation = 'NOTHING'
    data.use_nla = True
    return strip, pushed, old_actions, messages


def place_prep(owner, action, slot, start):
    """Put the prep `action` into the owner's NLA stack: the old prep track is removed, the active action is
    pushed down, and the prep track goes right above it, under the bake and refine tracks.
    Returns (prep strip, the old prep actions for the caller to delete)."""
    data = owner.animation_data or owner.animation_data_create()
    old_actions = []
    for track, roles in _our_tracks(owner):
        if PREP in roles:
            old_actions += [strip.action for strip in track.strips if is_ours(strip.action)
                            and strip.action[TAG] == PREP]
            data.nla_tracks.remove(track)
    ours = [track for track, _ in _our_tracks(owner)]
    below = _track_below(data, ours[0]) if ours else None
    lift = bool(ours) and below is None     # the bake tracks are at the bottom: they move up above the prep
    pushed = push_down(owner, None if lift else below)
    track = data.nla_tracks.new(prev=pushed if pushed is not None else below)
    track.name = TRACK_NAMES[PREP]
    strip = track.strips.new(action.name, int(math.floor(start)), action)
    if slot is not None:
        strip.action_slot = slot
    strip.blend_type = 'REPLACE'
    strip.extrapolation = 'NOTHING'
    if lift:
        for other in ours:
            _move_to_top(data, other)
    data.use_nla = True
    return strip, old_actions


def _remove_tracks(owner, which):
    """Remove the add-on's tracks whose roles `which` accepts; returns (removed actions, kept refine actions that
    hold keys)."""
    data = owner.animation_data
    removed, kept = [], []
    for track, roles in (_our_tracks(owner) if data is not None else ()):
        if not which(roles):
            continue
        for strip in track.strips:
            if is_ours(strip.action) and strip.action not in removed + kept:
                (kept if strip.action[TAG] == REFINE and fcurves(strip.action) else removed).append(strip.action)
        data.nla_tracks.remove(track)
    return removed, kept


def _after_removal(owner):
    """Once neither a bake nor a prep is left, put back the action they pushed down and forget the static values;
    put the static values back in any case."""
    left = bool(_our_tracks(owner))
    if not left and owner.animation_data is not None:
        restore_pushed(owner)
    apply_static(owner, forget=not left)


def remove_bake(owner):
    """Remove the add-on's bake and refine tracks from `owner` (the prep track stays), and put back the static
    values and, if no prep is left, the action the bake pushed down. Returns (removed actions, kept refine actions
    that hold keys)."""
    removed, kept = _remove_tracks(owner, lambda roles: PREP not in roles)
    _after_removal(owner)
    return removed, kept


def remove_prep(owner):
    """Remove the prep track from `owner` (the bake stays), as `remove_bake` does. Returns the removed actions."""
    removed, _ = _remove_tracks(owner, lambda roles: PREP in roles)
    _after_removal(owner)
    return removed
