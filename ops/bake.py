"""Bake operators (§8, §9): gtr.bake and gtr.reclamp go through the frames one by one, as modal operators with a
progress bar when invoked from the UI (Esc cancels and changes nothing) and to the end when called from a script;
gtr.smooth_bake and gtr.remove_bake. Diagnostics (§10.6): gtr.jump_worst_frame and gtr.show_diagnostics."""

import time
import traceback

import bpy
from bpy.props import EnumProperty, IntProperty

from ..core import baker, diagnostics, keys, solver
from ..rig import build
from .common import report, tag_redraw
from .rig import poll_solve

STEP_SECONDS = 0.1          # frames are solved for this long per timer event, between redraws


class _JobOperator:
    """Runs a baker.Job: to the end in execute, a slice of frames per timer event in modal."""

    _job = None
    _timer = None

    def make_job(self, context, rig):
        raise NotImplementedError

    def _start(self, context):
        try:
            return self.make_job(context, build.find(context.scene.gtr))
        except (baker.BakeError, solver.SolveError) as exc:
            self.report({'ERROR'}, str(exc))
            return None

    def _finished(self, context, messages):
        report(self, messages)
        tag_redraw(context)
        return {'FINISHED'}

    def execute(self, context):
        job = self._start(context)
        if job is None:
            return {'CANCELLED'}
        try:
            messages = job.run(context)
        except (baker.BakeError, solver.SolveError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        return self._finished(context, messages)

    def invoke(self, context, event):
        job = self._start(context)
        if job is None:
            return {'CANCELLED'}
        self._job = job
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.progress_begin(0, 100)
        wm.modal_handler_add(self)
        self._status(context)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        job = self._job
        if event.type == 'ESC':
            self._end(context)
            job.cancel(context)
            self.report({'WARNING'}, f"{self.bl_label} cancelled at frame {job.frame}: nothing was changed.")
            return {'CANCELLED'}
        if event.type != 'TIMER':
            return {'RUNNING_MODAL'}        # the scene must not change under the job
        try:
            deadline = time.perf_counter() + STEP_SECONDS
            while not job.done and time.perf_counter() < deadline:
                job.step(context)
            if job.done:
                self._end(context)
                return self._finished(context, job.finish(context))
        except Exception as exc:
            traceback.print_exc()
            self._end(context)
            job.cancel(context)
            self.report({'ERROR'}, f"{self.bl_label} failed at frame {job.frame}: {exc}")
            return {'CANCELLED'}
        context.window_manager.progress_update(job.progress * 100.0)
        self._status(context)
        return {'RUNNING_MODAL'}

    def _status(self, context):
        job = self._job
        if context.workspace is not None:
            context.workspace.status_text_set(f"{self.bl_label}: frame {job.frame} ({job.progress:.0%}). Esc to "
                                              "cancel.")

    def _end(self, context):
        wm = context.window_manager
        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None
        wm.progress_end()
        if context.workspace is not None:
            context.workspace.status_text_set(None)


class GTR_OT_bake(_JobOperator, bpy.types.Operator):
    """Solve every frame of the range and key the arms and the guitar into GuitarBake NLA strips, with a
    GuitarRefine layer on top for your corrections. Esc cancels"""

    bl_idname = "gtr.bake"
    bl_label = "Bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return poll_solve(cls, context)

    def make_job(self, context, rig):
        return baker.BakeJob(context, rig)


class GTR_OT_reclamp(_JobOperator, bpy.types.Operator):
    """Play the bake back and, on the frames where a hand went into a barrier or the chest collider, push it out
    and solve that arm again. Esc cancels"""

    bl_idname = "gtr.reclamp"
    bl_label = "Re-clamp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not poll_solve(cls, context):
            return False
        if keys.ARM not in keys.bake_strips(context.scene.gtr.armature):
            cls.poll_message_set("Bake first")
            return False
        return True

    def make_job(self, context, rig):
        return baker.ReclampJob(context, rig)


class GTR_OT_smooth_bake(bpy.types.Operator):
    """Low-pass the baked arm and guitar keys, forward and backward so nothing lags. Re-clamp afterwards to
    restore the contacts"""

    bl_idname = "gtr.smooth_bake"
    bl_label = "Smooth"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        if not any({keys.ARM, keys.GUITAR} & set(keys.bake_strips(owner)) for owner in baker.bake_owners(settings)):
            cls.poll_message_set("Bake first")
            return False
        return True

    def execute(self, context):
        try:
            messages = baker.smooth(context)
        except baker.BakeError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        report(self, messages)
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_remove_bake(bpy.types.Operator):
    """Remove the GuitarBake and GuitarRefine tracks and the bake actions, and put back the animation and the
    guitar's parent as they were before the bake. Refine actions with keys are kept"""

    bl_idname = "gtr.remove_bake"
    bl_label = "Remove Bake"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not baker.has_bake(context.scene.gtr):
            cls.poll_message_set("There is no bake")
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        build.deactivate(context.scene.gtr)
        report(self, baker.remove_bake(context))
        tag_redraw(context)
        return {'FINISHED'}


def _poll_diagnostics(cls, context):
    if diagnostics.action_of(diagnostics.find(context.scene.gtr)) is None:
        cls.poll_message_set("Bake first: the bake records the diagnostics")
        return False
    return True


class GTR_OT_jump_worst_frame(bpy.types.Operator):
    """Go to the frame where the last bake's solve was worst by the chosen measure"""

    bl_idname = "gtr.jump_worst_frame"
    bl_label = "Jump to Worst Frame"
    bl_options = {'REGISTER'}

    metric: EnumProperty(name="Measure", items=[metric[:3] for metric in diagnostics.METRICS])
    rank: IntProperty(name="Rank", default=1, min=1, description="1 for the worst frame, 2 for the next, and so on")

    @classmethod
    def poll(cls, context):
        return _poll_diagnostics(cls, context)

    @classmethod
    def description(cls, context, properties):
        _id, name, text, _unit = diagnostics.METRIC_BY_ID[properties.metric]
        which = "the worst frame" if properties.rank == 1 else f"worst frame #{properties.rank}"
        return f"Go to {which} by {name.lower()}: {text[0].lower()}{text[1:]}"

    def execute(self, context):
        scene = context.scene
        ranked = diagnostics.ranking(diagnostics.find(scene.gtr), self.metric, self.rank)
        name = diagnostics.METRIC_BY_ID[self.metric][1].lower()
        if len(ranked) < self.rank:
            self.report({'INFO'}, f"No frame of the bake has a {name} above 0." if not ranked else
                                  f"Only {len(ranked)} frames have a {name} above 0.")
            return {'CANCELLED'}
        frame, value = ranked[self.rank - 1]
        scene.frame_set(frame)
        self.report({'INFO'}, f"Frame {frame}: {name} {diagnostics.format_value(self.metric, value)}.")
        return {'FINISHED'}


class GTR_OT_show_diagnostics(bpy.types.Operator):
    """Select the GTR_Diagnostics empty, whose curves show what the solve did on each frame in the Graph Editor"""

    bl_idname = "gtr.show_diagnostics"
    bl_label = "Select Curves"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            cls.poll_message_set("Switch to Object Mode first")
            return False
        return _poll_diagnostics(cls, context)

    def execute(self, context):
        obj = diagnostics.find(context.scene.gtr)
        if not obj.visible_get():
            self.report({'WARNING'}, f"{obj.name} is hidden or in an excluded collection: unhide it to see its "
                                     "curves.")
            return {'CANCELLED'}
        for other in context.selected_objects:
            other.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        self.report({'INFO'}, f"Selected {obj.name}: its curves are in the Graph Editor.")
        return {'FINISHED'}


CLASSES = (GTR_OT_bake, GTR_OT_reclamp, GTR_OT_smooth_bake, GTR_OT_remove_bake, GTR_OT_jump_worst_frame,
           GTR_OT_show_diagnostics)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
