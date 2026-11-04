"""Setup operators: gtr.auto_map_bones and gtr.calibrate."""

import bpy

from ..i18n import CONTEXT, msg, report as rpt, tip
from .. import props
from ..core import bonemap, calibrate
from .common import report, tag_redraw, target_armature


def _poll_armature(cls, context):
    obj = target_armature(context)
    if obj is None:
        cls.poll_message_set(tip("Pick the character armature first"))
        return False
    if obj.mode == 'EDIT':
        cls.poll_message_set(tip("Leave Edit Mode first"))
        return False
    return True


class GTR_OT_auto_map_bones(bpy.types.Operator):
    """Guess the bone map from VRM metadata or from VRoid, Mixamo, Rigify, MMD, Unreal and generic bone names"""

    bl_idname = "gtr.auto_map_bones"
    bl_label = "Auto-Map Bones"
    bl_translation_context = CONTEXT
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
        report(self, result.messages)
        self.report({'INFO'}, rpt(msg(
            'Mapped {found} of {slots_count} bones ({source}). Check the map, then calibrate.',
            found=found, slots_count=len(slots), source=bonemap.source_message(result.source))))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_calibrate(bpy.types.Operator):
    """Measure the character in rest pose: character frame, rest-aligned frames, ratios, axis_rot, fingertips"""

    bl_idname = "gtr.calibrate"
    bl_label = "Calibrate"
    bl_translation_context = CONTEXT
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
                self.report({'ERROR'}, rpt(text))
            return {'CANCELLED'}
        try:
            cal = props.calibrate_object(obj, context.scene)
        except calibrate.CalibrationError as exc:
            calibration.is_valid = False
            self.report({'ERROR'}, rpt(exc))
            return {'CANCELLED'}
        report(self, cal.messages)
        self.report({'INFO'}, rpt(msg(
            'Calibrated: height {height:.2f} m; ratios arm {ratio_arm:.3f}, palm {ratio_palm:.3f}, spine '
            '{ratio_spine:.3f}',
            height=cal.height, ratio_arm=cal.ratio_arm, ratio_palm=cal.ratio_palm, ratio_spine=cal.ratio_spine)))
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_auto_map_bones, GTR_OT_calibrate)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
