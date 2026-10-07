"""Mocap prep operators (mocap_prep_plan §7): gtr.apply_prep goes through the frames one by one, as a modal
operator with a progress bar when invoked from the UI (Esc cancels and changes nothing) and to the end when called
from a script; gtr.remove_prep and gtr.toggle_prep (Show Original)."""

import bpy
from bpy.props import BoolProperty

from ..core import keys, prepjob
from ..rig import build
from .bake import _JobOperator
from .common import report, tag_redraw

_support = {}       # (armature session_uid, bone count, bone map) -> (supported, messages)


def support(obj):
    """(whether Prep can run on armature `obj`, messages about what it will leave out), cached."""
    bone_map = obj.gtr_char.bone_map
    key = (obj.session_uid, len(obj.data.bones), bone_map.chest,
           tuple(getattr(bone_map, f"{kind}_{side}") for kind in ("upper_arm", "forearm", "hand") for side in "LR"))
    if key not in _support:
        if len(_support) > 16:
            _support.clear()
        try:
            _support[key] = (True, prepjob.find_bones(obj).messages)
        except prepjob.PrepError as exc:
            _support[key] = (False, [('INFO', str(exc))])
    return _support[key]


def poll_prep(cls, context):
    obj = context.scene.gtr.armature
    if obj is None or not obj.gtr_char.calibration.is_valid:
        cls.poll_message_set("Calibrate first")
        return False
    if context.mode not in {'OBJECT', 'POSE'}:
        cls.poll_message_set("Switch to Object or Pose Mode first")
        return False
    if not support(obj)[0]:
        cls.poll_message_set(prepjob.NOT_MMD)
        return False
    return True


def _poll_layer(cls, context):
    if not keys.has_prep(context.scene.gtr.armature):
        cls.poll_message_set("Apply Prep first")
        return False
    return True


class GTR_OT_apply_prep(_JobOperator, bpy.types.Operator):
    """Touch up the mocap before the bake: wider and crisper picking strokes, an arm swing, crisp fretting
    fingers and the forearm roll on the twist bone. Reads the original mocap and writes a GuitarPrep NLA layer,
    which the solve and the bake then read. Esc cancels"""

    bl_idname = "gtr.apply_prep"
    bl_label = "Apply Prep"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_prep(cls, context)

    def make_job(self, context, rig):
        return prepjob.PrepJob(context, rig)


class GTR_OT_remove_prep(bpy.types.Operator):
    """Remove the GuitarPrep layer and its action: the solve and the bake read the original mocap again. The bake
    stays"""

    bl_idname = "gtr.remove_prep"
    bl_label = "Remove Prep"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_layer(cls, context)

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        build.deactivate(context.scene.gtr)
        report(self, prepjob.remove(context))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_toggle_prep(bpy.types.Operator):
    """Mute or unmute the GuitarPrep layer, to compare the prepped motion with the original"""

    bl_idname = "gtr.toggle_prep"
    bl_label = "Show Original"
    bl_options = {'REGISTER', 'UNDO'}

    original: BoolProperty(name="Original", description="Show the original mocap (mute the prep layer)")

    @classmethod
    def poll(cls, context):
        return _poll_layer(cls, context)

    def execute(self, context):
        build.deactivate(context.scene.gtr)
        prepjob.show_original(context, self.original)
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_apply_prep, GTR_OT_remove_prep, GTR_OT_toggle_prep)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
