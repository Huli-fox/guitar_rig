"""Landmark empties (§3.2): roles, lookup and placement under GTR_ROOT.

A landmark is an empty parented to GTR_ROOT with a `gtr_role` custom property. Its position and orientation
are read relative to GTR_ROOT, so it may sit anywhere in the hierarchy below it. For plane roles the empty's
local Z axis is the plane normal; point roles ignore the orientation.
"""

from dataclasses import dataclass

import bpy
from mathutils import Matrix, Quaternion, Vector

ROLE_PROP = "gtr_role"
DISPLAY_SIZE_M = 0.025      # landmark empties are drawn this big in world space


@dataclass(frozen=True)
class Role:
    id: str
    label: str
    kind: str                   # 'POINT' or 'PLANE'
    required: bool
    normal: tuple               # nominal normal in the guitar frame (planes)
    description: str


ROLES = (
    Role('NECK_PIVOT', "Neck Pivot", 'POINT', True, None,
         "Lower fretboard edge (-Y) near the neck/body joint: start of the neck axis the aim swings "
         "(SAO reference_origin)"),
    Role('NUT', "Nut", 'POINT', True, None,
         "Lower fretboard edge at the nut: end of the aimed neck axis (SAO reference_point)"),
    Role('FRETBOARD_PLANE', "Fretboard Plane", 'PLANE', True, (0.0, 0.0, 1.0),
         "Fretboard surface, normal +Z: the fretting hand snaps onto it (SAO magnet 3)"),
    Role('FRETBOARD_EDGE', "Fretboard Edge", 'PLANE', True, (0.0, 1.0, 0.0),
         "Plane through the lower fretboard edge, normal +Y: the fretting hand stays above it (SAO magnet 5)"),
    Role('NECK_BODY_BARRIER', "Neck/Body Barrier", 'PLANE', True, (1.0, 0.0, 0.0),
         "Normal +X: the fretting hand stays on the headstock side of the neck/body joint (SAO magnet 4)"),
    Role('NUT_BARRIER', "Nut Barrier", 'PLANE', False, (-1.0, 0.0, 0.0),
         "Optional, normal -X: the fretting hand stays on the body side of the nut (SAO magnet 6, ukulele)"),
    Role('STRUM_A', "Strum Line A", 'POINT', True, None,
         "Body end of the strum line the picking hand is pulled to (SAO magnet 0)"),
    Role('STRUM_B', "Strum Line B", 'POINT', True, None,
         "Neck end of the strum line (SAO magnet 0)"),
    Role('STRUM_X_PLANE', "Strum Position", 'PLANE', True, (1.0, 0.0, 0.0),
         "Normal +X: holds the picking hand's position along the strings (SAO magnet 1)"),
    Role('STRING_PLANE', "String Plane", 'PLANE', True, (0.0, 0.0, 1.0),
         "Normal +Z: the picking hand's fingertips stay above it (SAO magnet 2)"),
)
ROLE_BY_ID = {role.id: role for role in ROLES}


def role_of(obj):
    role = obj.get(ROLE_PROP) if obj is not None else None
    return role if role in ROLE_BY_ID else None


def find(root):
    """{role: landmark object} among the descendants of `root` (the first one found per role)."""
    found = {}
    if root is None:
        return found
    for obj in root.children_recursive:
        role = role_of(obj)
        if role is not None and role not in found:
            found[role] = obj
    return found


def missing(root):
    """Required roles without a landmark."""
    found = find(root)
    return [role for role in ROLES if role.required and role.id not in found]


def normal_rotation(normal):
    """A rotation turning +Z onto `normal`, with a stable roll (Y as close to +Y, or +Z, as possible)."""
    normal = Vector(normal).normalized()
    up = Vector((0.0, 1.0, 0.0)) if abs(normal.y) < 0.9 else Vector((0.0, 0.0, 1.0))
    x = up.cross(normal).normalized()
    y = normal.cross(x)
    return Matrix((x, y, normal)).transposed().to_quaternion()


def relative_matrix(root, obj):
    """The landmark's matrix in GTR_ROOT's local space."""
    return root.matrix_world.inverted() @ obj.matrix_world


def local_position(root, obj):
    return relative_matrix(root, obj).translation


def local_normal(root, obj):
    """The landmark's local Z axis in GTR_ROOT's space, normalised (scale does not change a normal's direction
    under uniform scale; non-uniform landmark scale is not supported)."""
    return (relative_matrix(root, obj).to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()


def place(root, role_id, position, normal=None, collection=None):
    """Create or move the landmark of `role_id` to `position` (GTR_ROOT local), facing `normal` for planes."""
    role = ROLE_BY_ID[role_id]
    obj = find(root).get(role_id)
    if obj is None:
        obj = bpy.data.objects.new(f"GTR_{role_id}", None)
        obj[ROLE_PROP] = role_id
        collections = [collection] if collection is not None else list(root.users_collection)
        for coll in collections or [bpy.context.scene.collection]:
            coll.objects.link(obj)
        obj.parent = root
        obj.show_in_front = True
    rotation = Quaternion()
    if role.kind == 'PLANE':
        rotation = normal_rotation(normal if normal is not None else role.normal)
    obj.empty_display_type = 'SINGLE_ARROW' if role.kind == 'PLANE' else 'SPHERE'
    scale = root.matrix_world.to_scale()
    obj.empty_display_size = DISPLAY_SIZE_M / max(sum(scale) / 3.0, 1e-9) / _metres_per_unit()
    if obj.parent is root:
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.rotation_mode = 'QUATERNION'
        obj.location = position
        obj.rotation_quaternion = rotation
        obj.scale = (1.0, 1.0, 1.0)
    else:
        obj.matrix_world = root.matrix_world @ Matrix.LocRotScale(position, rotation, None)
    return obj


def _metres_per_unit():
    scale = bpy.context.scene.unit_settings.scale_length
    return scale if scale > 0.0 else 1.0
