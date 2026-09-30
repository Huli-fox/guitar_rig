"""Property groups: scene settings (§3.5), magnets (§3.6), the per-armature bone map and calibration, and the
guitar frame of GTR_ROOT.

Scene.gtr holds the settings for the scene's character and guitar. Object.gtr_char holds an armature's bone
map and calibration, so they stay with the character when it is linked into another scene; Object.gtr_guitar
holds what normalising found on GTR_ROOT. Lengths in
metres say "(m)" in their names; they deliberately use no length unit, which the scene unit scale would
rescale.
"""

import math

import bpy
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty,
                       IntProperty, PointerProperty, StringProperty)
from bpy.types import PropertyGroup

from .core import bonemap, calibrate, magnets, presets

SIDE_ITEMS = (
    ('L', "Left", "The character's left hand"),
    ('R', "Right", "The character's right hand"),
)
MODE_ITEMS = (
    ('FOLLOW', "Follow", "The guitar yaws toward the fretting hand (SAO's default mode)"),
    ('ALIGN', "Align", "The guitar stays on the chest and the fretting hand slides along the fretboard edge "
                       "(SAO's Alt+A mode)"),
)
FINGER_ITEMS = (
    ('INDEX', "Index", ""),
    ('MIDDLE', "Middle", ""),
    ('RING', "Ring", ""),
)

# SAO defaults; MMD lengths are converted to metres (1 MMD unit = 1/11 m).
SAO_AIM_HAND_OFFSET = (0.6 / 11.0, -0.25 / 11.0, 0.0)
# rotation_reference offset {x: 60, y: 180, z: 0} (scene.json), for SAO's hand-tracking frame; with that frame's
# turn w (wrist.py) it is the hand's T-pose-aligned frame in the guitar frame.
SAO_WRIST_OFFSET = tuple(presets.sao_wrist((60.0, 180.0, 0.0)))
# Reference palm length / 4 (min.js, fingertip offsets), in metres before the arm ratio.
SAO_PALM_MARGIN = calibrate.REF_PALM_LEN / 4.0
# Right-arm root_rotation (0, 10, -15) degrees in three.js order ZYX, which is Blender's 'XYZ'.
SAO_RIGHT_ROOT_BIAS = (0.0, math.radians(10.0), math.radians(-15.0))


def _is_armature(self, obj):
    return obj.type == 'ARMATURE'


def _is_empty(self, obj):
    return obj.type == 'EMPTY'


def _redraw(self, context):
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def _mode_changed(self, context):
    magnets.apply_mode(self, self.mode)
    _redraw(self, context)


