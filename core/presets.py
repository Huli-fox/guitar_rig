"""Guitar presets (§3.2): landmarks, magnets, mount, aim and wrist settings for one instrument, and their fit to
the user's guitar.

A preset file keeps the numbers of its source, so SAO presets can be checked against the scene file they came
from. Positions are in the preset's length unit (`unit_m` metres, or SAO's `sao_placement_scale` / 11) and in
the preset's axes, which `frame` turns into the normalised guitar frame of §3.1. For SAO presets `frame` is the
small rotation between the prop's GLB axes and the frame the normaliser finds for that GLB (measured by
tools/measure_reference.py), so a preset fitted to its own prop reproduces SAO exactly. `reference` holds the
normaliser's measurements of that prop (metres, normalised frame, relative to the preset origin); fitting maps
them onto the same measurements of the user's guitar (see `fit`).

The preset origin is the point the guitar swings about when the neck is aimed, and the point the mount
places. For SAO presets it is the GLB origin; `fit` puts GTR_ROOT at the corresponding point of the user's
guitar.

Format 2 (M3) changed two things that files saved in format 1 still carry: a saved wrist `rotation` was SAO's
offset for its hand-tracking frame, and is now for the hand's T-pose-aligned frame (wrist.py); and magnets saved
`apply_axis_rot` off, the old default, where hand offsets now follow axis_rot like the neck aim. Format 1 files
are converted on loading. Format 3 (M5) adds the reference neck's heel and fretboard top line (`heel_x`,
`top_joint`, `top_nut`), which Auto-Place anchors landmarks on (autoland.py); without them it uses where the neck
narrows and a level fretboard.
"""

import json
import math
import os
from dataclasses import dataclass, field

import numpy as np
from mathutils import Euler, Quaternion, Vector

from .guitar_frame import Measurements
from .wrist import HAND_FRAME

PRESET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets")
NON_PRESET_FILES = frozenset({"bone_maps.json"})
SAO_UNITS_PER_M = 11.0      # 1 MMD unit = 1/11 m
FIT_WARN_RANGE = (0.5, 2.0)  # per-axis fit scales outside this range get a warning
FORMAT = 3


class PresetError(ValueError):
    """The preset file is missing, malformed or does not fit the guitar."""


@dataclass
class LandmarkSpec:
    position: Vector            # metres, normalised frame, relative to the preset origin
    normal: Vector = None       # unit vector in the normalised frame (planes only)


@dataclass
class Preset:
    id: str                     # built-in preset id, or the file path
    name: str
    description: str
    verified: bool
    notes: list
    reference: Measurements     # metres, normalised frame
    landmarks: dict             # role -> LandmarkSpec
    magnets: list               # dicts of GTR_Magnet fields; lengths in metres; `a`/`b` are landmark roles
    mount_t: Vector = None      # metres, rest-aligned chest frame (before the spine auto-scale)
    mount_q: Quaternion = None  # guitar frame in the rest-aligned chest frame
    aim_hand_offset: Vector = None
    wrist_offset: Quaternion = None
    wrist_blend: float = None
    raw: dict = field(default_factory=dict)


# SAO conventions -----------------------------------------------------------------------------------------------

def sao_mount(position, rotation_deg):
    """(offset in metres, rotation) of an SAO parent_bone mount, in the rest-aligned chest frame.

    jThree/index.js: the offset is auto_scale([x, y, -z]) and the rotation Euler(-rx, -ry, rz) in degrees with
    three.js order 'YXZ' (the matrix Ry·Rx·Rz, which is Blender's order 'ZXY'), both applied in the chest
    bone's frame, which at rest is the character frame (see calibrate.py).
    """
    x, y, z = position
    rx, ry, rz = (math.radians(v) for v in rotation_deg)
    offset = Vector((x, y, -z)) / SAO_UNITS_PER_M
    return offset, Euler((-rx, -ry, rz), 'ZXY').to_quaternion()


