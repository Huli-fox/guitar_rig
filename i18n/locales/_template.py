# SPDX-License-Identifier: GPL-3.0-or-later
# UTF-8. Edit translation values; empty values fall back to English.
# Updated by tools/i18n.py. See TRANSLATING.md.

translations = {
    # props.py:GTR_Magnet
    ('*', '0: linear falloff over the distance; 1: full snap within it; -9 or less: barrier clamp only'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('*', '1 for the worst frame, 2 for the next, and so on'): '',
    # props.py:GTR_Guitar
    ('*', "A feature was missing or the guitar's proportions are unusual: check the landmarks"): '',
    # ops/rig.py:GTR_OT_range_add
    ('*', "Add a frame range, from the current frame, solved in the other mode than the scene's. Lower ranges win\nwhere ranges overlap"): '',
    # ops/magnets.py:GTR_OT_magnet_add
    ('*', 'Add a magnet after the active one. Magnets act in list order'): '',
    # ops/rig.py:GTR_OT_build_rig
    ('*', 'Add the helper rig: an IK and a wrist-rotation constraint on each arm, switched off until a solve, and\ntheir empties in a GuitarRig collection. Replaces an older rig'): '',
    # props.py:GTR_Settings
    ('*', 'Aim point relative to the fretting wrist, in the rest-aligned hand frame (SAO: (0.6, -0.25, 0) MMD units)'): '',
    # props.py:GTR_Guitar
    ('*', 'All cues agree on the frame'): '',
    # props.py:GTR_Prep
    ('*', "Also snap the picking hand's fingers, for fingerpicking"): '',
    # props.py:GTR_Settings
    ('*', 'Always blend the shorter way'): '',
    # props.py:GTR_Calibration
    ('*', "Arm angle below horizontal of the avatar SAO's hand offsets were authored for: 0° for the T-pose VRM avatars the guitar scenes target, 37.42° for XR Animator's MMD skeleton. axis_rot turns this direction onto the rig's rest forearm"): '',
    # props.py:GTR_Prep
    ('*', "Arm swing added to the strokes: the wrist travels this many times the pick point's stroke, turned at the shoulder and the elbow (0: off)"): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Body end of the strum line the picking hand is pulled to (SAO magnet 0)'): '',
    # props.py:GTR_Settings
    ('*', 'Captured from a pose of the fretting hand on the guitar'): '',
    # props.py:GTR_Settings
    ('*', 'Captured from a pose of the guitar on the character'): '',
    # props.py:GTR_Settings
    ('*', 'Clamp a hand behind a barrier plane however far behind it is'): '',
    # props.py:GTR_Prep
    ('*', 'Counts the preps, so a bake can tell which one it read'): '',
    # props.py:GTR_Settings
    ('*', 'Counts the solves, so that an undone solve is not shown as current'): '',
    # props.py:GTR_Settings
    ('*', "Disable the scene's meshes in viewports during the bake, which makes it much faster. The pose does not depend on them, and they come back afterwards"): '',
    # props.py:GTR_Fingertip
    ('*', 'Distal head plus half the intermediate segment, as SAO does'): '',
    # props.py:GTR_Magnet
    ('*', 'Distance from the feature at which the weight is highest'): '',
    # props.py:GTR_Magnet
    ('*', 'Distance multiplier while a snap magnet (power 1 or more) holds the hand'): '',
    # props.py:GTR_Settings
    ('*', 'Draw the calibrated frames, fingertips, landmark lines and the mount in the viewport'): '',
    # props.py:GTR_Settings
    ('*', 'Draw the magnets in the overlay, the active one with its reach, and what they did in the solve the rig shows'): '',
    # props.py:GTR_Magnet
    ('*', 'End of the segment (line magnets only)'): '',
    # props.py:GTR_Settings
    ('*', 'Filter how far the collider and magnets move each wrist target. Not in SAO; the mocap itself is never filtered'): '',
    # props.py:GTR_Magnet
    ('*', 'Filter the angle about the guitar root'): '',
    # props.py:GTR_Settings
    ('*', 'Filter the fingertip shift of fingertip magnets (SAO)'): '',
    # props.py:GTR_Settings
    ('*', "Filter the fretting wrist's blended rotation, relative to the chest (SAO)"): '',
    # props.py:GTR_Settings
    ('*', "Filter the neck aim's swing. Not in SAO"): '',
    # props.py:GTR_Settings
    ('*', 'Filter the solve from frame to frame when baking, where SAO does. Solve Frame solves a frame as the first of a bake, where there is nothing to filter yet'): '',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('*', 'Find the guitar frame of the selected meshes (+X toward the headstock, +Z out of the strings), parent\nthem to GTR_ROOT with that frame, and move GTR_ROOT to the preset origin'): '',
    # ops/guitar.py:GTR_OT_auto_landmarks
    ('*', "Find the neck, the heel, the fretboard's tilt and the body on the guitar and place the landmarks on them,\nkeeping the preset's conventions: the string plane's height and the strum line's offsets. GTR_ROOT stays where\nit is. Check the landmarks afterwards"): '',
    # props.py:GTR_Prep
    ('*', 'Finger joints stay within the range they have in the mocap plus this margin'): '',
    # props.py:GTR_Prep
    ('*', "Finger moves smaller than this, in the finger's total bend over its joints, are left as they are"): '',
    # props.py:GTR_Fingertip
    ('*', "Fingertip in the distal bone's rest space (armature units)"): '',
    # props.py:GTR_RangeOverride
    ('*', 'First frame of the range'): '',
    # ops/guitar.py:GTR_OT_load_preset_file
    ('*', 'Fit a preset file to the guitar: landmarks, magnets, mount estimate, aim and wrist settings'): '',
    # ops/guitar.py:GTR_OT_load_preset
    ('*', 'Fit the chosen preset to the guitar: landmarks, magnets, mount estimate, aim and wrist settings'): '',
    # props.py:GTR_Guitar
    ('*', 'Fitted to the bounding box'): '',
    # props.py:GTR_Guitar
    ('*', 'Fitted to the neck: length, width and thickness'): '',
    # props.py:GTR_Settings
    ('*', 'Frame the mount was captured at'): '',
    # props.py:GTR_Settings
    ('*', 'Frame the wrist offset was captured at'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Fretboard surface, normal +Z: the fretting hand snaps onto it (SAO magnet 3)'): '',
    # props.py:GTR_Settings
    ('*', 'Frets with the left hand and strums with the right'): '',
    # props.py:GTR_Settings
    ('*', 'Frets with the right hand and strums with the left'): '',
    # props.py:GTR_Settings
    ('*', "Fretting-hand rotation relative to the guitar: the hand's rest-aligned frame turned by axis_rot (SAO: Euler 60°, 180°, 0° in its hand-tracking frame)"): '',
    # props.py:GTR_Settings
    ('*', 'From a preset'): '',
    # props.py:GTR_Settings
    ('*', 'From a preset: only an estimate'): '',
    # props.py:GTR_Settings
    ('*', 'GTR_ROOT: the empty that carries the normalised guitar frame'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('*', "Go to the frame where the last bake's solve was worst by the chosen measure"): '',
    # ops/setup.py:GTR_OT_auto_map_bones
    ('*', 'Guess the bone map from VRM metadata or from VRoid, Mixamo, Rigify, MMD, Unreal and generic bone names'): '',
    # ui/panels.py:bl_category
    ('*', 'Guitar'): '',
    # props.py:GTR_Settings
    ('*', 'Guitar frame in the rest-aligned chest frame'): '',
    # props.py:GTR_Settings
    ('*', "Guitar origin relative to the chest bone head, in the rest-aligned chest frame (X: the character's left, Y: up, Z: forward), before the spine auto-scale"): '',
    # props.py:GTR_Settings
    ('*', "Hands whose quick motion passes through the magnets: the magnets act on the slow part of the wrist's path, and the strokes ride on top. The fretting hand needs its magnets to hold it on the fretboard"): '',
    # props.py:GTR_BoneMap
    ('*', 'Head bone'): '',
    # props.py:GTR_BoneMap
    ('*', 'Hips bone'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far a hand point was behind a barrier plane before it was clamped'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far a solved wrist ended from its target'): '',
    # props.py:GTR_Settings
    ('*', 'How far fingertip magnets keep the nearest fingertip above their plane, before the arm-ratio scaling (SAO: the reference palm length / 4)'): '',
    # props.py:GTR_Settings
    ('*', "How far in front of the chest bone head the capsule's axis runs"): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the chest collider pushed a wrist'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the fretting wrist turned away from the mocap'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the neck aim turned the guitar from its mount'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the solve moved a wrist target from the mocap wrist'): '',
    # props.py:GTR_Settings
    ('*', "How lengths authored for SAO's reference avatar fit this character. Magnet distances scale with the arm, and the mount with the spine, except under None"): '',
    # props.py:GTR_Prep
    ('*', "How many frames the arm's swing leads the hand's stroke"): '',
    # props.py:GTR_Prep
    ('*', "How much larger the fretting fingers' quick moves get, per joint (1: unchanged). Quick presses overshoot slightly"): '',
    # props.py:GTR_Prep
    ('*', "How much larger the picking hand's quick turns get, relative to the forearm (1: unchanged)"): '',
    # props.py:GTR_Prep
    ('*', 'How much of the swing the elbow makes against the shoulder'): '',
    # props.py:GTR_BoneMap
    ('*', 'IK chain length from the IK forearm up to the IK upper arm (0: not a valid chain)'): '',
    # props.py:GTR_Guitar
    ('*', 'Id or file of the preset the landmarks were fitted from'): '',
    # props.py:GTR_Settings
    ('*', 'In the rest-aligned upper-arm frame. SAO: (0°, 10°, -15°), order ZYX in three.js'): '',
    # props.py:GTR_Settings
    ('*', 'Instrument preset: landmarks, magnets, mount, aim and wrist settings'): '',
    # props.py:GTR_Settings
    ('*', 'Keep the index, middle and ring fingertips out as well'): '',
    # props.py:GTR_Settings
    ('*', 'Keep wrist targets within this share of the arm chain length, or as far as the mocap wrist if it is further'): '',
    # props.py:GTR_Settings
    ('*', 'Key GTR_ROOT in world space, without a parent'): '',
    # props.py:GTR_RangeOverride
    ('*', 'Last frame of the range'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Forearm bone'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Hand bone'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Left Upper Arm bone'): '',
    # props.py:GTR_Settings
    ('*', "Low-pass only what the solve changed in the arms, so the mocap's own quick motion (and the prep's) stays"): '',
    # ops/bake.py:GTR_OT_smooth_bake
    ('*', 'Low-pass the baked arm and guitar keys, forward and backward so nothing lags; in Correction mode only what\nthe solve changed in the arms, so their quick motion stays. Re-clamp afterwards to restore the contacts. Esc\ncancels'): '',
    # props.py:GTR_Settings
    ('*', 'Low-pass the baked arm keys themselves'): '',
    # props.py:GTR_Settings
    ('*', "Lower end of the capsule's axis relative to the chest bone head"): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Lower fretboard edge (-Y) near the neck/body joint: start of the neck axis the aim swings (SAO reference_origin)'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Lower fretboard edge at the nut: end of the aimed neck axis (SAO reference_point)'): '',
    # props.py:GTR_Settings
    ('*', "Magnet hand offsets scale with the arm, like SAO's arm-normalised magnet space for VRM avatars"): '',
    # props.py:GTR_Settings
    ('*', 'Magnet hand offsets scale with the palm, like the neck aim'): '',
    # props.py:GTR_Settings
    ('*', 'Magnets whose Filter is One Euro: minimum cutoff (Hz), beta and derivative cutoff (Hz) on their pull (SAO)'): '',
    # props.py:GTR_Settings
    ('*', "Magnets whose Filter is Rotation: minimum cutoff (Hz), beta and derivative cutoff (Hz) on the hand's angle about the guitar origin (SAO)"): '',
    # ops/setup.py:GTR_OT_calibrate
    ('*', 'Measure the character in rest pose: character frame, rest-aligned frames, ratios, axis_rot, fingertips'): '',
    # props.py:GTR_Prep
    ('*', 'Motion slower than this is the posture, which Range and Snap keep; faster motion is the detail they work on'): '',
    # ops/magnets.py:GTR_OT_magnet_move
    ('*', 'Move the active magnet up or down the list. Magnets act in list order'): '',
    # props.py:GTR_Prep
    ('*', 'Move the forearm roll from the wrist onto the forearm twist bone (MMD 手捩) on both hands, so the forearm skin twists with it. The hands keep their pose'): '',
    # ops/mount.py:GTR_OT_place_on_mount
    ('*', "Move the guitar to its chest mount for the current frame's pose"): '',
    # ops/prep.py:GTR_OT_toggle_prep
    ('*', 'Mute or unmute the GuitarPrep layer, to compare the prepped motion with the original'): '',
    # props.py:GTR_Settings
    ('*', 'Name of the preset the mount came from'): '',
    # props.py:GTR_BoneMap
    ('*', 'Naming conventions the last auto-map matched'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Neck end of the strum line (SAO magnet 0)'): '',
    # props.py:GTR_Guitar
    ('*', 'No landmarks were placed by the add-on'): '',
    # props.py:GTR_Settings
    ('*', 'No mount yet: load a preset or capture it'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', "Normal +X: holds the picking hand's position along the strings (SAO magnet 1)"): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Normal +X: the fretting hand stays on the headstock side of the neck/body joint (SAO magnet 4)'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', "Normal +Z: the picking hand's fingertips stay above it (SAO magnet 2)"): '',
    # props.py:GTR_Settings
    ('*', 'Nothing is scaled to the character'): '',
    # props.py:GTR_Magnet
    ('*', 'Off: the plane is a barrier, and a hand behind it is clamped onto it with full weight'): '',
    # props.py:GTR_Magnet
    ('*', 'Offset from the wrist in the rest-aligned hand frame, in metres'): '',
    # props.py:GTR_Guitar
    ('*', 'One cue decided, or one of three disagreed'): '',
    # props.py:GTR_Magnet
    ('*', 'One-euro filter on the pull'): '',
    # props.py:GTR_Settings
    ('*', 'One-euro minimum cutoff (Hz), beta and derivative cutoff (Hz)'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Optional, normal -X: the fretting hand stays on the body side of the nut (SAO magnet 6, ukulele)'): '',
    # props.py:GTR_Settings
    ('*', 'Parent GTR_ROOT to the chest bone and key it relative to the bone, so the guitar follows later edits of the body'): '',
    # props.py:GTR_Magnet
    ('*', "Place the feature with the guitar's chest-mount rotation, before the neck aim"): '',
    # props.py:GTR_Guitar
    ('*', "Placed by the preset fitted to the guitar's bounds and neck"): '',
    # props.py:GTR_Guitar
    ('*', 'Placed on the neck, heel and body found on the mesh'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Plane through the lower fretboard edge, normal +Y: the fretting hand stays above it (SAO magnet 5)'): '',
    # ops/bake.py:GTR_OT_reclamp
    ('*', 'Play the bake back and, on the frames where a hand went into a barrier or the chest collider, push it out\nand solve that arm again. Esc cancels'): '',
    # props.py:GTR_Settings
    ('*', 'Post-bake low-pass cutoff for the arm channels'): '',
    # props.py:GTR_Settings
    ('*', 'Post-bake low-pass cutoff for the guitar channels'): '',
    # props.py:GTR_Magnet
    ('*', 'Pull toward the segment from landmark A to landmark B'): '',
    # props.py:GTR_Magnet
    ('*', "Pull toward, or clamp against, the plane through landmark A (normal: A's local Z)"): '',
    # props.py:GTR_Settings
    ('*', 'Push the wrists and their fingertips forward out of a capsule around the torso, before the magnets act'): '',
    # props.py:GTR_Settings
    ('*', 'Radius of the capsule, before the spine auto-scale'): '',
    # props.py:GTR_Settings
    ('*', 'Re-clamp re-solves the frames where a hand is further than this into a barrier or the chest collider'): '',
    # props.py:GTR_Magnet
    ('*', 'Reach of the magnet in metres, before arm-ratio scaling. Barriers need it too'): '',
    # ops/bake.py:GTR_OT_remove_bake
    ('*', "Remove the GuitarBake and GuitarRefine tracks and the bake actions, and put back the animation and the\nguitar's parent as they were before the bake. Refine actions with keys are kept"): '',
    # ops/prep.py:GTR_OT_remove_prep
    ('*', 'Remove the GuitarPrep layer and its action: the solve and the bake read the original mocap again. The bake\nstays'): '',
    # ops/magnets.py:GTR_OT_magnet_remove
    ('*', 'Remove the active magnet'): '',
    # ops/rig.py:GTR_OT_range_remove
    ('*', 'Remove the active range override'): '',
    # ops/rig.py:GTR_OT_clean_rig
    ('*', 'Remove the helper rig: its constraints, its empties and the GuitarRig collection'): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Replace the magnet list with the preset's"): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Replace the mount with the preset's estimate (off when the mount was captured)"): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Forearm bone'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Hand bone'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Distal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Intermediate bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Proximal bone (optional)'): '',
    # props.py:GTR_BoneMap
    ('*', 'Right Upper Arm bone'): '',
    # props.py:GTR_Magnet
    ('*', 'Role of the magnet in a preset (e.g. FRETBOARD_PLANE); mode switches find magnets by it'): '',
    # props.py:GTR_Magnet
    ('*', 'Rotate the offset by axis_rot, as SAO does for avatars whose rest pose is not a T-pose; axis_rot is the identity on T-pose rigs'): '',
    # props.py:GTR_Magnet
    ('*', "SAO's reference_point_offset_distance: shifts the plane along its normal for the fingertips. In GTR_ROOT units, so it scales with the guitar (metres for a real-size guitar at scale 1)"): '',
    # props.py:GTR_Settings
    ('*', "SAO's rotation_reference offset"): '',
    # props.py:GTR_Settings
    ('*', "SAO's setting (-1) in all guitar scenes"): '',
    # ops/guitar.py:GTR_OT_save_preset
    ('*', 'Save the landmarks, magnets, mount, aim and wrist settings as a preset file for other guitars'): '',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('*', 'Scale GTR_ROOT so that the guitar is this long, in metres; 0 keeps its size'): '',
    # props.py:GTR_Prep
    ('*', 'Scales every tool toward doing nothing (0) or beyond its strength (above 1)'): '',
    # ops/bake.py:GTR_OT_show_diagnostics
    ('*', 'Select the GTR_Diagnostics empty, whose curves show what the solve did on each frame in the Graph Editor'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Select the landmark, or add it at the 3D cursor if it does not exist'): '',
    # props.py:GTR_Settings
    ('*', 'Share of each new aim rotation taken per iteration; lower it if the guitar oscillates between iterations'): '',
    # props.py:GTR_Settings
    ('*', 'Share of the guitar-relative rotation in the fretting wrist'): '',
    # props.py:GTR_Settings
    ('*', 'Share of the quick wrist motion that passes through (0: the magnets act on all of it)'): '',
    # props.py:GTR_Magnet
    ('*', 'Shift the hand so that the nearest fingertip lands on the plane'): '',
    # ops/prep.py:GTR_OT_toggle_prep
    ('*', 'Show the original mocap (mute the prep layer)'): '',
    # props.py:GTR_Guitar
    ('*', "Size of the guitar relative to the preset's reference, along X (neck length), Y (neck width) and Z (neck thickness)"): '',
    # props.py:GTR_Settings
    ('*', 'Smooth between the per-frame keys'): '',
    # ops/bake.py:GTR_OT_bake
    ('*', 'Solve every frame of the range and key the arms and the guitar into GuitarBake NLA strips, with a\nGuitarRefine layer on top for your corrections. Esc cancels'): '',
    # props.py:GTR_Settings
    ('*', 'Solve iterations per frame: in Follow mode, neck aims, each followed by the magnets and the IK'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'Solve passes on the frames whose neck aim or wrists had not settled'): '',
    # ops/rig.py:GTR_OT_solve_frame
    ('*', 'Solve the current frame: the guitar goes on its mount and the magnets move the wrists. The arms show the\nresult until the frame changes'): '',
    # props.py:GTR_Prep
    ('*', "Steepness of the fretting fingers' presses and releases (1: unchanged)"): '',
    # props.py:GTR_Prep
    ('*', "Steepness of the picking fingers' moves (1: unchanged)"): '',
    # props.py:GTR_Prep
    ('*', "Steepness of the picking hand's strokes: each stroke is retimed along an S-curve with this exponent, keeping where it starts, ends and crosses half way (1: unchanged)"): '',
    # ops/mount.py:GTR_OT_capture_wrist_offset
    ('*', "Store the fretting hand's rotation relative to the guitar in the current frame's pose as the wrist target.\nPose the guitar and the fretting hand on its neck first"): '',
    # ops/mount.py:GTR_OT_capture_mount
    ('*', "Store where the guitar sits relative to the chest in the current frame's pose as the mount. Pose the\nguitar on the character first (move and rotate GTR_ROOT)"): '',
    # props.py:GTR_Settings
    ('*', 'Straight between the per-frame keys'): '',
    # props.py:GTR_Prep
    ('*', 'Strokes of the picking hand smaller than this are left as they are'): '',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Swap the headstock and body ends (half turn about Z)'): '',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Swap the string face and the back (half turn about X)'): '',
    # props.py:GTR_Settings
    ('*', 'Swing the neck toward the fretting wrist (FOLLOW mode)'): '',
    # ops/rig.py:GTR_OT_clear_solve
    ('*', "Switch the rig's constraints off, so that the arms play the mocap again"): '',
    # props.py:GTR_Settings
    ('*', "Switches the neck aim and the fretboard-edge magnet like SAO's Alt+A; the fields stay editable"): '',
    # props.py:GTR_Settings
    ('*', 'The GuitarRig collection that holds the helper empties'): '',
    # props.py:GTR_Magnet
    ('*', 'The aim hand offset (SAO\'s "parent_bone" offset)'): '',
    # props.py:GTR_Settings
    ('*', "The armature that carries the helper rig's constraints"): '',
    # props.py:GTR_BoneMap
    ('*', 'The bone the guitar mounts on: the humanoid chest (MMD 上半身2, VRM chest)'): '',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('*', "The character's left hand"): '',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('*', "The character's right hand"): '',
    # props.py:GTR_Guitar
    ('*', 'The cues disagree or are missing: check the axes'): '',
    # props.py:GTR_Fingertip
    ('*', "The distal bone's tail"): '',
    # props.py:GTR_Settings
    ('*', "The empty whose animated custom properties hold what the last bake's solve did on each frame"): '',
    # props.py:GTR_Magnet
    ('*', 'The fingertips may push the hand away from the plane but never pull it in'): '',
    # props.py:GTR_BoneMap
    ('*', 'The forearm that carries the IK constraint; on Rigify-style rigs, the FK control'): '',
    # props.py:GTR_Settings
    ('*', 'The frame whose solve the rig shows'): '',
    # props.py:GTR_Guitar
    ('*', 'The guitar frame or the body is doubtful: check the landmarks'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('*', "The guitar stays on the chest and the fretting hand slides along the fretboard edge (SAO's Alt+A mode)"): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('*', "The guitar yaws toward the fretting hand (SAO's default mode)"): '',
    # props.py:GTR_Magnet
    ('*', 'The hand point itself meets the plane'): '',
    # props.py:GTR_BoneMap
    ('*', 'The hand that gets the wrist rotation; on Rigify-style rigs, the FK control'): '',
    # props.py:GTR_BoneMap
    ('*', 'The left one is used for the spine length (optional)'): '',
    # props.py:GTR_RangeOverride
    ('*', "The mode's switch applies to these frames on top of the scene's settings"): '',
    # props.py:GTR_Guitar
    ('*', 'The neck, the heel and the body were all found'): '',
    # props.py:GTR_Magnet
    ('*', 'The offset vector below'): '',
    # props.py:GTR_Settings
    ('*', 'The retargeted character armature that plays the mocap'): '',
    # props.py:GTR_Settings
    ('*', "The rig's constraints are on and show the solve of Solve Frame"): '',
    # props.py:GTR_BoneMap
    ('*', 'The upper arm the IK drives; on Rigify-style rigs, the FK control'): '',
    # props.py:GTR_Magnet
    ('*', 'The wrist itself'): '',
    # ops/prep.py:GTR_OT_apply_prep
    ('*', 'Touch up the mocap before the bake: wider and crisper picking strokes, an arm swing, crisp fretting\nfingers and the forearm roll on the twist bone. Reads the original mocap and writes a GuitarPrep NLA layer,\nwhich the solve and the bake then read. Esc cancels'): '',
    # props.py:GTR_Calibration
    ('*', 'Turn the character frame half a turn about the up axis, if the detected facing is wrong'): '',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Turn the guitar frame half a turn (the guitar stays in place) and fit the landmarks again'): '',
    # props.py:GTR_Settings
    ('*', 'Turn the other way (+1)'): '',
    # props.py:GTR_Settings
    ('*', "Turn the right arm before the IK, like SAO's root_rotation: this moves where the right elbow points"): '',
    # props.py:GTR_Settings
    ('*', "Upper end of the capsule's axis above the chest bone head, along the chest's up axis"): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Use the preset's aim hand offset and wrist rotation (off when the wrist offset was captured)"): '',
    # props.py:GTR_BoneMap
    ('*', 'Used for the spine length (optional)'): '',
    # props.py:GTR_Prep
    ('*', 'What the last Apply Prep did'): '',
    # props.py:GTR_Settings
    ('*', 'What the last bake, smoothing or re-clamp did'): '',
    # props.py:GTR_Settings
    ('*', 'What the worst frames are ranked by'): '',
    # props.py:GTR_Settings
    ('*', "When the mocap wrist faces more than 120° away from the target about the up axis, turn it this way instead of the shorter way (SAO's constrained_direction)"): '',
    # props.py:GTR_Settings
    ('*', 'Wrist motion faster than this, relative to the chest, passes through the magnets'): '',
    # props.py:GTR_Settings
    ('*', "XR Animator's Stratocaster scene (guitar_collection_v9.1/scene - stratocaster guitar.json)"): '',
    # props.py:GTR_Settings
    ('*', "XR Animator's acoustic guitar scene (guitar_collection_v9.1/scene.json)"): '',
    # props.py:GTR_Settings
    ('*', "XR Animator's bass guitar scene (guitar_collection_v9.1/scene - bass guitar.json)"): '',
    # props.py:GTR_Settings
    ('*', "XR Animator's ukulele scene (guitar_collection_v9.1/scene - ukulele.json)"): '',
    # ui/panels.py:572
    ('GuitarRig', '   pass-through'): '',
    # ui/panels.py:578
    ('GuitarRig', '   {name}'): '',
    # core/solver.py:383
    ('GuitarRig', ' ({value})'): '',
    # core/guitar_frame.py:695
    ('GuitarRig', ' Conflicting cues: {cues}.'): '',
    # core/autoland.py:171
    ('GuitarRig', ' The body starts under the neck {past:.1f} cm past where the neck narrows (cutaways).'): '',
    # core/autoland.py:175
    ('GuitarRig', ' The heel reaches {value:.1f} cm up the neck from where it narrows.'): '',
    # core/bonemap.py:335
    ('GuitarRig', "'{name}' is mapped to both sides ({title} and its right twin)."): '',
    # core/bonemap.py:345
    ('GuitarRig', "'{name}' is used for both {value} and {title}."): '',
    # core/baker.py:753
    ('GuitarRig', '. Skipped curves whose keys are not one per frame: {skipped}'): '',
    # core/prepjob.py:557
    ('GuitarRig', '. Strokes snapped: {value}'): '',
    # core/prepjob.py:544
    ('GuitarRig', ". The pick point's travel: {value:.1f} → {value2:.1f} cm RMS"): '',
    # ui/panels.py:482
    ('GuitarRig', 'A capsule along the chest that pushes the wrists forward out of the torso before the magnets act. Lengths are metres before the spine auto-scale.'): '',
    # ui/panels.py:532
    ('GuitarRig', 'A range ends before it starts: it is ignored'): '',
    # presets/acoustic.json, props.py:GTR_Settings
    ('GuitarRig', 'Acoustic Guitar'): '',
    # ops/magnets.py:GTR_OT_magnet_add
    ('GuitarRig', 'Add Magnet'): '',
    # ops/rig.py:GTR_OT_range_add
    ('GuitarRig', 'Add Range Override'): '',
    # ops/guitar.py:498
    ('GuitarRig', 'Added {name} at the 3D cursor.'): '',
    # ui/panels.py:656
    ('GuitarRig', 'After the Bake'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Filter'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Hand Offset (m)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Neck'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Aim Offset'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Weight'): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('GuitarRig', 'Aim and Wrist'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('GuitarRig', 'Align'): '',
    # core/calibrate.py:233
    ('GuitarRig', 'An arm, palm or spine length is zero or negative; check the bone map.'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Apply Axis Rotation'): '',
    # ops/prep.py:GTR_OT_apply_prep
    ('GuitarRig', 'Apply Prep'): '',
    # ops/prep.py:48
    ('GuitarRig', 'Apply Prep first'): '',
    # ui/panels.py:307
    ('GuitarRig', 'Apply Prep touches up the mocap before the bake: wider, crisper picking strokes with an arm swing, crisp fretting fingers, and the forearm roll on the twist bone. Your action is not changed.'): '',
    # ui/panels.py:226, ui/panels.py:48
    ('GuitarRig', 'Arm'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Arm Cutoff (Hz)'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Length (m)'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Ratio'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Reference Angle'): '',
    # ops/setup.py:GTR_OT_auto_map_bones
    ('GuitarRig', 'Auto-Map Bones'): '',
    # ops/guitar.py:GTR_OT_auto_landmarks
    ('GuitarRig', 'Auto-Place'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Auto-Placed'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Auto-Scale'): '',
    # ui/panels.py:LANDMARK_TEXT
    ('GuitarRig', 'Auto-placed'): '',
    # ui/panels.py:143
    ('GuitarRig', 'Auto-placed ({confidence} confidence)'): '',
    # ops/guitar.py:550
    ('GuitarRig', "Auto-placed {landmarks_count} landmarks with the {name} preset's conventions ({value} confidence). Check them."): '',
    # ops/guitar.py:GTR_OT_flip_frame
    ('GuitarRig', 'Axis'): '',
    # ops/bake.py:GTR_OT_bake, ui/panels.py:GTR_PT_bake
    ('GuitarRig', 'Bake'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bake Report'): '',
    # ops/bake.py:142, ops/bake.py:164
    ('GuitarRig', 'Bake first'): '',
    # ops/bake.py:200
    ('GuitarRig', 'Bake first: the bake records the diagnostics'): '',
    # core/baker.py:799
    ('GuitarRig', 'Bake first: the character has no GuitarBake strip.'): '',
    # ui/panels.py:671
    ('GuitarRig', 'Bake keys the arms and the guitar into GuitarBake NLA strips; correct them on the GuitarRefine layer above.'): '',
    # ui/panels.py:686
    ('GuitarRig', "Bake to record what the solve did on each frame: the wrist corrections, each magnet's distance and weight, the neck swing."): '',
    # core/baker.py:529
    ('GuitarRig', 'Baked frames {start}-{end} ({count} frames) in {elapsed:.1f} s ({value:.1f} frames/s): {keyed} arm bones and the guitar.'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Barrier Depth'): '',
    # ui/lists.py:19
    ('GuitarRig', 'Barrier — Left'): '',
    # ui/lists.py:19
    ('GuitarRig', 'Barrier — Right'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Barriers Ignore Distance'): '',
    # presets/bass.json, props.py:GTR_Settings
    ('GuitarRig', 'Bass Guitar'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bezier'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bias'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Body'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Body end of the strum line the picking hand is pulled to (SAO magnet 0)'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Bone Tail'): '',
    # ui/panels.py:GTR_PT_bones
    ('GuitarRig', 'Bones'): '',
    # core/guitar_frame.py:685
    ('GuitarRig', 'Both ends are about as wide ({ratio:.2f}×): check that +X points to the headstock, and use Flip X if not.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bottom (m)'): '',
    # props.py:GTR_Guitar, ui/panels.py:117
    ('GuitarRig', 'Bounds'): '',
    # ops/rig.py:GTR_OT_build_rig, ui/panels.py:502
    ('GuitarRig', 'Build Rig'): '',
    # ui/panels.py:508
    ('GuitarRig', 'Build Rig adds IK and rotation constraints to each arm. They stay off, so the mocap plays as before, until you solve a frame.'): '',
    # ops/rig.py:29
    ('GuitarRig', 'Build the rig first'): '',
    # ops/rig.py:66
    ('GuitarRig', 'Built the helper rig on {name}. With its goals on the current pose, the IK reproduces the arms within {worst:.3f} mm.'): '',
    # ops/setup.py:GTR_OT_calibrate
    ('GuitarRig', 'Calibrate'): '',
    # ops/prep.py:35, ui/panels.py:259
    ('GuitarRig', 'Calibrate first'): '',
    # ops/mount.py:30, ops/rig.py:15
    ('GuitarRig', 'Calibrate the character first'): '',
    # core/prepjob.py:294, core/solver.py:398, ops/mount.py:23, rig/build.py:241
    ('GuitarRig', 'Calibrate the character first.'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Calibrated'): '',
    # ops/setup.py:82
    ('GuitarRig', 'Calibrated: height {height:.2f} m; ratios arm {ratio_arm:.3f}, palm {ratio_palm:.3f}, spine {ratio_spine:.3f}'): '',
    # ui/panels.py:GTR_PT_calibration
    ('GuitarRig', 'Calibration'): '',
    # core/presets.py:139
    ('GuitarRig', 'Cannot read the preset {preset_id_or_path!r}: {value}.'): '',
    # ops/guitar.py:466
    ('GuitarRig', 'Cannot write {path}: {value}.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Capture Frame'): '',
    # ops/mount.py:GTR_OT_capture_mount
    ('GuitarRig', 'Capture Mount'): '',
    # ops/mount.py:GTR_OT_capture_wrist_offset
    ('GuitarRig', 'Capture Wrist Offset'): '',
    # props.py:GTR_Settings, ui/panels.py:MOUNT_TEXT, ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'Captured'): '',
    # ui/panels.py:332, ui/panels.py:368
    ('GuitarRig', 'Captured at frame {frame}'): '',
    # props.py:GTR_BoneMap
    ('GuitarRig', 'Chain Count'): '',
    # ui/panels.py:187
    ('GuitarRig', 'Chain count: invalid'): '',
    # ui/panels.py:187
    ('GuitarRig', 'Chain count: {count}'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Character'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Character Frame'): '',
    # core/guitar_frame.py:698
    ('GuitarRig', 'Check that +Z points out of the strings, and use Flip Z if not.'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Chest (Mount)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Chest Bone'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Chest Collider'): '',
    # ui/overlay.py:306
    ('GuitarRig', 'Chest collider: {moved:.1f} cm'): '',
    # ops/rig.py:GTR_OT_clean_rig
    ('GuitarRig', 'Clean Rig'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Confidence'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Correction'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Correction Filter'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Crossable'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Custom'): '',
    # props.py:GTR_Prep, props.py:GTR_Settings
    ('GuitarRig', 'Cutoff (Hz)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Depth (m)'): '',
    # props.py:GTR_Settings, ui/panels.py:GTR_PT_diagnostics
    ('GuitarRig', 'Diagnostics'): '',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Direction'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Distal Bone'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Distance (m)'): '',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Down'): '',
    # core/baker.py:128
    ('GuitarRig', 'Drivers on GTR_ROOT override its baked keys.'): '',
    # core/baker.py:111
    ('GuitarRig', 'Drivers on {name} override its baked keys.'): '',
    # ui/panels.py:533
    ('GuitarRig', 'Each range solves its frames in its mode: the neck aim and the fretboard-edge magnet switch as with the mode buttons. Lower ranges win where they overlap. The neck aim fades over {FADE_FRAMES} frames at each change.'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Elbow Share'): '',
    # props.py:GTR_Magnet, props.py:GTR_RangeOverride
    ('GuitarRig', 'Enabled'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings, ui/panels.py:388
    ('GuitarRig', 'End'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Estimated'): '',
    # core/prepjob.py:298
    ('GuitarRig', 'Every tool is off (Intensity 0, or each strength neutral): there is nothing to apply.'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Filter'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Filters'): '',
    # ui/panels.py:428
    ('GuitarRig', 'Filters are switched off (Bake > Filters).'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Finger'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingers'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Fingertip Filter'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingertip Offset'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingertip v2'): '',
    # props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'Fingertips'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Fit'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Fit Scale'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Flip Facing'): '',
    # ops/guitar.py:GTR_OT_flip_frame
    ('GuitarRig', 'Flip Frame'): '',
    # ops/guitar.py:GTR_OT_flip_frame, ui/panels.py:108
    ('GuitarRig', 'Flip X'): '',
    # ops/guitar.py:GTR_OT_flip_frame, ui/panels.py:109
    ('GuitarRig', 'Flip Z'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('GuitarRig', 'Follow'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Forearm'): '',
    # ui/panels.py:524
    ('GuitarRig', 'Frame {frame}: {mode}'): '',
    # ui/panels.py:526
    ('GuitarRig', 'Frame {frame}: {mode} (range {range_number})'): '',
    # ops/bake.py:238
    ('GuitarRig', 'Frame {frame}: {name} {value}.'): '',
    # core/solver.py:390
    ('GuitarRig', 'Frame {frame}: {summary}.'): '',
    # ui/panels.py:698
    ('GuitarRig', 'Frame {frame}: {value}'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Fretboard Edge'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Fretboard Plane'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Fretboard surface, normal +Z: the fretting hand snaps onto it (SAO magnet 3)'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Fretting Fingers'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Fretting Wrist'): '',
    # ui/panels.py:584
    ('GuitarRig', 'Fretting wrist'): '',
    # core/mount.py:57
    ('GuitarRig', 'GTR_ROOT has a negative (mirroring) scale: use Flip X or Flip Z instead of a negative scale.'): '',
    # core/baker.py:126
    ('GuitarRig', 'GTR_ROOT has constraints, which act on top of its baked keys.'): '',
    # core/baker.py:122
    ('GuitarRig', 'GTR_ROOT has delta transforms: clear them (Object properties > Transform > Delta Transform) before baking.'): '',
    # ops/guitar.py:117, ops/guitar.py:527
    ('GuitarRig', 'GTR_ROOT has no meshes below it: normalise the guitar first.'): '',
    # ops/mount.py:73
    ('GuitarRig', 'GTR_ROOT is animated: its animation moves it back on the next frame change.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Gain'): '',
    # ops/bake.py:223
    ('GuitarRig', 'Go to worst frame #{rank} by {measure}: {description}'): '',
    # ui/panels.py:GTR_PT_guitar
    ('GuitarRig', 'Guitar'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Guitar Cutoff (Hz)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Guitar Keys'): '',
    # props.py:GTR_Guitar, props.py:GTR_Settings
    ('GuitarRig', 'Guitar Root'): '',
    # ops/guitar.py:243
    ('GuitarRig', 'Guitar frame found ({value} confidence); the guitar is {length:.2f} m long. Check the axes, then load a preset.'): '',
    # ui/panels.py:GTR_PT_main
    ('GuitarRig', 'GuitarRig'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_Magnet
    ('GuitarRig', 'Hand'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Hand Offset'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Handedness'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Hands'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Head'): '',
    # ui/panels.py:225
    ('GuitarRig', 'Height'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Height (m)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Hide Meshes While Baking'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'High'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Hips'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far a hand point was behind a barrier plane before it was clamped'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far a solved wrist ended from its target'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the chest collider pushed a wrist'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the fretting wrist turned away from the mocap'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the neck aim turned the guitar from its mount'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the solve moved a wrist target from the mocap wrist'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Hysteresis'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'IK Miss'): '',
    # ui/panels.py:233
    ('GuitarRig', 'IK chain L / R'): '',
    # ui/panels.py:359
    ('GuitarRig', 'In Follow mode the neck swings toward the magenta aim point on the fretting hand; Align mode switches the aim off.'): '',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Index'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Distal'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Intermediate'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Proximal'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Intensity'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Interpolation'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Iterations'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Joint Margin'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('GuitarRig', 'Jump to Worst Frame'): '',
    # core/baker.py:973
    ('GuitarRig', 'Kept the refine actions with your keys ({value}) with a fake user.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Keys'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Kind'): '',
    # ui/panels.py:222
    ('GuitarRig', 'L {left}, R {right} ({estimated} estimated)'): '',
    # ui/panels.py:218
    ('GuitarRig', 'L {value}, R {value2}'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Landmark A'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Landmark B'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Landmark Confidence'): '',
    # props.py:GTR_Guitar, ui/panels.py:137
    ('GuitarRig', 'Landmarks'): '',
    # ui/panels.py:136
    ('GuitarRig', 'Landmarks ({count} missing)'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Lead (frames)'): '',
    # ops/setup.py:17
    ('GuitarRig', 'Leave Edit Mode first'): '',
    # core/bonemap.py:318, props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'Left'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left Arm'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Left Axis Rotation'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Left Chain Length (m)'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left Fingers'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Forearm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Hand'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left IK Chain'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Forearm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Hand'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Upper Arm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Proximal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Proximal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Proximal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Upper Arm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Upper Leg'): '',
    # ui/panels.py:570
    ('GuitarRig', 'Left wrist'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Left-Handed'): '',
    # ui/panels.py:110
    ('GuitarRig', 'Length'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Length (m)'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Line'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Linear'): '',
    # ops/guitar.py:GTR_OT_load_preset
    ('GuitarRig', 'Load Preset'): '',
    # ops/guitar.py:GTR_OT_load_preset_file
    ('GuitarRig', 'Load Preset File'): '',
    # ui/panels.py:453
    ('GuitarRig', "Load a preset for SAO's magnets, or add your own. They act in list order."): '',
    # ui/panels.py:342
    ('GuitarRig', 'Load a preset for a first estimate, or pose the guitar on the character (move and rotate GTR_ROOT) and capture it.'): '',
    # ops/mount.py:36, ops/rig.py:35
    ('GuitarRig', 'Load a preset or capture the mount first'): '',
    # core/solver.py:585
    ('GuitarRig', 'Load a preset or capture the mount first.'): '',
    # ui/panels.py:158
    ('GuitarRig', 'Load a preset to place the landmarks, or Auto-Place them on the neck and body the add-on finds, then check them on the guitar.'): '',
    # ops/guitar.py:342
    ('GuitarRig', 'Loaded {name}: fitted to the {value} (×{value2:.2f} long, ×{value3:.2f} wide, ×{value4:.2f} deep). Check the landmarks.'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Low'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Lower fretboard edge (-Y) near the neck/body joint: start of the neck axis the aim swings (SAO reference_origin)'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Lower fretboard edge at the nut: end of the aimed neck axis (SAO reference_point)'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'MMD (Japanese names)'): '',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', "Magnet 3 uses SAO's offset_fingertip (v1), which min.js runs through the same code as v2: it is fingertip v2 without push-only."): '',
    # presets/ukulele.json
    ('GuitarRig', 'Magnet 6, the nut barrier, is only in the ukulele scene: its neck is short enough for the fretting hand to slide past the nut.'): '',
    # core/solver.py:142
    ('GuitarRig', 'Magnet {name} is missing a landmark and was skipped.'): '',
    # core/presets.py:323
    ('GuitarRig', 'Magnet {name}: there is no {value} landmark.'): '',
    # core/presets.py:334
    ('GuitarRig', 'Magnet {name}: unknown setting {key!r} ignored.'): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file, ui/panels.py:GTR_PT_magnets
    ('GuitarRig', 'Magnets'): '',
    # ops/mount.py:142
    ('GuitarRig', 'Map the fretting hand bone first'): '',
    # ops/setup.py:45
    ('GuitarRig', 'Mapped {found} of {slots_count} bones ({source}). Check the map, then calibrate.'): '',
    # ui/panels.py:174
    ('GuitarRig', 'Matched: {source}'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Max Swing'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Measure'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Medium'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Metres per Unit'): '',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Middle'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Distal'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Intermediate'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Proximal'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Mixamo'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('GuitarRig', 'Mode'): '',
    # core/baker.py:550
    ('GuitarRig', 'Modes: {text} (* range override). The filters restarted at the {value} changes, where the neck aim fades over {FADE_FRAMES} frames.'): '',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file, props.py:GTR_Settings
    ('GuitarRig', 'Mount'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Offset (m)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Preset'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Rotation'): '',
    # ui/panels.py:GTR_PT_mount
    ('GuitarRig', 'Mount and Wrist'): '',
    # ops/mount.py:111
    ('GuitarRig', 'Mount captured at frame {mount_frame}: the guitar origin is {value:.1f} cm from the chest bone.'): '',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Move Magnet'): '',
    # ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'Name'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap, props.py:GTR_Guitar, ui/panels.py:117
    ('GuitarRig', 'Neck'): '',
    # props.py:GTR_Settings, ui/panels.py:350
    ('GuitarRig', 'Neck Aim'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Neck Found'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Neck Pivot'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Neck Swing'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Neck end of the strum line (SAO magnet 0)'): '',
    # ui/panels.py:581
    ('GuitarRig', 'Neck swing'): '',
    # core/autoland.py:163
    ('GuitarRig', 'Neck {value:.0f} cm from the {value2} to the nut, {value3:.1f} cm wide at the nut; fretboard tilted {value4:+.1f}°.'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Neck/Body Barrier'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Negative'): '',
    # core/autoland.py:114
    ('GuitarRig', 'No body was found under the neck: the Neck/Body Barrier and the strum line are placed from where the neck narrows. Check them.'): '',
    # core/calibrate.py:261
    ('GuitarRig', 'No finger bones on the {hand_name} hand: fingertip v2 is off there and only the palm margin applies.'): '',
    # ui/panels.py:695
    ('GuitarRig', 'No frame has any {measure}'): '',
    # ops/bake.py:231
    ('GuitarRig', 'No frame of the bake has a {name} above 0.'): '',
    # core/baker.py:939
    ('GuitarRig', 'No frame of {value}-{value2} needed a re-clamp (tolerance {value3:.1f} mm).'): '',
    # core/baker.py:941
    ('GuitarRig', 'No frames to re-clamp.'): '',
    # core/bonemap.py:259
    ('GuitarRig', "No humanoid chest bone found: the guitar will mount on '{value}'. Check Chest (Mount), and capture the mount again if you change it."): '',
    # core/calibrate.py:218
    ('GuitarRig', 'No left middle-finger proximal bone: the palm length is taken from the hand bone.'): '',
    # core/calibrate.py:228
    ('GuitarRig', 'No left upper-leg bone: the spine length is measured from the hips instead.'): '',
    # core/calibrate.py:224
    ('GuitarRig', 'No neck bone: the spine length is measured up to the head instead.'): '',
    # core/presets.py:287
    ('GuitarRig', 'No neck found on the guitar: the landmarks are fitted to the bounding box. Check them.'): '',
    # core/presets.py:288
    ('GuitarRig', 'No neck found on the preset reference: the landmarks are fitted to the bounding box. Check them.'): '',
    # core/guitar_frame.py:703
    ('GuitarRig', 'No neck found: preset landmarks are fitted to the bounding box and need checking.'): '',
    # core/autoland.py:104
    ('GuitarRig', 'No neck was found on the guitar: place the landmarks by hand, or load the preset and check them.'): '',
    # core/prepjob.py:163
    ('GuitarRig', 'No twist bone between the {value} forearm and hand: Roll is off there.'): '',
    # props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'None'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', "Normal +X: holds the picking hand's position along the strings (SAO magnet 1)"): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Normal +X: the fretting hand stays on the headstock side of the neck/body joint (SAO magnet 4)'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', "Normal +Z: the picking hand's fingertips stay above it (SAO magnet 2)"): '',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('GuitarRig', 'Normalise Frame'): '',
    # ui/panels.py:322, ui/panels.py:497, ui/panels.py:621
    ('GuitarRig', 'Normalise the guitar and calibrate first'): '',
    # ops/guitar.py:155, ops/mount.py:33, ops/rig.py:32
    ('GuitarRig', 'Normalise the guitar first'): '',
    # core/solver.py:583, ops/mount.py:20
    ('GuitarRig', 'Normalise the guitar first.'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Not Placed'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Not Set'): '',
    # ui/panels.py:207
    ('GuitarRig', 'Not calibrated'): '',
    # ui/panels.py:MOUNT_TEXT
    ('GuitarRig', 'Not set'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Nut'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Nut Barrier'): '',
    # ui/panels.py:370
    ('GuitarRig', 'Offset'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Offset (m)'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'One Euro'): '',
    # props.py:GTR_Settings, ui/panels.py:640
    ('GuitarRig', 'One Euro Magnets'): '',
    # ui/panels.py:646
    ('GuitarRig', "One-euro filters: minimum cutoff (Hz), beta and derivative cutoff (Hz), with SAO's values by default. Lower cutoffs smooth more and lag more."): '',
    # ops/bake.py:232
    ('GuitarRig', 'Only {ranked_count} frames have a {name} above 0.'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Optional, normal -X: the fretting hand stays on the body side of the nut (SAO magnet 6, ukulele)'): '',
    # ui/panels.py:539
    ('GuitarRig', 'Options'): '',
    # ops/prep.py:GTR_OT_toggle_prep
    ('GuitarRig', 'Original'): '',
    # ui/panels.py:243
    ('GuitarRig', "Overlay: red X (character's left), green Y (up), blue Z (forward); yellow and orange dots are fingertips, magenta is the neck-aim point."): '',
    # ui/panels.py:227
    ('GuitarRig', 'Palm'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Palm Length (m)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Palm Margin (m)'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Palm Ratio'): '',
    # props.py:GTR_Settings, ui/panels.py:458
    ('GuitarRig', 'Pass-Through'): '',
    # ui/panels.py:457
    ('GuitarRig', 'Pass-Through ({hands})'): '',
    # ui/panels.py:590
    ('GuitarRig', 'Passes'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Peak (m)'): '',
    # ops/setup.py:14
    ('GuitarRig', 'Pick the character armature first'): '',
    # ops/mount.py:18, rig/build.py:238
    ('GuitarRig', 'Pick the character armature first.'): '',
    # core/prepjob.py:292
    ('GuitarRig', 'Pick the character first.'): '',
    # ui/panels.py:72
    ('GuitarRig', 'Pick the retargeted character'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Fingers'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Strength'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Wrist'): '',
    # ops/mount.py:GTR_OT_place_on_mount
    ('GuitarRig', 'Place on Mount'): '',
    # ui/panels.py:LANDMARK_TEXT
    ('GuitarRig', 'Placed by the preset fit'): '',
    # props.py:GTR_Magnet, ui/panels.py:386
    ('GuitarRig', 'Plane'): '',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Plane through the lower fretboard edge, normal +Y: the fretting hand stays above it (SAO magnet 5)'): '',
    # core/baker.py:570
    ('GuitarRig', 'Played back within {value:.2f} mm of the solve.'): '',
    # core/baker.py:565
    ('GuitarRig', 'Played back, the bake is {value:.1f} mm from the solve at frame {error_frame}: something acts on top of the keys (constraints, drivers, other NLA tracks above the bake).'): '',
    # presets/acoustic.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the acoustic_guitar prop; placement.scale 0.088 makes 1 unit 0.008 m."): '',
    # presets/bass.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the bass_guitar prop; placement.scale 5.5599 makes 1 unit 0.505447 m."): '',
    # presets/strat.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the stratocaster_guitar prop; placement.scale 8.8 makes 1 unit 0.8 m."): '',
    # presets/ukulele.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the ukulele prop; placement.scale 2.2 makes 1 unit 0.2 m."): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Positive'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Power'): '',
    # ui/panels.py:GTR_PT_prep
    ('GuitarRig', 'Prep'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Prep Report'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Prep Serial'): '',
    # core/prepjob.py:57
    ('GuitarRig', 'Prep supports MMD models (MMD Tools) in this version'): '',
    # core/prepjob.py:394
    ('GuitarRig', 'Prepped frames {start}-{end} ({count} frames) in {elapsed:.1f} s: {set_rotations____set_locations__count} bones keyed on the GuitarPrep layer.'): '',
    # props.py:GTR_Guitar, props.py:GTR_Settings, ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'Preset'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Preset Fit'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Preset ID'): '',
    # ui/panels.py:MOUNT_TEXT
    ('GuitarRig', 'Preset estimate'): '',
    # ui/panels.py:330
    ('GuitarRig', 'Preset estimate ({preset})'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Push Only'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Radius (m)'): '',
    # ui/panels.py:270
    ('GuitarRig', 'Range'): '',
    # ui/panels.py:514
    ('GuitarRig', 'Range Overrides'): '',
    # ui/panels.py:514
    ('GuitarRig', 'Range Overrides ({count})'): '',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('GuitarRig', 'Rank'): '',
    # ops/bake.py:GTR_OT_reclamp
    ('GuitarRig', 'Re-clamp'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Re-clamp Tolerance (m)'): '',
    # core/baker.py:763
    ('GuitarRig', 'Re-clamp restores the contacts that smoothing loosened.'): '',
    # core/baker.py:944
    ('GuitarRig', 'Re-clamped {frames_count} frames: the left hand on {value}, the right hand on {value2}. The deepest was {value3:.1f} mm ({value4} hand, frame {value5}).'): '',
    # ui/panels.py:416
    ('GuitarRig', 'Reach'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Reach Clamp'): '',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('GuitarRig', 'Real Length (m)'): '',
    # ui/panels.py:502
    ('GuitarRig', 'Rebuild Rig'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Relax'): '',
    # ops/bake.py:GTR_OT_remove_bake
    ('GuitarRig', 'Remove Bake'): '',
    # ops/magnets.py:GTR_OT_magnet_remove
    ('GuitarRig', 'Remove Magnet'): '',
    # ops/prep.py:GTR_OT_remove_prep
    ('GuitarRig', 'Remove Prep'): '',
    # ops/rig.py:GTR_OT_range_remove
    ('GuitarRig', 'Remove Range Override'): '',
    # core/baker.py:971
    ('GuitarRig', 'Removed the bake. Actions removed: {count}.'): '',
    # ops/rig.py:92
    ('GuitarRig', 'Removed the helper rig.'): '',
    # core/prepjob.py:611
    ('GuitarRig', 'Removed the prep. Actions removed: {count}.'): '',
    # ops/guitar.py:302
    ('GuitarRig', 'Removed the {label} landmark: the {name} preset does not use it.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Rig Armature'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Rig Collection'): '',
    # core/bonemap.py:318, props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'Right'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right Arm'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Right Axis Rotation'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Right Chain Length (m)'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right Fingers'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Forearm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Hand'): '',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right IK Chain'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Forearm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Hand'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Upper Arm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Proximal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Proximal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Distal'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Intermediate'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Proximal'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Right Root Bias'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Upper Arm'): '',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Upper Leg'): '',
    # ui/panels.py:570
    ('GuitarRig', 'Right wrist'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Right-Handed'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify (deform bones)'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify (generated rig)'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify metarig names'): '',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Ring'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Distal'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Intermediate'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Proximal'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Role'): '',
    # ui/panels.py:290
    ('GuitarRig', 'Roll and Safety'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Roll to Twist Bone'): '',
    # core/prepjob.py:568
    ('GuitarRig', 'Roll: the {value} twist bone turns {value2:.0f}° to {value3:.0f}° (1st to 99th percentile); the hand keeps its pose.'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Rotation'): '',
    # props.py:GTR_Settings, ui/panels.py:642
    ('GuitarRig', 'Rotation Magnets'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'SAO Default'): '',
    # ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'SAO default'): '',
    # presets/ukulele.json
    ('GuitarRig', "SAO's string plane point is the strum line's start; only its height above the fretboard matters."): '',
    # ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'Save Preset'): '',
    # ops/guitar.py:468
    ('GuitarRig', 'Saved the preset to {path}.'): '',
    # ops/bake.py:GTR_OT_show_diagnostics
    ('GuitarRig', 'Select Curves'): '',
    # ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Select Landmark'): '',
    # ui/panels.py:103
    ('GuitarRig', 'Select the guitar meshes (or the empty they hang from), then Normalise Frame.'): '',
    # ops/guitar.py:188
    ('GuitarRig', 'Select the guitar meshes first'): '',
    # ops/guitar.py:202
    ('GuitarRig', 'Select the guitar meshes first.'): '',
    # ops/bake.py:270
    ('GuitarRig', 'Selected {name}: its curves are in the Graph Editor.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Shorter Way'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Show Magnets'): '',
    # ops/rig.py:GTR_OT_clear_solve
    ('GuitarRig', 'Show Mocap'): '',
    # ops/prep.py:GTR_OT_toggle_prep, ui/panels.py:299
    ('GuitarRig', 'Show Original'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Show Overlay'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Showing a Solve'): '',
    # core/prepjob.py:237
    ('GuitarRig', 'Showing the original mocap: the GuitarPrep layer is muted.'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Side'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Smallest Finger Move'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Smallest Stroke'): '',
    # ops/bake.py:GTR_OT_smooth_bake, props.py:GTR_Settings
    ('GuitarRig', 'Smooth'): '',
    # core/baker.py:742
    ('GuitarRig', "Smoothed the solve's correction on {smoothed} {name} curves at {cutoff:g} Hz"): '',
    # core/baker.py:745
    ('GuitarRig', 'Smoothed {smoothed} {name} curves at {cutoff:g} Hz'): '',
    # core/baker.py:761
    ('GuitarRig', "Smoothing the arm keys also smooths away the prep's quick motion: use Smooth Correction to keep it."): '',
    # ui/panels.py:275
    ('GuitarRig', 'Snap'): '',
    # ui/panels.py:GTR_PT_solve
    ('GuitarRig', 'Solve'): '',
    # ops/rig.py:GTR_OT_solve_frame
    ('GuitarRig', 'Solve Frame'): '',
    # ui/panels.py:599
    ('GuitarRig', 'Solve Frame shows the solved arms until the frame changes.'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Solve Serial'): '',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'Solve passes on the frames whose neck aim or wrists had not settled'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Solved Frame'): '',
    # props.py:GTR_BoneMap, props.py:GTR_Fingertip
    ('GuitarRig', 'Source'): '',
    # ui/panels.py:230
    ('GuitarRig', 'Spine'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Spine Length (m)'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Spine Ratio'): '',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings, ui/panels.py:386
    ('GuitarRig', 'Start'): '',
    # presets/strat.json, props.py:GTR_Settings
    ('GuitarRig', 'Stratocaster'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'String Plane'): '',
    # core/guitar_frame.py:693
    ('GuitarRig', 'String face from: {cues}.'): '',
    # props.py:GTR_Prep
    ('GuitarRig', 'Strokes'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Line A'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Line B'): '',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Position'): '',
    # props.py:GTR_Prep, ui/panels.py:285
    ('GuitarRig', 'Swing'): '',
    # ops/bake.py:255, ops/guitar.py:158, ops/guitar.py:184
    ('GuitarRig', 'Switch to Object Mode first'): '',
    # ops/mount.py:39, ops/prep.py:38, ops/rig.py:18
    ('GuitarRig', 'Switch to Object or Pose Mode first'): '',
    # core/baker.py:353
    ('GuitarRig', 'The GuitarPrep layer is muted (Show Original): the bake read the mocap without the prep.'): '',
    # core/baker.py:560
    ('GuitarRig', 'The IK missed its target on {misses_count} frames ({value}): check the arm bones for IK locks, limits or stretch.'): '',
    # core/calibrate.py:173
    ('GuitarRig', 'The armature object has a mirroring (negative) scale; rotations may be wrong.'): '',
    # core/calibrate.py:176
    ('GuitarRig', 'The armature object has a non-uniform scale; apply it for reliable rotations.'): '',
    # rig/build.py:243
    ('GuitarRig', 'The armature uses the iTaSC IK solver: switch it to Standard (Armature properties > Inverse Kinematics).'): '',
    # ui/panels.py:596
    ('GuitarRig', 'The arms show a solve whose details were lost (undo or reload): solve the frame again, or show the mocap.'): '',
    # ops/guitar.py:161, ops/guitar.py:191
    ('GuitarRig', 'The bake animates GTR_ROOT: remove the bake first'): '',
    # core/prepjob.py:401
    ('GuitarRig', 'The bake still holds the arms solved from the mocap before this prep: bake again.'): '',
    # core/prepjob.py:240
    ('GuitarRig', 'The bake was made before this prep: bake again.'): '',
    # core/prepjob.py:241
    ('GuitarRig', 'The bake was made from a prep that has been removed: bake again.'): '',
    # core/prepjob.py:614
    ('GuitarRig', 'The bake was made from a prep: bake again.'): '',
    # core/autoland.py:129
    ('GuitarRig', 'The body is short next to the neck: check the strum line.'): '',
    # core/calibrate.py:238
    ('GuitarRig', "The character is {height:.2f} m tall. GuitarRig works in metres: check the object scale and the scene's unit scale."): '',
    # core/mount.py:28, core/prepjob.py:128, core/solver.py:588
    ('GuitarRig', 'The chest bone is not mapped, or not in the armature.'): '',
    # ui/panels.py:427
    ('GuitarRig', 'The filter acts from frame to frame when baking: Solve Frame shows a frame unfiltered.'): '',
    # core/baker.py:342, core/prepjob.py:310
    ('GuitarRig', 'The frame range is empty.'): '',
    # ui/panels.py:375
    ('GuitarRig', 'The fretting wrist turns Wrist Blend of the way from the mocap to this rotation on the guitar. To set it, pose the hand on the neck and capture it.'): '',
    # core/autoland.py:139
    ('GuitarRig', 'The guitar frame has low confidence: check its axes first.'): '',
    # ops/guitar.py:248
    ('GuitarRig', 'The guitar is {length:.2f} m long: use Real Length to scale it to real size.'): '',
    # core/presets.py:284
    ('GuitarRig', 'The guitar or the preset reference has no extent along an axis.'): '',
    # core/presets.py:295
    ('GuitarRig', "The guitar's proportions differ a lot from the preset's; check the landmarks."): '',
    # rig/build.py:298
    ('GuitarRig', 'The helper rig could not be built.'): '',
    # ui/panels.py:505
    ('GuitarRig', 'The helper rig does not match the character or its bone map: build it again.'): '',
    # core/calibrate.py:86
    ('GuitarRig', 'The hips and head, or the two upper arms, are at the same place in rest pose.'): '',
    # core/calibrate.py:202
    ('GuitarRig', 'The index fingers sit behind the ring fingers relative to the detected facing (Z): left and right may be swapped in the bone map. Check the overlay, and use Flip Facing if the frame is wrong.'): '',
    # core/prepjob.py:591
    ('GuitarRig', 'The joint clamp held the {value} fingers on {hit_count} frames ({value2}).'): '',
    # core/baker.py:535
    ('GuitarRig', 'The largest wrist correction was {value:.1f} cm (frame {largest_frame})'): '',
    # ui/panels.py:466
    ('GuitarRig', "The magnets act on the slow part of these wrists' path, and the quick strokes ride on top, kept out of the barriers. Without it, a strum-line magnet takes back most of a stroke."): '',
    # core/guitar_frame.py:636
    ('GuitarRig', 'The meshes are flat or a line: they do not look like a guitar.'): '',
    # core/guitar_frame.py:632
    ('GuitarRig', 'The meshes have no faces to measure.'): '',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', 'The mount is only a starting guess: pose the guitar on the character and use Capture Mount.'): '',
    # core/baker.py:555
    ('GuitarRig', 'The neck aim did not settle on {unconverged_count} frames ({value}): raise Iterations or lower Relax.'): '',
    # core/solver.py:726
    ('GuitarRig', 'The neck aim had not settled after {value} iterations: raise Iterations, or lower Relax if the guitar oscillates.'): '',
    # core/solver.py:722
    ('GuitarRig', 'The neck aim was limited to {value:.0f}° (Max Swing): the fretting hand is far from the neck.'): '',
    # core/solver.py:598
    ('GuitarRig', 'The neck is not aimed: the Neck Pivot or Nut landmark is missing.'): '',
    # core/autoland.py:126
    ('GuitarRig', 'The neck or the body has no length along X: check the guitar frame (Flip X).'): '',
    # core/prepjob.py:232
    ('GuitarRig', 'The prep covers frames {first}-{last} only, and the bake range is {start}-{end}: Apply Prep again.'): '',
    # core/autoland.py:144, ops/guitar.py:126
    ('GuitarRig', 'The preset has an unknown landmark role {role!r}.'): '',
    # ops/guitar.py:315
    ('GuitarRig', 'The preset has no {label} landmark: add it by hand.'): '',
    # ui/panels.py:345
    ('GuitarRig', 'The preset mount is only an estimate: Place on Mount, adjust GTR_ROOT on the character, then Capture Mount.'): '',
    # ops/guitar.py:326
    ('GuitarRig', 'The preset mount is only an estimate: pose the guitar on the character and use Capture Mount.'): '',
    # core/presets.py:154
    ('GuitarRig', 'The preset {value} is malformed: {exc!r}.'): '',
    # core/presets.py:143
    ('GuitarRig', 'The preset {value} is not valid JSON: {exc}.'): '',
    # ops/mount.py:109
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again, then capture the mount again.'): '',
    # ops/mount.py:163
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again, then capture the wrist offset again.'): '',
    # ops/mount.py:70, ops/rig.py:63
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again.'): '',
    # ui/panels.py:214
    ('GuitarRig', 'The rig or bone map changed: calibrate again'): '',
    # ops/rig.py:134
    ('GuitarRig', 'The rig shows no solve'): '',
    # core/prepjob.py:228
    ('GuitarRig', 'The settings changed since the prep was applied: Apply Prep again.'): '',
    # core/calibrate.py:90
    ('GuitarRig', 'The shoulder line is parallel to the hips-to-head line in rest pose.'): '',
    # core/guitar_frame.py:700
    ('GuitarRig', 'The string face could not be told from the geometry: check that +Z points out of the strings, and use Flip Z if not.'): '',
    # core/solver.py:717
    ('GuitarRig', 'The {name} IK misses its target by {value:.1f} mm: check the arm bones for IK locks, limits or stretch.'): '',
    # core/baker.py:749
    ('GuitarRig', 'The {name} cutoff, {cutoff:g} Hz, is above what {fps:g} frames/s can show: nothing changed'): '',
    # core/prepjob.py:561
    ('GuitarRig', 'The {name} elbow was too straight to swing on {swing__straight___count} frames ({value}): only the shoulder turned.'): '',
    # core/prepjob.py:586
    ('GuitarRig', 'The {name} fingers: {value} moves snapped.'): '',
    # core/prepjob.py:552
    ('GuitarRig', "The {name} hand's turns above {cutoff:g} Hz: {value:.1f}° → {value2:.1f}° RMS, speed {value3:.0f} → {value4:.0f}°/s (95th percentile)"): '',
    # core/autoland.py:107
    ('GuitarRig', 'The {name} preset has no neck measurements to place landmarks from.'): '',
    # ops/guitar.py:543
    ('GuitarRig', 'The {name} preset has no {label} landmark: add it by hand.'): '',
    # ops/guitar.py:337
    ('GuitarRig', 'The {name} preset is not verified against its source: check it.'): '',
    # core/autoland.py:118
    ('GuitarRig', "The {name} preset was saved without its guitar's heel: the Neck/Body Barrier and the strum line are placed from where the neck narrows. Check them, or save the preset again."): '',
    # core/solver.py:712
    ('GuitarRig', "The {name} wrist target was out of reach: it was kept within {reach_clamp:.1%} of the arm length, or the mocap wrist's distance if that is further."): '',
    # core/prepjob.py:534
    ('GuitarRig', "The {name} wrist's travel above {cutoff:g} Hz: {value:.1f} → {value2:.1f} cm RMS (99th percentile {value3:.1f} → {value4:.1f} cm)"): '',
    # rig/build.py:195
    ('GuitarRig', 'The {side_name} IK chain is not mapped to existing bones: check the bone map.'): '',
    # rig/build.py:199
    ('GuitarRig', 'The {side_name} IK forearm is not below the IK upper arm: check the bone map.'): '',
    # rig/build.py:203
    ('GuitarRig', 'The {side_name} IK hand is not below the IK forearm, so the IK would not move it: check the bone map.'): '',
    # core/calibrate.py:248
    ('GuitarRig', 'The {side} forearm and hand start at the same place in rest pose.'): '',
    # core/solver.py:789
    ('GuitarRig', 'The {value} IK does not reproduce the current pose: the elbow is {value2:.1f} mm and the wrist {value3:.1f} mm off. Check the arm bones for IK locks, limits or stretch.'): '',
    # rig/build.py:263
    ('GuitarRig', 'The {value} arm has its own IK ({value2}): mute it while you solve, or the pole target is ignored.'): '',
    # core/prepjob.py:134
    ('GuitarRig', "The {value} arm's bones are not mapped as a chain: check the bone map."): '',
    # core/prepjob.py:580
    ('GuitarRig', "The {value} fingers' presses and releases: {value2:.0f} → {value3:.0f} frames from 10 % to 90 % (median of {times_0__count}); {value4} moves snapped."): '',
    # core/prepjob.py:167
    ('GuitarRig', 'The {value} thumb or index finger is missing: Swing is off.'): '',
    # core/prepjob.py:471
    ('GuitarRig', "The {value} twist bone's fixed axis is {angle:.0f}° off the forearm: Roll turns it about the forearm."): '',
    # ops/guitar.py:434
    ('GuitarRig', 'There are no landmarks to save.'): '',
    # ops/bake.py:184
    ('GuitarRig', 'There is no bake'): '',
    # core/baker.py:679
    ('GuitarRig', 'There is no bake to smooth.'): '',
    # ops/rig.py:86
    ('GuitarRig', 'There is no helper rig'): '',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Tip'): '',
    # ui/panels.py:267
    ('GuitarRig', 'Tools'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Top (m)'): '',
    # presets/ukulele.json, props.py:GTR_Settings
    ('GuitarRig', 'Ukulele'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Unreal Mannequin (UE4)'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'Unreal Mannequin (UE5)'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Unsettled'): '',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Up'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Upper Arm'): '',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Upper Leg'): '',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Use Default Rotation'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Use Scene Range'): '',
    # core/bonemap.py:106
    ('GuitarRig', 'VRM humanoid'): '',
    # presets/bone_maps.json
    ('GuitarRig', 'VRoid / VRM (J_Bip)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'World'): '',
    # props.py:GTR_Settings, ui/panels.py:363
    ('GuitarRig', 'Wrist'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Blend'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Capture Frame'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Wrist Correction'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Corrections'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Filter'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Offset'): '',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Wrist Turn'): '',
    # ops/mount.py:165
    ('GuitarRig', 'Wrist offset captured at frame {wrist_frame}: the solve turns the fretting wrist {wrist_blend:.0%} of the way to this rotation on the guitar.'): '',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'X (char. left)'): '',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'X (headstock)'): '',
    # presets/strat.json
    ('GuitarRig', "XR Animator's Stratocaster scene (guitar_collection_v9.1/scene - stratocaster guitar.json)"): '',
    # presets/acoustic.json
    ('GuitarRig', "XR Animator's acoustic guitar scene (guitar_collection_v9.1/scene.json)"): '',
    # presets/bass.json
    ('GuitarRig', "XR Animator's bass guitar scene (guitar_collection_v9.1/scene - bass guitar.json)"): '',
    # presets/ukulele.json
    ('GuitarRig', "XR Animator's ukulele scene (guitar_collection_v9.1/scene - ukulele.json)"): '',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'Y'): '',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'Y (up)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'Yaw Direction'): '',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'Z (forward)'): '',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'Z (strings)'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'active_magnet_index'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'active_range_index'): '',
    # core/autoland.py:166
    ('GuitarRig', 'body'): '',
    # props.py:GTR_Character
    ('GuitarRig', 'bone_map'): '',
    # ops/guitar.py:345
    ('GuitarRig', 'bounds'): '',
    # props.py:GTR_Character
    ('GuitarRig', 'calibration'): '',
    # core/solver.py:379
    ('GuitarRig', 'chest collider {value:.1f} cm'): '',
    # core/solver.py:375, ui/overlay.py:313
    ('GuitarRig', 'clamp'): '',
    # ops/guitar.py:GTR_OT_load_preset_file, ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'filter_glob'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'fingerprint'): '',
    # props.py:GTR_Calibration
    ('GuitarRig', 'fingertips'): '',
    # core/presets.py:180
    ('GuitarRig', 'format {value} is newer than this add-on reads ({FORMAT})'): '',
    # core/bonemap.py:106
    ('GuitarRig', 'generic names'): '',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'headstock set-back'): '',
    # core/autoland.py:166
    ('GuitarRig', 'heel'): '',
    # core/guitar_frame.py:41
    ('GuitarRig', 'high'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'index.js'): '',
    # props.py:GTR_Guitar
    ('GuitarRig', 'landmark_messages'): '',
    # core/calibrate.py:260, core/solver.py:61, rig/build.py:32
    ('GuitarRig', 'left'): '',
    # core/guitar_frame.py:41
    ('GuitarRig', 'low'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'magnets'): '',
    # core/guitar_frame.py:41
    ('GuitarRig', 'medium'): '',
    # props.py:GTR_Calibration, props.py:GTR_Guitar
    ('GuitarRig', 'messages'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'min.js'): '',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', 'mocap_factor settings are ignored: they only matter for external VMC input.'): '',
    # ui/panels.py:569
    ('GuitarRig', 'moved {moved:.1f} cm'): '',
    # ui/panels.py:568
    ('GuitarRig', 'moved {moved:.1f} cm, reach clamped'): '',
    # ops/guitar.py:345
    ('GuitarRig', 'neck'): '',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'neck position'): '',
    # core/solver.py:385
    ('GuitarRig', 'neck swung {value:.1f}°'): '',
    # core/bonemap.py:106
    ('GuitarRig', 'no match'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'prep'): '',
    # props.py:GTR_Settings
    ('GuitarRig', 'range_overrides'): '',
    # core/calibrate.py:260, core/solver.py:61, rig/build.py:32
    ('GuitarRig', 'right'): '',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'strings'): '',
    # core/baker.py:539
    ('GuitarRig', 'the Max Swing limit'): '',
    # core/baker.py:538
    ('GuitarRig', 'the chest collider'): '',
    # core/baker.py:538
    ('GuitarRig', 'the reach clamp'): '',
    # ui/panels.py:587
    ('GuitarRig', 'turned {angle:.1f}°'): '',
    # ui/panels.py:584
    ('GuitarRig', 'turned {angle:.1f}°, yaw constrained'): '',
    # ui/panels.py:420, ui/panels.py:579
    ('GuitarRig', 'weight {weight:.2f}'): '',
    # core/prepjob.py:158
    ('GuitarRig', '{NOT_MMD}: no MMD finger bones (人指１…) were found on the {value} hand.'): '',
    # ui/panels.py:581
    ('GuitarRig', '{angle:.1f}°, limited'): '',
    # ui/panels.py:226
    ('GuitarRig', '{arm_len:.3f} m  ×{ratio_arm:.3f}'): '',
    # ops/guitar.py:283
    ('GuitarRig', '{axis} flipped by hand.'): '',
    # ops/bake.py:69
    ('GuitarRig', '{bl_label} cancelled at frame {frame}: nothing was changed.'): '',
    # ops/bake.py:86
    ('GuitarRig', '{bl_label} failed at frame {frame}: {exc}'): '',
    # ops/bake.py:97
    ('GuitarRig', '{bl_label}: frame {frame} ({progress:.0%}). Esc to cancel.'): '',
    # ui/panels.py:233
    ('GuitarRig', '{chain_len_L:.3f} / {chain_len_R:.3f} m'): '',
    # core/diagnostics.py:233
    ('GuitarRig', '{count:.0f} passes'): '',
    # ui/panels.py:590
    ('GuitarRig', '{count}, not settled'): '',
    # core/calibrate.py:268
    ('GuitarRig', '{estimated} fingertip(s) estimated from the finger joints because the bone tails look unreliable.'): '',
    # core/baker.py:546
    ('GuitarRig', '{first}-{last} {value}'): '',
    # core/baker.py:299
    ('GuitarRig', '{frames} and {count} more'): '',
    # ui/panels.py:225
    ('GuitarRig', '{height:.3f} m'): '',
    # core/autoland.py:181
    ('GuitarRig', '{label} is off the end of the guitar: check the strum line.'): '',
    # ui/panels.py:154
    ('GuitarRig', '{landmark}  (missing)'): '',
    # ui/panels.py:155
    ('GuitarRig', '{landmark}  (optional)'): '',
    # ui/panels.py:110
    ('GuitarRig', '{length_m:.3f} m'): '',
    # ui/panels.py:563
    ('GuitarRig', '{mode} (range {range_number})'): '',
    # core/baker.py:106
    ('GuitarRig', "{name} has constraints ({value}) that act on top of the baked keys: the baked arm will differ from the solve. Mute them, or bake the rig's FK controls."): '',
    # ops/guitar.py:500
    ('GuitarRig', '{name} is hidden or in an excluded collection.'): '',
    # ops/bake.py:262
    ('GuitarRig', '{name} is hidden or in an excluded collection: unhide it to see its curves.'): '',
    # core/baker.py:285
    ('GuitarRig', '{name} is in NLA tweak mode: leave it in the NLA editor first.'): '',
    # core/solver.py:373
    ('GuitarRig', '{name} {value}'): '',
    # ui/panels.py:705
    ('GuitarRig', "{name}'s curves hold every frame: each wrist's correction (cm) and IK miss (mm), each magnet's distance d (cm, negative behind a plane) and weight w, the neck swing and the fretting wrist's turn (°). They show the solve, before any Smooth or Re-clamp."): '',
    # ui/overlay.py:315
    ('GuitarRig', '{name}: {state}'): '',
    # ui/panels.py:227
    ('GuitarRig', '{palm_len:.3f} m  ×{ratio_palm:.3f}'): '',
    # ui/panels.py:416
    ('GuitarRig', '{reach:.3f} m on this character'): '',
    # core/bonemap.py:321
    ('GuitarRig', "{side_name} IK chain: '{name}' is not below '{name2}'."): '',
    # core/bonemap.py:326
    ('GuitarRig', "{side_name} IK hand '{name}' is not below the IK forearm '{name2}'."): '',
    # ui/panels.py:230
    ('GuitarRig', '{spine_len:.3f} m  ×{ratio_spine:.3f}'): '',
    # ui/panels.py:529
    ('GuitarRig', '{status}, neck aim fading ({weight:.2f})'): '',
    # core/guitar_frame.py:549, core/guitar_frame.py:559
    ('GuitarRig', '{strings_count} long thin parts'): '',
    # core/baker.py:541
    ('GuitarRig', '{text} acted on {number} frames'): '',
    # core/bonemap.py:315
    ('GuitarRig', "{title} '{name}' is not a child of '{name2}'."): '',
    # core/calibrate.py:167
    ('GuitarRig', '{title} is not mapped to a bone.'): '',
    # core/bonemap.py:303
    ('GuitarRig', '{title} is not mapped.'): '',
    # core/bonemap.py:305
    ('GuitarRig', "{title}: there is no bone '{name}'."): '',
    # ui/panels.py:573
    ('GuitarRig', '{value:.1f} cm'): '',
    # ui/panels.py:421
    ('GuitarRig', '{value:.1f} cm away, {state}'): '',
    # ui/panels.py:115
    ('GuitarRig', '{value}  ×{value2:.2f} ×{value3:.2f} ×{value4:.2f}'): '',
    # core/solver.py:382
    ('GuitarRig', '{value} wrist moved {moved:.1f} cm'): '',
    # core/solver.py:387
    ('GuitarRig', '{value} wrist turned {value2:.1f}°'): '',
    # ui/panels.py:122, ui/panels.py:241
    ('GuitarRig', '{x:+.2f}  {y:+.2f}  {z:+.2f}'): '',
}
