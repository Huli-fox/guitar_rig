"""SAO's guitar collection (guitar_collection_v9.1, next to the add-on folder) for the tests: its scenes, their
hand-placed guitar points, and their props imported with SAO's placement scale.

A prop is imported under an empty scaled by placement.scale / 11, so that one Blender unit is a metre and the
empty stands for the prop's object3D (its origin and GLB axes).
"""

import json
import os

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SAO_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "guitar_collection_v9.1"))
SCENES = {
    "acoustic": "scene.json",
    "acoustic02": "scene - acoustic guitar - 02.json",
    "bass": "scene - bass guitar.json",
    "bass5": "scene - bass 5-string - cluster.json",
    "electric": "scene - electric guitar - cluster.json",
    "strat": "scene - stratocaster guitar.json",
    "ukulele": "scene - ukulele.json",
}
# Scenes whose guitar points SAO copied, in GLB units, from another scene instead of placing them on their own
# prop: they are no measure of where the points belong on these props.
COPIED = {"acoustic02": "acoustic", "bass5": "bass"}
GLTF_TO_BLENDER = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))


def available():
    return os.path.isdir(SAO_DIR)


def scene(key):
    with open(os.path.join(SAO_DIR, SCENES[key]), encoding="utf-8") as f:
        return json.load(f)["XR_Animator_scene"]


def _find_magnets(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "magnet" and isinstance(value, list):
                return value
            found = _find_magnets(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_magnets(value)
            if found:
                return found
    return None


def _vector(d):
    return Vector((d["x"], d["y"], d["z"]))


class Prop:
    """One scene's prop and its SAO points (GLB units, GLB axes)."""

    def __init__(self, key):
        data = scene(key)
        obj = data["object3D_list"][0]
        para = obj["model_para"]
        self.key = key
        self.unit = para["placement"]["scale"] / 11.0          # metres per GLB unit
        folder = os.path.join(SAO_DIR, os.path.dirname(obj["path"]))
        stem = os.path.basename(obj["path"])
        names = sorted(n for n in os.listdir(folder) if n.endswith(".glb"))
        self.glb = os.path.join(folder, next((n for n in names if n.startswith(stem)), names[0]))
        aim = para["parent_bone"]["rotation"]["align_with_external_point"]
        self.points = {"aim_origin": _vector(aim["reference_origin"]), "aim_point": _vector(aim["reference_point"])}
        self.magnets = [m for m in _find_magnets(data) if m.get("type") == "object3D"]
        for magnet in self.magnets:
            magnet["point"] = _vector(magnet["reference_point"])
            if "line_end" in magnet:
                magnet["end"] = _vector(magnet["line_end"])
            if "plane_normal" in magnet:
                magnet["normal"] = _vector(magnet["plane_normal"])

    def magnet(self, hand, kind, normal=None):
        """The first magnet for `hand` ('left'/'right') of `kind` ('line'/'plane'), with that plane normal."""
        for magnet in self.magnets:
            if hand in magnet["hand_affected"] and magnet["magnet_type"] == kind and (
                    normal is None or tuple(magnet["normal"]) == tuple(normal)):
                return magnet
        return None

    def load(self):
        """Import the prop under a new empty; returns (empty, mesh objects)."""
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=self.glb)
        imported = [obj for obj in bpy.data.objects if obj not in before]
        empty = bpy.data.objects.new(f"SAO_{self.key}", None)
        bpy.context.scene.collection.objects.link(empty)
        empty.scale = (self.unit,) * 3
        for obj in imported:
            if obj.parent is None:
                obj.parent = empty
        bpy.context.view_layer.update()
        return empty, [obj for obj in imported if obj.type == 'MESH']

    @staticmethod
    def to_world(empty, p):
        """World position of a GLB point of the loaded prop."""
        return empty.matrix_world @ (GLTF_TO_BLENDER @ Vector(p))

    @staticmethod
    def direction_to_world(empty, n):
        return (empty.matrix_world.to_3x3().normalized() @ (GLTF_TO_BLENDER @ Vector(n))).normalized()
