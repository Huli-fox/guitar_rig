"""Bake diagnostics (§7, §10.6): what the solve did on every frame, as curves, and the worst frames.

A bake records, per frame, each wrist's correction (how far the collider, the magnets and the reach clamp moved
its target from the mocap wrist), the IK's miss, the chest collider's push, and for each magnet that saw the hand
its distance d (signed for planes: negative behind the plane) and its weight w; and for the frame the neck swing,
the fretting wrist's turn, the solve passes and whether they settled, the mode and the neck aim weight.

The curves are keyed as animated custom properties of an empty, GTR_Diagnostics (the scene's
settings.diagnostics), one key per frame in an action of its own, so that the Graph Editor shows them with the
empty selected. The action's `gtr_diag_channels` property says what each curve holds. The worst frames for a
measure (`METRICS`) are ranked from the curves, so they survive saving the file; they describe the solve, not
later Smooth or Re-clamp passes.
"""

import bpy
import numpy as np

from . import keys

OBJECT_NAME = "GTR_Diagnostics"
CHANNELS_PROP = "gtr_diag_channels"    # on the action: {property name: {"kind", "side", "barrier"}}
SERIAL_PROP = "gtr_diag_serial"        # on the action: counts the writes, for the ranking cache
MAX_LABEL = 36                          # magnet names are cut to this many characters in property names
RANK_COUNT = 5
MODE_VALUES = {'FOLLOW': 0.0, 'ALIGN': 1.0}

# (id, name, description, unit) of the measures frames are ranked by.
METRICS = (
    ('CORRECTION', "Wrist Correction", "How far the solve moved a wrist target from the mocap wrist", "cm"),
    ('BARRIER', "Barrier Depth", "How far a hand point was behind a barrier plane before it was clamped", "cm"),
    ('IK_MISS', "IK Miss", "How far a solved wrist ended from its target", "mm"),
    ('SWING', "Neck Swing", "How far the neck aim turned the guitar from its mount", "°"),
    ('WRIST_TURN', "Wrist Turn", "How far the fretting wrist turned away from the mocap", "°"),
    ('COLLIDER', "Chest Collider", "How far the chest collider pushed a wrist", "cm"),
    ('UNSETTLED', "Unsettled", "Solve passes on the frames whose neck aim or wrists had not settled", " passes"),
)
METRIC_BY_ID = {metric[0]: metric for metric in METRICS}

_cache = {}                 # (action session_uid, serial, metric) -> ranking


def _label(item, index, names):
    label = item.name.replace('"', "'").replace("\\", "/")[:MAX_LABEL] or f"Magnet {index + 1}"
    return f"{label} #{index + 1}" if names.count(item.name) > 1 else label


class Recorder:
    """Per-frame values for the frames of a bake, filled from its FrameResults."""

    def __init__(self, frames, magnets):
        self.frames = np.asarray(frames, dtype=np.float64)
        self.channels = {}      # property name -> (meta dict, values with NaN where unset)
        names = [item.name for item in magnets]
        self.labels = {index: _label(item, index, names) for index, item in enumerate(magnets)}
        self.barriers = {index for index, item in enumerate(magnets) if item.kind == 'PLANE' and not item.crossable}

    def _set(self, name, i, value, kind, side="", barrier=False):
        if name not in self.channels:
            meta = {"kind": kind, "side": side, "barrier": int(barrier)}
            self.channels[name] = (meta, np.full(len(self.frames), np.nan))
        self.channels[name][1][i] = value

    def note(self, i, result):
        """Record frame number `i` of the bake from its solver.FrameResult."""
        cm = result.metres_per_bu * 100.0
        for side, side_result in result.sides.items():
            self._set(f"{side} wrist correction (cm)", i, (side_result.target - side_result.fk_wrist).length * cm,
                      'CORRECTION', side)
            self._set(f"{side} IK miss (mm)", i, side_result.error * cm * 10.0, 'IK_MISS', side)
            contact = side_result.collider
            if contact is not None:
                pushed = contact.moved.length * cm if contact.weight > 0.0 else 0.0
                self._set(f"{side} chest collider (cm)", i, pushed, 'COLLIDER', side)
            for index, hit in side_result.hits:
                label = self.labels.get(index, f"Magnet {index + 1}")
                barrier = index in self.barriers
                signed = hit.signed if hit.signed is not None else hit.distance
                self._set(f"{side} {label} d (cm)", i, signed * cm, 'DISTANCE', side, barrier)
                self._set(f"{side} {label} w", i, hit.weight, 'WEIGHT', side, barrier)
        self._set("neck swing (°)", i, np.degrees(result.swing), 'SWING')
        self._set("fretting wrist turn (°)", i, np.degrees(result.wrist_turn), 'WRIST_TURN')
        self._set("solve passes", i, result.iterations, 'PASSES')
        self._set("settled", i, float(result.converged), 'SETTLED')
        frame_mode = result.frame_mode
        self._set("mode (0 follow, 1 align)", i, MODE_VALUES.get(result.mode, 0.0), 'MODE')
        self._set("neck aim weight", i, frame_mode.aim_weight if frame_mode is not None else 0.0, 'AIM_WEIGHT')


