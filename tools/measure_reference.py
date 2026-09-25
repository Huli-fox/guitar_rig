"""Measure a preset's reference prop and store the result in the preset file.

    blender -b --factory-startup --python tools/measure_reference.py -- PRESET_ID GLB_PATH [--write]

Imports the GLB, runs the guitar-frame normaliser on it in the GLB's own coordinates (glTF, Y up), and prints
the preset's "frame" (the rotation from GLB axes to the normalised frame) and "reference" (the normaliser's
measurements in metres, relative to the GLB origin). With --write, both entries are replaced in
presets/PRESET_ID.json and the rest of the file is left as it is.
"""

import json
import os
import re
import sys

import bpy
import numpy as np
from mathutils import Matrix

ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(ADDON_DIR))

from guitar_rig.core import guitar_frame, presets  # noqa: E402

# Blender world -> glTF coordinates (the importer turns glTF's Y up into Blender's Z up).
BLENDER_TO_GLTF = np.array(((1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, -1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))


def measure_glb(path):
    """(frame quaternion, Measurements in GLB units, Detection) of the GLB at `path`."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    geometry = guitar_frame.gather(meshes, bpy.context.evaluated_depsgraph_get(), BLENDER_TO_GLTF)
    samples = guitar_frame.sample_surface(geometry)
    detection = guitar_frame.detect(samples, geometry)
    frame = Matrix(detection.axes.T.tolist()).to_quaternion()
    return frame, detection.measurements, detection


def _rounded(value, digits=6):
    if isinstance(value, dict):
        return {k: _rounded(v, digits) for k, v in value.items()}
    if isinstance(value, list):
        return [_rounded(v, digits) for v in value]
    return round(value, digits) if isinstance(value, float) else value


def _replace_entry(text, key, value_text):
    """Replace the JSON value of top-level `key` (a list or an object) in `text`."""
    match = re.search(rf'\n  "{key}": ', text)
    if match is None:
        raise ValueError(f"no {key!r} entry")
    start = match.end()
    opening = text[start]
    closing = {"[": "]", "{": "}"}[opening]
    depth = 0
    for end in range(start, len(text)):
        depth += {opening: 1, closing: -1}.get(text[end], 0)
        if depth == 0:
            return text[:start] + value_text + text[end + 1:]
    raise ValueError(f"unbalanced {key!r} entry")


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    preset_id, glb = args[0], args[1]
    path = presets.builtin_path(preset_id)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    unit = presets._unit(json.loads(text))

    frame, measurements, detection = measure_glb(glb)
    reference = _rounded(measurements.scaled(unit).as_dict())
    frame_text = json.dumps(_rounded(list(frame), 8))
    reference_text = "{\n" + ",\n".join(f'    "{k}": {json.dumps(v)}' for k, v in reference.items()) + "\n  }"
    print("confidence", detection.confidence)
    print('"frame":', frame_text)
    print('"reference":', reference_text)
    if "--write" in args:
        text = _replace_entry(text, "frame", frame_text)
        text = _replace_entry(text, "reference", reference_text)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote", path)


main()