class GTR_Magnet(PropertyGroup):
    """A line or plane in guitar space that pulls one wrist target (§3.6, §5.5). `name` is the display name.
    Edits redraw the viewport, whose overlay shows the magnets."""

    enabled: BoolProperty(name="Enabled", default=True, update=_redraw)
    preset_id: StringProperty(
        name="Preset ID",
        description="Role of the magnet in a preset (e.g. FRETBOARD_PLANE); mode switches find magnets by it")
    hand: EnumProperty(name="Hand", items=SIDE_ITEMS, default='L', update=_redraw)
    kind: EnumProperty(
        name="Kind", default='PLANE', update=_redraw,
        items=(('LINE', "Line", "Pull toward the segment from landmark A to landmark B"),
               ('PLANE', "Plane", "Pull toward, or clamp against, the plane through landmark A "
                                  "(normal: A's local Z)")))
    landmark_a: PointerProperty(name="Landmark A", type=bpy.types.Object, poll=_is_empty, update=_redraw)
    landmark_b: PointerProperty(name="Landmark B", type=bpy.types.Object, poll=_is_empty, update=_redraw,
                                description="End of the segment (line magnets only)")
    crossable: BoolProperty(
        name="Crossable", default=True, update=_redraw,
        description="Off: the plane is a barrier, and a hand behind it is clamped onto it with full weight")
    effective_distance_m: FloatProperty(
        name="Distance (m)", default=0.27, min=0.0, soft_max=1.0, precision=4, update=_redraw,
        description="Reach of the magnet in metres, before arm-ratio scaling. Barriers need it too")
    peak: FloatProperty(name="Peak (m)", default=0.0, min=0.0, precision=4, update=_redraw,
                        description="Distance from the feature at which the weight is highest")
    power: FloatProperty(
        name="Power", default=0.0, soft_min=-99.0, soft_max=1.0, update=_redraw,
        description="0: linear falloff over the distance; 1: full snap within it; -9 or less: barrier "
                    "clamp only")
    use_default_rotation: BoolProperty(
        name="Use Default Rotation", default=False, update=_redraw,
        description="Place the feature with the guitar's chest-mount rotation, before the neck aim")
    hand_offset_mode: EnumProperty(
        name="Hand Offset", default='NONE', update=_redraw,
        items=(('PARENT_BONE', "Aim Offset", "The aim hand offset (SAO's \"parent_bone\" offset)"),
               ('CUSTOM', "Custom", "The offset vector below"),
               ('NONE', "None", "The wrist itself")))
    hand_offset: FloatVectorProperty(
        name="Offset (m)", size=3, precision=4, update=_redraw,
        description="Offset from the wrist in the rest-aligned hand frame, in metres")
    apply_axis_rot: BoolProperty(
        name="Apply Axis Rotation", default=True, update=_redraw,
        description="Rotate the offset by axis_rot, as SAO does for avatars whose rest pose is not a T-pose; "
                    "axis_rot is the identity on T-pose rigs")
    fingertip_mode: EnumProperty(
        name="Fingertips", default='NONE', update=_redraw,
        items=(('NONE', "None", "The hand point itself meets the plane"),
               ('V2', "Fingertip v2", "Shift the hand so that the nearest fingertip lands on the plane")))
    fingers: EnumProperty(name="Fingers", items=FINGER_ITEMS, options={'ENUM_FLAG'},
                          default={'INDEX', 'MIDDLE', 'RING'}, update=_redraw)
    fingertip_offset_m: FloatProperty(
        name="Fingertip Offset", default=0.0, precision=4, update=_redraw,
        description="SAO's reference_point_offset_distance: shifts the plane along its normal for the fingertips. "
                    "In GTR_ROOT units, so it scales with the guitar (metres for a real-size guitar at scale 1)")
    push_only: BoolProperty(
        name="Push Only", default=False, update=_redraw,
        description="The fingertips may push the hand away from the plane but never pull it in")
    filter: EnumProperty(
        name="Filter", default='NONE', update=_redraw,
        items=(('NONE', "None", ""),
               ('ONE_EURO', "One Euro", "One-euro filter on the pull"),
               ('ROTATION_BASED', "Rotation", "Filter the angle about the guitar root")))
    hysteresis: FloatProperty(
        name="Hysteresis", default=1.15, min=1.0, soft_max=2.0, update=_redraw,
        description="Distance multiplier while a snap magnet (power 1 or more) holds the hand")


class GTR_RangeOverride(PropertyGroup):
    """A frame range solved in another mode (§5.8)."""

    frame_start: IntProperty(name="Start", default=1)
    frame_end: IntProperty(name="End", default=250)
    mode: EnumProperty(name="Mode", items=MODE_ITEMS, default='ALIGN')


def _bone_map_changed(self, context):
    obj = self.id_data
    if getattr(obj, "type", None) != 'ARMATURE':
        return
    for side in bonemap.SIDES:
        count = bonemap.chain_count(obj.data.bones, getattr(self, f"chain_upper_arm_{side}"),
                                    getattr(self, f"chain_forearm_{side}"))
        if getattr(self, f"chain_count_{side}") != count:
            setattr(self, f"chain_count_{side}", count)


