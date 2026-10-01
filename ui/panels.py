"""Sidebar panels in View3D > Sidebar > Guitar: character, guitar and landmarks, bones, calibration, mount,
magnets, solve (with the range overrides), bake and diagnostics."""

import math
import textwrap

import bpy
from mathutils import Quaternion, Vector

from ..core import bonemap, calibrate, diagnostics, landmarks, magnets, modes, solver
from ..core.bonemap import SIDES
from ..rig import build

MESSAGE_ICONS = {'ERROR': 'CANCEL', 'WARNING': 'ERROR', 'INFO': 'INFO'}
AXIS_NAMES = ("X (char. left)", "Y (up)", "Z (forward)")
GUITAR_AXIS_NAMES = ("X (headstock)", "Y", "Z (strings)")
CONFIDENCE_ICONS = {'HIGH': 'CHECKMARK', 'MEDIUM': 'INFO', 'LOW': 'ERROR'}
MOUNT_TEXT = {'NONE': "Not set", 'PRESET': "Preset estimate", 'CAPTURE': "Captured"}
WRIST_TEXT = {'DEFAULT': "SAO default", 'PRESET': "Preset", 'CAPTURE': "Captured"}
LANDMARK_TEXT = {'PRESET': "Placed by the preset fit", 'AUTO': "Auto-placed"}


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
            body.operator("gtr.auto_landmarks", icon='SHADERFX')
            if info.landmark_source != 'NONE':
                text = LANDMARK_TEXT[info.landmark_source]
                if info.landmark_source == 'AUTO':
                    text += f" ({info.landmark_confidence.lower()} confidence)"
                body.label(text=text, icon=CONFIDENCE_ICONS[info.landmark_confidence]
                           if info.landmark_source == 'AUTO' else 'INFO')
                draw_messages(body, context, calibrate.parse_messages(info.landmark_messages))
            col = body.column(align=True)
            for role in landmarks.ROLES:
                obj = found.get(role.id)
                icon = 'CHECKMARK' if obj is not None else ('ERROR' if role.required else 'DOT')
                text = role.label + ("" if obj is not None else ("  (missing)" if role.required else "  (optional)"))
                col.operator("gtr.select_landmark", text=text, icon=icon, emboss=False).role = role.id
            if not found:
                draw_messages(body, context, [('INFO', "Load a preset to place the landmarks, or Auto-Place them "
                                                       "on the neck and body the add-on finds, then check them on "
                                                       "the guitar.")])


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
    bl_label = "Mount and Wrist"

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

        header, body = layout.panel("GTR_aim", default_closed=True)
        header.label(text="Neck Aim")
        if body is not None:
            col = body.column()
            col.prop(settings, "aim_enabled")
            sub = col.column()
            sub.active = settings.aim_enabled
            sub.prop(settings, "aim_weight")
            sub.prop(settings, "aim_max_swing")
            sub.prop(settings, "aim_hand_offset")
            draw_messages(body, context, [('INFO', "In Follow mode the neck swings toward the magenta aim point on "
                                                   "the fretting hand; Align mode switches the aim off.")])

        header, body = layout.panel("GTR_wrist", default_closed=True)
        header.label(text="Wrist")
        if body is not None:
            body.operator("gtr.capture_wrist_offset", icon='PINNED')
            text = WRIST_TEXT[settings.wrist_source]
            if settings.wrist_source == 'CAPTURE':
                text += f" at frame {settings.wrist_frame}"
            euler = Quaternion(settings.wrist_offset).to_euler('XYZ')
            draw_rows(body, [("Offset", text), ("Rotation", "  ".join(f"{math.degrees(a):.1f}°" for a in euler))],
                      factor=0.3)
            col = body.column()
            col.prop(settings, "wrist_blend")
            col.prop(settings, "wrist_direction")
            draw_messages(body, context, [('INFO', "The fretting wrist turns Wrist Blend of the way from the mocap "
                                                   "to this rotation on the guitar. To set it, pose the hand on the "
                                                   "neck and capture it.")])


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
    if item.filter != 'NONE':
        text = ("The filter acts from frame to frame when baking: Solve Frame shows a frame unfiltered."
                if settings.use_filters else "Filters are switched off (Bake > Filters).")
        draw_messages(box, context, [('INFO', text)])


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

        header, body = layout.panel("GTR_collider", default_closed=True)
        header.prop(settings, "collider_enabled")
        if body is not None:
            col = body.column()
            col.active = settings.collider_enabled
            col.row(align=True).prop(settings, "collider_hands")
            col.prop(settings, "collider_fingertips")
            sub = col.column(align=True)
            sub.prop(settings, "collider_radius_m")
            sub.prop(settings, "collider_top_m")
            sub.prop(settings, "collider_bottom_m")
            sub.prop(settings, "collider_depth_m")
            draw_messages(body, context, [('INFO', "A capsule along the chest that pushes the wrists forward out of "
                                                   "the torso before the magnets act. Lengths are metres before the "
                                                   "spine auto-scale.")])


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
        header, body = layout.panel("GTR_ranges", default_closed=not len(settings.range_overrides))
        count = sum(item.enabled for item in settings.range_overrides)
        header.label(text="Range Overrides" + (f" ({count})" if count else ""))
        if body is not None:
            row = body.row()
            row.template_list("GTR_UL_ranges", "", settings, "range_overrides", settings, "active_range_index",
                              rows=3)
            col = row.column(align=True)
            col.operator("gtr.range_add", text="", icon='ADD')
            col.operator("gtr.range_remove", text="", icon='REMOVE')
            frame_mode = modes.Schedule(settings).at(scene.frame_current)
            text = f"Frame {scene.frame_current}: {frame_mode.mode.title()}"
            if frame_mode.override != modes.SCENE:
                text += f" (range {frame_mode.override + 1})"
            if 0.0 < frame_mode.aim_weight < settings.aim_weight:
                text += f", neck aim fading ({frame_mode.aim_weight:.2f})"
            body.label(text=text)
            if any(item.frame_end < item.frame_start for item in settings.range_overrides):
                body.label(text="A range ends before it starts: it is ignored", icon='ERROR')
            draw_messages(body, context, [('INFO', "Each range solves its frames in its mode: the neck aim and the "
                                                   "fretboard-edge magnet switch as with the mode buttons. Lower "
                                                   f"ranges win where they overlap. The neck aim fades over "
                                                   f"{modes.FADE_FRAMES} frames at each change.")])
        header, body = layout.panel("GTR_solve_options", default_closed=True)
        header.label(text="Options")
        if body is not None:
            col = body.column()
            col.prop(settings, "iterations")
            col.prop(settings, "relax")
            col.prop(settings, "reach_clamp")
            col.prop(settings, "barriers_ignore_distance")
            col.prop(settings, "palm_margin_m")
            col.prop(settings, "autoscale_policy")
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
            frame_mode = result.frame_mode
            if frame_mode is not None and (frame_mode.override != modes.SCENE or len(settings.range_overrides)):
                text = frame_mode.mode.title() + ("" if frame_mode.override == modes.SCENE
                                                  else f" (range {frame_mode.override + 1})")
                rows.append(("Mode", text))
            for side in SIDES:
                side_result = result.sides[side]
                moved = (side_result.target - side_result.fk_wrist).length * result.metres_per_bu * 100.0
                text = f"moved {moved:.1f} cm" + (", reach clamped" if side_result.clamped else "")
                rows.append((f"{'Left' if side == 'L' else 'Right'} wrist", text))
                for index, hit in side_result.hits:
                    if hit.weight > 0.0 and index < len(settings.magnets):
                        rows.append(("   " + settings.magnets[index].name,
                                     "clamp" if hit.barrier else f"weight {hit.weight:.2f}"))
            if result.neck is not None:
                rows.append(("Neck swing", f"{math.degrees(result.swing):.1f}°"
                                           + (", limited" if result.neck.clamped else "")))
            if result.wrist_turn > 0.0:
                rows.append(("Fretting wrist", f"turned {math.degrees(result.wrist_turn):.1f}°"
                                               + (", yaw constrained" if result.wrist_constrained else "")))
            rows.append(("Passes", f"{result.iterations}" + ("" if result.converged else ", not settled")))
            draw_rows(layout, rows, factor=0.5)
            messages += result.messages
        elif settings.solve_active:
            messages.append(('INFO', "The arms show a solve whose details were lost (undo or reload): solve the "
                                     "frame again, or show the mocap."))
        else:
            messages.append(('INFO', "Solve Frame shows the solved arms until the frame changes."))
        draw_messages(layout, context, messages)