def sao_euler_xyz(rotation_deg):
    """An SAO rotation offset in degrees: three.js order 'XYZ' is the matrix Rx·Ry·Rz, Blender's order 'ZYX'."""
    return Euler([math.radians(v) for v in rotation_deg], 'ZYX').to_quaternion()


def sao_wrist(rotation_deg, side='L'):
    """An SAO rotation_reference offset as a wrist offset: the hand's T-pose-aligned frame in the guitar frame.

    SAO's offset is for its hand-tracking frame; the T-pose-aligned hand frame is that frame times w (wrist.py).
    """
    return (sao_euler_xyz(rotation_deg) @ HAND_FRAME[side]).normalized()


# Loading -------------------------------------------------------------------------------------------------------

def builtin_ids():
    """Ids of the preset files shipped in presets/, sorted by name."""
    ids = []
    for name in os.listdir(PRESET_DIR):
        if name.endswith(".json") and name not in NON_PRESET_FILES:
            ids.append(name[:-5])
    return sorted(ids)


def builtin_path(preset_id):
    return os.path.join(PRESET_DIR, preset_id + ".json")


def enum_items():
    """(id, name, description) for an EnumProperty of the built-in presets."""
    items = []
    for preset_id in builtin_ids():
        try:
            with open(builtin_path(preset_id), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        name = data.get("name", preset_id)
        if not data.get("verified", False):
            name += " (unverified)"
        items.append((preset_id, name, data.get("description", "")))
    return items or [("NONE", "None", "No presets found")]


def load(preset_id_or_path):
    """A Preset from a built-in id or a file path."""
    path = preset_id_or_path
    if not os.path.isabs(path) and not os.path.exists(path):
        path = builtin_path(preset_id_or_path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as exc:
        raise PresetError(f"Cannot read the preset {preset_id_or_path!r}: {exc.strerror or exc}.") from exc
    except ValueError as exc:
        raise PresetError(f"The preset {os.path.basename(path)} is not valid JSON: {exc}.") from exc
    try:
        return parse(data, preset_id_or_path)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise PresetError(f"The preset {os.path.basename(path)} is malformed: {exc!r}.") from exc


def _unit(data):
    if "unit_m" in data:
        return float(data["unit_m"])
    return float(data["sao_placement_scale"]) / SAO_UNITS_PER_M


MAGNET_LENGTHS = (
    # (key, space): SAO magnet distances are in arm space (MMD units); the fingertip offset is a guitar-space
    # length (SAO multiplies it by the prop scale), so it is in the preset's length unit. Entries with an "_m"
    # suffix are metres already.
    ("effective_distance", None),
    ("peak", None),
    ("fingertip_offset", 'GUITAR'),
    ("hand_offset", None),
)
MAGNET_PROPS = {"peak_m": "peak", "hand_offset_m": "hand_offset"}  # GTR_Magnet names of metre fields


def parse(data, preset_id=""):
    version = data.get("format", FORMAT)
    if version > FORMAT:
        raise ValueError(f"format {data['format']} is newer than this add-on reads ({FORMAT})")
    unit = _unit(data)
    frame = Quaternion(data.get("frame", (1.0, 0.0, 0.0, 0.0))).normalized()
    landmarks = {}
    for role, entry in data["landmarks"].items():
        position = frame @ (Vector(entry["position"]) * unit)
        normal = entry.get("normal")
        landmarks[role] = LandmarkSpec(position, (frame @ Vector(normal)).normalized() if normal else None)

    magnets = []
    for entry in data.get("magnets", []):
        magnet = {key: value for key, value in entry.items() if key not in {"sao_index", "note"}}
        if version < 2:
            magnet.pop("apply_axis_rot", None)
        for key, space in MAGNET_LENGTHS:
            raw = magnet.pop(key, None)
            if raw is None or key + "_m" in magnet:
                continue
            factor = unit if space == 'GUITAR' else 1.0 / SAO_UNITS_PER_M
            magnet[key + "_m"] = [v * factor for v in raw] if isinstance(raw, list) else raw * factor
        for key, prop in MAGNET_PROPS.items():
            if key in magnet:
                magnet[prop] = magnet.pop(key)
        magnets.append(magnet)

    mount_t = mount_q = None
    mount = data.get("mount")
    if mount:
        if "sao_position" in mount:
            mount_t, mount_q = sao_mount(mount["sao_position"], mount["sao_rotation"])
        else:
            mount_t, mount_q = Vector(mount["offset_m"]), Quaternion(mount["rotation"])
        # The mount places the preset axes; the guitar frame is `frame` applied to them.
        mount_q = (mount_q @ frame.inverted()).normalized()

    aim_hand_offset = None
    aim = data.get("aim")
    if aim:
        aim_hand_offset = (Vector(aim["sao_offset"]) / SAO_UNITS_PER_M if "sao_offset" in aim
                           else Vector(aim["offset_m"]))

    wrist_offset = wrist_blend = None
    wrist = data.get("wrist")
    if wrist:
        if "sao_offset" in wrist:
            rotation = sao_wrist(wrist["sao_offset"])
        else:
            rotation = Quaternion(wrist["rotation"])
            if version < 2:
                rotation = rotation @ HAND_FRAME['L']
        wrist_offset = (frame @ rotation).normalized()      # hand frame -> preset axes -> guitar frame
        wrist_blend = wrist.get("weight")

    return Preset(
        id=preset_id, name=data.get("name", preset_id), description=data.get("description", ""),
        verified=bool(data.get("verified", False)), notes=list(data.get("notes", [])),
        reference=Measurements.from_dict(data["reference"]), landmarks=landmarks, magnets=magnets,
        mount_t=mount_t, mount_q=mount_q, aim_hand_offset=aim_hand_offset, wrist_offset=wrist_offset,
        wrist_blend=wrist_blend, raw=data,
    )


# Fitting -------------------------------------------------------------------------------------------------------

@dataclass
class Fit:
    method: str                 # 'NECK' or 'BOUNDS'
    scale: np.ndarray           # (3,) target units per preset metre, per axis
    origin: np.ndarray          # (3,) the preset origin in target frame coordinates
    messages: list = field(default_factory=list)

    def point(self, position):
        """A preset position (metres, relative to the preset origin) relative to the fitted origin."""
        return Vector(np.asarray(position, dtype=float) * self.scale)

    def normal(self, normal):
        """A preset plane normal after the per-axis scaling (normals scale inversely)."""
        n = np.asarray(normal, dtype=float) / self.scale
        return Vector(n / np.linalg.norm(n))

    def length(self, value, axis=2):
        return value * float(self.scale[axis])


def fit(reference, target):
    """Map the preset's reference guitar onto the target guitar, per axis.

    With a neck on both: X by the neck length from the neck/body joint, Y by the neck width about the neck
    centre, Z by the neck thickness from the fretboard top, so landmarks on the neck land on the neck.
    Otherwise the bounding boxes are matched. `target` is in the target's frame coordinates and units.
    """
    messages = []
    method = 'BOUNDS'
    r, t = reference.neck, target.neck
    if r is not None and t is not None and min(r.length, r.width, r.thickness, t.length, t.width, t.thickness) > 0:
        method = 'NECK'
        scale = np.array((t.length / r.length, t.width / r.width, t.thickness / r.thickness))
        anchor_ref = np.array((r.joint_x, r.center_y, r.fret_z))
        anchor = np.array((t.joint_x, t.center_y, t.fret_z))
    else:
        size_ref, size = reference.size, target.size
        if np.any(size_ref <= 0.0) or np.any(size <= 0.0):
            raise PresetError("The guitar or the preset reference has no extent along an axis.")
        scale = size / size_ref
        anchor_ref, anchor = reference.bounds_min, target.bounds_min
        messages.append(('WARNING', "No neck found on " + ("the guitar" if t is None else "the preset reference")
                                    + ": the landmarks are fitted to the bounding box. Check them."))
    origin = anchor - anchor_ref * scale
    ratios = scale / float(np.exp(np.mean(np.log(scale))))
    lo, hi = FIT_WARN_RANGE
    if np.any(ratios < lo) or np.any(ratios > hi):
        messages.append(('WARNING', "The guitar's proportions differ a lot from the preset's; check the landmarks."))
    return Fit(method, scale, origin, messages)


# Magnets and saving --------------------------------------------------------------------------------------------

MAGNET_FIELDS = ("name", "enabled", "preset_id", "hand", "kind", "crossable", "effective_distance_m", "peak", "power",
                 "use_default_rotation", "hand_offset_mode", "hand_offset", "apply_axis_rot", "fingertip_mode",
                 "fingers", "fingertip_offset_m", "push_only", "filter", "hysteresis")


def store_magnets(collection, specs, landmark_objects, fitted):
    """Replace the GTR_Magnet `collection` with the preset magnet `specs`; returns (level, text) messages.

    Landmark roles `a` and `b` are resolved in `landmark_objects` ({role: object}); the guitar-space fingertip
    offset (metres on the reference guitar) is scaled into GTR_ROOT units with the fit's Z scale, like the
    landmark heights it shifts.
    """
    messages = []
    collection.clear()
    for spec in specs:
        item = collection.add()
        name = spec.get("name", spec.get("preset_id", "magnet"))
        for key, value in spec.items():
            if key in ("a", "b"):
                obj = landmark_objects.get(value)
                if obj is None:
                    messages.append(('WARNING', f"Magnet {name}: there is no {value} landmark."))
                setattr(item, "landmark_" + key, obj)
            elif key == "fingers":
                item.fingers = set(value)
            elif key == "fingertip_offset_m":
                item.fingertip_offset_m = fitted.length(value, 2)
            elif key in MAGNET_FIELDS:
                setattr(item, key, value)
            else:
                messages.append(('WARNING', f"Magnet {name}: unknown setting {key!r} ignored."))
    return messages


def magnet_dict(item, roles, metres_per_unit):
    """A saved-preset entry for a GTR_Magnet; `roles` gives the landmark role of an object (or None)."""
    entry = {}
    for key in MAGNET_FIELDS:
        value = getattr(item, key)
        if key == "fingers":
            value = sorted(value)
        elif key == "hand_offset":
            key, value = "hand_offset_m", list(value)
        elif key == "peak":
            key = "peak_m"
        elif key == "fingertip_offset_m":
            value *= metres_per_unit
        entry[key] = value
    for key in ("a", "b"):
        role = roles(getattr(item, "landmark_" + key))
        if role is not None:
            entry[key] = role
    return entry


def rounded(value, digits=6):
    if isinstance(value, dict):
        return {k: rounded(v, digits) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [rounded(v, digits) for v in value]
    if isinstance(value, float):
        value = round(value, digits)
        return 0.0 if value == 0.0 else value
    return value


def dumps(data, width=110):
    """JSON with two-space indents that keeps short objects and number lists on one line."""
    def encode(value, level):
        flat = json.dumps(value, ensure_ascii=False)
        pad = "  " * (level + 1)
        if not isinstance(value, (dict, list)) or len(flat) + len(pad) <= width and not (
                isinstance(value, dict) and any(isinstance(v, dict) for v in value.values())):
            return flat
        if isinstance(value, dict):
            items = [f"{pad}{json.dumps(k, ensure_ascii=False)}: {encode(v, level + 1)}" for k, v in value.items()]
            return "{\n" + ",\n".join(items) + "\n" + "  " * level + "}"
        items = [pad + encode(v, level + 1) for v in value]
        return "[\n" + ",\n".join(items) + "\n" + "  " * level + "]"
    return encode(data, 0) + "\n"
