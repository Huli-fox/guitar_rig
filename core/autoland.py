"""Automatic landmark placement (§12).

The normaliser's measurements (guitar_frame.Neck) give the features a landmark can sit on: the nut, the heel
(where the body starts under the neck), the fretboard top line with its tilt, the neck's lower edge and centre
lines, and the end of the body. A preset says where its landmarks sit relative to the same features of its
reference guitar, and that is kept: the string plane's height and the strum line's offsets are conventions
tuned with the preset's magnets (the string barrier's fingertip offset cancels the string plane's height, for
one), not features of the mesh.

Each landmark is anchored along X, Y and Z:
- X: neck landmarks on the heel, the nut and its barrier on the nut, scaled by the neck length between them;
  strum landmarks on the heel, scaled by the body length from the heel to the end of the body;
- Y: the lower edge line (neck pivot, nut and the planes through them) or the centre line;
- Z: the fretboard top line, tilt included.
Offsets from the anchors scale with the neck width (Y) and thickness (Z), like presets.fit, so that the
magnets' guitar-space lengths that Load Preset scaled the same way still match. Plane normals map with the
placement, so they turn with the fretboard's tilt. On the preset's own reference guitar the landmarks are the
preset's.

Checked against SAO's own placements on the five guitar scenes whose points SAO placed for their own prop,
with the acoustic preset (tests/test_autoland): the neck lines within about a centimetre (SAO's own points
scatter that much around the meshes), the neck/body barrier within 2 cm where the plain preset fit puts it up
to 11 cm off on guitars with cutaways, and the strum line's middle within 8 cm, closer than the fit overall.
SAO's strum lines are wrist lines tuned per instrument, 9 to 26 cm long; on its acoustic the rule puts the line
on the soundhole, where SAO has it. GTR_ROOT does not move.
"""

import math
from dataclasses import dataclass, field

from mathutils import Matrix, Vector

from . import landmarks, presets

NECK, NUT, BODY = 'NECK', 'NUT', 'BODY'      # X anchors
EDGE, CENTRE = 'EDGE', 'CENTRE'             # Y anchors
ANCHORS = {
    "NECK_PIVOT": (NECK, EDGE),
    "NUT": (NUT, EDGE),
    "FRETBOARD_PLANE": (NECK, EDGE),
    "FRETBOARD_EDGE": (NECK, EDGE),
    "STRING_PLANE": (NECK, EDGE),
    "NECK_BODY_BARRIER": (NECK, CENTRE),
    "NUT_BARRIER": (NUT, CENTRE),
    "STRUM_A": (BODY, CENTRE),
    "STRUM_B": (BODY, CENTRE),
    "STRUM_X_PLANE": (BODY, CENTRE),
}
MIN_BODY_SHARE = 0.2        # a body shorter than this share of the guitar's length gets a warning
HEEL_NOTE_CM = 1.0          # the report mentions a heel further than this from where the neck narrows
CONFIDENCE_ORDER = ('LOW', 'MEDIUM', 'HIGH')


class AutoError(ValueError):
    """The guitar or the preset lacks what the landmarks are placed on."""


@dataclass
class Features:
    """The anchors of one guitar, in its frame coordinates and units."""
    neck: object                # guitar_frame.Neck
    heel: float
    tail: float                 # X of the end of the body

    def x(self, kind):
        return self.heel if kind in (NECK, BODY) else self.neck.nut_x

    def y(self, kind, x):
        return self.neck.edge_at(x) if kind == EDGE else self.neck.center_y

    def z(self, x):
        return self.neck.top_at(x)

    def y_slope(self, kind):
        """dY/dX of the Y anchor line."""
        if kind != EDGE:
            return 0.0
        return -0.5 * (self.neck.width_nut - self.neck.width_joint) / max(self.neck.length, 1e-12)


@dataclass
class Placement:
    landmarks: dict             # role -> (position Vector, unit normal Vector or None), in target units
    confidence: str             # 'HIGH', 'MEDIUM' or 'LOW'
    messages: list = field(default_factory=list)


def _features(measurements, use_heel):
    neck = measurements.neck
    heel = neck.heel_x if use_heel else neck.joint_x
    return Features(neck, heel, float(measurements.bounds_min[0]))


def _lower(confidence, level):
    return min(confidence, level, key=CONFIDENCE_ORDER.index)


