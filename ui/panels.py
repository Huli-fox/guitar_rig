"""Sidebar panels in View3D > Sidebar > Guitar: character, guitar and landmarks, bones, calibration, mount,
magnets and solve."""

import math
import textwrap

import bpy
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate, landmarks, magnets, solver
from ..core.bonemap import SIDES
from ..rig import build

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


def draw_magnet(layout, context, settings, item, index):
    """The settings of one magnet, its reach on the character, and what it did in the solve the rig shows."""
    box = layout.box()
    col = box.column()
    col.row(align=True).prop(item, "hand", expand=True)
    col.row(align=True).prop(item, "kind", expand=True)
    col.prop(item, "landmark_a", text="Plane" if item.kind == 'PLANE' else "Start")
    if item.kind == 'LINE':
        col.prop(item, "landmark_b", text="End")
    else:
        col.prop(item, "crossable")
    col.prop(item, "use_default_rotation")
    col = box.column(align=True)
    col.prop(item, "effective_distance_m")
    col.prop(item, "peak")
    col.prop(item, "power")
    col.prop(item, "hysteresis")
    col = box.column()
    col.prop(item, "hand_offset_mode")
    if item.hand_offset_mode == 'CUSTOM':
        col.prop(item, "hand_offset")
    if item.hand_offset_mode != 'NONE':
        col.prop(item, "apply_axis_rot")
    if item.kind == 'PLANE':
        col.prop(item, "fingertip_mode")
        if item.fingertip_mode == 'V2':
            col.row(align=True).prop(item, "fingers")
            col.prop(item, "fingertip_offset_m")
            col.prop(item, "push_only")
    col.prop(item, "filter")

    rows = []
    obj = settings.armature
    cal = obj.gtr_char.calibration if obj is not None else None
    if cal is not None and cal.is_valid:
        reach = item.effective_distance_m * magnets.distance_scale(settings.autoscale_policy, cal.ratio_arm)
        rows.append(("Reach", f"{reach:.3f} m on this character"))
    result = solver.shown_result(context.scene)
    hit = result.hit(index) if result is not None else None
    if hit is not None:
        state = "clamp" if hit.barrier else f"weight {hit.weight:.2f}"
        rows.append(("Solve", f"{hit.distance * result.metres_per_bu * 100.0:.1f} cm away, {state}"))
    if rows:
        draw_rows(box, rows, factor=0.3)
    if (item.kind == 'PLANE' and item.fingertip_mode != 'NONE') or item.filter != 'NONE':
        draw_messages(box, context, [('INFO', "Fingertips and filters are not applied by the solver yet.")])


class GTR_PT_magnets(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_magnets"
    bl_label = "Magnets"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        row = layout.row()
        row.template_list("GTR_UL_magnets", "", settings, "magnets", settings, "active_magnet_index", rows=4)
        col = row.column(align=True)
        col.operator("gtr.magnet_add", text="", icon='ADD')
        col.operator("gtr.magnet_remove", text="", icon='REMOVE')
        col.separator()
        col.operator("gtr.magnet_move", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("gtr.magnet_move", text="", icon='TRIA_DOWN').direction = 'DOWN'
        layout.prop(settings, "show_magnets")
        index = settings.active_magnet_index
        if 0 <= index < len(settings.magnets):
            draw_magnet(layout, context, settings, settings.magnets[index], index)
        else:
            draw_messages(layout, context, [('INFO', "Load a preset for SAO's magnets, or add your own. They act "
                                                     "in list order.")])


class GTR_PT_solve(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_solve"
    bl_label = "Solve"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.gtr
        if settings.guitar_root is None or not settings.armature.gtr_char.calibration.is_valid:
            layout.label(text="Normalise the guitar and calibrate first", icon='INFO')
            return
        rig = build.find(settings)
        messages = []
        row = layout.row(align=True)
        row.operator("gtr.build_rig", text="Rebuild Rig" if rig is not None else "Build Rig", icon='CON_KINEMATIC')
        row.operator("gtr.clean_rig", text="", icon='TRASH')
        if rig is None and settings.rig_collection is not None:
            messages.append(('WARNING', "The helper rig does not match the character or its bone map: build it "
                                        "again."))
        elif rig is None:
            messages.append(('INFO', "Build Rig adds IK and rotation constraints to each arm. They stay off, so "
                                     "the mocap plays as before, until you solve a frame."))

        layout.prop(settings, "mode", expand=True)
        if settings.mode == 'FOLLOW':
            messages.append(('INFO', "The neck aim is not solved yet: the guitar stays on its mount in both "
                                     "modes."))
        header, body = layout.panel("GTR_solve_options", default_closed=True)
        header.label(text="Options")
        if body is not None:
            col = body.column()
            col.prop(settings, "reach_clamp")
            col.prop(settings, "barriers_ignore_distance")
            col.prop(settings, "autoscale_policy")
            col.prop(settings, "iterations")
            col.prop(settings, "use_right_root_bias")
            sub = col.column()
            sub.active = settings.use_right_root_bias
            sub.prop(settings, "right_root_bias")

        row = layout.row(align=True)
        row.operator("gtr.solve_frame", icon='PLAY')
        row.operator("gtr.clear_solve", text="", icon='ARMATURE_DATA')
        result = solver.shown_result(scene)
        if result is not None:
            rows = []
            for side in SIDES:
                side_result = result.sides[side]
                moved = (side_result.target - side_result.fk_wrist).length * result.metres_per_bu * 100.0
                text = f"moved {moved:.1f} cm" + (", reach clamped" if side_result.clamped else "")
                rows.append((f"{'Left' if side == 'L' else 'Right'} wrist", text))
                for index, hit in side_result.hits:
                    if hit.weight > 0.0 and index < len(settings.magnets):
                        rows.append(("   " + settings.magnets[index].name,
                                     "clamp" if hit.barrier else f"weight {hit.weight:.2f}"))
            draw_rows(layout, rows, factor=0.5)
            messages += result.messages
        elif settings.solve_active:
            messages.append(('INFO', "The arms show a solve whose details were lost (undo or reload): solve the "
                                     "frame again, or show the mocap."))
        else:
            messages.append(('INFO', "Solve Frame shows the solved arms until the frame changes."))
        draw_messages(layout, context, messages)


CLASSES = (GTR_PT_main, GTR_PT_guitar, GTR_PT_bones, GTR_PT_calibration, GTR_PT_mount, GTR_PT_magnets,
           GTR_PT_solve)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
