"""Viewport overlay for checking the calibration, the landmarks and the mount.

Tripods show rest-aligned frames Q_b(t) (red X: character's left, green Y: up, blue Z: forward): a large one
at the hips (the character frame carried by the hips; C_char at rest) and small ones at the chest and hands.
At rest they are all parallel. Dots mark the calibrated fingertips (yellow: bone tail, orange: estimated)
and, in magenta, the neck-aim target of §5.4 on the left wrist, which shows the effect of axis_rot.
On the guitar, a cyan line runs along the aimed neck axis (neck pivot to nut) and an orange one along the
strum line. A pale tripod (X: headstock, Z: strings) shows where the chest mount puts the guitar in the
current pose.

Magnets are drawn in their hand's colour (left: blue, right: orange): lines as lines, planes as a square with
a normal, barrier planes crossed. The active magnet also shows its reach D on this character: a cylinder
around a line, a bar along the normal of a plane. While the rig shows a solve, a white line runs from each FK
wrist to its target, and each magnet that saw the hand draws its pull, from grey (weight 0) to full colour
(weight 1), red for a barrier clamp, with the weights as text. The geometry is built without the gpu module, so
tests can check it in background mode.
"""

import math

import blf
import bpy
import gpu
from bpy_extras import view3d_utils
from gpu_extras.batch import batch_for_shader
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate, landmarks, magnets, mount, solver
from ..core.mathx import auto_scale

AXIS_COLORS = ((0.95, 0.25, 0.25, 1.0), (0.35, 0.9, 0.3, 1.0), (0.3, 0.5, 1.0, 1.0))
TIP_COLORS = {'TAIL': (1.0, 0.85, 0.2, 1.0), 'ESTIMATE': (1.0, 0.5, 0.1, 1.0)}
AIM_COLOR = (1.0, 0.3, 0.9, 1.0)
LANDMARK_LINES = (("NECK_PIVOT", "NUT", (0.2, 0.85, 0.95, 1.0)), ("STRUM_A", "STRUM_B", (1.0, 0.6, 0.15, 1.0)))
MOUNT_COLORS = tuple((0.5 + 0.5 * r, 0.5 + 0.5 * g, 0.5 + 0.5 * b, 0.6) for r, g, b, _ in AXIS_COLORS)
MAGNET_COLORS = {'L': (0.3, 0.75, 1.0, 1.0), 'R': (1.0, 0.55, 0.2, 1.0)}
IDLE_COLOR = (0.55, 0.55, 0.55, 1.0)
BARRIER_COLOR = (1.0, 0.25, 0.25, 1.0)
WRIST_COLOR = (1.0, 1.0, 1.0, 1.0)
HIPS_AXIS_LEN = 0.25    # metres
BONE_AXIS_LEN = 0.08
MOUNT_AXIS_LEN = 0.2
PLANE_HALF = 0.05       # half the side of a plane magnet's square
NORMAL_LEN = 0.04
TICK_HALF = 0.01
CIRCLE_SEGMENTS = 32
LABEL_OFFSET = (12.0, -4.0)     # pixels from the wrist target to the first label line
LABEL_LINE = 15.0               # pixels between label lines

_handles = []


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

    def loop(self, points, color):
        for a, b in zip(points, points[1:] + points[:1]):
            self.line(a, b, color)

    def square(self, centre, u, v, half, color):
        corners = [centre + (u * su + v * sv) * half for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        self.loop(corners, color)
        return corners

    def circle(self, centre, u, v, radius, color):
        steps = [2.0 * math.pi * i / CIRCLE_SEGMENTS for i in range(CIRCLE_SEGMENTS)]
        points = [centre + (u * math.cos(t) + v * math.sin(t)) * radius for t in steps]
        self.loop(points, color)
        return points


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


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _plane_axes(normal, rotation):
    """Two unit vectors in a plane: the guitar's X (or else Y) axis made square to the normal, and a third."""
    for axis in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)):
        u = rotation @ Vector(axis)
        u -= normal * u.dot(normal)
        if u.length > 0.3:
            u.normalize()
            return u, normal.cross(u)
    u = normal.orthogonal().normalized()
    return u, normal.cross(u)


def _reach_scale(settings):
    """Scene units per metre of a magnet distance on the calibrated character, or None."""
    obj = settings.armature
    cal = obj.gtr_char.calibration if obj is not None else None
    if cal is not None and cal.is_valid:
        return solver.reach_scale(settings, cal)
    return None


