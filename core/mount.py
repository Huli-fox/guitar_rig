"""Chest mount (§5.3): the default guitar transform carried by the chest bone, and Capture Mount.

The mount is stored as an offset `mount_t` (metres) and a rotation `mount_q`, both in the rest-aligned chest
frame Q_chest (calibrate.py: X the character's left, Y up, Z forward at rest):

    M_def = T(P_chest + Q_chest @ (s · mount_t)) @ R(Q_chest @ mount_q) @ S(gtr_scale)

where P_chest is the chest bone head, s the spine auto-scale factor, and gtr_scale GTR_ROOT's own scale,
kept apart from its rotation. Capture Mount inverts this for the current pose, dividing the offset by the
same s, so that the captured mount scales back to exactly the pose it was captured from.
"""

from mathutils import Matrix, Quaternion, Vector

from . import calibrate
from .mathx import auto_scale_factor


class MountError(ValueError):
    """The character or the guitar is not ready for the mount."""


def chest_pose(arm_obj, cal, chest_bone):
    """(P_chest, Q_chest) in world space for the armature's current pose."""
    pbone = arm_obj.pose.bones.get(chest_bone) if chest_bone else None
    if pbone is None:
        raise MountError("The chest bone is not mapped, or not in the armature.")
    matrix = arm_obj.matrix_world @ pbone.matrix
    offset = calibrate.rest_aligned_offset(pbone.bone, Quaternion(cal.char_frame))
    return matrix.translation.copy(), calibrate.rest_aligned(matrix.to_quaternion(), offset).normalized()


def spine_factor(cal, policy):
    """The auto-scale factor s of the mount offset (§5.1: spine ratio, f = 1; none under the NONE policy)."""
    return 1.0 if policy == 'NONE' else auto_scale_factor(cal.ratio_spine, 1.0)


def mount_matrix(chest_pos, chest_frame, mount_t, mount_q, factor, gtr_scale, metres_per_bu=1.0):
    """M_def, the guitar's world matrix on the mount."""
    location = chest_pos + chest_frame @ (Vector(mount_t) * (factor / metres_per_bu))
    rotation = chest_frame @ Quaternion(mount_q)
    return Matrix.LocRotScale(location, rotation.normalized(), Vector(gtr_scale))


def capture(chest_pos, chest_frame, gtr_matrix, factor, metres_per_bu=1.0):
    """(mount_t, mount_q) that put the guitar at `gtr_matrix` for this chest pose."""
    location, rotation, _ = gtr_matrix.decompose()
    inverse = chest_frame.inverted()
    mount_t = (inverse @ (location - chest_pos)) * (metres_per_bu / factor)
    return mount_t, (inverse @ rotation).normalized()


def root_scale(root):
    """gtr_scale: GTR_ROOT's world scale. Raises MountError for a mirroring scale, which a rotation cannot hold."""
    if root.matrix_world.to_3x3().determinant() <= 0.0:
        raise MountError("GTR_ROOT has a negative (mirroring) scale: use Flip X or Flip Z instead of a negative scale.")
    return root.matrix_world.to_scale()


def rebase(mount_t, mount_q, old_matrix, new_matrix, factor, metres_per_bu=1.0):
    """The mount that keeps the guitar where it was when GTR_ROOT moves relative to the guitar.

    `old_matrix` and `new_matrix` are GTR_ROOT's world matrices before and after a change of frame or origin
    (a flip, re-normalising, a new preset origin) that leaves the meshes in place. The offset of the new
    origin, seen in the old guitar frame, is added to the mount offset, and the frame change to the rotation.
    """
    old_location, old_rotation, _ = old_matrix.decompose()
    new_location, new_rotation, _ = new_matrix.decompose()
    offset = old_rotation.inverted() @ (new_location - old_location)
    mount_q = Quaternion(mount_q)
    mount_t = Vector(mount_t) + mount_q @ offset * (metres_per_bu / factor)
    return mount_t, (mount_q @ old_rotation.inverted() @ new_rotation).normalized()
