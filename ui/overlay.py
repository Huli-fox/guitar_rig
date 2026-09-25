"""Viewport overlay for checking the calibration.

Tripods show rest-aligned frames Q_b(t) (red X: character's left, green Y: up, blue Z: forward): a large one
at the hips (the character frame carried by the hips; C_char at rest) and small ones at the chest and hands.
At rest they are all parallel. Dots mark the calibrated fingertips (yellow: bone tail, orange: estimated)
and, in magenta, the neck-aim target of §5.4 on the left wrist, which shows the effect of axis_rot.
The geometry is built without the gpu module, so tests can check it in background mode.
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate
from ..core.mathx import auto_scale

AXIS_COLORS = ((0.95, 0.25, 0.25, 1.0), (0.35, 0.9, 0.3, 1.0), (0.3, 0.5, 1.0, 1.0))
TIP_COLORS = {'TAIL': (1.0, 0.85, 0.2, 1.0), 'ESTIMATE': (1.0, 0.5, 0.1, 1.0)}
AIM_COLOR = (1.0, 0.3, 0.9, 1.0)
HIPS_AXIS_LEN = 0.25    # metres
BONE_AXIS_LEN = 0.08

_handle = None


def rest_aligned_world(arm_obj, pbone, char_frame):
    """(head position, Q_b) of a pose bone in world space."""
    matrix = arm_obj.matrix_world @ pbone.matrix
    offset = calibrate.rest_aligned_offset(pbone.bone, char_frame)
    return matrix.translation, calibrate.rest_aligned(matrix.to_quaternion(), offset)


def aim_point(arm_obj, settings, cal, hand):
    """World position of the §5.4 aim target on the left `hand` pose bone."""
    head, frame = rest_aligned_world(arm_obj, hand, Quaternion(cal.char_frame))
    offset = Vector(settings.aim_hand_offset)
    if settings.autoscale_policy != 'NONE':
        offset = auto_scale(offset, cal.ratio_palm, 1.0)
    return head + frame @ (Quaternion(cal.axis_rot_L) @ offset) / cal.metres_per_bu


def build_geometry(context):
    """(line points, line colours, dot points, dot colours) in world space, or None if there is nothing to draw."""
    settings = context.scene.gtr
    obj = settings.armature
    if obj is None or not settings.show_overlay:
        return None
    cal = obj.gtr_char.calibration
    if not cal.is_valid:
        return None
    names = bonemap.mapping_from(obj.gtr_char.bone_map)
    unit = 1.0 / cal.metres_per_bu
    char_frame = Quaternion(cal.char_frame)
    lines, line_colors, dots, dot_colors = [], [], [], []

    def pose_bone(key):
        name = names.get(key, "")
        return obj.pose.bones.get(name) if name else None

    for key, length in (("hips", HIPS_AXIS_LEN), ("chest", BONE_AXIS_LEN),
                        ("hand_L", BONE_AXIS_LEN), ("hand_R", BONE_AXIS_LEN)):
        pbone = pose_bone(key)
        if pbone is None:
            continue
        origin, frame = rest_aligned_world(obj, pbone, char_frame)
        for i, color in enumerate(AXIS_COLORS):
            axis = Vector([float(j == i) for j in range(3)])
            lines.extend((origin, origin + frame @ axis * (length * unit)))
            line_colors.extend((color, color))

    for tip in cal.fingertips:
        pbone = obj.pose.bones.get(tip.bone)
        if pbone is not None:
            dots.append(obj.matrix_world @ (pbone.matrix @ Vector(tip.tip_local)))
            dot_colors.append(TIP_COLORS.get(tip.source, TIP_COLORS['TAIL']))

    hand = pose_bone("hand_L")
    if hand is not None:
        aim = aim_point(obj, settings, cal, hand)
        lines.extend((obj.matrix_world @ hand.head, aim))
        line_colors.extend((AIM_COLOR, AIM_COLOR))
        dots.append(aim)
        dot_colors.append(AIM_COLOR)

    if not lines and not dots:
        return None
    return lines, line_colors, dots, dot_colors


def _draw():
    context = bpy.context
    try:
        geometry = build_geometry(context)
    except (AttributeError, KeyError, ReferenceError, ValueError):
        return  # the rig is being edited or deleted; the next redraw tries again
    if geometry is None:
        return
    lines, line_colors, dots, dot_colors = geometry
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('NONE')
    if lines:
        shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
        shader.uniform_float("viewportSize", gpu.state.viewport_get()[2:])
        shader.uniform_float("lineWidth", 2.0)
        batch_for_shader(shader, 'LINES', {"pos": lines, "color": line_colors}).draw(shader)
    if dots:
        gpu.state.point_size_set(7.0)
        shader = gpu.shader.from_builtin('POINT_FLAT_COLOR')
        batch_for_shader(shader, 'POINTS', {"pos": dots, "color": dot_colors}).draw(shader)
        gpu.state.point_size_set(1.0)
    gpu.state.blend_set('NONE')


def register():
    global _handle
    if not bpy.app.background:
        _handle = bpy.types.SpaceView3D.draw_handler_add(_draw, (), 'WINDOW', 'POST_VIEW')


def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