_SLOT_HELP = {
    "chest": "The bone the guitar mounts on: the humanoid chest (MMD 上半身2, VRM chest)",
    "neck": "Used for the spine length",
    "thigh": "The left one is used for the spine length",
    "chain_upper_arm": "The upper arm the IK drives; on Rigify-style rigs, the FK control",
    "chain_forearm": "The forearm that carries the IK constraint; on Rigify-style rigs, the FK control",
    "chain_hand": "The hand that gets the wrist rotation; on Rigify-style rigs, the FK control",
}


def _bone_map_annotations():
    annotations = {
        "source": StringProperty(name="Source", description="Naming conventions the last auto-map matched"),
    }
    for slot in bonemap.SLOTS:
        text = _SLOT_HELP.get(slot.kind, f"{slot.title} bone")
        annotations[slot.key] = StringProperty(
            name=slot.title, update=_bone_map_changed,
            description=text if slot.required else f"{text} (optional)")
    for side in bonemap.SIDES:
        annotations[f"chain_count_{side}"] = IntProperty(
            name="Chain Count", min=0,
            description="IK chain length from the IK forearm up to the IK upper arm (0: not a valid chain)")
    return annotations


class GTR_BoneMap(PropertyGroup):
    """Humanoid bones of one armature (§3.3)."""

    __annotations__ = _bone_map_annotations()


def calibrate_object(obj, scene):
    """Calibrate armature `obj` from its bone map and store the result on it. Returns the Calibration."""
    char = obj.gtr_char
    cal = calibrate.compute(obj, bonemap.mapping_from(char.bone_map),
                            flip=char.calibration.flip_facing, ref_angle=char.calibration.axis_rot_ref_angle,
                            metres_per_bu=scene.unit_settings.scale_length)
    calibrate.store(cal, char.calibration)
    return cal


def _recalibrate(self, context):
    obj = self.id_data
    if self.is_valid and getattr(obj, "type", None) == 'ARMATURE':
        try:
            calibrate_object(obj, context.scene)
        except calibrate.CalibrationError:
            self.is_valid = False


class GTR_Fingertip(PropertyGroup):
    side: EnumProperty(name="Side", items=SIDE_ITEMS)
    finger: EnumProperty(name="Finger", items=FINGER_ITEMS)
    bone: StringProperty(name="Distal Bone")
    tip_local: FloatVectorProperty(name="Tip", size=3, precision=5,
                                   description="Fingertip in the distal bone's rest space (armature units)")
    source: EnumProperty(
        name="Source",
        items=(('TAIL', "Bone Tail", "The distal bone's tail"),
               ('ESTIMATE', "Estimated", "Distal head plus half the intermediate segment, as SAO does")))


class GTR_Calibration(PropertyGroup):
    """Rest-pose calibration (§3.4), written by gtr.calibrate. Lengths are in metres."""

    flip_facing: BoolProperty(
        name="Flip Facing", update=_recalibrate,
        description="Turn the character frame half a turn about the up axis, if the detected facing is wrong")
    axis_rot_ref_angle: FloatProperty(
        name="Arm Reference Angle", subtype='ANGLE', default=0.0,
        min=math.radians(-80.0), max=math.radians(80.0), update=_recalibrate,
        description="Arm angle below horizontal of the avatar SAO's hand offsets were authored for: 0° for "
                    "the T-pose VRM avatars the guitar scenes target, 37.42° for XR Animator's MMD skeleton. "
                    "axis_rot turns this direction onto the rig's rest forearm")
    is_valid: BoolProperty(name="Calibrated")
    fingerprint: StringProperty()
    char_frame: FloatVectorProperty(name="Character Frame", size=4, subtype='QUATERNION',
                                    default=(1.0, 0.0, 0.0, 0.0))
    metres_per_bu: FloatProperty(name="Metres per Unit", default=1.0)
    height: FloatProperty(name="Height (m)")
    arm_len: FloatProperty(name="Arm Length (m)")
    palm_len: FloatProperty(name="Palm Length (m)")
    spine_len: FloatProperty(name="Spine Length (m)")
    chain_len_L: FloatProperty(name="Left Chain Length (m)")
    chain_len_R: FloatProperty(name="Right Chain Length (m)")
    ratio_arm: FloatProperty(name="Arm Ratio", default=1.0)
    ratio_palm: FloatProperty(name="Palm Ratio", default=1.0)
    ratio_spine: FloatProperty(name="Spine Ratio", default=1.0)
    axis_rot_L: FloatVectorProperty(name="Left Axis Rotation", size=4, subtype='QUATERNION',
                                    default=(1.0, 0.0, 0.0, 0.0))
    axis_rot_R: FloatVectorProperty(name="Right Axis Rotation", size=4, subtype='QUATERNION',
                                    default=(1.0, 0.0, 0.0, 0.0))
    fingertips: CollectionProperty(type=GTR_Fingertip)
    messages: StringProperty()


