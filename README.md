# GuitarRig

GuitarRig is a Blender add-on that bakes guitar-playing arms onto a motion-captured character. You give it a character that already plays your mocap and a guitar model. It hangs the guitar on the character's chest, keeps the fretting hand on the fretboard and the picking hand over the strings, and bakes the result into new actions. Your own animation is never changed.

It is a port of the guitar system in XR Animator / System Animator Online (SAO), solved offline frame by frame instead of live:
- The guitar is mounted on the upper chest.
- The guitar's neck swings toward the fretting hand.
- The wrists are pulled onto, or held back by, lines and planes on the guitar ("magnets").

**Requirements:**
- Blender 4.2 or later. The tests run on Blender 5.2.
- A humanoid armature already retargeted to your mocap, so it plays the motion through an action, the NLA or constraints. Fingers help but are optional.
- A guitar-like mesh: a body, a narrower neck and a headstock.

**Not covered:**
- Retargeting.
- Fingering real frets and strings.
- Left-handed players. This is planned; only right-handed playing is solved today.
- Real-time use.

## Installing

Install the add-on as a Blender extension:
1. Build the package with `blender --command extension build --source-dir guitar_rig`, or use a package you were given.
2. In Blender, open **Edit > Preferences > Get Extensions** and choose **Install from Disk**.

The add-on lives in the 3D Viewport sidebar (N), on the **Guitar** tab.

## Workflow

Each panel greys out or explains what is missing until the step before it is done.

### 1. Character

1. Pick the retargeted armature as **Character** in the **GuitarRig** panel.
2. **Bones > Auto-Map Bones** guesses the bone map. It knows these naming conventions:
   - VRoid/VRM;
   - Mixamo;
   - Rigify (generated, deform and metarig names);
   - MMD (Japanese names);
   - the Unreal Mannequin (UE4 and UE5).
3. Check the map:
   - **Chest** is the bone the guitar hangs from. Use the upper chest if there is one.
   - The **IK Chain** groups are the bones the IK drives. On Rigify-style rigs these are the FK controls.
4. Click **Calibration > Calibrate**. The overlay draws the character's frame on the hips, the chest and the hands:
   - red is the character's left;
   - green is up;
   - blue is forward.

   If forward points backward, use **Flip Facing**.

### 2. Prep (optional)

Capture and filtering smooth away some of a performance: the picking arm hardly swings, the strokes are small and slow, and the fretting fingers press and release lazily. **Prep** touches up the mocap before the bake to restore some of that. It needs only the calibrated character, not the guitar, so you can judge the result on the bare character.

This version supports MMD models imported with MMD Tools (bones are found by their Japanese names) and right-handed players.

1. Set **Intensity** in the **Prep** panel. It scales every tool toward doing nothing (0) or past its strength (above 1). The per-tool strengths are under **Tools**.
2. Click **Apply Prep**. It reads your original mocap and writes the result to a **GuitarPrep** NLA layer; Esc cancels. The report gives the picking wrist's travel, the hand's turn speed and the finger press times, before and after.
3. Scrub the timeline. **Show Original** mutes the layer for a before-and-after comparison.
4. Change the settings and apply again as often as you like: Apply Prep always starts from the original mocap, so the strengths never add up.

The tools:

| Tool | What it does | Default |
|---|---|---|
| Range | Makes the quick part of a motion larger and keeps the posture: the picking hand relative to the forearm, and each fretting finger joint. Quick presses overshoot slightly. | Picking wrist ×1.5, fretting fingers ×1.3, above 1 Hz |
| Snap | Makes each move steeper, keeping where it starts, ends and crosses half way: the picking strokes and the fretting fingers' presses. **Picking Fingers** also snaps the picking hand's fingers, for fingerpicking. | Strokes 2, fretting fingers 2, picking fingers off |
| Swing | Adds the arm swing a strum makes: the wrist follows the pick point's stroke, turned at the shoulder and the elbow, the arm leading by a frame. | 1× the stroke, elbow share 0.7 |
| Roll | Moves the forearm roll from the wrist onto the forearm twist bone (手捩) on both hands, so the forearm skin twists as it should. The hands keep their pose. | On |

