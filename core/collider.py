"""Chest collider (§13, "magnet -1"): keeps the wrists and their fingertips out of the torso, before the magnets act.

SAO pushes hands out of the body with spheres and capsules on the head, chest, waist and hips (MMD_SA.js,
colliders_for_hands), moving the hand along the chest's forward axis onto the front of the shape ("z_push").
This is one such capsule, carried by the chest bone like the guitar mount: its axis runs along the rest-aligned
chest frame's Y (up) from `bottom` to `top`, `depth` in front of the chest bone head, with radius `radius`. The
plan's plane would also push an arm hanging at the side forward; a capsule leaves it alone, and moves a hand
continuously as it enters from the side.

A point is pushed only from the front half of the capsule (in front of its axis): a hand behind the body is left
where it is. The push moves the wrist along the forward axis far enough that every given point (the wrist, and
the fingertips when the hand has finger bones) is on the surface or outside. As with the mount, the lengths are
metres before the spine auto-scale.
"""

import math
from dataclasses import dataclass

from mathutils import Vector

from .mathx import auto_scale_factor


@dataclass
class Capsule:
    """The collider in world space."""
    origin: Vector          # the chest bone head plus the depth along the forward axis
    frame: object           # Quaternion: the rest-aligned chest frame (X: character's left, Y: up, Z: forward)
    bottom: float           # the axis ends along Y, in scene units from `origin`
    top: float
    radius: float

    @property
    def forward(self):
        return self.frame @ Vector((0.0, 0.0, 1.0))

    def local(self, point):
        return self.frame.inverted() @ (point - self.origin)

    def world(self, local):
        return self.origin + self.frame @ Vector(local)

    def push(self, point):
        """How far `point` must move forward to leave the capsule: 0 outside it or behind its axis."""
        x, y, z = self.local(point)
        along = min(max(y, self.bottom), self.top)
        room = self.radius * self.radius - x * x - (y - along) * (y - along)
        if room <= 0.0 or z < 0.0:
            return 0.0
        front = math.sqrt(room)
        return front - z if z < front else 0.0


@dataclass
class Contact:
    """What the collider did to one wrist."""
    point: Vector           # the wrist before the push
    moved: Vector           # the push (zero if none)
    deepest: Vector         # the point that needed the push (the wrist or a fingertip), or None

    @property
    def weight(self):
        return 1.0 if self.moved.length > 0.0 else 0.0


def capsule(settings, cal, chest_pos, chest_frame, policy_factor=None):
    """The scene's collider for a chest pose (P_chest, Q_chest), in scene units, or None when it is off."""
    if not settings.collider_enabled:
        return None
    factor = policy_factor
    if factor is None:
        factor = 1.0 if settings.autoscale_policy == 'NONE' else auto_scale_factor(cal.ratio_spine, 1.0)
    unit = factor / cal.metres_per_bu
    bottom, top = sorted((settings.collider_bottom_m, settings.collider_top_m))
    origin = chest_pos + chest_frame @ Vector((0.0, 0.0, settings.collider_depth_m * unit))
    return Capsule(origin, chest_frame, bottom * unit, top * unit, settings.collider_radius_m * unit)


def push(body, wrist, tips=()):
    """(wrist, Contact): the wrist moved forward so that it and the fingertip points (world points that move with
    it) are out of the capsule `body`. A push can carry a point from behind the axis into the front half, so it
    is repeated until nothing is inside."""
    points = [wrist, *tips]
    forward = body.forward
    depth, deepest = 0.0, None
    for _ in range(4):
        needs = [body.push(p + forward * depth) for p in points]
        worst = max(range(len(points)), key=needs.__getitem__)
        if needs[worst] <= 1e-12:
            break
        if deepest is None:
            deepest = points[worst].copy()
        depth += needs[worst]
    if depth <= 0.0:
        return wrist, Contact(wrist.copy(), Vector((0.0, 0.0, 0.0)), None)
    moved = forward * depth
    return wrist + moved, Contact(wrist.copy(), moved, deepest)
