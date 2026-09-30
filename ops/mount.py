"""Mount and wrist operators (§5.3, §5.7): place the guitar on the chest mount, Capture Mount and Capture Wrist
Offset."""

import bpy
from mathutils import Quaternion

from ..core import calibrate, mount, wrist
from ..core.solver import FRET_SIDE
from .common import calibration_stale, tag_redraw


def _mount_inputs(context):
    """(armature, calibration, chest bone, GTR_ROOT) or raise MountError."""
    settings = context.scene.gtr
    obj, root = settings.armature, settings.guitar_root
    if obj is None:
        raise mount.MountError("Pick the character armature first.")
    if root is None:
        raise mount.MountError("Normalise the guitar first.")
    cal = obj.gtr_char.calibration
    if not cal.is_valid:
        raise mount.MountError("Calibrate the character first.")
    return obj, cal, obj.gtr_char.bone_map.chest, root


def _poll(cls, context, need_mount):
    settings = context.scene.gtr
    if settings.armature is None or not settings.armature.gtr_char.calibration.is_valid:
        cls.poll_message_set("Calibrate the character first")
        return False
    if settings.guitar_root is None:
        cls.poll_message_set("Normalise the guitar first")
        return False
    if need_mount and settings.mount_source == 'NONE':
        cls.poll_message_set("Load a preset or capture the mount first")
        return False
    if context.mode not in {'OBJECT', 'POSE'}:
        cls.poll_message_set("Switch to Object or Pose Mode first")
        return False
    return True


class GTR_OT_place_on_mount(bpy.types.Operator):
    """Move the guitar to its chest mount for the current frame's pose"""

    bl_idname = "gtr.place_on_mount"
    bl_label = "Place on Mount"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll(cls, context, True)

    def execute(self, context):
        settings = context.scene.gtr
        try:
            obj, cal, chest, root = _mount_inputs(context)
            context.view_layer.update()
            chest_pos, chest_frame = mount.chest_pose(obj, cal, chest)
            matrix = mount.mount_matrix(chest_pos, chest_frame, settings.mount_t, settings.mount_q,
                                        mount.spine_factor(cal, settings.autoscale_policy),
                                        mount.root_scale(root), cal.metres_per_bu)
        except mount.MountError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        root.matrix_world = matrix
        if calibration_stale(context, obj):
            self.report({'WARNING'}, "The rig or bone map changed since calibration: calibrate again.")
        animation = root.animation_data
        if animation is not None and (animation.action is not None or animation.nla_tracks):
            self.report({'WARNING'}, "GTR_ROOT is animated: its animation moves it back on the next frame change.")
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_capture_mount(bpy.types.Operator):
    """Store where the guitar sits relative to the chest in the current frame's pose as the mount. Pose the
    guitar on the character first (move and rotate GTR_ROOT)"""

    bl_idname = "gtr.capture_mount"
    bl_label = "Capture Mount"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _poll(cls, context, False)

    def execute(self, context):
        settings = context.scene.gtr
        try:
            obj, cal, chest, root = _mount_inputs(context)
            mount.root_scale(root)
            context.view_layer.update()
            chest_pos, chest_frame = mount.chest_pose(obj, cal, chest)
        except mount.MountError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        mount_t, mount_q = mount.capture(chest_pos, chest_frame, root.matrix_world,
                                         mount.spine_factor(cal, settings.autoscale_policy), cal.metres_per_bu)
        settings.mount_t = mount_t
        settings.mount_q = mount_q
        settings.mount_source = 'CAPTURE'
        settings.mount_frame = context.scene.frame_current
        settings.mount_preset = ""
        if calibration_stale(context, obj):
            self.report({'WARNING'}, "The rig or bone map changed since calibration: calibrate again, then capture "
                                     "the mount again.")
        self.report({'INFO'}, f"Mount captured at frame {settings.mount_frame}: the guitar origin is "
                              f"{mount_t.length * 100.0:.1f} cm from the chest bone.")
        tag_redraw(context)
        return {'FINISHED'}


def fret_hand(obj):
    """The fretting hand's pose bone: the IK hand the solver rotates, or the bone-map hand."""
    bone_map = obj.gtr_char.bone_map
    for name in (getattr(bone_map, f"chain_hand_{FRET_SIDE}"), getattr(bone_map, f"hand_{FRET_SIDE}")):
        pbone = obj.pose.bones.get(name) if name else None
        if pbone is not None:
            return pbone
    return None


class GTR_OT_capture_wrist_offset(bpy.types.Operator):
    """Store the fretting hand's rotation relative to the guitar in the current frame's pose as the wrist target.
    Pose the guitar and the fretting hand on its neck first"""

    bl_idname = "gtr.capture_wrist_offset"
    bl_label = "Capture Wrist Offset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if not _poll(cls, context, False):
            return False
        if fret_hand(context.scene.gtr.armature) is None:
            cls.poll_message_set("Map the fretting hand bone first")
            return False
        return True

    def execute(self, context):
        settings = context.scene.gtr
        try:
            obj, cal, _, root = _mount_inputs(context)
            mount.root_scale(root)
        except mount.MountError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        context.view_layer.update()
        hand = fret_hand(obj)
        rotation = (obj.matrix_world @ hand.matrix).to_quaternion()
        frame = calibrate.rest_aligned(rotation, calibrate.rest_aligned_offset(hand.bone, Quaternion(cal.char_frame)))
        guitar = root.matrix_world.decompose()[1]
        settings.wrist_offset = wrist.capture(guitar, frame, Quaternion(getattr(cal, f"axis_rot_{FRET_SIDE}")))
        settings.wrist_source = 'CAPTURE'
        settings.wrist_frame = context.scene.frame_current
        if calibration_stale(context, obj):
            self.report({'WARNING'}, "The rig or bone map changed since calibration: calibrate again, then capture "
                                     "the wrist offset again.")
        self.report({'INFO'}, f"Wrist offset captured at frame {settings.wrist_frame}: the solve turns the fretting "
                              f"wrist {settings.wrist_blend:.0%} of the way to this rotation on the guitar.")
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_place_on_mount, GTR_OT_capture_mount, GTR_OT_capture_wrist_offset)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