The fretting fingers stay within the range they have in the mocap plus **Joint Margin** (5°).

The solve and the bake read the GuitarPrep layer as the mocap. If you apply Prep after a bake, the report and the panel ask you to bake again. **Remove Prep** (the trash icon) removes the layer and leaves the bake.

### 3. Guitar

1. Select the guitar meshes, or the empty they hang from, and click **Guitar > Normalise Frame**.
   - It creates `GTR_ROOT`, with +X along the neck toward the headstock and +Z out of the strings, and parents the guitar to it.
   - If the model is not real size, set **Real Length** in the operator's redo panel.
2. Check the axes in the panel or the viewport. Use **Flip X** or **Flip Z** if the headstock or the string face is the wrong way.
3. Choose the [preset](#presets) closest to your instrument and click **Load Preset**. It places the landmarks, the magnets, a mount estimate, and the aim and wrist settings.
4. Click **Landmarks > Auto-Place** (see [Auto-placed landmarks](#auto-placed-landmarks)). This is recommended when no preset is close to your guitar, for example an electric with the Acoustic Guitar preset, or a tilted neck.
5. Check the landmarks. Click an entry in the checklist to select its empty, or to add it at the 3D cursor if it is missing. Move or rotate the empties as needed. For a plane, the empty's local Z axis is the plane's normal.

### 4. Mount and wrist

1. Go to a frame where the character holds the guitar in a typical pose.
2. Click **Place on Mount**, move and rotate `GTR_ROOT` until the guitar sits right on the body, and click **Capture Mount**. This step is required: the preset's mount is only an estimate.
3. Optionally, pose a good fretting frame and click **Wrist > Capture Wrist Offset**. **Wrist Blend** sets how much of that rotation the fretting wrist takes.

### 5. Solve and tune

1. Click **Solve > Build Rig**. It adds an IK and a rotation constraint to each arm, plus their helper empties in a `GuitarRig` collection. The constraints stay off, so your animation plays as before.
2. Go to a problem frame and click **Solve Frame**. The arms show the solve until the frame changes; **Show Mocap** switches it off.
   - The overlay shows each magnet and how far it pulled.
   - The panel lists how far each wrist moved and which magnets acted.
3. Choose the **Mode**:
   - **Follow** (SAO's default): the guitar swings toward the fretting hand.
   - **Align** (SAO's Alt+A): the guitar stays on the chest, and the fretting hand slides along the fretboard edge.

   Use **Range Overrides** to solve some frames in the other mode.
4. Tune the magnets in the **Magnets** panel if needed. Switch on the **Chest Collider** if the hands pass through the torso.

### 6. Bake and refine

1. Click **Bake**. It solves every frame of the range with a progress bar; Esc cancels and leaves everything as it was. The report gives:
   - the speed;
   - the largest wrist correction;
   - frames that did not settle or where the IK missed;
   - how closely the played-back keys match the solve.
2. Check the worst frames in **Diagnostics**. Fix what is wrong (landmarks, magnets, mode ranges) and bake again.
3. Optional post-processing:
   - **Smooth** low-passes the bake: 6 Hz for the arms and 3 Hz for the guitar by default. In **Correction** mode (the default) it smooths only what the solve changed in the arms, so the quick motion of the mocap and the prep stays; **Keys** smooths the arm keys themselves.
   - **Re-clamp** then pushes any hand that smoothing moved into a barrier or the chest collider back out, re-keying only those frames.
4. Refine the result on the **GuitarRefine** NLA layer:
   - chord shapes and fretting fingers;
   - wrist twist about the neck;
   - strum accents and contacts.
5. **Remove Bake** (the trash icon) puts back everything the bake changed. Refine actions that hold keys are kept.

## What the bake writes

On both the character and `GTR_ROOT`, from the bottom of the NLA up:
- your own tracks, with the active action pushed down into a track of its own;
- **GuitarPrep** (the character only, after Apply Prep): the touched-up channels, with blend Replace and one key per frame over the bake range;
- **GuitarBake**: the solved arm chains, or the guitar, with blend Replace and one key per frame;
- **GuitarRefine**: an empty Combine layer for your corrections. A re-bake replaces only GuitarBake, so your refine work survives.

The arm channels:
- The three mapped bones of each arm (upper arm, forearm, hand) always get rotation keys, in each bone's own rotation mode.
- Twist bones between them are keyed only if the solve turned them.
- Location and scale are keyed only where they changed.

**Guitar Keys** sets how the guitar is keyed:
- **Chest Bone** (the default): `GTR_ROOT` is parented to the chest bone and keyed relative to it, so later edits to the body carry the guitar along.
- **World**: the guitar is keyed in world space.

## Presets

Each preset comes from one of SAO's guitar scenes and keeps that scene's numbers: the landmarks, the magnets, the mount estimate, and the aim and wrist settings. Load Preset fits the landmarks to your guitar's neck and body.

| Preset | SAO scene | Differences |
|---|---|---|
| Acoustic Guitar | `scene.json` | The default |
| Bass Guitar | `scene - bass guitar.json` | Mounted about 2 cm lower, and turned 10° further about the character's left–right axis |
| Stratocaster | `scene - stratocaster guitar.json` | Mounted like the bass |
| Ukulele | `scene - ukulele.json` | Mounted about 6 cm closer to the middle of the chest and rolled 10° further; a 26 cm strum line that reaches up the neck; a Nut Barrier |

The magnet settings are the same in all four; their landmarks are placed on each prop. The tests check every preset against its scene file.

On SAO's electric guitars and bass, the Stratocaster and Bass Guitar presets put the strum line closer to where SAO has it than the Acoustic Guitar preset does, also after Auto-Place. With Load Preset alone they put the Neck/Body Barrier within 1 cm of SAO's; Auto-Place moves it to the heel, which is 2–3 cm away on these guitars.

The Ukulele preset is the only one with a Nut Barrier landmark. When you load another preset with its magnets, Load Preset removes a Nut Barrier that no magnet uses.

## Landmarks

Landmarks are empties under `GTR_ROOT`. Each has a role, stored in its `gtr_role` custom property; the magnets and the neck aim read them.

| Landmark | Where it goes | Used by |
|---|---|---|
| Neck Pivot | Lower (−Y) fretboard edge, toward the body | Neck aim axis |
| Nut | Lower fretboard edge at the nut | Neck aim axis |
| Fretboard Plane | Fretboard surface, normal +Z | Fretting hand snaps onto it |
| Fretboard Edge | Through the lower edge, normal +Y | Fretting hand stays above the edge |
| Neck/Body Barrier | Where the body starts under the neck, normal +X | Fretting wrist stays on the neck |
| Nut Barrier (optional) | Near the nut, normal −X | Fretting wrist stays off the headstock (Ukulele preset) |
| Strum Line A/B | Body and neck ends of the strum line | Picking wrist is pulled to it |
| Strum Position | At Strum Line A, normal +X | Holds the picking hand's position along the strings |
| String Plane | Above the strings, normal +Z | Picking fingertips stay above it |

Some positions are conventions tuned together with the magnets, not features of the mesh:
- The String Plane sits about 4 cm above the fretboard, and its magnet's **Fingertip Offset** of −4 cm cancels that height.
- The strum line is a line for the wrist, not for the pick.

### Auto-placed landmarks

**Auto-Place** measures the guitar under `GTR_ROOT`:
- the nut;
- the heel, where the body starts under the neck;
- the fretboard's top line, including its tilt;
- the neck's lower edge and centre lines;
- the length of the body.

It then puts each landmark where the chosen preset has it relative to the same features on the preset's own guitar. This keeps the preset's conventions, such as the string plane's height and the strum line's offsets, consistent with its magnets. `GTR_ROOT` does not move, and on the preset's own guitar the landmarks are exactly the preset's.

Compared with the plain fit that Load Preset does:
- **Neck/body barrier:** set at the heel. On guitars with cutaways, Load Preset's fit puts it where the neck narrows, which can be 10 cm too far toward the headstock.
- **Fretboard planes:** they follow the fretboard's tilt.
- **Strum line:** it keeps its share of the body length from the heel. On an acoustic guitar that puts it on the soundhole.

The tests check Auto-Place with the Acoustic Guitar preset against SAO's own hand-placed points on five of its guitars:
- **Barrier:** within 2 cm.
- **Neck lines:** within about 1 cm, which is how much SAO's own points scatter.
- **Strum line:** within 8 cm, closer than the plain fit. SAO's strum lines are 9–26 cm long and tuned per instrument.

With each preset on its own SAO guitar, Auto-Place puts every landmark within 2 mm of SAO's.

Auto-Place reports a confidence, with messages:
- **High:** the neck, heel and body were all found.
- **Medium:** no body was found under the neck, the preset predates heel measurement, or the proportions are unusual.
- **Low:** the guitar frame itself is doubtful.

Always check the landmarks afterwards. Normalise, Flip and Load Preset place them by the plain fit again, so run Auto-Place again after those.

## Magnets

A magnet is a line or a plane on the guitar that acts on one wrist. Magnets act in list order.

| Setting | Meaning |
|---|---|
| Distance (m) | Reach of the magnet before arm-length scaling. Barriers need it too. |
| Power | 0: a linear pull that fades out at the distance. 1: a full snap anywhere within it. −9 or less: no pull, only a barrier. |
| Crossable | Off makes a plane a barrier: a hand behind it is clamped onto it. |
| Hand Offset | The point of the hand that the magnet acts on: the wrist, the aim offset, or a custom offset. |
| Fingertips | Fingertip v2 shifts the hand so that the lowest chosen fingertip lands on the plane. **Push Only** lets fingertips push the hand away but never pull it in. |
| Filter | Smooths the magnet's pull from frame to frame during a bake. **Rotation** filters the angle about the guitar origin. |
| Hysteresis | A snap magnet that held the hand reaches this much further on the next frame. |

The presets' magnets, as in SAO:
- **Right hand:** the strum line, the strum position and the string barrier.
- **Left hand:** the fretboard plane, the neck/body barrier and the fretboard edge, plus the nut barrier on the Ukulele preset.

A magnet that pulls the wrist toward a line shrinks the wrist's distance from it, so it would take back most of a stroke. **Pass-Through** (in the Magnets panel, on for the right hand) lets the quick wrist motion through: the magnets act on the slow part of the wrist's path relative to the chest (below 1 Hz by default), the strokes are added back on top, and the barriers and the chest collider then push the result out again. It is off for the fretting hand, which the fretboard magnets must hold. The bake reads every frame's wrist first for this; Solve Frame reads 2 s each side of its frame. The diagnostics show it as `R pass-through (cm)`.

The **Chest Collider** is a capsule around the torso that pushes the wrists and fingertips forward before the magnets act. It is off by default.

## Modes and range overrides

The **Mode** buttons switch the neck aim and the Fretboard Edge magnet the way SAO's Alt+A does:

| | Follow | Align |
|---|---|---|
| Neck aim | On | Off |
| Fretboard Edge magnet | Barrier (power −99), Rotation filter | Snap (power 1), no filter |

The fields stay editable afterwards. **Range Overrides** solve frame ranges in a given mode:
- A range applies its mode's switch, on top of the scene's settings, for its frames.
- Where enabled ranges overlap, the one lower in the list wins.
- Where the mode changes, the bake restarts its filters and hysteresis, and the neck aim fades over 5 frames.
- Solve Frame uses the same schedule, so it shows a frame as the bake solves it.
- The Range Overrides panel shows the current frame's mode and any fade in progress.

## Diagnostics

Every bake records what the solve did on each frame. The values are keyed as animated custom properties on the `GTR_Diagnostics` empty. Click **Select Curves** and open the Graph Editor to see them.

| Curve | Meaning |
|---|---|
| `L`/`R wrist correction (cm)` | How far the collider, magnets and reach clamp moved the wrist target from the mocap wrist |
| `L`/`R IK miss (mm)` | How far the solved wrist ended from its target |
| `L`/`R chest collider (cm)` | The collider's push (only when the collider is on) |
| `L`/`R pass-through (cm)` | The quick wrist motion that passed through the magnets (pass-through hands only) |
| `L`/`R <magnet> d (cm)` | The hand point's distance from the magnet. For planes it is signed: negative means behind the plane. |
| `L`/`R <magnet> w` | The magnet's weight: 1 is a full snap or a barrier clamp |
| `neck swing (°)`, `fretting wrist turn (°)` | How far the guitar and the fretting wrist turned |
| `solve passes`, `settled` | Solve iterations, and whether the aim and wrists settled |
| `mode (0 follow, 1 align)`, `neck aim weight` | The frame's mode and aim weight |

The **Diagnostics** panel ranks the five worst frames for a chosen measure; click one to jump there. The measures:
- **Wrist Correction**;
- **Barrier Depth**: how far a hand was behind a barrier before it was clamped;
- **IK Miss**;
- **Neck Swing**;
- **Wrist Turn**;
- **Chest Collider**;
- **Unsettled**.

The diagnostics describe the solve, not later Smooth or Re-clamp passes. Remove Bake removes them.

## Troubleshooting

| Symptom | What to check |
|---|---|
| "The IK misses its target" | IK locks, limits or stretch on the arm bones, or a chain that does not reach |
| "Played back, the bake is … mm from the solve" | Constraints, drivers or NLA tracks acting on top of the baked arm bones or `GTR_ROOT` |
| The guitar wobbles between iterations | Lower **Relax**, or raise **Iterations** (Solve > Options) |
| "The neck aim was limited" | The fretting hand is far from the neck. Check the mount, or raise **Max Swing**. |
| A hand goes through the neck or the body | The landmarks (Fretboard Plane, Edge, Barrier). Bake again, or use Re-clamp after smoothing. |
| The guitar sits in the torso | Capture the mount again, or switch on the Chest Collider |
| Character frame arrows are wrong | **Flip Facing**, or the bone map's shoulders and head |
| Landmarks jumped after Flip or Load Preset | Those operators place them by the preset fit; run Auto-Place again |
| "Prep supports MMD models" | Prep finds bones by their MMD names (人指１, 手捩 …). Import the model with MMD Tools. |
| The forearm twists badly when the strokes are boosted | Keep **Roll to Twist Bone** on. Without a 手捩 bone, Roll is off: lower the picking wrist's Range. |
| The prep's strokes disappear after Smooth | Use Smooth **Correction**, not **Keys** |

## For developers

Run the tests inside Blender from the add-on folder:

```
blender -b --factory-startup --python-exit-code 1 --python tests/run.py -- [-v] [-k PATTERN]
```

- The tests that compare with SAO run when its `guitar_collection_v9.1` folder sits next to the add-on folder. Without it, they are skipped.
- The prep test on a real model runs when `GTR_TEST_PMX` and `GTR_TEST_VMD` point at an MMD model and motion (example.pmx and part1.vmd for the numbers it checks) and the MMD Tools extension is installed.
- `tools/measure_reference.py` measures a preset's reference prop and writes the preset's `frame` and `reference` entries.
- The code is laid out as follows:
  - `core/`: the maths and the solve, testable without the UI (`prep.py` and `prepjob.py` are the mocap prep);
  - `ops/`: the operators;
  - `ui/`: the panels, lists and viewport overlay;
  - `rig/`: the helper rig;
  - `presets/`: instrument presets and bone-name conventions.
