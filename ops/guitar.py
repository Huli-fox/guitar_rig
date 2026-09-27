"""Guitar operators: frame normalisation and flips (§3.1), presets and landmarks (§3.2)."""

import math
import os

import bpy
import numpy as np
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Matrix, Vector

from ..core import calibrate, guitar_frame, landmarks, mount, presets
from ..core.magnets import apply_mode
from .common import report, tag_redraw

ROLE_ITEMS = tuple((role.id, role.label, role.description) for role in landmarks.ROLES)
ROOT_NAME = "GTR_ROOT"


# Guitar objects ------------------------------------------------------------------------------------------------

def _belongs_to(obj, armature):
    """Whether mesh `obj` is part of the character `armature`: below it, or deformed by it."""
    if armature is None:
        return False
    return (any(parent is armature for parent in _ancestors(obj))
            or any(modifier.type == 'ARMATURE' and modifier.object is armature for modifier in obj.modifiers))


def selected_meshes(context):
    """Selected meshes and the meshes below selected objects, leaving out the character's meshes.

    Only the character armature's meshes are left out: a guitar may be rigged with an armature of its own.
    """
    character = context.scene.gtr.armature
    meshes = []
    for obj in context.selected_objects:
        for item in (obj, *obj.children_recursive):
            if item.type == 'MESH' and not _belongs_to(item, character) and item not in meshes:
                meshes.append(item)
    return meshes


def root_meshes(root):
    return [obj for obj in root.children_recursive if obj.type == 'MESH']


def _top(obj, root=None):
    """The topmost ancestor of `obj`, or its ancestor right below `root`."""
    while obj.parent is not None and obj.parent is not root:
        obj = obj.parent
    return obj


def _ancestors(obj):
    while obj.parent is not None:
        obj = obj.parent
        yield obj


def set_root_matrix(root, matrix):
    """Give GTR_ROOT a new world matrix while its children, except landmarks, stay where they are in world space.

    The children's own transforms are kept; the change goes into their parent inverse matrices.
    """
    old = root.matrix_world.copy()
    correction = matrix.inverted() @ old
    for child in root.children:
        if landmarks.role_of(child) is None:
            child.matrix_parent_inverse = correction @ child.matrix_parent_inverse
    root.matrix_world = matrix


def move_root(context, root, matrix):
    """set_root_matrix, keeping a captured mount on the guitar (see mount.rebase)."""
    old = root.matrix_world.copy()
    set_root_matrix(root, matrix)
    settings = context.scene.gtr
    if settings.mount_source != 'CAPTURE' or root is not settings.guitar_root:
        return
    obj = settings.armature
    cal = obj.gtr_char.calibration if obj is not None else None
    factor = mount.spine_factor(cal, settings.autoscale_policy) if cal is not None and cal.is_valid else 1.0
    metres = cal.metres_per_bu if cal is not None and cal.is_valid else metres_per_unit(context)
    settings.mount_t, settings.mount_q = mount.rebase(settings.mount_t, settings.mount_q, old, matrix, factor, metres)


def metres_per_unit(context):
    scale = context.scene.unit_settings.scale_length
    return scale if scale > 0.0 else 1.0


def root_metres(context, root):
    """Metres per GTR_ROOT local unit."""
    return float(np.mean(root.matrix_world.to_scale())) * metres_per_unit(context)


def preset_for(context, root):
    """The preset the guitar was fitted with, or the scene's chosen preset."""
    return presets.load(root.gtr_guitar.preset or context.scene.gtr.preset)


def refit(context, root, preset, create=False):
    """Fit `preset` to the guitar below GTR_ROOT: move GTR_ROOT to the preset origin and place the landmarks.

    Existing landmarks are always re-placed; missing ones are created only with `create`. Returns the Fit.
    """
    meshes = root_meshes(root)
    if not meshes:
        raise presets.PresetError("GTR_ROOT has no meshes below it: normalise the guitar first.")
    context.view_layer.update()
    geometry = guitar_frame.gather(meshes, context.evaluated_depsgraph_get(), root.matrix_world.inverted())
    measurements = guitar_frame.measure_geometry(geometry)
    fitted = presets.fit(preset.reference, measurements)
    move_root(context, root, root.matrix_world @ Matrix.Translation(Vector(fitted.origin)))
    existing = landmarks.find(root)
    for role, spec in preset.landmarks.items():
        if role not in landmarks.ROLE_BY_ID:
            fitted.messages.append(('WARNING', f"The preset has an unknown landmark role {role!r}."))
            continue
        if create or role in existing:
            normal = fitted.normal(spec.normal) if spec.normal is not None else None
            landmarks.place(root, role, fitted.point(spec.position), normal)
    context.view_layer.update()

    info = root.gtr_guitar
    info.is_root = True
    info.length_m = measurements.length * root_metres(context, root)
    info.neck_found = measurements.neck is not None
    info.fit_method = fitted.method
    info.fit_scale = fitted.scale * root_metres(context, root)
    info.preset = preset.id
    return fitted


