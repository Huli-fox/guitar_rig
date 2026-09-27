"""Arm IK maths (§4): pole targets for Blender's IK constraint, and the reach clamp.

Before it solves, Blender's IK (intern/iksolver, IK_QJacobianSolver::ConstrainPoleVector) turns the chain about
its root so that the root bone's up axis, X·cos(pole_angle) + Z·sin(pole_angle) of its pose before IK, points at
the pole target; both are seen from the root, square to the direction of the goal. The solve then only bends the
chain in that plane. `pole_position` puts the pole where the smallest swing from the FK arm direction to the goal
direction takes the FK up axis: the IK then swings the FK arm onto the goal and changes only the elbow bend. The
tests check this against Blender's result on every test rig.

So the pole angle does not change the solved pose; it only decides where the pole is drawn, and
`rest_pole_angle` picks the angle that puts the pole behind the elbow. Nothing has to be found by trial, and a
straight arm cannot flip, because the up axis comes from the upper arm's own rotation, not from the elbow.

A chain that starts straight is the one thing the IK cannot solve: its elbow moves square to the arm, so it cannot
shorten the arm, and it leaves it straight, pointing at the goal. On the test rigs it fails below a 0.05° bend and
works from 0.2°, whatever the goal needs. `seed_bend` gives such an arm a 1° bend toward the pole's side before the
IK, and `reach_clamp` is never shorter than the FK arm, which is reachable as it is.
"""

import math

from mathutils import Quaternion

POLE_SHARE = 0.3            # the pole is this share of the chain length from the arm...
POLE_MIN_M = 0.15           # ...and at least this many metres
SEED_BEND = math.radians(1.0)       # bend given to a straight FK arm that has to shorten
STRAIGHT = math.radians(0.5)        # FK elbows bent less than this count as straight


def up_axis(x_axis, z_axis, pole_angle):
    """The IK root bone's up axis for `pole_angle`, from its X and Z axes."""
    return x_axis * math.cos(pole_angle) + z_axis * math.sin(pole_angle)


def _square(v, axis):
    """`v` without its component along the unit vector `axis`."""
    return v - axis * v.dot(axis)


def pole_position(shoulder, elbow, tip, up, goal, distance, bias=None):
    """World position of the pole target that makes the IK swing the FK arm onto `goal`.

    `shoulder`, `elbow` and `tip` are the chain root's head, the IK forearm's head and its tail in the FK pose;
    `up` is the root's up axis in that pose (`up_axis`). The pole goes beside the arm at the elbow's height,
    `distance` from the line to the goal. `bias`, a world rotation about the shoulder, turns the FK arm first:
    the IK then swings the turned arm onto the goal, so the elbow ends up turned about the line to the goal.
    """
    arm = (tip - shoulder).normalized()
    side = _square(up, arm)
    if side.length < 1e-9:
        # The up axis is square to the upper arm, so this needs a forearm folded exactly onto it.
        side = _square(arm.orthogonal(), arm)
    side.normalize()
    height = (elbow - shoulder).dot(arm)
    if bias is not None:
        arm, side = bias @ arm, bias @ side
    to_goal = goal - shoulder
    direction = to_goal.normalized() if to_goal.length > 1e-9 else arm
    swing = arm.rotation_difference(direction)
    return shoulder + direction * height + (swing @ side) * distance


def pole_distance(chain_length, metres_per_bu=1.0):
    """How far the pole sits from the arm, in scene units, for a chain `chain_length` long (scene units)."""
    return max(POLE_SHARE * chain_length, POLE_MIN_M / metres_per_bu)


def rest_pole_angle(x_axis, z_axis, arm, bend):
    """The pole angle whose up axis points along `bend`, both seen square to the arm direction `arm`.

    At build time `x_axis` and `z_axis` are the IK upper arm's rest axes and `bend` is the way the elbow points
    when the forearm bends forward: backward.
    """
    arm = arm.normalized()
    b = _square(bend, arm).normalized()
    w = arm.cross(b)
    x, z = _square(x_axis, arm), _square(z_axis, arm)
    angle = math.atan2(-x.dot(w), z.dot(w))
    if x.dot(b) * math.cos(angle) + z.dot(b) * math.sin(angle) < 0.0:
        angle += math.pi
    return math.atan2(math.sin(angle), math.cos(angle))


def seed_bend(shoulder, elbow, tip, up, forearm, goal):
    """The local rotation of the IK forearm that bends a straight FK arm by SEED_BEND toward the pole's side, so
    that the IK can shorten it; the identity when the arm is bent or the goal is not nearer than the tip.

    `forearm` is the IK forearm's world rotation in the FK pose; the result goes after its own rotation.
    """
    upper, lower = elbow - shoulder, tip - elbow
    if upper.length < 1e-9 or lower.length < 1e-9 or upper.angle(lower) >= STRAIGHT:
        return Quaternion()
    if (goal - shoulder).length >= (tip - shoulder).length * (1.0 - 1e-6):
        return Quaternion()
    arm = (tip - shoulder).normalized()
    side = _square(up, arm)
    if side.length < 1e-9:
        return Quaternion()
    # Turning the forearm about side × lower moves the tip toward -side, which puts the elbow on the pole's side.
    turn = Quaternion(side.cross(lower).normalized(), SEED_BEND)
    return forearm.inverted() @ turn @ forearm


def reach_clamp(point, shoulder, reach, fk_distance=0.0):
    """(point, clamped): `point` moved toward `shoulder` so that it is at most `reach` from it, or at most as far
    as the FK arm reaches (`fk_distance`) if that is further: the FK pose is always reachable."""
    offset = point - shoulder
    limit = max(reach, fk_distance)
    if offset.length <= limit:
        return point, False
    return shoulder + offset.normalized() * limit, True
