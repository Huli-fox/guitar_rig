"""Magnets (§5.5): pull a wrist target onto, or clamp it against, a line or plane on the guitar.

SAO applies its magnets in SA_system_emulation.min.js (Tt) in an arm-normalised space: positions relative to the
shoulder, times c = reference arm length / avatar arm length. A length in that space is `ratio_arm` times as long
in world space. For VRM avatars, which the guitar scenes target (MMD_SA.THREEX), SAO does not auto-scale the
distances (auto_scale_property(..., false)), so a magnet distance D in world space is D · ratio_arm. The plan's
auto_scale(D, ratio_arm, 0.9) is SAO's branch for MMD models, which have c = 1. SAO adds the hand offset e in
the normalised space as well, so there e also scales with the arm ratio: the MIN_JS policy. INDEX_JS scales e with
the palm, like the neck aim in jThree/index.js; NONE scales nothing.

One magnet acts on a hand point P = F + e (F the wrist):
- line: n is the closest point of the segment [A, B], d = |P - n|;
- plane: n is the projection of P, and d = |s| for the signed distance s along the normal N. A point behind a
  plane that is not crossable (s < 0) gets weight 1 however far behind it is: a barrier. SAO checks no distance
  there; with `barriers_ignore_distance` off, the barrier holds only within D;
- weight: w = 1 - |d - peak| / (D - peak) for d < D, then w^(1 - power) for a power above -9, and 0 for -9 or
  less. Power 1 snaps anywhere within D, 0 falls off linearly, -99 leaves only the barrier;
- a peak moves the pull target off the feature by `peak`, toward P;
- P += w (target - P), and the wrist is P - e again.
Magnets act in list order, each on the wrist the ones before it left.

Fingertip v2 (plane magnets; min.js offset_fingertip[_v2], which SAO's v1 shares) shifts the hand along the
normal so that its lowest chosen fingertip, less a margin (the fingertip offset plus the palm margin), is level
with P: with v the signed distance of P and best the lowest fingertip's minus the margin, the wrist also moves by
-N (best - v). Push-only caps best at v, so the shift only ever moves the hand away from the plane. The weight
and the barrier test still see P, and SAO shifts the hand whatever the weight, as this port does. So a snap puts
the lowest fingertip `margin` above the plane; a push-only barrier puts it `margin` above the plane from behind,
and from in front leaves it no lower than P's own height plus the margin: a hand whose fingertips hang lower than
that toward the plane is lifted, however far from the plane it is. On a hand without finger bones the solver
passes P itself as the only fingertip, with the palm margin alone.

Filters (the bake, §9) hook in where SAO filters (min.js, Tt): `tip_filter` takes the fingertip shift and
returns it filtered; `pull_filter` takes (P, pull target, w) and returns P's move in place of w (target - P), as
SAO's reference_point_filter does (see solver.py for the two kinds).

`clamp_out` is the re-clamp's hard contact (§9): it only ever pushes a hand out of a barrier.
"""

from dataclasses import dataclass

from mathutils import Matrix, Vector

from .mathx import auto_scale_factor

BARRIER_POWER = -9.0        # at or below this power a magnet pulls nowhere: only its barrier clamp is left
SNAP_POWER = 1.0            # magnets with at least this power snap, and get the hysteresis

# SAO's Alt+A hotkey ("guitar_fixed"), the same in all eight guitar scenes: it switches the neck aim off, makes
# the fretboard-edge magnet (5) snap instead of block, and disables its rotation-based filter. Magnets are found
# by preset id. Magnet 3's mocap_factor change only matters for VMC input and is left out.
MODE_PRESETS = {
    'FOLLOW': {"aim_enabled": True, "magnets": {"FRETBOARD_EDGE": {"power": -99.0, "filter": 'ROTATION_BASED'}}},
    'ALIGN': {"aim_enabled": False, "magnets": {"FRETBOARD_EDGE": {"power": 1.0, "filter": 'NONE'}}},
}


def apply_mode(settings, mode):
    """Switch the scene settings to a mode preset. The fields stay editable afterwards."""
    preset = MODE_PRESETS[mode]
    settings.aim_enabled = preset["aim_enabled"]
    for item in settings.magnets:
        for key, value in preset["magnets"].get(item.preset_id, {}).items():
            setattr(item, key, value)


# Geometry ------------------------------------------------------------------------------------------------------