class GTR_Character(PropertyGroup):
    bone_map: PointerProperty(type=GTR_BoneMap)
    calibration: PointerProperty(type=GTR_Calibration)


class GTR_Guitar(PropertyGroup):
    """The guitar frame found by gtr.normalize_frame and the preset fit, stored on GTR_ROOT."""

    is_root: BoolProperty(name="Guitar Root")
    confidence: EnumProperty(
        name="Confidence", default='LOW',
        items=(('HIGH', "High", "All cues agree on the frame"),
               ('MEDIUM', "Medium", "One cue decided, or one of three disagreed"),
               ('LOW', "Low", "The cues disagree or are missing: check the axes")))
    messages: StringProperty()
    length_m: FloatProperty(name="Length (m)")
    neck_found: BoolProperty(name="Neck Found")
    preset: StringProperty(name="Preset", description="Id or file of the preset the landmarks were fitted from")
    fit_method: EnumProperty(
        name="Fit", default='BOUNDS',
        items=(('NECK', "Neck", "Fitted to the neck: length, width and thickness"),
               ('BOUNDS', "Bounds", "Fitted to the bounding box")))
    fit_scale: FloatVectorProperty(name="Fit Scale", size=3, default=(1.0, 1.0, 1.0),
                                   description="Size of the guitar relative to the preset's reference, along X "
                                               "(neck length), Y (neck width) and Z (neck thickness)")


MOUNT_SOURCE_ITEMS = (
    ('NONE', "Not Set", "No mount yet: load a preset or capture it"),
    ('PRESET', "Preset", "From a preset: only an estimate"),
    ('CAPTURE', "Captured", "Captured from a pose of the guitar on the character"),
)
_PRESET_ITEMS = presets.enum_items()


