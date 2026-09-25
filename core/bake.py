"""World -> local conversion for the bake (§8, steps 3 and 4).

Matrices are NumPy arrays of shape (frames, 4, 4), row-major like mathutils. Bones that inherit rotation and
full scale and use local location (almost every FK bone) are converted in one vectorised step:

    basis = (L_parent @ parent_rest⁻¹ @ bone_rest)⁻¹ @ M_bone          (armature space)

Other bones go through Bone.convert_local_to_pose frame by frame, which handles every inheritance option.
"""

import math

import numpy as np
from mathutils import Matrix

EULER_ORDERS = ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX')


def as_matrices(value, frames=None):
    """`value` (a Matrix, a sequence of matrices or an array) as a float64 array of shape (frames, 4, 4).

    A single matrix is broadcast to `frames` when that is given.
    """
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim == 2:
        arr = arr[None]
    if arr.ndim != 3 or arr.shape[1:] != (4, 4):
        raise ValueError(f"expected 4x4 matrices, got shape {arr.shape}")
    if frames is not None and len(arr) != frames:
        if len(arr) != 1:
            raise ValueError(f"expected {frames} frames, got {len(arr)}")
        arr = np.broadcast_to(arr, (frames, 4, 4))
    return arr


def world_to_armature(world, object_world):
    """Armature-space matrices from world matrices and the armature object's world matrix (fixed or per frame)."""
    world = as_matrices(world)
    return np.linalg.inv(as_matrices(object_world, len(world))) @ world


def has_default_inheritance(bone):
    return bone.use_inherit_rotation and bone.inherit_scale == 'FULL' and bone.use_local_location


def _parent_offset(bone):
    """parent_rest⁻¹ @ bone_rest (bone_rest for a root bone)."""
    rest = np.array(bone.matrix_local, dtype=np.float64)
    if bone.parent is None:
        return rest
    return np.linalg.inv(np.array(bone.parent.matrix_local, dtype=np.float64)) @ rest


def _check_parent(bone, parent_pose, frames):
    if bone.parent is None:
        return None
    if parent_pose is None:
        raise ValueError(f"'{bone.name}' has a parent, so the parent's pose is needed")
    return as_matrices(parent_pose, frames)


def bone_pose_to_basis(bone, pose, parent_pose=None):
    """matrix_basis values that give `bone` the armature-space `pose` under `parent_pose` (before constraints)."""
    pose = as_matrices(pose)
    parent_pose = _check_parent(bone, parent_pose, len(pose))
    if has_default_inheritance(bone):
        offset = _parent_offset(bone)
        return np.linalg.inv(offset if parent_pose is None else parent_pose @ offset) @ pose
    return _convert(bone, pose, parent_pose, invert=True)


def bone_basis_to_pose(bone, basis, parent_pose=None):
    """Armature-space pose of `bone` from matrix_basis values and its parent's pose (inverse of the above)."""
    basis = as_matrices(basis)
    parent_pose = _check_parent(bone, parent_pose, len(basis))
    if has_default_inheritance(bone):
        offset = _parent_offset(bone)
        return (offset if parent_pose is None else parent_pose @ offset) @ basis
    return _convert(bone, basis, parent_pose, invert=False)


def _convert(bone, matrices, parent_pose, invert):
    rest = bone.matrix_local
    parent_rest = bone.parent.matrix_local if bone.parent is not None else None
    out = np.empty(matrices.shape)
    for i, m in enumerate(matrices):
        m = Matrix(m.tolist())
        if parent_rest is None:
            result = bone.convert_local_to_pose(m, rest, invert=invert)
        else:
            result = bone.convert_local_to_pose(m, rest, parent_matrix=Matrix(parent_pose[i].tolist()),
                                                parent_matrix_local=parent_rest, invert=invert)
        out[i] = np.array(result)
    return out


def parent_first(bones, names):
    """`names` ordered so that every bone comes after its ancestors."""
    def depth(name):
        count, bone = 0, bones[name].parent
        while bone is not None:
            count, bone = count + 1, bone.parent
        return count
    return sorted(names, key=depth)


def _frames(poses):
    return max((len(m) for m in poses.values()), default=0)