# Storage -------------------------------------------------------------------------------------------------------

def find(settings):
    """The diagnostics empty of the scene, if it is still there."""
    obj = settings.diagnostics
    return obj if obj is not None and obj.name in bpy.data.objects else None


def action_of(obj):
    data = obj.animation_data if obj is not None else None
    action = data.action if data is not None else None
    return action if action is not None and CHANNELS_PROP in action else None


def remove(settings):
    """Remove the diagnostics empty and its action."""
    obj = find(settings)
    if obj is None:
        return
    action = action_of(obj)
    bpy.data.objects.remove(obj)
    if action is not None and action.users == 0:
        bpy.data.actions.remove(action)
    settings.diagnostics = None


def write(settings, recorder, collections):
    """Key the recorded curves on the diagnostics empty (created in `collections` if needed). Returns it."""
    obj = find(settings)
    if obj is None:
        obj = bpy.data.objects.new(OBJECT_NAME, None)
        obj.empty_display_size = 0.01
        obj.hide_render = True
        for collection in collections:
            collection.objects.link(obj)
        settings.diagnostics = obj
    old = action_of(obj)
    serial = old.get(SERIAL_PROP, 0) + 1 if old is not None else 1
    for name in list(obj.keys()):
        if old is not None and name in old[CHANNELS_PROP]:
            del obj[name]
    data = obj.animation_data or obj.animation_data_create()
    data.action = None
    if old is not None and old.users == 0:
        bpy.data.actions.remove(old)

    action = bpy.data.actions.new(OBJECT_NAME)
    channels = keys.Channels(action, obj)
    meta = {}
    for name, (info, values) in recorder.channels.items():
        keep = ~np.isnan(values)
        if not keep.any():
            continue
        obj[name] = 0.0
        group = "Frame" if not info["side"] else ("Left Hand" if info["side"] == 'L' else "Right Hand")
        keys.write(channels.new(f'["{name}"]', 0, group), recorder.frames[keep], values[keep])
        meta[name] = info
    action[CHANNELS_PROP] = meta
    action[SERIAL_PROP] = serial
    data.action = action
    if channels.slot is not None:
        data.action_slot = channels.slot
    return obj


# Ranking -------------------------------------------------------------------------------------------------------

def read(obj):
    """(frames, {property name: (meta, values)}) of the diagnostics curves on `obj`, or None."""
    action = action_of(obj)
    if action is None:
        return None
    meta = action[CHANNELS_PROP]
    curves = {}
    for fcurve in keys.fcurves(action):
        name = fcurve.data_path[2:-2]
        if name in meta:
            curves[name] = (meta[name].to_dict(), *keys.read(fcurve))
    if not curves:
        return None
    frames = np.unique(np.concatenate([curve_frames for _, curve_frames, _ in curves.values()]))
    aligned = {}
    for name, (info, curve_frames, values) in curves.items():
        row = np.full(len(frames), np.nan)
        row[np.searchsorted(frames, curve_frames)] = values
        aligned[name] = (info, row)
    return frames, aligned


def scores(frames, curves, metric):
    """The value of `metric` on each of `frames` (NaN where nothing was recorded)."""
    def of(kind, transform=None, barrier=False):
        rows = [values if transform is None else transform(values) for info, values in curves.values()
                if info["kind"] == kind and (not barrier or info["barrier"])]
        if not rows:
            return np.full(len(frames), np.nan)
        largest = np.where(np.isnan(rows), -np.inf, rows).max(axis=0)
        return np.where(np.isinf(largest), np.nan, largest)

    if metric == 'CORRECTION':
        return of('CORRECTION')
    if metric == 'BARRIER':
        return of('DISTANCE', lambda d: np.maximum(-d, 0.0), barrier=True)
    if metric == 'IK_MISS':
        return of('IK_MISS')
    if metric == 'SWING':
        return of('SWING')
    if metric == 'WRIST_TURN':
        return of('WRIST_TURN')
    if metric == 'COLLIDER':
        return of('COLLIDER')
    if metric == 'UNSETTLED':
        return of('PASSES') * (1.0 - of('SETTLED'))
    raise ValueError(f"unknown metric {metric!r}")


def ranking(obj, metric, count=RANK_COUNT):
    """[(frame, value)] of the frames worst in `metric`, worst first, leaving out frames where it is 0."""
    action = action_of(obj)
    if action is None:
        return []
    key = (action.session_uid, action.get(SERIAL_PROP, 0), metric, count)
    if key not in _cache:
        found = read(obj)
        ranked = []
        if found is not None:
            frames, curves = found
            values = scores(frames, curves, metric)
            order = np.argsort(-np.nan_to_num(values, nan=-np.inf), kind='stable')
            ranked = [(int(round(frames[i])), float(values[i])) for i in order[:count]
                      if np.isfinite(values[i]) and values[i] > 0.0]
        if len(_cache) > 64:
            _cache.clear()
        _cache[key] = ranked
    return _cache[key]


def format_value(metric, value):
    unit = METRIC_BY_ID[metric][3]
    if metric == 'UNSETTLED':
        return f"{value:.0f}{unit}"
    return f"{value:.1f}{'' if unit == '°' else ' '}{unit}"