class GTR_Settings(PropertyGroup):
    """Scene settings (§3.5)."""

    armature: PointerProperty(name="Character", type=bpy.types.Object, poll=_is_armature,
                              description="The retargeted character armature that plays the mocap")
    guitar_root: PointerProperty(name="Guitar Root", type=bpy.types.Object, poll=_is_empty,
                                 description="GTR_ROOT: the empty that carries the normalised guitar frame")
    show_overlay: BoolProperty(name="Show Overlay", default=True, update=_redraw,
                               description="Draw the calibrated frames, fingertips, landmark lines and the mount "
                                           "in the viewport")
    show_magnets: BoolProperty(name="Show Magnets", default=True, update=_redraw,
                               description="Draw the magnets in the overlay, the active one with its reach, and "
                                           "what they did in the solve the rig shows")
    preset: EnumProperty(name="Preset", items=_PRESET_ITEMS,
                         description="Instrument preset: landmarks, magnets, mount, aim and wrist settings")

    # Mount (§5.3)
    mount_source: EnumProperty(name="Mount", items=MOUNT_SOURCE_ITEMS, default='NONE')
    mount_t: FloatVectorProperty(
        name="Mount Offset (m)", size=3, precision=4, update=_redraw,
        description="Guitar origin relative to the chest bone head, in the rest-aligned chest frame (X: the "
                    "character's left, Y: up, Z: forward), before the spine auto-scale")
    mount_q: FloatVectorProperty(
        name="Mount Rotation", size=4, subtype='QUATERNION', default=(1.0, 0.0, 0.0, 0.0), update=_redraw,
        description="Guitar frame in the rest-aligned chest frame")
    mount_frame: IntProperty(name="Capture Frame", description="Frame the mount was captured at")
    mount_preset: StringProperty(name="Mount Preset", description="Name of the preset the mount came from")

    # Mode and range (§5.8)
    mode: EnumProperty(name="Mode", items=MODE_ITEMS, default='FOLLOW', update=_mode_changed,
                       description="Switches the neck aim and the fretboard-edge magnet like SAO's Alt+A; the "
                                   "fields stay editable")
    range_overrides: CollectionProperty(type=GTR_RangeOverride)
    active_range_index: IntProperty()
    handedness: EnumProperty(
        name="Handedness", default='RIGHT',
        items=(('RIGHT', "Right-Handed", "Frets with the left hand and strums with the right"),
               ('LEFT', "Left-Handed", "Frets with the right hand and strums with the left")))
    iterations: IntProperty(name="Iterations", default=4, min=1, soft_max=10,
                            description="Solve iterations per frame: in Follow mode, neck aims, each followed by "
                                        "the magnets and the IK")
    relax: FloatProperty(name="Relax", default=1.0, min=0.05, max=1.0,
                         description="Share of each new aim rotation taken per iteration; lower it if the "
                                     "guitar oscillates between iterations")
    use_scene_frame_range: BoolProperty(name="Use Scene Range", default=True)
    frame_start: IntProperty(name="Start", default=1)
    frame_end: IntProperty(name="End", default=250)

    # Aim (§5.4)
    aim_enabled: BoolProperty(name="Aim Neck", default=True,
                              description="Swing the neck toward the fretting wrist (FOLLOW mode)")
    aim_weight: FloatProperty(name="Aim Weight", default=1.0, min=0.0, max=1.0)
    aim_max_swing: FloatProperty(name="Max Swing", subtype='ANGLE', default=math.radians(35.0),
                                 min=0.0, max=math.pi)
    aim_hand_offset: FloatVectorProperty(
        name="Aim Hand Offset (m)", size=3, precision=4, default=SAO_AIM_HAND_OFFSET,
        description="Aim point relative to the fretting wrist, in the rest-aligned hand frame "
                    "(SAO: (0.6, -0.25, 0) MMD units)")

    # Wrist (§5.7)
    wrist_blend: FloatProperty(name="Wrist Blend", default=0.5, min=0.0, max=1.0,
                               description="Share of the guitar-relative rotation in the fretting wrist")
    wrist_offset: FloatVectorProperty(
        name="Wrist Offset", size=4, subtype='QUATERNION', default=SAO_WRIST_OFFSET,
        description="Fretting-hand rotation relative to the guitar: the hand's rest-aligned frame turned by "
                    "axis_rot (SAO: Euler 60°, 180°, 0° in its hand-tracking frame)")
    wrist_source: EnumProperty(
        name="Wrist", default='DEFAULT',
        items=(('DEFAULT', "SAO Default", "SAO's rotation_reference offset"),
               ('PRESET', "Preset", "From a preset"),
               ('CAPTURE', "Captured", "Captured from a pose of the fretting hand on the guitar")))
    wrist_frame: IntProperty(name="Wrist Capture Frame", description="Frame the wrist offset was captured at")
    wrist_direction: EnumProperty(
        name="Yaw Direction", default='NEGATIVE',
        description="When the mocap wrist faces more than 120° away from the target about the up axis, turn it "
                    "this way instead of the shorter way (SAO's constrained_direction)",
        items=(('NEGATIVE', "Negative", "SAO's setting (-1) in all guitar scenes"),
               ('POSITIVE', "Positive", "Turn the other way (+1)"),
               ('NONE', "Shorter Way", "Always blend the shorter way")))

    # Scaling (§5.1)
    autoscale_policy: EnumProperty(
        name="Auto-Scale", default='INDEX_JS',
        description="How lengths authored for SAO's reference avatar fit this character. Magnet distances scale "
                    "with the arm, and the mount with the spine, except under None",
        items=(('INDEX_JS', "index.js", "Magnet hand offsets scale with the palm, like the neck aim"),
               ('MIN_JS', "min.js", "Magnet hand offsets scale with the arm, like SAO's arm-normalised magnet "
                                    "space for VRM avatars"),
               ('NONE', "None", "Nothing is scaled to the character")))

    # Reach (§5.5)
    reach_clamp: FloatProperty(name="Reach Clamp", default=0.995, min=0.5, max=1.0,
                               description="Keep wrist targets within this share of the arm chain length, or as "
                                           "far as the mocap wrist if it is further")
    use_right_root_bias: BoolProperty(
        name="Right Root Bias", default=False,
        description="Turn the right arm before the IK, like SAO's root_rotation: this moves where the right "
                    "elbow points")
    right_root_bias: FloatVectorProperty(name="Bias", size=3, subtype='EULER', default=SAO_RIGHT_ROOT_BIAS,
                                         description="In the rest-aligned upper-arm frame. SAO: (0°, 10°, -15°), "
                                                     "order ZYX in three.js")

    # Magnets (§5.5)
    magnets: CollectionProperty(type=GTR_Magnet)
    active_magnet_index: IntProperty()
    barriers_ignore_distance: BoolProperty(
        name="Barriers Ignore Distance", default=True,
        description="Clamp a hand behind a barrier plane however far behind it is")
    palm_margin_m: FloatProperty(
        name="Palm Margin (m)", default=SAO_PALM_MARGIN, min=0.0, soft_max=0.1, precision=4, update=_redraw,
        description="How far fingertip magnets keep the nearest fingertip above their plane, before the "
                    "arm-ratio scaling (SAO: the reference palm length / 4)")

    # Filters (§9)
    filter_min_cutoff: FloatProperty(name="Min Cutoff", default=1.0, min=0.001,
                                     description="One-euro filter on the wrist targets")
    filter_beta: FloatProperty(name="Beta", default=0.02, min=0.0)
    filter_d_cutoff: FloatProperty(name="Derivative Cutoff", default=1.0, min=0.001)
    smooth_cutoff_arms: FloatProperty(name="Arm Cutoff (Hz)", default=6.0, min=0.1,
                                      description="Post-bake low-pass cutoff for the arm channels")
    smooth_cutoff_guitar: FloatProperty(name="Guitar Cutoff (Hz)", default=3.0, min=0.1,
                                        description="Post-bake low-pass cutoff for the guitar channels")

    # Helper rig and Solve Frame (§4, §6)
    rig_collection: PointerProperty(name="Rig Collection", type=bpy.types.Collection,
                                    description="The GuitarRig collection that holds the helper empties")
    rig_armature: PointerProperty(name="Rig Armature", type=bpy.types.Object,
                                  description="The armature that carries the helper rig's constraints")
    solve_active: BoolProperty(name="Showing a Solve",
                               description="The rig's constraints are on and show the solve of Solve Frame")
    solve_frame: IntProperty(name="Solved Frame", description="The frame whose solve the rig shows")
    solve_serial: IntProperty(name="Solve Serial", description="Counts the solves, so that an undone solve is "
                                                               "not shown as current")


CLASSES = (
    GTR_Magnet,
    GTR_RangeOverride,
    GTR_BoneMap,
    GTR_Fingertip,
    GTR_Calibration,
    GTR_Character,
    GTR_Guitar,
    GTR_Settings,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.gtr = PointerProperty(type=GTR_Settings)
    bpy.types.Object.gtr_char = PointerProperty(type=GTR_Character)
    bpy.types.Object.gtr_guitar = PointerProperty(type=GTR_Guitar)


def unregister():
    del bpy.types.Object.gtr_guitar
    del bpy.types.Object.gtr_char
    del bpy.types.Scene.gtr
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
