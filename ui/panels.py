"""Sidebar panels in View3D > Sidebar > Guitar: character, guitar and landmarks, bones, calibration, mount."""

import math
import textwrap

import bpy
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate, landmarks

MESSAGE_ICONS = {'ERROR': 'CANCEL', 'WARNING': 'ERROR', 'INFO': 'INFO'}
AXIS_NAMES = ("X (char. left)", "Y (up)", "Z (forward)")
GUITAR_AXIS_NAMES = ("X (headstock)", "Y", "Z (strings)")
CONFIDENCE_ICONS = {'HIGH': 'CHECKMARK', 'MEDIUM': 'INFO', 'LOW': 'ERROR'}
MOUNT_TEXT = {'NONE': "Not set", 'PRESET': "Preset estimate", 'CAPTURE': "Captured"}


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


def draw_rows(layout, rows, factor=0.45):
    col = layout.box().column(align=True)
    for label, value in rows:
        split = col.split(factor=factor)
        split.label(text=label)
        split.label(text=value)


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
        layout.prop(settings, "guitar_root")
        layout.prop(settings, "show_overlay")


class _SubPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Guitar"
    bl_parent_id = "GTR_PT_main"

    @classmethod
    def poll(cls, context):
        return context.scene.gtr.armature is not None


class GTR_PT_guitar(bpy.types.Panel):
    bl_idname = "GTR_PT_guitar"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Guitar"
    bl_parent_id = "GTR_PT_main"
    bl_label = "Guitar"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        root = settings.guitar_root
        layout.operator("gtr.normalize_frame", icon='EMPTY_ARROWS')
        if root is None:
            draw_messages(layout, context, [('INFO', "Select the guitar meshes (or the empty they hang from), "
                                                     "then Normalise Frame.")])
            return
        info = root.gtr_guitar
        row = layout.row(align=True)
        row.operator("gtr.flip_frame", text="Flip X").axis = 'X'
        row.operator("gtr.flip_frame", text="Flip Z").axis = 'Z'
        rows = [("Length", f"{info.length_m:.3f} m"), ("Confidence", info.confidence.title())]
        if info.preset:
            scale = info.fit_scale
            rows.append(("Fit", f"{'Neck' if info.fit_method == 'NECK' else 'Bounds'}  "
                                f"×{scale[0]:.2f} ×{scale[1]:.2f} ×{scale[2]:.2f}"))
        frame = root.matrix_world.to_quaternion()
        for i, name in enumerate(GUITAR_AXIS_NAMES):
            axis = frame @ Vector([float(j == i) for j in range(3)])
            rows.append((name, f"{axis.x:+.2f}  {axis.y:+.2f}  {axis.z:+.2f}"))
        draw_rows(layout, rows)
        draw_messages(layout, context, calibrate.parse_messages(info.messages))

        col = layout.column(align=True)
        col.prop(settings, "preset", text="")
        row = col.row(align=True)
        row.operator("gtr.load_preset", icon='IMPORT')
        row.operator("gtr.load_preset_file", text="", icon='FILE_FOLDER')
        row.operator("gtr.save_preset", text="", icon='FILE_TICK')

        header, body = layout.panel("GTR_landmarks", default_closed=False)
        found = landmarks.find(root)
        missing = [role for role in landmarks.ROLES if role.required and role.id not in found]
        header.label(text="Landmarks" + (f" ({len(missing)} missing)" if missing else ""))
        if body is not None:
            col = body.column(align=True)
            for role in landmarks.ROLES:
                obj = found.get(role.id)
                icon = 'CHECKMARK' if obj is not None else ('ERROR' if role.required else 'DOT')
                text = role.label + ("" if obj is not None else ("  (missing)" if role.required else "  (optional)"))
                col.operator("gtr.select_landmark", text=text, icon=icon, emboss=False).role = role.id
            if not found:
                draw_messages(body, context, [('INFO', "Load a preset to place the landmarks, then check them "
                                                       "on the guitar.")])


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
        draw_rows(layout, rows)
        messages = [('INFO', "Overlay: red X (character's left), green Y (up), blue Z (forward); yellow and "
                             "orange dots are fingertips, magenta is the neck-aim point.")]
        draw_messages(layout, context, messages + calibrate.parse_messages(cal.messages))


class GTR_PT_mount(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_mount"
    bl_label = "Mount"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        if settings.guitar_root is None or not settings.armature.gtr_char.calibration.is_valid:
            layout.label(text="Normalise the guitar and calibrate first", icon='INFO')
            return
        row = layout.row(align=True)
        row.operator("gtr.place_on_mount", icon='SNAP_ON')
        row.operator("gtr.capture_mount", icon='PINNED')
        source = settings.mount_source
        text = MOUNT_TEXT[source]
        if source == 'PRESET' and settings.mount_preset:
            text += f" ({settings.mount_preset})"
        elif source == 'CAPTURE':
            text += f" at frame {settings.mount_frame}"
        rows = [("Mount", text)]
        if source != 'NONE':
            euler = Quaternion(settings.mount_q).to_euler('XYZ')
            rows.append(("Rotation", "  ".join(f"{math.degrees(a):.1f}°" for a in euler)))
        draw_rows(layout, rows, factor=0.3)
        if source != 'NONE':
            layout.prop(settings, "mount_t", text="")
        messages = []
        if source == 'NONE':
            messages.append(('INFO', "Load a preset for a first estimate, or pose the guitar on the character "
                                     "(move and rotate GTR_ROOT) and capture it."))
        elif source == 'PRESET':
            messages.append(('WARNING', "The preset mount is only an estimate: Place on Mount, adjust GTR_ROOT on "
                                        "the character, then Capture Mount."))
        draw_messages(layout, context, messages)


CLASSES = (GTR_PT_main, GTR_PT_guitar, GTR_PT_bones, GTR_PT_calibration, GTR_PT_mount)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
