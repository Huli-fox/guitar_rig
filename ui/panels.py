"""Sidebar panels in View3D > Sidebar > Guitar: character, bones and calibration."""

import textwrap

import bpy
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate

MESSAGE_ICONS = {'ERROR': 'CANCEL', 'WARNING': 'ERROR', 'INFO': 'INFO'}
AXIS_NAMES = ("X (char. left)", "Y (up)", "Z (forward)")


def draw_messages(layout, context, messages):
    """Labels for (level, text) messages, wrapped to the region width."""
    if not messages:
        return
    width = context.region.width if context.region is not None else 300
    scale = context.preferences.system.ui_scale or 1.0   # 0 without a window (background mode)
    chars = max(24, int(width / (7.0 * scale)))
    col = layout.column(align=True)
    for level, text in messages:
        icon = MESSAGE_ICONS.get(level, 'INFO')
        for i, line in enumerate(textwrap.wrap(text, chars) or [""]):
            col.label(text=line, icon=icon if i == 0 else 'BLANK1')


def _slot_groups():
    groups = [("BODY", "Body", [s for s in bonemap.SLOTS if s.group == 'BODY'])]
    for group, title in (('ARM', "Arm"), ('FINGERS', "Fingers"), ('CHAIN', "IK Chain")):
        for side, side_name in (('L', "Left"), ('R', "Right")):
            slots = [s for s in bonemap.SLOTS if s.group == group and s.side == side]
            groups.append((f"{group}_{side}", f"{side_name} {title}", slots))
    return groups


SLOT_GROUPS = _slot_groups()


class GTR_PT_main(bpy.types.Panel):
    bl_idname = "GTR_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Guitar"
    bl_label = "GuitarRig"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        layout.prop(settings, "armature")
        if settings.armature is None:
            layout.label(text="Pick the retargeted character", icon='INFO')
        layout.prop(settings, "show_overlay")


class _SubPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Guitar"
    bl_parent_id = "GTR_PT_main"

    @classmethod
    def poll(cls, context):
        return context.scene.gtr.armature is not None


class GTR_PT_bones(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_bones"
    bl_label = "Bones"

    def draw(self, context):
        layout = self.layout
        obj = context.scene.gtr.armature
        bone_map = obj.gtr_char.bone_map
        layout.operator("gtr.auto_map_bones", icon='BONE_DATA')
        if bone_map.source:
            layout.label(text=f"Matched: {bone_map.source}")
        for group_id, title, slots in SLOT_GROUPS:
            header, body = layout.panel(f"GTR_bones_{group_id}", default_closed=group_id != "BODY")
            header.label(text=title)
            if body is None:
                continue
            col = body.column(align=True)
            for slot in slots:
                col.prop_search(bone_map, slot.key, obj.data, "bones", text=slot.label)
            if group_id.startswith("CHAIN"):
                count = getattr(bone_map, f"chain_count_{group_id[-1]}")
                col.label(text=f"Chain count: {count}" if count else "Chain count: invalid",
                          icon='NONE' if count else 'ERROR')
        mapping = bonemap.mapping_from(bone_map)
        draw_messages(layout, context, bonemap.validate(obj.data.bones, mapping))


class GTR_PT_calibration(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_calibration"
    bl_label = "Calibration"

    def draw(self, context):
        layout = self.layout
        obj = context.scene.gtr.armature
        cal = obj.gtr_char.calibration
        layout.operator("gtr.calibrate", icon='ARMATURE_DATA')
        col = layout.column()
        col.prop(cal, "flip_facing")
        col.prop(cal, "axis_rot_ref_angle")
        if not cal.is_valid:
            layout.label(text="Not calibrated", icon='INFO')
            return

        mapping = bonemap.mapping_from(obj.gtr_char.bone_map)
        current = calibrate.fingerprint(obj, mapping, cal.flip_facing, cal.axis_rot_ref_angle,
                                        context.scene.unit_settings.scale_length)
        if current != cal.fingerprint:
            layout.label(text="The rig or bone map changed: calibrate again", icon='ERROR')

        tips = list(cal.fingertips)
        estimated = sum(1 for tip in tips if tip.source == 'ESTIMATE')
        tip_text = f"L {sum(t.side == 'L' for t in tips)}, R {sum(t.side == 'R' for t in tips)}"
        if estimated:
            tip_text += f" ({estimated} estimated)"
        rows = [
            ("Height", f"{cal.height:.3f} m"),
            ("Arm", f"{cal.arm_len:.3f} m  ×{cal.ratio_arm:.3f}"),
            ("Palm", f"{cal.palm_len:.3f} m  ×{cal.ratio_palm:.3f}"),
            ("Spine", f"{cal.spine_len:.3f} m  ×{cal.ratio_spine:.3f}"),
            ("IK chain L / R", f"{cal.chain_len_L:.3f} / {cal.chain_len_R:.3f} m"),
            ("Fingertips", tip_text),
        ]
        frame = calibrate.char_frame_world(Quaternion(cal.char_frame), obj.matrix_world)
        for i, name in enumerate(AXIS_NAMES):
            axis = frame @ Vector([float(j == i) for j in range(3)])
            rows.append((name, f"{axis.x:+.2f}  {axis.y:+.2f}  {axis.z:+.2f}"))
        col = layout.box().column(align=True)
        for label, value in rows:
            split = col.split(factor=0.45)
            split.label(text=label)
            split.label(text=value)
        messages = [('INFO', "Overlay: red X (character's left), green Y (up), blue Z (forward); yellow and "
                             "orange dots are fingertips, magenta is the neck-aim point.")]
        draw_messages(layout, context, messages + calibrate.parse_messages(cal.messages))


CLASSES = (GTR_PT_main, GTR_PT_bones, GTR_PT_calibration)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