@dataclass
class Feature:
    """A magnet's line or plane in world space."""
    kind: str                   # 'LINE' or 'PLANE'
    a: Vector                   # the segment start, or a point on the plane
    b: Vector = None            # the segment end
    normal: Vector = None       # the unit plane normal


@dataclass
class GuitarPose:
    """Where the solver puts GTR_ROOT: its location, rotation and scale. `default_rotation` is the chest-mount
    rotation before the neck aim, which magnets with use_default_rotation use."""
    location: Vector
    rotation: object            # Quaternion
    default_rotation: object
    scale: Vector

    def matrix(self):
        return Matrix.LocRotScale(self.location, self.rotation, self.scale)

    def point(self, local, default=False):
        """World position of a point in GTR_ROOT's local space."""
        rotation = self.default_rotation if default else self.rotation
        return self.location + rotation @ (Vector(local) * self.scale)

    def normal(self, local, default=False):
        """World direction of a plane normal given in GTR_ROOT's local space (normals scale inversely)."""
        rotation = self.default_rotation if default else self.rotation
        n = Vector(local)
        return (rotation @ Vector([n[i] / self.scale[i] for i in range(3)])).normalized()


@dataclass
class Shape:
    """A magnet's landmarks in GTR_ROOT's local space."""
    kind: str
    a: Vector
    b: Vector = None
    normal: Vector = None

    def world(self, guitar, default=False):
        if self.kind == 'LINE':
            return Feature('LINE', guitar.point(self.a, default), guitar.point(self.b, default))
        return Feature('PLANE', guitar.point(self.a, default), normal=guitar.normal(self.normal, default))


# Pull ----------------------------------------------------------------------------------------------------------

@dataclass
class Params:
    """A magnet's settings in world units."""
    reach: float                # D
    peak: float = 0.0
    power: float = 0.0
    crossable: bool = True
    hysteresis: float = 1.0     # reach multiplier while a snap magnet holds the hand


@dataclass
class Hit:
    """What one magnet did to one hand point."""
    point: Vector               # the hand point before the pull
    nearest: Vector             # the nearest point of the feature
    target: Vector              # where the pull goes: the nearest point, moved off by the peak
    distance: float             # d
    reach: float                # D, with the hysteresis if it applied
    weight: float               # w
    barrier: bool               # clamped behind a plane that is not crossable
    moved: Vector               # displacement of the hand point
    shift: float = 0.0          # the fingertip move along the plane normal (SAO's E = best - v): -N·shift
    tip: Vector = None          # the lowest fingertip before the pull (fingertip v2)
    signed: float = None        # planes: the signed distance s, negative behind the plane; lines: d

    @property
    def holds(self):
        """Whether the magnet had the hand within reach: a snap magnet then keeps its hysteresis next frame."""
        return self.distance < self.reach


def nearest_point(feature, point):
    """(n, d, s): the feature's point nearest to `point`, the distance, and the signed distance (lines: d)."""
    if feature.kind == 'LINE':
        a, ab = feature.a, feature.b - feature.a
        length2 = ab.length_squared
        t = 0.0 if length2 < 1e-24 else min(max((point - a).dot(ab) / length2, 0.0), 1.0)
        n = a + ab * t
        d = (point - n).length
        return n, d, d
    s = (point - feature.a).dot(feature.normal)
    return point - feature.normal * s, abs(s), s


def falloff(d, reach, peak=0.0, power=0.0):
    """SAO's weight for a hand point at distance `d` from the feature, in [0, 1]."""
    if d >= reach:
        return 0.0
    w = 1.0 - abs(d - peak) / max(reach - peak, 1e-12)
    if power != 0.0:
        if power <= BARRIER_POWER:
            return 0.0
        # SAO raises w unclamped: a negative w (d far below the peak) gives NaN there, and a power above 1
        # overshoots the feature.
        w = max(w, 0.0) ** (1.0 - power)
    return min(max(w, 0.0), 1.0)