def place(preset, target, metres=1.0, frame_confidence='HIGH'):
    """Where the landmarks of `preset` go on the guitar measured as `target` (guitar_frame.Measurements in the
    guitar's frame coordinates). `metres`: metres per target unit, for the messages. Raises AutoError."""
    reference = preset.reference
    if target.neck is None:
        raise AutoError("No neck was found on the guitar: place the landmarks by hand, or load the preset and "
                        "check them.")
    if reference.neck is None:
        raise AutoError(f"The {preset.name} preset has no neck measurements to place landmarks from.")
    messages, confidence = [], 'HIGH'
    heel_found = target.neck.heel_x is not None
    use_heel = heel_found and reference.neck.heel_x is not None
    ref, tgt = _features(reference, use_heel), _features(target, use_heel)
    if not heel_found:
        confidence = _lower(confidence, 'MEDIUM')
        messages.append(('WARNING', "No body was found under the neck: the Neck/Body Barrier and the strum line "
                                    "are placed from where the neck narrows. Check them."))
    elif not use_heel:
        confidence = _lower(confidence, 'MEDIUM')
        messages.append(('WARNING', f"The {preset.name} preset was saved without its guitar's heel: the Neck/Body "
                                    "Barrier and the strum line are placed from where the neck narrows. Check them, "
                                    "or save the preset again."))

    neck_ref, neck_tgt = ref.neck.nut_x - ref.heel, tgt.neck.nut_x - tgt.heel
    body_ref, body_tgt = ref.heel - ref.tail, tgt.heel - tgt.tail
    if min(neck_ref, neck_tgt, body_ref) <= 0.0:
        raise AutoError("The neck or the body has no length along X: check the guitar frame (Flip X).")
    if body_tgt < MIN_BODY_SHARE * target.length:
        confidence = _lower(confidence, 'LOW')
        messages.append(('WARNING', "The body is short next to the neck: check the strum line."))
        body_tgt = max(body_tgt, MIN_BODY_SHARE * target.length)
    fitted = presets.fit(reference, target)     # Y and Z scales: neck width and thickness, as Load Preset uses
    scale_x = {NECK: neck_tgt / neck_ref, NUT: neck_tgt / neck_ref, BODY: body_tgt / body_ref}
    scale_y, scale_z = float(fitted.scale[1]), float(fitted.scale[2])
    if fitted.messages:
        confidence = _lower(confidence, 'MEDIUM')
        messages += fitted.messages
    if frame_confidence == 'LOW':
        confidence = 'LOW'
        messages.append(('WARNING', "The guitar frame has low confidence: check its axes first."))

    placed = {}
    for role, spec in preset.landmarks.items():
        if role not in ANCHORS:
            messages.append(('WARNING', f"The preset has an unknown landmark role {role!r}."))
            continue
        along, across = ANCHORS[role]
        p, sx = spec.position, scale_x[along]
        x = tgt.x(along) + (p.x - ref.x(along)) * sx
        y = tgt.y(across, x) + (p.y - ref.y(across, p.x)) * scale_y
        z = tgt.z(x) + (p.z - ref.z(p.x)) * scale_z
        normal = None
        if spec.normal is not None:
            # A normal maps by the inverse transpose of the placement's derivative, so that it stays square to
            # the same surface: the planes turn with the fretboard's tilt and the neck's taper.
            slope_y = tgt.y_slope(across) * sx - ref.y_slope(across) * scale_y
            slope_z = tgt.neck.fret_slope * sx - ref.neck.fret_slope * scale_z
            jacobian = Matrix(((sx, 0.0, 0.0), (slope_y, scale_y, 0.0), (slope_z, 0.0, scale_z)))
            normal = (jacobian.inverted().transposed() @ spec.normal).normalized()
        placed[role] = (Vector((x, y, z)), normal)

    cm = metres * 100.0
    neck = tgt.neck
    text = (f"Neck {neck_tgt * cm:.0f} cm from the {'heel' if use_heel else 'body'} to the nut, "
            f"{neck.width_at(neck.nut_x) * cm:.1f} cm wide at the nut; fretboard tilted "
            f"{math.degrees(math.atan(neck.fret_slope)):+.1f}°.")
    if heel_found:
        past = (neck.joint_x - neck.heel_x) * cm
        if past > HEEL_NOTE_CM:
            text += f" The body starts under the neck {past:.1f} cm past where the neck narrows (cutaways)."
        elif past < -HEEL_NOTE_CM:
            text += f" The heel reaches {-past:.1f} cm up the neck from where it narrows."
    messages.insert(0, ('INFO', text))
    extent = (float(target.bounds_min[0]), float(target.bounds_max[0]))
    for role in ("STRUM_A", "STRUM_B"):
        if role in placed and not extent[0] <= placed[role][0].x <= extent[1]:
            confidence = _lower(confidence, 'MEDIUM')
            messages.append(('WARNING', f"{landmarks.ROLE_BY_ID[role].label} is off the end of the guitar: check "
                                        "the strum line."))
    return Placement(placed, confidence, messages)
