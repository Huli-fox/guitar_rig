"""Setup operators: gtr.auto_map_bones and gtr.calibrate."""

import bpy

from .. import props
from ..core import bonemap, calibrate


def target_armature(context):
    """The scene's character armature, or the active object if it is an armature."""
    obj = context.scene.gtr.armature
    if obj is None:
        active = context.active_object
        if active is not None and active.type == 'ARMATURE':
            obj = active
    return obj


def _poll_armature(cls, context):
    obj = target_armature(context)
    if obj is None:
        cls.poll_message_set("Pick the character armature first")
        return False
    if obj.mode == 'EDIT':
        cls.poll_message_set("Leave Edit Mode first")
        return False
    return True


def _report(op, messages):
    for level, text in messages:
        op.report({'WARNING'} if level in {'ERROR', 'WARNING'} else {'INFO'}, text)


def _tag_redraw(context):
    screen = context.screen
    for area in (screen.areas if screen is not None else ()):
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class GTR_OT_auto_map_bones(bpy.types.Operator):
    """Guess the bone map from VRM metadata or from VRoid, Mixamo, Rigify, MMD, Unreal and generic bone names"""

    bl_idname = "gtr.auto_map_bones"
    bl_label = "Auto-Map Bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_armature(cls, context)

    def execute(self, context):
        obj = target_armature(context)
        context.scene.gtr.armature = obj
        result = bonemap.guess(obj)
        bone_map = obj.gtr_char.bone_map
        for key, name in result.mapping.items():
            setattr(bone_map, key, name)
        bone_map.source = result.source
        slots = [slot for slot in bonemap.SLOTS if slot.group != 'CHAIN']
        found = sum(1 for slot in slots if result.mapping[slot.key])
        _report(self, result.messages)
        self.report({'INFO'}, f"Mapped {found} of {len(slots)} bones ({result.source}). "
                              "Check the map, then calibrate.")
        _tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_calibrate(bpy.types.Operator):
    """Measure the character in rest pose: character frame, rest-aligned frames, ratios, axis_rot, fingertips"""

    bl_idname = "gtr.calibrate"
    bl_label = "Calibrate"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_armature(cls, context)

    def execute(self, context):
        obj = target_armature(context)
        context.scene.gtr.armature = obj
        calibration = obj.gtr_char.calibration
        mapping = bonemap.mapping_from(obj.gtr_char.bone_map)
        errors = [text for level, text in bonemap.validate(obj.data.bones, mapping) if level == 'ERROR']
        if errors:
            calibration.is_valid = False
            for text in errors:
                self.report({'ERROR'}, text)
            return {'CANCELLED'}
        try:
            cal = props.calibrate_object(obj, context.scene)
        except calibrate.CalibrationError as exc:
            calibration.is_valid = False
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        _report(self, cal.messages)
        self.report({'INFO'}, f"Calibrated: height {cal.height:.2f} m; ratios arm {cal.ratio_arm:.3f}, "
                              f"palm {cal.ratio_palm:.3f}, spine {cal.ratio_spine:.3f}")
        _tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_auto_map_bones, GTR_OT_calibrate)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
