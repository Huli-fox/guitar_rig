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


def pull(point, feature, params, *, holding=False, barriers_ignore_distance=True):
    """(new hand point, Hit) after one magnet. `holding`: the magnet held this hand on the previous frame."""
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
    moved = (target - point) * w
    return point + moved, Hit(point.copy(), n, target, d, reach, w, barrier, moved)


@dataclass
class Entry:
    """One magnet ready to act on a wrist: its list index, world feature, world settings and the world vector
    from the wrist to its hand point."""
    index: int
    feature: Feature
    params: Params
    offset: Vector


def apply(wrist, entries, *, barriers_ignore_distance=True, holding=frozenset()):
    """(wrist, [(magnet index, Hit)]) after the magnets in list order. `holding`: indices of the snap magnets
    that held this hand on the previous frame."""
    hits = []
    for entry in entries:
        point, hit = pull(wrist + entry.offset, entry.feature, entry.params, holding=entry.index in holding,
                          barriers_ignore_distance=barriers_ignore_distance)
        wrist = point - entry.offset
        hits.append((entry.index, hit))
    return wrist, hits


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