def pose_to_basis(bones, solved, fk=None):
    """matrix_basis values that reproduce the armature-space poses in `solved`.

    solved: {bone name: pose matrices}. fk: {bone name: pose matrices} for parents outside `solved`.
    A bone's parent pose comes from `solved` when the parent is there, otherwise from `fk` (§8 step 3).
    Returns {bone name: (frames, 4, 4)}.
    """
    fk = fk or {}
    solved = {name: as_matrices(m) for name, m in solved.items()}
    frames = _frames(solved)
    out = {}
    for name in parent_first(bones, solved):
        bone = bones[name]
        parent_pose = None
        if bone.parent is not None:
            parent_pose = solved.get(bone.parent.name)
            if parent_pose is None:
                parent_pose = fk.get(bone.parent.name)
            if parent_pose is None:
                raise KeyError(f"no pose for '{bone.parent.name}', the parent of '{name}'")
        out[name] = bone_pose_to_basis(bone, as_matrices(solved[name], frames), parent_pose)
    return out


def complete_chain(bones, solved, fk):
    """`solved` plus every bone lying between two solved bones, carried along by its solved parent.

    Twist and helper bones between solved bones (MMD 手捩 between the elbow and the wrist, Rigify's
    MCH-hand_fk, ...) keep their FK basis. Their FK pose must not parent a solved bone, because the solve
    moved them. `fk` needs the FK poses of those bones and of their parents. Returns a new dict.
    """
    solved = {name: as_matrices(m) for name, m in solved.items()}
    frames = _frames(solved)
    between = set()
    for name in solved:
        path, bone = [], bones[name].parent
        while bone is not None and bone.name not in solved:
            path.append(bone.name)
            bone = bone.parent
        if bone is not None:
            between.update(path)
    for name in parent_first(bones, between):
        bone = bones[name]
        parent = bone.parent.name
        basis = bone_pose_to_basis(bone, as_matrices(fk[name], frames), as_matrices(fk[parent], frames))
        solved[name] = bone_basis_to_pose(bone, basis, solved[parent])
    return solved


def decompose(basis):
    """Split matrices into location (frames, 3), rotation matrices (frames, 3, 3) and scale (frames, 3).

    As in Blender, a mirroring matrix gets a negative scale on all three axes.
    """
    basis = as_matrices(basis)
    loc = basis[:, :3, 3].copy()
    m3 = basis[:, :3, :3]
    scale = np.linalg.norm(m3, axis=1)
    scale[np.linalg.det(m3) < 0.0] *= -1.0
    rot = m3 / np.where(scale == 0.0, 1.0, scale)[:, None, :]
    return loc, rot, scale


def rotation_channels(rot, mode):
    """Rotation matrices (frames, 3, 3) as channel values for a bone's rotation_mode, continuous in time.

    QUATERNION: (w, x, y, z) with consistent signs. AXIS_ANGLE: (angle, x, y, z) with a consistent axis and
    an unwrapped angle. Euler orders: the solution nearest the previous frame (Matrix.to_euler compat).
    """
    if mode not in EULER_ORDERS and mode not in ('QUATERNION', 'AXIS_ANGLE'):
        raise ValueError(f"unknown rotation mode {mode!r}")
    values = []
    prev_q = prev_axis = prev_angle = prev_euler = None
    for m in np.asarray(rot, dtype=np.float64):
        mat = Matrix(m.tolist())
        if mode in EULER_ORDERS:
            prev_euler = mat.to_euler(mode) if prev_euler is None else mat.to_euler(mode, prev_euler)
            values.append(tuple(prev_euler))
            continue
        q = mat.to_quaternion()
        if prev_q is not None:
            q.make_compatible(prev_q)
        prev_q = q
        if mode == 'QUATERNION':
            values.append(tuple(q))
            continue
        axis, angle = q.to_axis_angle()
        if prev_axis is not None:
            if abs(angle) < 1e-7:
                axis = prev_axis.copy()      # the axis means nothing at zero angle
            elif axis.dot(prev_axis) < 0.0:
                axis.negate()
                angle = -angle
            angle += 2.0 * math.pi * round((prev_angle - angle) / (2.0 * math.pi))
        prev_axis, prev_angle = axis, angle
        values.append((angle, *axis))
    return np.array(values, dtype=np.float64).reshape(len(values), 3 if mode in EULER_ORDERS else 4)


def channels(basis, mode):
    """(location, rotation channels, scale) of matrix_basis values for a bone whose rotation_mode is `mode`."""
    loc, rot, scale = decompose(basis)
    return loc, rotation_channels(rot, mode), scale
