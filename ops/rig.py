"""Rig and solve operators (§4, §6): gtr.build_rig, gtr.clean_rig, gtr.solve_frame and gtr.clear_solve; the range
overrides' gtr.range_add and gtr.range_remove (§5.8)."""

import bpy

from ..i18n import CONTEXT, msg, report as rpt, tip
from ..core import solver
from ..rig import build
from .common import calibration_stale, report, tag_redraw


def _poll_character(cls, context):
    obj = context.scene.gtr.armature
    if obj is None or not obj.gtr_char.calibration.is_valid:
        cls.poll_message_set(tip("Calibrate the character first"))
        return False
    if context.mode not in {'OBJECT', 'POSE'}:
        cls.poll_message_set(tip("Switch to Object or Pose Mode first"))
        return False
    return True


def poll_solve(cls, context):
    """Whether the scene is ready to solve: calibrated, rig built, guitar normalised, mount set."""
    if not _poll_character(cls, context):
        return False
    settings = context.scene.gtr
    if build.find(settings) is None:
        cls.poll_message_set(tip("Build the rig first"))
        return False
    if settings.guitar_root is None:
        cls.poll_message_set(tip("Normalise the guitar first"))
        return False
    if settings.mount_source == 'NONE':
        cls.poll_message_set(tip("Load a preset or capture the mount first"))
        return False
    return True


class GTR_OT_build_rig(bpy.types.Operator):
    """Add the helper rig: an IK and a wrist-rotation constraint on each arm, switched off until a solve, and
    their empties in a GuitarRig collection. Replaces an older rig"""

    bl_idname = "gtr.build_rig"
    bl_label = "Build Rig"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll_character(cls, context)

    def execute(self, context):
        settings = context.scene.gtr
        try:
            rig, messages = build.build(context, settings)
            errors = solver.check_rig(context, rig)
        except (build.RigError, solver.SolveError) as exc:
            self.report({'ERROR'}, rpt(exc))
            return {'CANCELLED'}
        messages += solver.check_messages(errors)
        if calibration_stale(context, rig.armature):
            messages.append(('WARNING', msg("The rig or bone map changed since calibration: calibrate again.")))
        report(self, messages)
        worst = max(max(pair) for pair in errors.values()) * 1000.0
        self.report({'INFO'}, rpt(msg(
            'Built the helper rig on {name}. With its goals on the current pose, the IK reproduces the arms '
            'within {worst:.3f} mm.',
            name=rig.armature.name, worst=worst)))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_clean_rig(bpy.types.Operator):
    """Remove the helper rig: its constraints, its empties and the GuitarRig collection"""

    bl_idname = "gtr.clean_rig"
    bl_label = "Clean Rig"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        if settings.rig_collection is None and settings.rig_armature is None:
            cls.poll_message_set(tip("There is no helper rig"))
            return False
        return True

    def execute(self, context):
        build.clean(context.scene.gtr)
        self.report({'INFO'}, rpt("Removed the helper rig."))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_solve_frame(bpy.types.Operator):
    """Solve the current frame: the guitar goes on its mount and the magnets move the wrists. The arms show the
    result until the frame changes"""

    bl_idname = "gtr.solve_frame"
    bl_label = "Solve Frame"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_solve(cls, context)

    def execute(self, context):
        settings = context.scene.gtr
        try:
            result = solver.solve(context, build.find(settings))
        except solver.SolveError as exc:
            self.report({'ERROR'}, rpt(exc))
            return {'CANCELLED'}
        report(self, result.messages)
        self.report({'INFO'}, rpt(solver.summary(result, settings.magnets)))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_clear_solve(bpy.types.Operator):
    """Switch the rig's constraints off, so that the arms play the mocap again"""

    bl_idname = "gtr.clear_solve"
    bl_label = "Show Mocap"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.scene.gtr.solve_active:
            cls.poll_message_set(tip("The rig shows no solve"))
            return False
        return True

    def execute(self, context):
        build.deactivate(context.scene.gtr)
        tag_redraw(context)
        return {'FINISHED'}


RANGE_LENGTH = 48           # frames a new range override spans, from the current frame


class GTR_OT_range_add(bpy.types.Operator):
    """Add a frame range, from the current frame, solved in the other mode than the scene's. Lower ranges win
    where ranges overlap"""

    bl_idname = "gtr.range_add"
    bl_label = "Add Range Override"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        settings = scene.gtr
        item = settings.range_overrides.add()
        item.frame_start = scene.frame_current
        item.frame_end = max(scene.frame_current, min(scene.frame_current + RANGE_LENGTH - 1, scene.frame_end))
        item.mode = 'ALIGN' if settings.mode == 'FOLLOW' else 'FOLLOW'
        settings.active_range_index = len(settings.range_overrides) - 1
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_range_remove(bpy.types.Operator):
    """Remove the active range override"""

    bl_idname = "gtr.range_remove"
    bl_label = "Remove Range Override"
    bl_translation_context = CONTEXT
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        return 0 <= settings.active_range_index < len(settings.range_overrides)

    def execute(self, context):
        settings = context.scene.gtr
        settings.range_overrides.remove(settings.active_range_index)
        settings.active_range_index = max(0, min(settings.active_range_index, len(settings.range_overrides) - 1))
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_build_rig, GTR_OT_clean_rig, GTR_OT_solve_frame, GTR_OT_clear_solve, GTR_OT_range_add,
           GTR_OT_range_remove)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
