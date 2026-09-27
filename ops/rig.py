"""Rig and solve operators (§4, §6): gtr.build_rig, gtr.clean_rig, gtr.solve_frame and gtr.clear_solve."""

import bpy

from ..core import solver
from ..rig import build
from .common import calibration_stale, report, tag_redraw


def _poll_character(cls, context):
    obj = context.scene.gtr.armature
    if obj is None or not obj.gtr_char.calibration.is_valid:
        cls.poll_message_set("Calibrate the character first")
        return False
    if context.mode not in {'OBJECT', 'POSE'}:
        cls.poll_message_set("Switch to Object or Pose Mode first")
        return False
    return True


class GTR_OT_build_rig(bpy.types.Operator):
    """Add the helper rig: an IK and a wrist-rotation constraint on each arm, switched off until a solve, and
    their empties in a GuitarRig collection. Replaces an older rig"""

    bl_idname = "gtr.build_rig"
    bl_label = "Build Rig"
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
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        messages += solver.check_messages(errors)
        if calibration_stale(context, rig.armature):
            messages.append(('WARNING', "The rig or bone map changed since calibration: calibrate again."))
        report(self, messages)
        worst = max(max(pair) for pair in errors.values()) * 1000.0
        self.report({'INFO'}, f"Built the helper rig on {rig.armature.name}. With its goals on the current pose, "
                              f"the IK reproduces the arms within {worst:.3f} mm.")
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_clean_rig(bpy.types.Operator):
    """Remove the helper rig: its constraints, its empties and the GuitarRig collection"""

    bl_idname = "gtr.clean_rig"
    bl_label = "Clean Rig"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        if settings.rig_collection is None and settings.rig_armature is None:
            cls.poll_message_set("There is no helper rig")
            return False
        return True

    def execute(self, context):
        build.clean(context.scene.gtr)
        self.report({'INFO'}, "Removed the helper rig.")
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_solve_frame(bpy.types.Operator):
    """Solve the current frame: the guitar goes on its mount and the magnets move the wrists. The arms show the
    result until the frame changes"""

    bl_idname = "gtr.solve_frame"
    bl_label = "Solve Frame"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not _poll_character(cls, context):
            return False
        settings = context.scene.gtr
        if build.find(settings) is None:
            cls.poll_message_set("Build the rig first")
            return False
        if settings.guitar_root is None:
            cls.poll_message_set("Normalise the guitar first")
            return False
        if settings.mount_source == 'NONE':
            cls.poll_message_set("Load a preset or capture the mount first")
            return False
        return True

    def execute(self, context):
        settings = context.scene.gtr
        try:
            result = solver.solve(context, build.find(settings))
        except solver.SolveError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        report(self, result.messages)
        self.report({'INFO'}, solver.summary(result, settings.magnets))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_clear_solve(bpy.types.Operator):
    """Switch the rig's constraints off, so that the arms play the mocap again"""

    bl_idname = "gtr.clear_solve"
    bl_label = "Show Mocap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not context.scene.gtr.solve_active:
            cls.poll_message_set("The rig shows no solve")
            return False
        return True

    def execute(self, context):
        build.deactivate(context.scene.gtr)
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_build_rig, GTR_OT_clean_rig, GTR_OT_solve_frame, GTR_OT_clear_solve)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
