"""Viewport overlay for checking the calibration, the landmarks and the mount.

Tripods show rest-aligned frames Q_b(t) (red X: character's left, green Y: up, blue Z: forward): a large one
at the hips (the character frame carried by the hips; C_char at rest) and small ones at the chest and hands.
At rest they are all parallel. Dots mark the calibrated fingertips (yellow: bone tail, orange: estimated)
and, in magenta, the neck-aim target of §5.4 on the left wrist, which shows the effect of axis_rot.
On the guitar, a cyan line runs along the aimed neck axis (neck pivot to nut) and an orange one along the
strum line. A pale tripod (X: headstock, Z: strings) shows where the chest mount puts the guitar in the
current pose. The geometry is built without the gpu module, so tests can check it in background mode.
"""

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate, landmarks, mount
from ..core.mathx import auto_scale

AXIS_COLORS = ((0.95, 0.25, 0.25, 1.0), (0.35, 0.9, 0.3, 1.0), (0.3, 0.5, 1.0, 1.0))
TIP_COLORS = {'TAIL': (1.0, 0.85, 0.2, 1.0), 'ESTIMATE': (1.0, 0.5, 0.1, 1.0)}
AIM_COLOR = (1.0, 0.3, 0.9, 1.0)
LANDMARK_LINES = (("NECK_PIVOT", "NUT", (0.2, 0.85, 0.95, 1.0)), ("STRUM_A", "STRUM_B", (1.0, 0.6, 0.15, 1.0)))
MOUNT_COLORS = tuple((0.5 + 0.5 * r, 0.5 + 0.5 * g, 0.5 + 0.5 * b, 0.6) for r, g, b, _ in AXIS_COLORS)
HIPS_AXIS_LEN = 0.25    # metres
BONE_AXIS_LEN = 0.08
MOUNT_AXIS_LEN = 0.2

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


class _Geometry:
    def __init__(self):
        self.lines, self.line_colors, self.dots, self.dot_colors = [], [], [], []

    def line(self, a, b, color):
        self.lines.extend((a, b))
        self.line_colors.extend((color, color))

    def dot(self, p, color):
        self.dots.append(p)
        self.dot_colors.append(color)

    def tripod(self, origin, frame, length, colors=AXIS_COLORS):
        for i, color in enumerate(colors):
            axis = Vector([float(j == i) for j in range(3)])
            self.line(origin, origin + frame @ axis * length, color)


def _character(geo, settings):
    obj = settings.armature
    cal = obj.gtr_char.calibration if obj is not None else None
    if cal is None or not cal.is_valid:
        return
    names = bonemap.mapping_from(obj.gtr_char.bone_map)
    unit = 1.0 / cal.metres_per_bu
    char_frame = Quaternion(cal.char_frame)

    def pose_bone(key):
        name = names.get(key, "")
        return obj.pose.bones.get(name) if name else None

    for key, length in (("hips", HIPS_AXIS_LEN), ("chest", BONE_AXIS_LEN),
                        ("hand_L", BONE_AXIS_LEN), ("hand_R", BONE_AXIS_LEN)):
        pbone = pose_bone(key)
        if pbone is not None:
            origin, frame = rest_aligned_world(obj, pbone, char_frame)
            geo.tripod(origin, frame, length * unit)

    for tip in cal.fingertips:
        pbone = obj.pose.bones.get(tip.bone)
        if pbone is not None:
            geo.dot(obj.matrix_world @ (pbone.matrix @ Vector(tip.tip_local)),
                    TIP_COLORS.get(tip.source, TIP_COLORS['TAIL']))

    hand = pose_bone("hand_L")
    if hand is not None:
        aim = aim_point(obj, settings, cal, hand)
        geo.line(obj.matrix_world @ hand.head, aim, AIM_COLOR)
        geo.dot(aim, AIM_COLOR)


def _guitar(geo, settings):
    root = settings.guitar_root
    if root is None:
        return
    found = landmarks.find(root)
    for a, b, color in LANDMARK_LINES:
        if a in found and b in found:
            geo.line(found[a].matrix_world.translation, found[b].matrix_world.translation, color)


def _mount(geo, settings, unit_scale):
    obj, root = settings.armature, settings.guitar_root
    if obj is None or root is None or settings.mount_source == 'NONE':
        return
    cal = obj.gtr_char.calibration
    if not cal.is_valid:
        return
    try:
        chest_pos, chest_frame = mount.chest_pose(obj, cal, obj.gtr_char.bone_map.chest)
        scale = mount.root_scale(root)
    except mount.MountError:
        return
    matrix = mount.mount_matrix(chest_pos, chest_frame, settings.mount_t, settings.mount_q,
                                mount.spine_factor(cal, settings.autoscale_policy), scale, cal.metres_per_bu)
    geo.tripod(matrix.translation, matrix.to_quaternion(), MOUNT_AXIS_LEN / unit_scale, MOUNT_COLORS)


def build_geometry(context):
    """(line points, line colours, dot points, dot colours) in world space, or None if there is nothing to draw."""
    settings = context.scene.gtr
    if not settings.show_overlay:
        return None
    unit_scale = context.scene.unit_settings.scale_length or 1.0
    geo = _Geometry()
    _character(geo, settings)
    _guitar(geo, settings)
    _mount(geo, settings, unit_scale)
    if not geo.lines and not geo.dots:
        return None
    return geo.lines, geo.line_colors, geo.dots, geo.dot_colors


def _draw():
    context = bpy.context
    try:
        geometry = build_geometry(context)
    except (AttributeError, KeyError, ReferenceError, ValueError, ZeroDivisionError):
        return  # the rig or guitar is being edited or deleted; the next redraw tries again
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
