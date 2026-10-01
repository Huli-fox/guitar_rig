"""A synthetic guitar for the tests, built in its own frame (x: toward the headstock, z: out of the strings) in
metres, then placed anywhere in world space.

Body top at z = 0 (back at -0.1), neck/body joint at x = 0, nut at x = NUT_X, fretboard top at FRET_Z, a
headstock recessed below the fretboard with tuners sticking out sideways, six string parts and a bridge.
"""

import math

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

BODY_X = (-0.50, 0.0)
BODY_BACK_Z = -0.10
NECK_START_X = -0.02            # the neck overlaps the body a little
NUT_X = 0.36
HEAD_END_X = 0.56
FRET_Z = 0.008
NECK_BACK_Z = -0.014
NECK_WIDTH = (0.056, 0.044)     # at the joint and at the nut
STRING_Z = 0.012
BRIDGE_X = -0.30
LENGTH = HEAD_END_X - BODY_X[0]

# A world placement: turned every way, moved, and a centimetre-scaled parent like an FBX or GLB import.
WORLD_ROTATION = Euler((0.7, -0.4, 2.1)).to_matrix().to_4x4()
WORLD_OFFSET = Vector((0.4, -1.2, 0.9))


def _body_outline(n=48):
    def half(x):
        values = [0.0]
        for cx, r in ((-0.31, 0.19), (-0.13, 0.13)):
            d = r * r - (x - cx) ** 2
            if d > 0.0:
                values.append(math.sqrt(d))
        return max(values)
    xs = np.linspace(BODY_X[0] + 0.002, BODY_X[1] - 0.002, n)
    return [(x, half(x)) for x in xs] + [(x, -half(x)) for x in xs[::-1]]


def _prism(bm, outline, z0, z1):
    bottom = [bm.verts.new((x, y, z0)) for x, y in outline]
    top = [bm.verts.new((x, y, z1)) for x, y in outline]
    bm.faces.new(top)
    bm.faces.new(bottom[::-1])
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm.faces.new((bottom[i], bottom[j], top[j], top[i]))


def _box(bm, lo, hi):
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    _prism(bm, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def _neck(bm, rings=30, segments=12):
    loops = []
    for i in range(rings):
        t = i / (rings - 1)
        x = NECK_START_X + (NUT_X - NECK_START_X) * t
        w = NECK_WIDTH[0] + (NECK_WIDTH[1] - NECK_WIDTH[0]) * max(x, 0.0) / NUT_X
        depth = FRET_Z - NECK_BACK_Z
        ring = [bm.verts.new((x, 0.5 * w * math.cos(a), FRET_Z - depth * math.sin(a)))
                for a in np.linspace(0.0, math.pi, segments)]
        loops.append(ring)
    for a, b in zip(loops, loops[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(loops[0])
    bm.faces.new(loops[-1][::-1])


def _strings(bm, count=6):
    for k in range(count):
        s = (k / (count - 1)) - 0.5
        y0, y1 = s * 0.05, s * 0.036
        a, b = Vector((BRIDGE_X, y0, STRING_Z)), Vector((NUT_X, y1, STRING_Z))
        side = Vector((0.0, 0.0006, 0.0))
        up = Vector((0.0, 0.0, 0.0006))
        corners = [(p + dy + dz) for p in (a, b) for dy, dz in ((-side, -up), (side, -up), (side, up), (-side, up))]
        v = [bm.verts.new(c) for c in corners]
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((v[i], v[j], v[4 + j], v[4 + i]))


def _mesh(name, build):
    bm = bmesh.new()
    build(bm)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


PARTS = {
    "Body": lambda bm: (_prism(bm, _body_outline(), BODY_BACK_Z, 0.0), _box(bm, (BRIDGE_X - 0.01, -0.05, 0.0),
                                                                           (BRIDGE_X + 0.01, 0.05, 0.01))),
    "Neck": _neck,
    "Headstock": lambda bm: (_box(bm, (NUT_X, -0.0425, -0.012), (HEAD_END_X, 0.0425, 0.002)),
                             [_box(bm, (x - 0.01, sy * 0.0425, -0.011), (x + 0.01, sy * 0.085, -0.003))
                              for x in (0.42, 0.47, 0.52) for sy in (-1.0, 1.0)]),
    "Strings": _strings,
}


def _low_poly_neck(bm):
    """A neck of long faces, each a loose part, like low-poly props (every face passes as a string)."""
    _neck(bm, rings=2)
    bmesh.ops.split_edges(bm, edges=bm.edges[:])


HORN_END_X = 0.12               # cutaway horns beside the neck reach this far toward the headstock


def _horns(bm):
    """Two horns beside the neck, like a double-cutaway electric: the body outline goes on past the heel."""
    for sy in (-1.0, 1.0):
        y0, y1 = sorted((sy * 0.045, sy * 0.12))
        _box(bm, (-0.05, y0, BODY_BACK_Z), (HORN_END_X, y1, 0.0))


TILTED = ("Neck", "Headstock", "Strings")


def _tilted(build_part, angle):
    """`build_part` with its vertices turned about the Y axis through the fretboard top at the joint, so that the
    fretboard rises toward the headstock by `angle`."""
    def build_tilted(bm):
        start = len(bm.verts)
        build_part(bm)
        bm.verts.ensure_lookup_table()
        pivot = Vector((0.0, 0.0, FRET_Z))
        bmesh.ops.rotate(bm, verts=bm.verts[start:], cent=pivot, matrix=Matrix.Rotation(-angle, 3, 'Y'))
    return build_tilted


def build(name="Guitar", strings=True, joined=False, matrix=None, parent_scale=None, low_poly=False, horns=False,
          neck_tilt=0.0):
    """Guitar objects in the scene: one per part (joined: one mesh), under a scaled empty if `parent_scale`.

    `matrix` places the guitar frame in world space; `horns` adds cutaway horns; `neck_tilt` (radians) tilts the
    neck, headstock and strings up toward the headstock. Returns (objects, the empty or None).
    """
    parts = [key for key in PARTS if strings or key != "Strings"] + (["Horns"] if horns else [])
    build_part = dict(PARTS, Horns=_horns)
    if low_poly:
        build_part["Neck"] = _low_poly_neck
    if neck_tilt:
        build_part.update({key: _tilted(build_part[key], neck_tilt) for key in TILTED})
    matrix = Matrix.Identity(4) if matrix is None else matrix
    collection = bpy.context.scene.collection
    if joined:
        meshes = [(name, _mesh(name, lambda bm: [build_part[key](bm) for key in parts]))]
    else:
        meshes = [(f"{name}_{key}", _mesh(f"{name}_{key}", build_part[key])) for key in parts]
    parent = None
    if parent_scale is not None:
        parent = bpy.data.objects.new(f"{name}_Import", None)
        collection.objects.link(parent)
        parent.matrix_world = matrix @ Matrix.Scale(parent_scale, 4)
    objects = []
    for obj_name, mesh in meshes:
        obj = bpy.data.objects.new(obj_name, mesh)
        collection.objects.link(obj)
        if parent is not None:
            mesh.transform(Matrix.Scale(1.0 / parent_scale, 4))    # mesh data in the import's units
            obj.parent = parent
        else:
            obj.matrix_world = matrix
        objects.append(obj)
    bpy.context.view_layer.update()
    return objects, parent


def world_placement():
    return Matrix.Translation(WORLD_OFFSET) @ WORLD_ROTATION


def clear():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