def _line_reach(geo, feature, reach, color):
    """A cylinder of radius `reach` around a line magnet."""
    axis = feature.b - feature.a
    if axis.length < 1e-9:
        axis = Vector((0.0, 0.0, 1.0))
    u = axis.orthogonal().normalized()
    v = axis.normalized().cross(u)
    ends = [geo.circle(p, u, v, reach, color) for p in (feature.a, feature.b)]
    for i in range(0, CIRCLE_SEGMENTS, CIRCLE_SEGMENTS // 4):
        geo.line(ends[0][i], ends[1][i], color)


def _magnets(geo, context, settings, unit):
    root = settings.guitar_root
    if root is None or not settings.show_magnets or not len(settings.magnets):
        return
    result = solver.shown_result(context.scene)
    if result is not None:
        guitar = result.guitar
    else:
        location, rotation, _ = root.matrix_world.decompose()
        guitar = magnets.GuitarPose(location, rotation, rotation.copy(), root.matrix_world.to_scale())
    shapes, _ = solver.magnet_shapes(root, settings.magnets)
    reach_scale = _reach_scale(settings) or unit
    for index, shape in shapes.items():
        item = settings.magnets[index]
        feature = shape.world(guitar, item.use_default_rotation)
        color = MAGNET_COLORS[item.hand]
        reach = item.effective_distance_m * reach_scale if index == settings.active_magnet_index else None
        if feature.kind == 'LINE':
            geo.line(feature.a, feature.b, color)
            if reach:
                _line_reach(geo, feature, reach, color)
            continue
        rotation = guitar.default_rotation if item.use_default_rotation else guitar.rotation
        u, v = _plane_axes(feature.normal, rotation)
        corners = geo.square(feature.a, u, v, PLANE_HALF * unit, color)
        if not item.crossable:
            geo.line(corners[0], corners[2], color)
            geo.line(corners[1], corners[3], color)
        geo.line(feature.a, feature.a + feature.normal * (NORMAL_LEN * unit), color)
        if reach:
            ends = [feature.a + feature.normal * (sign * reach) for sign in (-1.0, 1.0)]
            geo.line(ends[0], ends[1], color)
            for end in ends:
                geo.square(end, u, v, TICK_HALF * unit, color)
    if result is None:
        return
    for side, side_result in result.sides.items():
        geo.line(side_result.fk_wrist, side_result.target, WRIST_COLOR)
        geo.dot(side_result.fk_wrist, IDLE_COLOR)
        geo.dot(side_result.target, WRIST_COLOR)
        for _index, hit in side_result.hits:
            if hit.weight <= 0.0 and not hit.holds:
                continue
            color = BARRIER_COLOR if hit.barrier else _mix(IDLE_COLOR, MAGNET_COLORS[side], hit.weight)
            geo.line(hit.point, hit.target, color)
            geo.dot(hit.target, color)


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
    _magnets(geo, context, settings, 1.0 / unit_scale)
    if not geo.lines and not geo.dots:
        return None
    return geo.lines, geo.line_colors, geo.dots, geo.dot_colors


def build_labels(context):
    """[(world position, line number, text, colour)]: the weights of the magnets in the solve the rig shows."""
    settings = context.scene.gtr
    if not settings.show_overlay or not settings.show_magnets:
        return []
    result = solver.shown_result(context.scene)
    if result is None:
        return []
    labels = []
    for side, side_result in result.sides.items():
        line = 0
        for index, hit in side_result.hits:
            if hit.weight <= 0.0 or index >= len(settings.magnets):
                continue
            state = "clamp" if hit.barrier else f"{hit.weight:.2f}"
            color = BARRIER_COLOR if hit.barrier else MAGNET_COLORS[side]
            labels.append((side_result.target, line, f"{settings.magnets[index].name}: {state}", color))
            line += 1
    return labels


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


def _draw_labels():
    context = bpy.context
    region, view = context.region, context.region_data
    if region is None or view is None:
        return
    try:
        labels = build_labels(context)
    except (AttributeError, KeyError, ReferenceError, ValueError, ZeroDivisionError):
        return
    scale = context.preferences.system.ui_scale or 1.0
    font = 0
    blf.size(font, 11.0 * scale)
    for position, line, text, color in labels:
        point = view3d_utils.location_3d_to_region_2d(region, view, position)
        if point is None:
            continue
        blf.color(font, *color)
        blf.position(font, point.x + LABEL_OFFSET[0] * scale,
                     point.y + (LABEL_OFFSET[1] - LABEL_LINE * line) * scale, 0.0)
        blf.draw(font, text)


def register():
    if not bpy.app.background:
        _handles.append(bpy.types.SpaceView3D.draw_handler_add(_draw, (), 'WINDOW', 'POST_VIEW'))
        _handles.append(bpy.types.SpaceView3D.draw_handler_add(_draw_labels, (), 'WINDOW', 'POST_PIXEL'))


def unregister():
    while _handles:
        bpy.types.SpaceView3D.draw_handler_remove(_handles.pop(), 'WINDOW')