def _store_detection(info, detection, extra=()):
    info.confidence = detection.confidence
    info.messages = calibrate.format_messages(list(detection.messages) + list(extra))


def _poll_root(cls, context):
    root = context.scene.gtr.guitar_root
    if root is None:
        cls.poll_message_set("Normalise the guitar first")
        return False
    if context.mode != 'OBJECT':
        cls.poll_message_set("Switch to Object Mode first")
        return False
    return True


# Frame ---------------------------------------------------------------------------------------------------------

class GTR_OT_normalize_frame(bpy.types.Operator):
    """Find the guitar frame of the selected meshes (+X toward the headstock, +Z out of the strings), parent
    them to GTR_ROOT with that frame, and move GTR_ROOT to the preset origin"""

    bl_idname = "gtr.normalize_frame"
    bl_label = "Normalise Frame"
    bl_options = {'REGISTER', 'UNDO'}

    real_length: FloatProperty(
        name="Real Length (m)", default=0.0, min=0.0, soft_max=2.0, precision=3,
        description="Scale GTR_ROOT so that the guitar is this long, in metres; 0 keeps its size")

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Switch to Object Mode first")
            return False
        if not selected_meshes(context) and context.scene.gtr.guitar_root is None:
            cls.poll_message_set("Select the guitar meshes first")
            return False
        return True

    def execute(self, context):
        settings = context.scene.gtr
        root = settings.guitar_root
        meshes = selected_meshes(context)
        if root is not None:
            meshes = list(dict.fromkeys(root_meshes(root) + meshes))
        if not meshes:
            self.report({'ERROR'}, "Select the guitar meshes first.")
            return {'CANCELLED'}
        try:
            preset = presets.load(root.gtr_guitar.preset if root is not None and root.gtr_guitar.preset
                                  else settings.preset)
            geometry = guitar_frame.gather(meshes, context.evaluated_depsgraph_get())
            samples = guitar_frame.sample_surface(geometry)
            detection = guitar_frame.detect(samples, geometry)
        except (guitar_frame.FrameError, presets.PresetError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        rotation = Matrix(detection.axes.tolist()).to_quaternion()
        if root is None:
            root = bpy.data.objects.new(ROOT_NAME, None)
            root.empty_display_type = 'ARROWS'
            collections = _top(meshes[0]).users_collection or (context.scene.collection,)
            collections[0].objects.link(root)
            root.matrix_world = Matrix.LocRotScale(Vector(samples.points.mean(axis=0)), rotation, None)
            context.view_layer.update()
        ancestors = {root, *_ancestors(root)}
        for top in dict.fromkeys(_top(mesh, root) for mesh in meshes):
            if top not in ancestors and top.parent is not root:
                top.parent = root
                top.matrix_parent_inverse = root.matrix_world.inverted()
        location, _, scale = root.matrix_world.decompose()
        move_root(context, root, Matrix.LocRotScale(location, rotation, scale))
        if self.real_length > 0.0:
            length = detection.measurements.length * metres_per_unit(context)   # world metres
            root.matrix_world = Matrix.LocRotScale(location, rotation, scale * (self.real_length / length))
        root.empty_display_size = 0.15 / root_metres(context, root)
        settings.guitar_root = root

        try:
            fitted = refit(context, root, preset)
        except presets.PresetError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        _store_detection(root.gtr_guitar, detection, fitted.messages)
        report(self, detection.messages + fitted.messages)
        length = root.gtr_guitar.length_m
        self.report({'INFO'}, f"Guitar frame found ({detection.confidence.lower()} confidence); the guitar is "
                              f"{length:.2f} m long. Check the axes, then load a preset.")
        if not 0.4 <= length <= 1.6:
            self.report({'WARNING'}, f"The guitar is {length:.2f} m long: use Real Length to scale it to real size.")
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_flip_frame(bpy.types.Operator):
    """Turn the guitar frame half a turn (the guitar stays in place) and fit the landmarks again"""

    bl_idname = "gtr.flip_frame"
    bl_label = "Flip Frame"
    bl_options = {'REGISTER', 'UNDO'}

    axis: EnumProperty(
        name="Axis",
        items=(('X', "Flip X", "Swap the headstock and body ends (half turn about Z)"),
               ('Z', "Flip Z", "Swap the string face and the back (half turn about X)")))

    @classmethod
    def poll(cls, context):
        return _poll_root(cls, context)

    def execute(self, context):
        root = context.scene.gtr.guitar_root
        about = 'Z' if self.axis == 'X' else 'X'
        move_root(context, root, root.matrix_world @ Matrix.Rotation(math.pi, 4, about))
        try:
            fitted = refit(context, root, preset_for(context, root))
        except presets.PresetError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        info = root.gtr_guitar
        info.confidence = 'HIGH'
        info.messages = calibrate.format_messages([('INFO', f"{self.axis} flipped by hand.")] + fitted.messages)
        report(self, fitted.messages)
        tag_redraw(context)
        return {'FINISHED'}


# Presets -------------------------------------------------------------------------------------------------------

def apply_preset(op, context, preset, magnets=True, mount=True, aim_wrist=True):
    settings = context.scene.gtr
    root = settings.guitar_root
    fitted = refit(context, root, preset, create=True)
    messages = list(fitted.messages)
    found = landmarks.find(root)
    for role in landmarks.missing(root):
        messages.append(('WARNING', f"The preset has no {role.label} landmark: add it by hand."))
    if magnets:
        messages += presets.store_magnets(settings.magnets, preset.magnets, found, fitted)
        apply_mode(settings, settings.mode)
        settings.active_magnet_index = 0
    if mount and preset.mount_t is not None:
        settings.mount_t = preset.mount_t
        settings.mount_q = preset.mount_q
        settings.mount_source = 'PRESET'
        settings.mount_preset = preset.name
        messages.append(('INFO', "The preset mount is only an estimate: pose the guitar on the character and "
                                 "use Capture Mount."))
    if aim_wrist:
        if preset.aim_hand_offset is not None:
            settings.aim_hand_offset = preset.aim_hand_offset
        if preset.wrist_offset is not None:
            settings.wrist_offset = preset.wrist_offset
        if preset.wrist_blend is not None:
            settings.wrist_blend = preset.wrist_blend
    if not preset.verified:
        messages.append(('WARNING', f"The {preset.name} preset is not verified against its source: check it."))
    report(op, messages)
    scale = root.gtr_guitar.fit_scale
    op.report({'INFO'}, f"Loaded {preset.name}: fitted to the {'neck' if fitted.method == 'NECK' else 'bounds'} "
                        f"(×{scale[0]:.2f} long, ×{scale[1]:.2f} wide, ×{scale[2]:.2f} deep). Check the landmarks.")
    tag_redraw(context)


class _LoadPresetOptions:
    magnets: BoolProperty(name="Magnets", default=True, description="Replace the magnet list with the preset's")
    mount: BoolProperty(name="Mount", default=True,
                        description="Replace the mount with the preset's estimate (off when the mount was captured)")
    aim_wrist: BoolProperty(name="Aim and Wrist", default=True,
                            description="Use the preset's aim hand offset and wrist rotation")

    def _set_defaults(self, context):
        if not self.properties.is_property_set("mount"):
            self.mount = context.scene.gtr.mount_source != 'CAPTURE'

    def _apply(self, context, source):
        try:
            apply_preset(self, context, presets.load(source), self.magnets, self.mount, self.aim_wrist)
        except presets.PresetError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return {'FINISHED'}


class GTR_OT_load_preset(_LoadPresetOptions, bpy.types.Operator):
    """Fit the chosen preset to the guitar: landmarks, magnets, mount estimate, aim and wrist settings"""

    bl_idname = "gtr.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_root(cls, context)

    def invoke(self, context, event):
        self._set_defaults(context)
        return self.execute(context)

    def execute(self, context):
        self._set_defaults(context)
        return self._apply(context, context.scene.gtr.preset)


class GTR_OT_load_preset_file(_LoadPresetOptions, bpy.types.Operator, ImportHelper):
    """Fit a preset file to the guitar: landmarks, magnets, mount estimate, aim and wrist settings"""

    bl_idname = "gtr.load_preset_file"
    bl_label = "Load Preset File"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return _poll_root(cls, context)

    def execute(self, context):
        self._set_defaults(context)
        return self._apply(context, os.path.abspath(bpy.path.abspath(self.filepath)))


class GTR_OT_save_preset(bpy.types.Operator, ExportHelper):
    """Save the landmarks, magnets, mount, aim and wrist settings as a preset file for other guitars"""

    bl_idname = "gtr.save_preset"
    bl_label = "Save Preset"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    name: StringProperty(name="Name", default="My Guitar")

    @classmethod
    def poll(cls, context):
        return _poll_root(cls, context)

    def execute(self, context):
        settings = context.scene.gtr
        root = settings.guitar_root
        found = landmarks.find(root)
        if not found:
            self.report({'ERROR'}, "There are no landmarks to save.")
            return {'CANCELLED'}
        context.view_layer.update()
        geometry = guitar_frame.gather(root_meshes(root), context.evaluated_depsgraph_get(),
                                       root.matrix_world.inverted())
        measurements = guitar_frame.measure_geometry(geometry)
        unit = root_metres(context, root)
        data = {
            "format": presets.FORMAT, "name": self.name, "description": "",
            "source": f"Saved from {os.path.basename(bpy.data.filepath) or 'an unsaved file'}", "verified": False,
            "notes": [], "unit_m": unit, "frame": [1.0, 0.0, 0.0, 0.0],
            "reference": measurements.scaled(unit).as_dict(),
            "landmarks": {},
        }
        for role in landmarks.ROLES:
            obj = found.get(role.id)
            if obj is None:
                continue
            entry = {"position": list(landmarks.local_position(root, obj))}
            if role.kind == 'PLANE':
                entry["normal"] = list(landmarks.local_normal(root, obj))
            data["landmarks"][role.id] = entry
        if settings.mount_source != 'NONE':
            data["mount"] = {"offset_m": list(settings.mount_t), "rotation": list(settings.mount_q)}
        data["aim"] = {"offset_m": list(settings.aim_hand_offset)}
        data["wrist"] = {"rotation": list(settings.wrist_offset), "weight": settings.wrist_blend}
        data["magnets"] = [presets.magnet_dict(item, landmarks.role_of, unit) for item in settings.magnets]
        path = bpy.path.abspath(self.filepath)
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(presets.dumps(presets.rounded(data)))
        except OSError as exc:
            self.report({'ERROR'}, f"Cannot write {path}: {exc.strerror or exc}.")
            return {'CANCELLED'}
        self.report({'INFO'}, f"Saved the preset to {path}.")
        return {'FINISHED'}


# Landmarks -----------------------------------------------------------------------------------------------------

class GTR_OT_select_landmark(bpy.types.Operator):
    """Select the landmark, or add it at the 3D cursor if it does not exist"""

    bl_idname = "gtr.select_landmark"
    bl_label = "Select Landmark"
    bl_options = {'REGISTER', 'UNDO'}

    role: EnumProperty(name="Role", items=ROLE_ITEMS)

    @classmethod
    def poll(cls, context):
        return _poll_root(cls, context)

    @classmethod
    def description(cls, context, properties):
        return landmarks.ROLE_BY_ID[properties.role].description

    def execute(self, context):
        root = context.scene.gtr.guitar_root
        obj = landmarks.find(root).get(self.role)
        if obj is None:
            position = root.matrix_world.inverted() @ context.scene.cursor.location
            obj = landmarks.place(root, self.role, position)
            self.report({'INFO'}, f"Added {obj.name} at the 3D cursor.")
        if not obj.visible_get():
            self.report({'WARNING'}, f"{obj.name} is hidden or in an excluded collection.")
            return {'FINISHED'}
        for other in context.selected_objects:
            other.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}


CLASSES = (GTR_OT_normalize_frame, GTR_OT_flip_frame, GTR_OT_load_preset, GTR_OT_load_preset_file,
           GTR_OT_save_preset, GTR_OT_select_landmark)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