def pull(point, feature, params, *, holding=False, barriers_ignore_distance=True, tips=None, margin=0.0,
         push_only=False, tip_filter=None, pull_filter=None):
    """(new hand point, Hit) after one magnet. `holding`: the magnet held this hand on the previous frame.

    `tips`: world fingertip points for fingertip v2 (plane magnets), with its `margin` and `push_only`; the
    filters are the bake's (see the module notes).
    """
    n, d, s = nearest_point(feature, point)
    reach = params.reach
    if holding and params.power >= SNAP_POWER:
        reach *= params.hysteresis
    barrier = (feature.kind == 'PLANE' and s < 0.0 and not params.crossable
               and (barriers_ignore_distance or d < reach))
    target = n
    if barrier:
        w = 1.0
    else:
        w = falloff(d, reach, params.peak, params.power)
        if params.peak > 0.0 and w > 0.0 and d > 1e-12:
            target = n + (point - n) * (params.peak / d)
    moved = (target - point) * w if pull_filter is None else pull_filter(point, target, w)
    shift, nearest = 0.0, None
    if tips and feature.kind == 'PLANE':
        heights = [(tip - feature.a).dot(feature.normal) for tip in tips]
        low = min(range(len(tips)), key=heights.__getitem__)
        best = heights[low] - margin
        if push_only:
            best = min(best, s)
        shift, nearest = best - s, tips[low].copy()
        if tip_filter is not None:
            shift = tip_filter(shift)
        moved = moved - feature.normal * shift
    return point + moved, Hit(point.copy(), n, target, d, reach, w, barrier, moved, shift, nearest, s)


@dataclass
class Fingertips:
    """Fingertip v2 settings of a magnet on one hand, in world units."""
    vectors: list               # world vectors from the wrist to each chosen fingertip
    margin: float               # fingertip offset plus palm margin
    push_only: bool = False


@dataclass
class Entry:
    """One magnet ready to act on a wrist: its list index, world feature, world settings, the world vector
    from the wrist to its hand point, its fingertips (or None), and the bake's filter hooks (or None)."""
    index: int
    feature: Feature
    params: Params
    offset: Vector
    fingertips: Fingertips = None
    tip_filter: object = None
    pull_filter: object = None


def apply(wrist, entries, *, barriers_ignore_distance=True, holding=frozenset()):
    """(wrist, [(magnet index, Hit)]) after the magnets in list order. `holding`: indices of the snap magnets
    that held this hand on the previous frame."""
    hits = []
    for entry in entries:
        tips = entry.fingertips
        point, hit = pull(wrist + entry.offset, entry.feature, entry.params, holding=entry.index in holding,
                          barriers_ignore_distance=barriers_ignore_distance,
                          tips=[wrist + v for v in tips.vectors] if tips is not None else None,
                          margin=tips.margin if tips is not None else 0.0,
                          push_only=tips is not None and tips.push_only,
                          tip_filter=entry.tip_filter, pull_filter=entry.pull_filter)
        wrist = point - entry.offset
        hits.append((entry.index, hit))
    return wrist, hits


def is_barrier(entry):
    """Whether a magnet entry is a barrier: a plane the hand may not cross."""
    return entry.feature.kind == 'PLANE' and not entry.params.crossable


def clamp_out(wrist, entry):
    """(wrist, push) with the wrist pushed along a barrier's normal just far enough that its hand point is not
    behind the plane and, with fingertips, that the lowest one is at least the fingertip margin above it (the
    margin can be negative: the string barrier lets the fingertips reach below the string plane). `push` is the
    distance moved, 0 when nothing penetrates. Unlike `pull` this never moves a hand toward the plane."""
    feature = entry.feature
    normal = feature.normal
    push = -(wrist + entry.offset - feature.a).dot(normal)
    tips = entry.fingertips
    if tips is not None and tips.vectors:
        lowest = min((wrist + v - feature.a).dot(normal) for v in tips.vectors)
        push = max(push, tips.margin - lowest)
    if push <= 0.0:
        return wrist, 0.0
    return wrist + normal * push, push


# Scaling -------------------------------------------------------------------------------------------------------

def distance_scale(policy, ratio_arm):
    """World metres per metre of a magnet distance (reach and peak): SAO's arm space, or 1 under NONE."""
    return 1.0 if policy == 'NONE' else ratio_arm


def offset_scale(policy, ratio_arm, ratio_palm):
    """World metres per metre of a magnet hand offset under the auto-scale policy."""
    if policy == 'INDEX_JS':
        return auto_scale_factor(ratio_palm, 1.0)
    if policy == 'MIN_JS':
        return ratio_arm
    return 1.0


def hand_offset(offset, hand_frame, scale=1.0, axis_rot=None):
    """The world vector from the wrist to a magnet's hand point.

    `offset` is in the rest-aligned hand frame `hand_frame` (Q_hand, world); `axis_rot` (character-frame
    coordinates) turns it first when given, as SAO does for avatars that are not in T-pose.
    """
    v = Vector(offset) * scale
    if axis_rot is not None:
        v = axis_rot @ v
    return hand_frame @ v