def _filter_row(layout, settings, toggle, values):
    col = layout.column(align=True)
    if toggle is not None:
        col.prop(settings, toggle)
    sub = col.row(align=True)
    sub.active = toggle is None or getattr(settings, toggle)
    sub.prop(settings, values, text="")


class GTR_PT_bake(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_bake"
    bl_label = "Bake"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        if settings.guitar_root is None or not settings.armature.gtr_char.calibration.is_valid:
            layout.label(text="Normalise the guitar and calibrate first", icon='INFO')
            return
        col = layout.column()
        col.prop(settings, "use_scene_frame_range")
        if not settings.use_scene_frame_range:
            row = col.row(align=True)
            row.prop(settings, "frame_start")
            row.prop(settings, "frame_end")
        col.prop(settings, "guitar_space")
        col.prop(settings, "bake_interpolation")
        col.prop(settings, "bake_hide_meshes")

        header, body = layout.panel("GTR_filters", default_closed=True)
        header.prop(settings, "use_filters")
        if body is not None:
            col = body.column()
            col.active = settings.use_filters
            _filter_row(col, settings, "use_filter_fingertips", "filter_fingertip")
            _filter_row(col, settings, "use_filter_wrist", "filter_wrist")
            col.label(text="One Euro Magnets")
            _filter_row(col, settings, None, "filter_pull")
            col.label(text="Rotation Magnets")
            _filter_row(col, settings, None, "filter_rotation")
            _filter_row(col, settings, "use_filter_targets", "filter_target")
            _filter_row(col, settings, "use_filter_guitar", "filter_guitar")
            draw_messages(body, context, [('INFO', "One-euro filters: minimum cutoff (Hz), beta and derivative "
                                                   "cutoff (Hz), with SAO's values by default. Lower cutoffs smooth "
                                                   "more and lag more.")])

        row = layout.row(align=True)
        row.scale_y = 1.4
        row.operator("gtr.bake", icon='REC')
        row.operator("gtr.remove_bake", text="", icon='TRASH')

        header, body = layout.panel("GTR_post", default_closed=False)
        header.label(text="After the Bake")
        if body is not None:
            col = body.column(align=True)
            col.prop(settings, "smooth_cutoff_arms")
            col.prop(settings, "smooth_cutoff_guitar")
            col.operator("gtr.smooth_bake", icon='MOD_SMOOTH')
            col = body.column(align=True)
            col.prop(settings, "reclamp_tolerance_m")
            col.operator("gtr.reclamp", icon='SNAP_FACE')

        if settings.bake_report:
            box = layout.box()
            draw_messages(box, context, calibrate.parse_messages(settings.bake_report))
        else:
            draw_messages(layout, context, [('INFO', "Bake keys the arms and the guitar into GuitarBake NLA strips; "
                                                     "correct them on the GuitarRefine layer above.")])


class GTR_PT_diagnostics(_SubPanel, bpy.types.Panel):
    bl_idname = "GTR_PT_diagnostics"
    bl_label = "Diagnostics"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gtr
        obj = diagnostics.find(settings)
        if diagnostics.action_of(obj) is None:
            draw_messages(layout, context, [('INFO', "Bake to record what the solve did on each frame: the wrist "
                                                     "corrections, each magnet's distance and weight, the neck "
                                                     "swing.")])
            return
        metric = settings.diagnostics_metric
        layout.prop(settings, "diagnostics_metric")
        col = layout.column(align=True)
        ranked = diagnostics.ranking(obj, metric)
        if not ranked:
            col.label(text=f"No frame has any {diagnostics.METRIC_BY_ID[metric][1].lower()}", icon='CHECKMARK')
        for rank, (frame, value) in enumerate(ranked, 1):
            op = col.operator("gtr.jump_worst_frame", text=f"Frame {frame}: {diagnostics.format_value(metric, value)}",
                              icon='TIME' if rank == 1 else 'BLANK1')
            op.metric = metric
            op.rank = rank
        layout.operator("gtr.show_diagnostics", icon='GRAPH')
        draw_messages(layout, context, [('INFO', f"{obj.name}'s curves hold every frame: each wrist's correction "
                                                 "(cm) and IK miss (mm), each magnet's distance d (cm, negative "
                                                 "behind a plane) and weight w, the neck swing and the fretting "
                                                 "wrist's turn (°). They show the solve, before any Smooth or "
                                                 "Re-clamp.")])


CLASSES = (GTR_PT_main, GTR_PT_guitar, GTR_PT_bones, GTR_PT_calibration, GTR_PT_mount, GTR_PT_magnets,
           GTR_PT_solve, GTR_PT_bake, GTR_PT_diagnostics)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
