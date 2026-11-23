# SPDX-License-Identifier: GPL-3.0-or-later
# UTF-8. Edit translation values; empty values fall back to English.
# Updated by tools/i18n.py. See TRANSLATING.md.

translations = {
    # props.py:GTR_Magnet
    ('*', '0: linear falloff over the distance; 1: full snap within it; -9 or less: barrier clamp only'): '0：在作用距离内线性衰减；1：在作用距离内完全吸附；-9 或更低：仅作阻挡限位',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('*', '1 for the worst frame, 2 for the next, and so on'): '1 表示最差帧，2 表示次差帧，依此类推',
    # props.py:GTR_Guitar
    ('*', "A feature was missing or the guitar's proportions are unusual: check the landmarks"): '缺失某项几何特征或吉他比例较为特殊：请检查标定点',
    # ops/rig.py:GTR_OT_range_add
    ('*', "Add a frame range, from the current frame, solved in the other mode than the scene's. Lower ranges win\nwhere ranges overlap"): '从当前帧开始添加一个帧区间，使用与场景不同的模式进行求解。区间重叠时，列表中靠下的区间优先生效',
    # ops/magnets.py:GTR_OT_magnet_add
    ('*', 'Add a magnet after the active one. Magnets act in list order'): '在当前活动磁铁后添加一个磁铁。磁铁按列表顺序依次生效',
    # ops/rig.py:GTR_OT_build_rig
    ('*', 'Add the helper rig: an IK and a wrist-rotation constraint on each arm, switched off until a solve, and\ntheir empties in a GuitarRig collection. Replaces an older rig'): '添加辅助绑定：为双臂添加 IK 与手腕旋转约束（求解前保持关闭），并将辅助空物体放入 GuitarRig 集合中。会替换旧的辅助绑定',
    # props.py:GTR_Settings
    ('*', 'Aim point relative to the fretting wrist, in the rest-aligned hand frame (SAO: (0.6, -0.25, 0) MMD units)'): '相对于按弦手腕的瞄准点，位于静置对齐手部坐标系中（SAO：(0.6, -0.25, 0) MMD 单位）',
    # props.py:GTR_Guitar
    ('*', 'All cues agree on the frame'): '所有检测线索对坐标系方向一致',
    # props.py:GTR_Prep
    ('*', "Also snap the picking hand's fingers, for fingerpicking"): '同时锐化拨弦手的手指动作，适用于指弹',
    # props.py:GTR_Settings
    ('*', 'Always blend the shorter way'): '始终沿较短路径混合旋转',
    # props.py:GTR_Calibration
    ('*', "Arm angle below horizontal of the avatar SAO's hand offsets were authored for: 0° for the T-pose VRM avatars the guitar scenes target, 37.42° for XR Animator's MMD skeleton. axis_rot turns this direction onto the rig's rest forearm"): '制作 SAO 手部偏移时参考角色手臂低于水平面的角度：吉他场景面向的 T-pose VRM 角色为 0°，XR Animator 的 MMD 骨架为 37.42°。axis_rot 会将该方向旋转对齐到当前绑定的静置前臂',
    # props.py:GTR_Prep
    ('*', "Arm swing added to the strokes: the wrist travels this many times the pick point's stroke, turned at the shoulder and the elbow (0: off)"): '为扫弦添加的手臂摆动倍率：手腕移动距离为拨片点扫弦幅度的该倍数，由肩部和肘部转动实现（0：关闭）',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Body end of the strum line the picking hand is pulled to (SAO magnet 0)'): '牵引拨弦手的扫弦线琴体端（SAO 磁铁 0）',
    # props.py:GTR_Settings
    ('*', 'Captured from a pose of the fretting hand on the guitar'): '从按弦手放在吉他上的姿态捕获',
    # props.py:GTR_Settings
    ('*', 'Captured from a pose of the guitar on the character'): '从吉他放置在角色身上的姿态捕获',
    # props.py:GTR_Settings
    ('*', 'Clamp a hand behind a barrier plane however far behind it is'): '无论手部深入阻挡面后方多远，都将其限位推回平面上',
    # props.py:GTR_Prep
    ('*', 'Counts the preps, so a bake can tell which one it read'): '预处理计数器，用于让烘焙识别其读取的是哪一次预处理',
    # props.py:GTR_Settings
    ('*', 'Counts the solves, so that an undone solve is not shown as current'): '求解计数器，防止已撤销的求解结果仍被当作当前结果显示',
    # props.py:GTR_Settings
    ('*', "Disable the scene's meshes in viewports during the bake, which makes it much faster. The pose does not depend on them, and they come back afterwards"): '烘焙期间在视图中隐藏场景网格以大幅提速。姿态求解不依赖网格，烘焙完成后会自动恢复显示',
    # props.py:GTR_Fingertip
    ('*', 'Distal head plus half the intermediate segment, as SAO does'): '采用远节骨骼起点加上中节骨骼长度的一半，与 SAO 一致',
    # props.py:GTR_Magnet
    ('*', 'Distance from the feature at which the weight is highest'): '权重达到最大值时与几何特征的距离',
    # props.py:GTR_Magnet
    ('*', 'Distance multiplier while a snap magnet (power 1 or more) holds the hand'): '当吸附磁铁（幂次 ≥ 1）保持吸附手部时，作用距离的放大倍率',
    # props.py:GTR_Settings
    ('*', 'Draw the calibrated frames, fingertips, landmark lines and the mount in the viewport'): '在视图中绘制校准坐标系、指尖点、标定点连线和挂载位置',
    # props.py:GTR_Settings
    ('*', 'Draw the magnets in the overlay, the active one with its reach, and what they did in the solve the rig shows'): '在叠加层中绘制磁铁、当前活动磁铁的作用范围，以及当前显示求解中各磁铁的作用效果',
    # props.py:GTR_Magnet
    ('*', 'End of the segment (line magnets only)'): '线段终点（仅直线磁铁）',
    # props.py:GTR_Settings
    ('*', 'Filter how far the collider and magnets move each wrist target. Not in SAO; the mocap itself is never filtered'): '对碰撞体和磁铁造成的手腕目标偏移量进行滤波。SAO 中无此项；原始动捕本身不会被滤波',
    # props.py:GTR_Magnet
    ('*', 'Filter the angle about the guitar root'): '对绕吉他原点的角度进行滤波',
    # props.py:GTR_Settings
    ('*', 'Filter the fingertip shift of fingertip magnets (SAO)'): '对指尖磁铁的指尖偏移量进行滤波（SAO）',
    # props.py:GTR_Settings
    ('*', "Filter the fretting wrist's blended rotation, relative to the chest (SAO)"): '对混合后的按弦手腕旋转（相对于胸骨）进行滤波（SAO）',
    # props.py:GTR_Settings
    ('*', "Filter the neck aim's swing. Not in SAO"): '对琴颈瞄准的摆动进行滤波。SAO 中无此项',
    # props.py:GTR_Settings
    ('*', 'Filter the solve from frame to frame when baking, where SAO does. Solve Frame solves a frame as the first of a bake, where there is nothing to filter yet'): '烘焙时按 SAO 的方式逐帧滤波。“求解当前帧”按烘焙首帧处理，此时尚无历史数据可供滤波',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('*', 'Find the guitar frame of the selected meshes (+X toward the headstock, +Z out of the strings), parent\nthem to GTR_ROOT with that frame, and move GTR_ROOT to the preset origin'): '识别所选网格的吉他坐标系（+X 指向琴头，+Z 垂直琴弦向外），将其设为 GTR_ROOT 的子级，并将 GTR_ROOT 移至预设原点',
    # ops/guitar.py:GTR_OT_auto_landmarks
    ('*', "Find the neck, the heel, the fretboard's tilt and the body on the guitar and place the landmarks on them,\nkeeping the preset's conventions: the string plane's height and the strum line's offsets. GTR_ROOT stays where\nit is. Check the landmarks afterwards"): '检测吉他上的琴颈、琴踵、指板倾角与琴体并自动放置标定点，同时保留预设约定（如琴弦平面高度与扫弦线偏移）。GTR_ROOT 位置不变。完成后请检查标定点',
    # props.py:GTR_Prep
    ('*', 'Finger joints stay within the range they have in the mocap plus this margin'): '手指关节活动范围将限制在原动捕范围加上此余量之内',
    # props.py:GTR_Prep
    ('*', "Finger moves smaller than this, in the finger's total bend over its joints, are left as they are"): '整根手指各关节总弯曲变化小于此阈值的动作保持原样',
    # props.py:GTR_Fingertip
    ('*', "Fingertip in the distal bone's rest space (armature units)"): '远节骨骼静置空间中的指尖位置（骨架单位）',
    # props.py:GTR_RangeOverride
    ('*', 'First frame of the range'): '区间的起始帧',
    # ops/guitar.py:GTR_OT_load_preset_file
    ('*', 'Fit a preset file to the guitar: landmarks, magnets, mount estimate, aim and wrist settings'): '将预设文件适配到当前吉他：包含标定点、磁铁、挂载估计值以及瞄准与手腕设置',
    # ops/guitar.py:GTR_OT_load_preset
    ('*', 'Fit the chosen preset to the guitar: landmarks, magnets, mount estimate, aim and wrist settings'): '将所选预设适配到当前吉他：包含标定点、磁铁、挂载估计值以及瞄准与手腕设置',
    # props.py:GTR_Guitar
    ('*', 'Fitted to the bounding box'): '按包围盒尺寸适配',
    # props.py:GTR_Guitar
    ('*', 'Fitted to the neck: length, width and thickness'): '按琴颈长度、宽度与厚度适配',
    # props.py:GTR_Settings
    ('*', 'Frame the mount was captured at'): '捕获挂载位置时所在的帧',
    # props.py:GTR_Settings
    ('*', 'Frame the wrist offset was captured at'): '捕获手腕偏移时所在的帧',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Fretboard surface, normal +Z: the fretting hand snaps onto it (SAO magnet 3)'): '指板表面，法线 +Z：按弦手会吸附到该平面（SAO 磁铁 3）',
    # props.py:GTR_Settings
    ('*', 'Frets with the left hand and strums with the right'): '左手按弦，右手拨弦',
    # props.py:GTR_Settings
    ('*', 'Frets with the right hand and strums with the left'): '右手按弦，左手拨弦',
    # props.py:GTR_Settings
    ('*', "Fretting-hand rotation relative to the guitar: the hand's rest-aligned frame turned by axis_rot (SAO: Euler 60°, 180°, 0° in its hand-tracking frame)"): '按弦手相对于吉他的旋转：经 axis_rot 旋转后的手部静置对齐坐标系（SAO：手部追踪坐标系下的欧拉角 60°、180°、0°）',
    # props.py:GTR_Settings
    ('*', 'From a preset'): '来自预设',
    # props.py:GTR_Settings
    ('*', 'From a preset: only an estimate'): '来自预设：仅为初始估计',
    # props.py:GTR_Settings
    ('*', 'GTR_ROOT: the empty that carries the normalised guitar frame'): 'GTR_ROOT：承载规范化吉他坐标系的空物体',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('*', "Go to the frame where the last bake's solve was worst by the chosen measure"): '跳转到上次烘焙中按所选指标表现最差的帧',
    # ops/setup.py:GTR_OT_auto_map_bones
    ('*', 'Guess the bone map from VRM metadata or from VRoid, Mixamo, Rigify, MMD, Unreal and generic bone names'): '根据 VRM 元数据，或 VRoid、Mixamo、Rigify、MMD、Unreal 及通用骨骼命名自动推测骨骼映射',
    # ui/panels.py:bl_category
    ('*', 'Guitar'): '吉他',
    # props.py:GTR_Settings
    ('*', 'Guitar frame in the rest-aligned chest frame'): '静置对齐胸骨坐标系中的吉他朝向',
    # props.py:GTR_Settings
    ('*', "Guitar origin relative to the chest bone head, in the rest-aligned chest frame (X: the character's left, Y: up, Z: forward), before the spine auto-scale"): '在脊柱自动缩放之前，静置对齐胸骨坐标系中吉他原点相对于胸骨起点的偏移（X：角色左侧，Y：上方，Z：前方）',
    # props.py:GTR_Settings
    ('*', "Hands whose quick motion passes through the magnets: the magnets act on the slow part of the wrist's path, and the strokes ride on top. The fretting hand needs its magnets to hold it on the fretboard"): '允许快速动作直通磁铁的手：磁铁仅作用于手腕路径的低速部分，快速拨弦动作叠加在其上。按弦手需要磁铁将其固定在指板上',
    # props.py:GTR_BoneMap
    ('*', 'Head bone'): '头部骨骼',
    # props.py:GTR_BoneMap
    ('*', 'Hips bone'): '臀部骨骼',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far a hand point was behind a barrier plane before it was clamped'): '手部参考点在被限位前深入阻挡面后方的距离',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far a solved wrist ended from its target'): '求解后的手腕最终偏离目标点的距离',
    # props.py:GTR_Settings
    ('*', 'How far fingertip magnets keep the nearest fingertip above their plane, before the arm-ratio scaling (SAO: the reference palm length / 4)'): '在按臂长比例缩放前，指尖磁铁将最近指尖保持在平面上方的距离（SAO：参考手掌长度 / 4）',
    # props.py:GTR_Settings
    ('*', "How far in front of the chest bone head the capsule's axis runs"): '胶囊体轴线位于胸骨起点前方的距离',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the chest collider pushed a wrist'): '胸部碰撞体将手腕推离的距离',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the fretting wrist turned away from the mocap'): '按弦手腕偏离原始动捕的转动角度',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the neck aim turned the guitar from its mount'): '琴颈瞄准使吉他偏离挂载位的摆动角度',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'How far the solve moved a wrist target from the mocap wrist'): '求解将手腕目标从动捕手腕移动的距离',
    # props.py:GTR_Settings
    ('*', "How lengths authored for SAO's reference avatar fit this character. Magnet distances scale with the arm, and the mount with the spine, except under None"): '如何将按 SAO 参考角色制作的长度参数适配到当前角色。除“无”以外，磁铁距离随臂长缩放，挂载偏移随脊柱缩放',
    # props.py:GTR_Prep
    ('*', "How many frames the arm's swing leads the hand's stroke"): '手臂摆动提前于手部扫弦的帧数',
    # props.py:GTR_Prep
    ('*', "How much larger the fretting fingers' quick moves get, per joint (1: unchanged). Quick presses overshoot slightly"): '按弦手指各关节快速动作的放大倍数（1：不变）。快速按压会产生轻微过冲',
    # props.py:GTR_Prep
    ('*', "How much larger the picking hand's quick turns get, relative to the forearm (1: unchanged)"): '拨弦手相对于前臂的快速转动放大倍数（1：不变）',
    # props.py:GTR_Prep
    ('*', 'How much of the swing the elbow makes against the shoulder'): '手臂摆动中肘部相对于肩部分担的比例',
    # props.py:GTR_BoneMap
    ('*', 'IK chain length from the IK forearm up to the IK upper arm (0: not a valid chain)'): '从 IK 前臂到 IK 上臂的 IK 骨骼链长度（0：无效链）',
    # props.py:GTR_Guitar
    ('*', 'Id or file of the preset the landmarks were fitted from'): '用于适配标定点的预设 ID 或文件路径',
    # props.py:GTR_Settings
    ('*', 'In the rest-aligned upper-arm frame. SAO: (0°, 10°, -15°), order ZYX in three.js'): '位于静置对齐上臂坐标系中。SAO：(0°, 10°, -15°)，three.js 中顺序为 ZYX',
    # props.py:GTR_Settings
    ('*', 'Instrument preset: landmarks, magnets, mount, aim and wrist settings'): '乐器预设：包含标定点、磁铁、挂载、瞄准和手腕设置',
    # props.py:GTR_Settings
    ('*', 'Keep the index, middle and ring fingertips out as well'): '同时将食指、中指和无名指指尖保持在碰撞体外',
    # props.py:GTR_Settings
    ('*', 'Keep wrist targets within this share of the arm chain length, or as far as the mocap wrist if it is further'): '将手腕目标限制在手臂链长度的该比例以内；若原始动捕手腕更远，则以动捕距离为上限',
    # props.py:GTR_Settings
    ('*', 'Key GTR_ROOT in world space, without a parent'): '在世界空间中为 GTR_ROOT 打帧，不设置父级',
    # props.py:GTR_RangeOverride
    ('*', 'Last frame of the range'): '区间的结束帧',
    # props.py:GTR_BoneMap
    ('*', 'Left Forearm bone'): '左前臂骨骼',
    # props.py:GTR_BoneMap
    ('*', 'Left Hand bone'): '左手骨骼',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Distal bone (optional)'): '左手食指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Intermediate bone (optional)'): '左手食指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Index Proximal bone (optional)'): '左手食指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Distal bone (optional)'): '左手中指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Intermediate bone (optional)'): '左手中指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Middle Proximal bone (optional)'): '左手中指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Distal bone (optional)'): '左手无名指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Intermediate bone (optional)'): '左手无名指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Ring Proximal bone (optional)'): '左手无名指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Left Upper Arm bone'): '左上臂骨骼',
    # props.py:GTR_Settings
    ('*', "Low-pass only what the solve changed in the arms, so the mocap's own quick motion (and the prep's) stays"): '仅对求解在手臂上产生的修正量进行低通滤波，从而保留动捕（及预处理）原有的快速动作',
    # ops/bake.py:GTR_OT_smooth_bake
    ('*', 'Low-pass the baked arm and guitar keys, forward and backward so nothing lags; in Correction mode only what\nthe solve changed in the arms, so their quick motion stays. Re-clamp afterwards to restore the contacts. Esc\ncancels'): '对已烘焙的手臂和吉他关键帧执行双向零相位低通滤波（无延迟）；在“修正量”模式下仅平滑求解对手臂的改变量，以保留快速动作。平滑后可执行“重新限位”恢复接触。按 Esc 取消',
    # props.py:GTR_Settings
    ('*', 'Low-pass the baked arm keys themselves'): '直接对已烘焙的手臂关键帧本身进行低通滤波',
    # props.py:GTR_Settings
    ('*', "Lower end of the capsule's axis relative to the chest bone head"): '胶囊体轴线下端相对于胸骨起点的位置',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Lower fretboard edge (-Y) near the neck/body joint: start of the neck axis the aim swings (SAO reference_origin)'): '靠近琴颈/琴体连接处的指板下缘（-Y）：琴颈瞄准摆动轴线的起点（SAO reference_origin）',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Lower fretboard edge at the nut: end of the aimed neck axis (SAO reference_point)'): '上弦枕处的指板下缘：琴颈瞄准轴线的终点（SAO reference_point）',
    # props.py:GTR_Settings
    ('*', "Magnet hand offsets scale with the arm, like SAO's arm-normalised magnet space for VRM avatars"): '磁铁手部偏移随臂长缩放，与 SAO 面向 VRM 角色的臂长归一化磁铁空间一致',
    # props.py:GTR_Settings
    ('*', 'Magnet hand offsets scale with the palm, like the neck aim'): '磁铁手部偏移随手掌长度缩放，与琴颈瞄准一致',
    # props.py:GTR_Settings
    ('*', 'Magnets whose Filter is One Euro: minimum cutoff (Hz), beta and derivative cutoff (Hz) on their pull (SAO)'): '采用 One Euro 滤波的磁铁：作用于牵引力的最小截止频率 (Hz)、beta 与导数截止频率 (Hz)（SAO）',
    # props.py:GTR_Settings
    ('*', "Magnets whose Filter is Rotation: minimum cutoff (Hz), beta and derivative cutoff (Hz) on the hand's angle about the guitar origin (SAO)"): '采用旋转滤波的磁铁：作用于手部绕吉他原点角度的最小截止频率 (Hz)、beta 与导数截止频率 (Hz)（SAO）',
    # ops/setup.py:GTR_OT_calibrate
    ('*', 'Measure the character in rest pose: character frame, rest-aligned frames, ratios, axis_rot, fingertips'): '在静置姿态下测量角色：角色坐标系、静置对齐坐标系、比例系数、axis_rot 与指尖位置',
    # props.py:GTR_Prep
    ('*', 'Motion slower than this is the posture, which Range and Snap keep; faster motion is the detail they work on'): '低于此频率的运动视为基础姿态，“幅度”和“锐化”会保留它；高于此频率的快速运动视为待增强的细节',
    # ops/magnets.py:GTR_OT_magnet_move
    ('*', 'Move the active magnet up or down the list. Magnets act in list order'): '在列表中上移或下移当前活动磁铁。磁铁按列表顺序依次生效',
    # props.py:GTR_Prep
    ('*', 'Move the forearm roll from the wrist onto the forearm twist bone (MMD 手捩) on both hands, so the forearm skin twists with it. The hands keep their pose'): '将双手手腕的前臂自旋转移到前臂扭转骨骼（MMD 手捩）上，使前臂蒙皮正常跟随扭转，同时保持手部姿态不变',
    # ops/mount.py:GTR_OT_place_on_mount
    ('*', "Move the guitar to its chest mount for the current frame's pose"): '按当前帧姿态将吉他移动到其胸部挂载位',
    # ops/prep.py:GTR_OT_toggle_prep
    ('*', 'Mute or unmute the GuitarPrep layer, to compare the prepped motion with the original'): '静音或取消静音 GuitarPrep 图层，用于将预处理后的动作与原始动作对比',
    # props.py:GTR_Settings
    ('*', 'Name of the preset the mount came from'): '挂载设置来源的预设名称',
    # props.py:GTR_BoneMap
    ('*', 'Naming conventions the last auto-map matched'): '上次自动映射匹配到的骨骼命名规范',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Neck end of the strum line (SAO magnet 0)'): '扫弦线的琴颈端（SAO 磁铁 0）',
    # props.py:GTR_Guitar
    ('*', 'No landmarks were placed by the add-on'): '插件尚未放置任何标定点',
    # props.py:GTR_Settings
    ('*', 'No mount yet: load a preset or capture it'): '尚未设置挂载：请加载预设或捕获挂载',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', "Normal +X: holds the picking hand's position along the strings (SAO magnet 1)"): '法线 +X：控制拨弦手沿琴弦方向的位置（SAO 磁铁 1）',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Normal +X: the fretting hand stays on the headstock side of the neck/body joint (SAO magnet 4)'): '法线 +X：使按弦手保持在琴颈/琴体连接处靠琴头一侧（SAO 磁铁 4）',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', "Normal +Z: the picking hand's fingertips stay above it (SAO magnet 2)"): '法线 +Z：使拨弦手指尖保持在该平面上方（SAO 磁铁 2）',
    # props.py:GTR_Settings
    ('*', 'Nothing is scaled to the character'): '不对角色进行任何比例缩放',
    # props.py:GTR_Magnet
    ('*', 'Off: the plane is a barrier, and a hand behind it is clamped onto it with full weight'): '关闭时：该平面作为阻挡面，位于其后方的手会以满权重被限位推回平面上',
    # props.py:GTR_Magnet
    ('*', 'Offset from the wrist in the rest-aligned hand frame, in metres'): '静置对齐手部坐标系中相对于手腕的偏移（米）',
    # props.py:GTR_Guitar
    ('*', 'One cue decided, or one of three disagreed'): '仅由单一线索决定，或三条线索中有一条存在分歧',
    # props.py:GTR_Magnet
    ('*', 'One-euro filter on the pull'): '对磁铁牵引力应用 One Euro 滤波',
    # props.py:GTR_Settings
    ('*', 'One-euro minimum cutoff (Hz), beta and derivative cutoff (Hz)'): 'One Euro 滤波参数：最小截止频率 (Hz)、beta 与导数截止频率 (Hz)',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Optional, normal -X: the fretting hand stays on the body side of the nut (SAO magnet 6, ukulele)'): '可选，法线 -X：使按弦手保持在上弦枕靠琴体一侧（SAO 磁铁 6，尤克里里）',
    # props.py:GTR_Settings
    ('*', 'Parent GTR_ROOT to the chest bone and key it relative to the bone, so the guitar follows later edits of the body'): '将 GTR_ROOT 设为胸骨的子级并相对于胸骨打帧，使吉他能跟随后续对身体的动画修改',
    # props.py:GTR_Magnet
    ('*', "Place the feature with the guitar's chest-mount rotation, before the neck aim"): '使用吉他琴颈瞄准前的胸部挂载旋转来放置该几何特征',
    # props.py:GTR_Guitar
    ('*', "Placed by the preset fitted to the guitar's bounds and neck"): '按预设对吉他包围盒和琴颈的适配结果放置',
    # props.py:GTR_Guitar
    ('*', 'Placed on the neck, heel and body found on the mesh'): '根据网格上检测到的琴颈、琴踵与琴体自动放置',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Plane through the lower fretboard edge, normal +Y: the fretting hand stays above it (SAO magnet 5)'): '穿过指板下缘的平面，法线 +Y：使按弦手保持在该边缘上方（SAO 磁铁 5）',
    # ops/bake.py:GTR_OT_reclamp
    ('*', 'Play the bake back and, on the frames where a hand went into a barrier or the chest collider, push it out\nand solve that arm again. Esc cancels'): '回放烘焙结果，在手部进入阻挡面或胸部碰撞体的帧将其推回安全位置并重新求解该手臂。按 Esc 取消',
    # props.py:GTR_Settings
    ('*', 'Post-bake low-pass cutoff for the arm channels'): '烘焙后平滑手臂通道的低通截止频率',
    # props.py:GTR_Settings
    ('*', 'Post-bake low-pass cutoff for the guitar channels'): '烘焙后平滑吉他通道的低通截止频率',
    # props.py:GTR_Magnet
    ('*', 'Pull toward the segment from landmark A to landmark B'): '向标定点 A 到标定点 B 组成的线段牵引',
    # props.py:GTR_Magnet
    ('*', "Pull toward, or clamp against, the plane through landmark A (normal: A's local Z)"): '向穿过标定点 A 的平面牵引或进行阻挡限位（法线为 A 的局部 Z 轴）',
    # props.py:GTR_Settings
    ('*', 'Push the wrists and their fingertips forward out of a capsule around the torso, before the magnets act'): '在磁铁生效前，将手腕及指尖从包裹躯干的胶囊体中向前推出',
    # props.py:GTR_Settings
    ('*', 'Radius of the capsule, before the spine auto-scale'): '脊柱自动缩放前的胶囊体半径',
    # props.py:GTR_Settings
    ('*', 'Re-clamp re-solves the frames where a hand is further than this into a barrier or the chest collider'): '当手部深入阻挡面或胸部碰撞体超过此容差时，“重新限位”会重新求解对应帧',
    # props.py:GTR_Magnet
    ('*', 'Reach of the magnet in metres, before arm-ratio scaling. Barriers need it too'): '按臂长比例缩放前的磁铁作用距离（米）。阻挡面同样需要此参数',
    # ops/bake.py:GTR_OT_remove_bake
    ('*', "Remove the GuitarBake and GuitarRefine tracks and the bake actions, and put back the animation and the\nguitar's parent as they were before the bake. Refine actions with keys are kept"): '移除 GuitarBake 与 GuitarRefine 轨道及烘焙动作，并恢复烘焙前的原有动画与吉他父级关系。带有关键帧的精修动作会被保留',
    # ops/prep.py:GTR_OT_remove_prep
    ('*', 'Remove the GuitarPrep layer and its action: the solve and the bake read the original mocap again. The bake\nstays'): '移除 GuitarPrep 图层及其动作：求解和烘焙将重新读取原始动捕。已有的烘焙结果会被保留',
    # ops/magnets.py:GTR_OT_magnet_remove
    ('*', 'Remove the active magnet'): '移除当前活动磁铁',
    # ops/rig.py:GTR_OT_range_remove
    ('*', 'Remove the active range override'): '移除当前活动区间覆盖',
    # ops/rig.py:GTR_OT_clean_rig
    ('*', 'Remove the helper rig: its constraints, its empties and the GuitarRig collection'): '移除辅助绑定：删除其约束、空物体以及 GuitarRig 集合',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Replace the magnet list with the preset's"): '用预设的磁铁列表替换当前磁铁列表',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Replace the mount with the preset's estimate (off when the mount was captured)"): '用预设的挂载估计值替换当前挂载（若已手动捕获挂载则默认关闭）',
    # props.py:GTR_BoneMap
    ('*', 'Right Forearm bone'): '右前臂骨骼',
    # props.py:GTR_BoneMap
    ('*', 'Right Hand bone'): '右手骨骼',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Distal bone (optional)'): '右手食指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Intermediate bone (optional)'): '右手食指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Index Proximal bone (optional)'): '右手食指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Distal bone (optional)'): '右手中指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Intermediate bone (optional)'): '右手中指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Middle Proximal bone (optional)'): '右手中指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Distal bone (optional)'): '右手无名指远节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Intermediate bone (optional)'): '右手无名指中节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Ring Proximal bone (optional)'): '右手无名指近节骨骼（可选）',
    # props.py:GTR_BoneMap
    ('*', 'Right Upper Arm bone'): '右上臂骨骼',
    # props.py:GTR_Magnet
    ('*', 'Role of the magnet in a preset (e.g. FRETBOARD_PLANE); mode switches find magnets by it'): '磁铁在预设中的角色标识（例如 FRETBOARD_PLANE）；模式切换依赖此标识查找磁铁',
    # props.py:GTR_Magnet
    ('*', 'Rotate the offset by axis_rot, as SAO does for avatars whose rest pose is not a T-pose; axis_rot is the identity on T-pose rigs'): '按 SAO 的方式用 axis_rot 旋转偏移量（用于非 T-pose 静置姿态的角色；T-pose 绑定上 axis_rot 为单位旋转）',
    # props.py:GTR_Magnet
    ('*', "SAO's reference_point_offset_distance: shifts the plane along its normal for the fingertips. In GTR_ROOT units, so it scales with the guitar (metres for a real-size guitar at scale 1)"): 'SAO 的 reference_point_offset_distance：沿平面法线为指尖平移平面。使用 GTR_ROOT 单位，因此会随吉他缩放（缩放为 1 的真实尺寸吉他即为米）',
    # props.py:GTR_Settings
    ('*', "SAO's rotation_reference offset"): 'SAO 的 rotation_reference 偏移',
    # props.py:GTR_Settings
    ('*', "SAO's setting (-1) in all guitar scenes"): 'SAO 所有吉他场景中的默认设置（-1）',
    # ops/guitar.py:GTR_OT_save_preset
    ('*', 'Save the landmarks, magnets, mount, aim and wrist settings as a preset file for other guitars'): '将当前的标定点、磁铁、挂载、瞄准和手腕设置保存为预设文件，供其他吉他复用',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('*', 'Scale GTR_ROOT so that the guitar is this long, in metres; 0 keeps its size'): '缩放 GTR_ROOT 使吉他总长达到该数值（米）；填 0 则保持原尺寸',
    # props.py:GTR_Prep
    ('*', 'Scales every tool toward doing nothing (0) or beyond its strength (above 1)'): '统一缩放所有预处理工具的效果：0 表示不生效，大于 1 表示超过默认强度',
    # ops/bake.py:GTR_OT_show_diagnostics
    ('*', 'Select the GTR_Diagnostics empty, whose curves show what the solve did on each frame in the Graph Editor'): '选中 GTR_Diagnostics 空物体，以便在曲线编辑器中查看每帧的求解曲线',
    # ops/guitar.py:GTR_OT_select_landmark
    ('*', 'Select the landmark, or add it at the 3D cursor if it does not exist'): '选中该标定点；若不存在，则在 3D 游标处创建',
    # props.py:GTR_Settings
    ('*', 'Share of each new aim rotation taken per iteration; lower it if the guitar oscillates between iterations'): '每次迭代采纳新瞄准旋转的比例；如果吉他在迭代间来回抖动，请调低此值',
    # props.py:GTR_Settings
    ('*', 'Share of the guitar-relative rotation in the fretting wrist'): '按弦手腕采纳相对于吉他旋转目标的比例',
    # props.py:GTR_Settings
    ('*', 'Share of the quick wrist motion that passes through (0: the magnets act on all of it)'): '允许直通磁铁的快速手腕动作比例（0：磁铁作用于全部动作）',
    # props.py:GTR_Magnet
    ('*', 'Shift the hand so that the nearest fingertip lands on the plane'): '平移手部，使最近的指尖恰好落在平面上',
    # ops/prep.py:GTR_OT_toggle_prep
    ('*', 'Show the original mocap (mute the prep layer)'): '显示原始动捕（静音预处理图层）',
    # props.py:GTR_Guitar
    ('*', "Size of the guitar relative to the preset's reference, along X (neck length), Y (neck width) and Z (neck thickness)"): '吉他相对于预设参考模型的比例，分别对应 X（琴颈长度）、Y（琴颈宽度）与 Z（琴颈厚度）',
    # props.py:GTR_Settings
    ('*', 'Smooth between the per-frame keys'): '在逐帧关键帧之间平滑插值',
    # ops/bake.py:GTR_OT_bake
    ('*', 'Solve every frame of the range and key the arms and the guitar into GuitarBake NLA strips, with a\nGuitarRefine layer on top for your corrections. Esc cancels'): '求解范围内的每一帧，将手臂与吉他打帧到 GuitarBake NLA 片段中，并在上方创建 GuitarRefine 图层供手动精修。按 Esc 取消',
    # props.py:GTR_Settings
    ('*', 'Solve iterations per frame: in Follow mode, neck aims, each followed by the magnets and the IK'): '每帧的求解迭代次数：在跟随模式下，每次迭代先执行琴颈瞄准，再计算磁铁与 IK',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('*', 'Solve passes on the frames whose neck aim or wrists had not settled'): '琴颈瞄准或手腕尚未收敛帧的求解轮数',
    # ops/rig.py:GTR_OT_solve_frame
    ('*', 'Solve the current frame: the guitar goes on its mount and the magnets move the wrists. The arms show the\nresult until the frame changes'): '求解当前帧：将吉他放上挂载位并用磁铁移动手腕。双臂会展示求解结果，直到切换帧为止',
    # props.py:GTR_Prep
    ('*', "Steepness of the fretting fingers' presses and releases (1: unchanged)"): '按弦手指按压与抬起的陡峭程度（1：不变）',
    # props.py:GTR_Prep
    ('*', "Steepness of the picking fingers' moves (1: unchanged)"): '拨弦手指动作的陡峭程度（1：不变）',
    # props.py:GTR_Prep
    ('*', "Steepness of the picking hand's strokes: each stroke is retimed along an S-curve with this exponent, keeping where it starts, ends and crosses half way (1: unchanged)"): '拨弦手拨弦动作的陡峭程度：每次拨弦按该指数的 S 曲线重定时，保持起止位置和过半时刻不变（1：不变）',
    # ops/mount.py:GTR_OT_capture_wrist_offset
    ('*', "Store the fretting hand's rotation relative to the guitar in the current frame's pose as the wrist target.\nPose the guitar and the fretting hand on its neck first"): '将当前帧姿态下按弦手相对于吉他的旋转保存为手腕目标。请先在琴颈上摆好吉他和按弦手姿势',
    # ops/mount.py:GTR_OT_capture_mount
    ('*', "Store where the guitar sits relative to the chest in the current frame's pose as the mount. Pose the\nguitar on the character first (move and rotate GTR_ROOT)"): '将当前帧姿态下吉他相对于胸骨的位置与朝向保存为挂载设置。请先移动和旋转 GTR_ROOT 在角色身上摆好吉他',
    # props.py:GTR_Settings
    ('*', 'Straight between the per-frame keys'): '在逐帧关键帧之间线性插值',
    # props.py:GTR_Prep
    ('*', 'Strokes of the picking hand smaller than this are left as they are'): '拨弦手幅度小于此阈值的动作保持原样',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Swap the headstock and body ends (half turn about Z)'): '交换琴头与琴体两端（绕 Z 轴旋转 180°）',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Swap the string face and the back (half turn about X)'): '交换琴弦面与背面（绕 X 轴旋转 180°）',
    # props.py:GTR_Settings
    ('*', 'Swing the neck toward the fretting wrist (FOLLOW mode)'): '将琴颈朝按弦手腕方向摆动（跟随模式）',
    # ops/rig.py:GTR_OT_clear_solve
    ('*', "Switch the rig's constraints off, so that the arms play the mocap again"): '关闭辅助绑定的约束，使双臂恢复播放原始动捕',
    # props.py:GTR_Settings
    ('*', "Switches the neck aim and the fretboard-edge magnet like SAO's Alt+A; the fields stay editable"): '像 SAO 的 Alt+A 一样切换琴颈瞄准与指板边缘磁铁；切换后各项参数仍可编辑',
    # props.py:GTR_Settings
    ('*', 'The GuitarRig collection that holds the helper empties'): '存放辅助空物体的 GuitarRig 集合',
    # props.py:GTR_Magnet
    ('*', 'The aim hand offset (SAO\'s "parent_bone" offset)'): '瞄准手部偏移（SAO 的 "parent_bone" 偏移）',
    # props.py:GTR_Settings
    ('*', "The armature that carries the helper rig's constraints"): '承载辅助绑定约束的骨架',
    # props.py:GTR_BoneMap
    ('*', 'The bone the guitar mounts on: the humanoid chest (MMD 上半身2, VRM chest)'): '吉他挂载所用的骨骼：人形胸骨（MMD 上半身2，VRM chest）',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('*', "The character's left hand"): '角色的左手',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('*', "The character's right hand"): '角色的右手',
    # props.py:GTR_Guitar
    ('*', 'The cues disagree or are missing: check the axes'): '检测线索存在冲突或缺失：请检查坐标轴',
    # props.py:GTR_Fingertip
    ('*', "The distal bone's tail"): '远节骨骼的末端',
    # props.py:GTR_Settings
    ('*', "The empty whose animated custom properties hold what the last bake's solve did on each frame"): '通过动画自定义属性记录上次烘焙每帧求解信息的空物体',
    # props.py:GTR_Magnet
    ('*', 'The fingertips may push the hand away from the plane but never pull it in'): '允许指尖将手推离平面，但绝不将手拉向平面',
    # props.py:GTR_BoneMap
    ('*', 'The forearm that carries the IK constraint; on Rigify-style rigs, the FK control'): '承载 IK 约束的前臂骨骼；在 Rigify 风格绑定中为 FK 控制器',
    # props.py:GTR_Settings
    ('*', 'The frame whose solve the rig shows'): '辅助绑定当前正在展示求解结果的帧',
    # props.py:GTR_Guitar
    ('*', 'The guitar frame or the body is doubtful: check the landmarks'): '吉他坐标系或琴体检测存在疑点：请检查标定点',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('*', "The guitar stays on the chest and the fretting hand slides along the fretboard edge (SAO's Alt+A mode)"): '吉他保持在胸前不动，按弦手沿指板边缘滑动（SAO 的 Alt+A 模式）',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('*', "The guitar yaws toward the fretting hand (SAO's default mode)"): '吉他朝按弦手方向偏航摆动（SAO 默认模式）',
    # props.py:GTR_Magnet
    ('*', 'The hand point itself meets the plane'): '手部参考点本身贴合平面',
    # props.py:GTR_BoneMap
    ('*', 'The hand that gets the wrist rotation; on Rigify-style rigs, the FK control'): '接收手腕旋转约束的手部骨骼；在 Rigify 风格绑定中为 FK 控制器',
    # props.py:GTR_BoneMap
    ('*', 'The left one is used for the spine length (optional)'): '左侧大腿骨用于测量脊柱长度（可选）',
    # props.py:GTR_RangeOverride
    ('*', "The mode's switch applies to these frames on top of the scene's settings"): '该模式的切换设置会在场景设置的基础上应用于这些帧',
    # props.py:GTR_Guitar
    ('*', 'The neck, the heel and the body were all found'): '已成功检测到琴颈、琴踵与琴体',
    # props.py:GTR_Magnet
    ('*', 'The offset vector below'): '下方指定的自定义偏移向量',
    # props.py:GTR_Settings
    ('*', 'The retargeted character armature that plays the mocap'): '已重定向并播放动捕动画的角色骨架',
    # props.py:GTR_Settings
    ('*', "The rig's constraints are on and show the solve of Solve Frame"): '辅助绑定的约束已开启，正在显示“求解当前帧”的结果',
    # props.py:GTR_BoneMap
    ('*', 'The upper arm the IK drives; on Rigify-style rigs, the FK control'): '受 IK 驱动的上臂骨骼；在 Rigify 风格绑定中为 FK 控制器',
    # props.py:GTR_Magnet
    ('*', 'The wrist itself'): '手腕本身',
    # ops/prep.py:GTR_OT_apply_prep
    ('*', 'Touch up the mocap before the bake: wider and crisper picking strokes, an arm swing, crisp fretting\nfingers and the forearm roll on the twist bone. Reads the original mocap and writes a GuitarPrep NLA layer,\nwhich the solve and the bake then read. Esc cancels'): '在烘焙前润色动捕：放大并锐化拨弦动作、添加手臂摆动、使按弦手指更干脆，并将前臂自旋转移到扭转骨骼。读取原始动捕并写入 GuitarPrep NLA 图层，供后续求解和烘焙使用。按 Esc 取消',
    # props.py:GTR_Calibration
    ('*', 'Turn the character frame half a turn about the up axis, if the detected facing is wrong'): '如果检测到的角色朝向相反，绕上方轴将角色坐标系旋转 180°',
    # ops/guitar.py:GTR_OT_flip_frame
    ('*', 'Turn the guitar frame half a turn (the guitar stays in place) and fit the landmarks again'): '将吉他坐标系旋转 180°（吉他本身原地不动）并重新适配标定点',
    # props.py:GTR_Settings
    ('*', 'Turn the other way (+1)'): '向相反方向转动（+1）',
    # props.py:GTR_Settings
    ('*', "Turn the right arm before the IK, like SAO's root_rotation: this moves where the right elbow points"): '在 IK 求解前旋转右臂，类似 SAO 的 root_rotation：用于调整右肘指向',
    # props.py:GTR_Settings
    ('*', "Upper end of the capsule's axis above the chest bone head, along the chest's up axis"): '胶囊体轴线上端沿胸部上方轴超出胸骨起点的位置',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('*', "Use the preset's aim hand offset and wrist rotation (off when the wrist offset was captured)"): '使用预设的瞄准手部偏移与手腕旋转（若已手动捕获手腕偏移则默认关闭）',
    # props.py:GTR_BoneMap
    ('*', 'Used for the spine length (optional)'): '用于测量脊柱长度（可选）',
    # props.py:GTR_Prep
    ('*', 'What the last Apply Prep did'): '上次执行“应用预处理”的报告摘要',
    # props.py:GTR_Settings
    ('*', 'What the last bake, smoothing or re-clamp did'): '上次执行烘焙、平滑或重新限位的报告摘要',
    # props.py:GTR_Settings
    ('*', 'What the worst frames are ranked by'): '用于排序最差帧的诊断指标',
    # props.py:GTR_Settings
    ('*', "When the mocap wrist faces more than 120° away from the target about the up axis, turn it this way instead of the shorter way (SAO's constrained_direction)"): '当动捕手腕绕上方轴偏离目标超过 120° 时，改用此方向转动而非较短路径（SAO 的 constrained_direction）',
    # props.py:GTR_Settings
    ('*', 'Wrist motion faster than this, relative to the chest, passes through the magnets'): '相对于胸部高于此频率的手腕动作将直通磁铁',
    # props.py:GTR_Settings
    ('*', "XR Animator's Stratocaster scene (guitar_collection_v9.1/scene - stratocaster guitar.json)"): 'XR Animator 的 Stratocaster 电吉他场景（guitar_collection_v9.1/scene - stratocaster guitar.json）',
    # props.py:GTR_Settings
    ('*', "XR Animator's acoustic guitar scene (guitar_collection_v9.1/scene.json)"): 'XR Animator 的木吉他场景（guitar_collection_v9.1/scene.json）',
    # props.py:GTR_Settings
    ('*', "XR Animator's bass guitar scene (guitar_collection_v9.1/scene - bass guitar.json)"): 'XR Animator 的电贝斯场景（guitar_collection_v9.1/scene - bass guitar.json）',
    # props.py:GTR_Settings
    ('*', "XR Animator's ukulele scene (guitar_collection_v9.1/scene - ukulele.json)"): 'XR Animator 的尤克里里场景（guitar_collection_v9.1/scene - ukulele.json）',
    # ui/panels.py:573
    ('GuitarRig', '   pass-through'): '   直通',
    # ui/panels.py:579
    ('GuitarRig', '   {name}'): '   {name}',
    # core/solver.py:383
    ('GuitarRig', ' ({causes})'): '（{causes}）',
    # core/guitar_frame.py:695
    ('GuitarRig', ' Conflicting cues: {cues}.'): ' 冲突线索：{cues}。',
    # core/autoland.py:171
    ('GuitarRig', ' The body starts under the neck {past:.1f} cm past where the neck narrows (cutaways).'): ' 琴体在琴颈收窄处后方 {past:.1f} cm 处开始（缺角）。',
    # core/autoland.py:175
    ('GuitarRig', ' The heel reaches {length:.1f} cm up the neck from where it narrows.'): ' 琴踵从琴颈收窄处沿琴颈延伸 {length:.1f} cm。',
    # core/bonemap.py:335
    ('GuitarRig', "'{name}' is mapped to both sides ({title} and its right twin)."): '“{name}”被同时映射到了左右两侧（{title} 及其右侧对应项）。',
    # core/bonemap.py:345
    ('GuitarRig', "'{name}' is used for both {first_slot} and {second_slot}."): '“{name}”被同时用于 {first_slot} 和 {second_slot}。',
    # core/baker.py:760
    ('GuitarRig', '. Skipped curves whose keys are not one per frame: {skipped}'): '。已跳过非逐帧打帧的曲线：{skipped}',
    # core/prepjob.py:557
    ('GuitarRig', '. Strokes snapped: {moves}'): '。已锐化拨弦次数：{moves}',
    # core/prepjob.py:544
    ('GuitarRig', ". The pick point's travel: {before:.1f} → {after:.1f} cm RMS"): '。拨片点位移：{before:.1f} → {after:.1f} cm RMS',
    # ui/panels.py:483
    ('GuitarRig', 'A capsule along the chest that pushes the wrists forward out of the torso before the magnets act. Lengths are metres before the spine auto-scale.'): '沿胸部的胶囊体，在磁铁生效前将双手手腕向前推出躯干。长度单位为脊柱自动缩放前的米。',
    # ui/panels.py:533
    ('GuitarRig', 'A range ends before it starts: it is ignored'): '存在结束帧早于起始帧的区间：已忽略',
    # presets/acoustic.json, props.py:GTR_Settings
    ('GuitarRig', 'Acoustic Guitar'): '木吉他',
    # ops/magnets.py:GTR_OT_magnet_add
    ('GuitarRig', 'Add Magnet'): '添加磁铁',
    # ops/rig.py:GTR_OT_range_add
    ('GuitarRig', 'Add Range Override'): '添加区间覆盖',
    # ops/guitar.py:498
    ('GuitarRig', 'Added {name} at the 3D cursor.'): '已在 3D 游标处添加 {name}。',
    # ui/panels.py:657
    ('GuitarRig', 'After the Bake'): '烘焙后处理',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Filter'): '瞄准滤波',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Hand Offset (m)'): '瞄准手部偏移 (m)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Neck'): '瞄准琴颈',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Aim Offset'): '瞄准偏移',
    # props.py:GTR_Settings
    ('GuitarRig', 'Aim Weight'): '瞄准权重',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file
    ('GuitarRig', 'Aim and Wrist'): '瞄准与手腕',
    # core/modes.py:21, props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('GuitarRig', 'Align'): '对齐',
    # core/calibrate.py:233
    ('GuitarRig', 'An arm, palm or spine length is zero or negative; check the bone map.'): '手臂、手掌或脊柱长度为零或负值；请检查骨骼映射。',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Apply Axis Rotation'): '应用轴向旋转',
    # ops/prep.py:GTR_OT_apply_prep
    ('GuitarRig', 'Apply Prep'): '应用预处理',
    # ops/prep.py:48
    ('GuitarRig', 'Apply Prep first'): '请先应用预处理',
    # ui/panels.py:308
    ('GuitarRig', 'Apply Prep touches up the mocap before the bake: wider, crisper picking strokes with an arm swing, crisp fretting fingers, and the forearm roll on the twist bone. Your action is not changed.'): '应用预处理会在烘焙前润色动捕：放大并锐化拨弦动作、添加手臂摆动、使按弦手指更干脆，并将前臂自旋转移到扭转骨骼。你原有的动作不会被修改。',
    # ui/panels.py:227, ui/panels.py:49
    ('GuitarRig', 'Arm'): '手臂',
    # props.py:GTR_Settings
    ('GuitarRig', 'Arm Cutoff (Hz)'): '手臂截止频率 (Hz)',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Length (m)'): '臂长 (m)',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Ratio'): '臂长比例',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Arm Reference Angle'): '手臂参考角',
    # ops/setup.py:GTR_OT_auto_map_bones
    ('GuitarRig', 'Auto-Map Bones'): '自动映射骨骼',
    # ops/guitar.py:GTR_OT_auto_landmarks
    ('GuitarRig', 'Auto-Place'): '自动放置',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Auto-Placed'): '自动放置',
    # props.py:GTR_Settings
    ('GuitarRig', 'Auto-Scale'): '自动缩放',
    # ui/panels.py:LANDMARK_TEXT
    ('GuitarRig', 'Auto-placed'): '已自动放置',
    # ui/panels.py:144
    ('GuitarRig', 'Auto-placed ({confidence} confidence)'): '已自动放置（置信度：{confidence}）',
    # ops/guitar.py:550
    ('GuitarRig', "Auto-placed {landmarks_count} landmarks with the {name} preset's conventions ({confidence} confidence). Check them."): '已按 {name} 预设的约定自动放置 {landmarks_count} 个标定点（置信度：{confidence}）。请检查确认。',
    # ops/guitar.py:GTR_OT_flip_frame
    ('GuitarRig', 'Axis'): '轴向',
    # ops/bake.py:GTR_OT_bake, ui/panels.py:GTR_PT_bake
    ('GuitarRig', 'Bake'): '烘焙',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bake Report'): '烘焙报告',
    # ops/bake.py:142, ops/bake.py:164
    ('GuitarRig', 'Bake first'): '请先执行烘焙',
    # ops/bake.py:200
    ('GuitarRig', 'Bake first: the bake records the diagnostics'): '请先执行烘焙：烘焙过程会记录诊断数据',
    # core/baker.py:806
    ('GuitarRig', 'Bake first: the character has no GuitarBake strip.'): '请先执行烘焙：角色没有 GuitarBake 片段。',
    # ui/panels.py:672
    ('GuitarRig', 'Bake keys the arms and the guitar into GuitarBake NLA strips; correct them on the GuitarRefine layer above.'): '烘焙会将手臂和吉他打帧到 GuitarBake NLA 片段中；你可以在上方的 GuitarRefine 图层上进行手动精修。',
    # ui/panels.py:687
    ('GuitarRig', "Bake to record what the solve did on each frame: the wrist corrections, each magnet's distance and weight, the neck swing."): '执行烘焙即可记录每帧的求解详情：手腕修正量、各磁铁的距离与权重以及琴颈摆动角度。',
    # core/baker.py:529
    ('GuitarRig', 'Baked frames {start}-{end} ({count} frames) in {elapsed:.1f} s ({rate:.1f} frames/s): {keyed} arm bones and the guitar.'): '已烘焙第 {start}-{end} 帧（共 {count} 帧），耗时 {elapsed:.1f} 秒（{rate:.1f} 帧/秒）：已为 {keyed} 根手臂骨骼和吉他打帧。',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Barrier Depth'): '阻挡深度',
    # ui/lists.py:19
    ('GuitarRig', 'Barrier — Left'): '阻挡面 — 左手',
    # ui/lists.py:19
    ('GuitarRig', 'Barrier — Right'): '阻挡面 — 右手',
    # props.py:GTR_Settings
    ('GuitarRig', 'Barriers Ignore Distance'): '阻挡面忽略距离',
    # presets/bass.json, props.py:GTR_Settings
    ('GuitarRig', 'Bass Guitar'): '电贝斯',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bezier'): '贝塞尔',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bias'): '偏置',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Body'): '躯干',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Body end of the strum line the picking hand is pulled to (SAO magnet 0)'): '牵引拨弦手的扫弦线琴体端（SAO 磁铁 0）',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Bone Tail'): '骨骼末端',
    # ui/panels.py:GTR_PT_bones
    ('GuitarRig', 'Bones'): '骨骼',
    # core/guitar_frame.py:685
    ('GuitarRig', 'Both ends are about as wide ({ratio:.2f}×): check that +X points to the headstock, and use Flip X if not.'): '两端宽度相近（{ratio:.2f}×）：请检查 +X 是否指向琴头，若相反请点击“翻转 X”。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Bottom (m)'): '下端 (m)',
    # props.py:GTR_Guitar, ui/panels.py:118
    ('GuitarRig', 'Bounds'): '包围盒',
    # ops/rig.py:GTR_OT_build_rig, ui/panels.py:503
    ('GuitarRig', 'Build Rig'): '构建绑定',
    # ui/panels.py:509
    ('GuitarRig', 'Build Rig adds IK and rotation constraints to each arm. They stay off, so the mocap plays as before, until you solve a frame.'): '“构建绑定”会为双臂添加 IK 与旋转约束。求解前这些约束保持关闭，因此动捕动画仍照常播放。',
    # ops/rig.py:29
    ('GuitarRig', 'Build the rig first'): '请先构建绑定',
    # ops/rig.py:66
    ('GuitarRig', 'Built the helper rig on {name}. With its goals on the current pose, the IK reproduces the arms within {worst:.3f} mm.'): '已在 {name} 上构建辅助绑定。以当前姿态作为目标时，IK 复现双臂的最大误差在 {worst:.3f} mm 以内。',
    # ops/setup.py:GTR_OT_calibrate
    ('GuitarRig', 'Calibrate'): '校准',
    # ops/prep.py:35, ui/panels.py:260
    ('GuitarRig', 'Calibrate first'): '请先校准',
    # ops/mount.py:30, ops/rig.py:15
    ('GuitarRig', 'Calibrate the character first'): '请先校准角色',
    # core/prepjob.py:294, core/solver.py:398, ops/mount.py:23, rig/build.py:241
    ('GuitarRig', 'Calibrate the character first.'): '请先校准角色。',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Calibrated'): '已校准',
    # ops/setup.py:82
    ('GuitarRig', 'Calibrated: height {height:.2f} m; ratios arm {ratio_arm:.3f}, palm {ratio_palm:.3f}, spine {ratio_spine:.3f}'): '校准完成：身高 {height:.2f} m；比例系数：臂长 {ratio_arm:.3f}、手掌 {ratio_palm:.3f}、脊柱 {ratio_spine:.3f}',
    # ui/panels.py:GTR_PT_calibration
    ('GuitarRig', 'Calibration'): '校准',
    # core/presets.py:139
    ('GuitarRig', 'Cannot read the preset {preset!r}: {reason}.'): '无法读取预设 {preset!r}：{reason}。',
    # ops/guitar.py:466
    ('GuitarRig', 'Cannot write {path}: {reason}.'): '无法写入 {path}：{reason}。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Capture Frame'): '捕获帧',
    # ops/mount.py:GTR_OT_capture_mount
    ('GuitarRig', 'Capture Mount'): '捕获挂载',
    # ops/mount.py:GTR_OT_capture_wrist_offset
    ('GuitarRig', 'Capture Wrist Offset'): '捕获手腕偏移',
    # props.py:GTR_Settings, ui/panels.py:MOUNT_TEXT, ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'Captured'): '已捕获',
    # ui/panels.py:333, ui/panels.py:369
    ('GuitarRig', 'Captured at frame {frame}'): '已于第 {frame} 帧捕获',
    # props.py:GTR_BoneMap
    ('GuitarRig', 'Chain Count'): '骨骼链数量',
    # ui/panels.py:188
    ('GuitarRig', 'Chain count: invalid'): '骨骼链数量：无效',
    # ui/panels.py:188
    ('GuitarRig', 'Chain count: {count}'): '骨骼链数量：{count}',
    # props.py:GTR_Settings
    ('GuitarRig', 'Character'): '角色',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Character Frame'): '角色坐标系',
    # core/guitar_frame.py:698
    ('GuitarRig', 'Check that +Z points out of the strings, and use Flip Z if not.'): '请检查 +Z 是否垂直琴弦向外，若相反请点击“翻转 Z”。',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Chest (Mount)'): '胸骨（挂载）',
    # props.py:GTR_Settings
    ('GuitarRig', 'Chest Bone'): '胸骨',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Chest Collider'): '胸部碰撞体',
    # ui/overlay.py:306
    ('GuitarRig', 'Chest collider: {moved:.1f} cm'): '胸部碰撞体：{moved:.1f} cm',
    # ops/rig.py:GTR_OT_clean_rig
    ('GuitarRig', 'Clean Rig'): '清理绑定',
    # props.py:GTR_Guitar, ui/panels.py:113
    ('GuitarRig', 'Confidence'): '置信度',
    # props.py:GTR_Settings
    ('GuitarRig', 'Correction'): '修正量',
    # props.py:GTR_Settings
    ('GuitarRig', 'Correction Filter'): '修正量滤波',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Crossable'): '可穿越',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Custom'): '自定义',
    # props.py:GTR_Prep, props.py:GTR_Settings
    ('GuitarRig', 'Cutoff (Hz)'): '截止频率 (Hz)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Depth (m)'): '前移深度 (m)',
    # props.py:GTR_Settings, ui/panels.py:GTR_PT_diagnostics
    ('GuitarRig', 'Diagnostics'): '诊断',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Direction'): '方向',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Distal Bone'): '远节骨骼',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Distance (m)'): '距离 (m)',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Down'): '下移',
    # core/baker.py:128
    ('GuitarRig', 'Drivers on GTR_ROOT override its baked keys.'): 'GTR_ROOT 上的驱动器会覆盖其烘焙关键帧。',
    # core/baker.py:111
    ('GuitarRig', 'Drivers on {name} override its baked keys.'): '{name} 上的驱动器会覆盖其烘焙关键帧。',
    # ui/panels.py:534
    ('GuitarRig', 'Each range solves its frames in its mode: the neck aim and the fretboard-edge magnet switch as with the mode buttons. Lower ranges win where they overlap. The neck aim fades over {fade_frames} frames at each change.'): '每个区间会按其指定模式求解对应帧：琴颈瞄准与指板边缘磁铁的切换方式与模式按钮一致。重叠时列表中靠下的区间优先。每次切换时琴颈瞄准会在 {fade_frames} 帧内平滑过渡。',
    # props.py:GTR_Prep
    ('GuitarRig', 'Elbow Share'): '肘部占比',
    # props.py:GTR_Magnet, props.py:GTR_RangeOverride
    ('GuitarRig', 'Enabled'): '启用',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings, ui/panels.py:389
    ('GuitarRig', 'End'): '结束',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Estimated'): '估算',
    # core/prepjob.py:298
    ('GuitarRig', 'Every tool is off (Intensity 0, or each strength neutral): there is nothing to apply.'): '所有预处理工具均未开启（强度为 0，或各项参数均为中性值）：无需应用。',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Filter'): '滤波',
    # props.py:GTR_Settings
    ('GuitarRig', 'Filters'): '滤波器',
    # ui/panels.py:429
    ('GuitarRig', 'Filters are switched off (Bake > Filters).'): '滤波器已关闭（烘焙 > 滤波器）。',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Finger'): '手指',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingers'): '手指',
    # props.py:GTR_Settings
    ('GuitarRig', 'Fingertip Filter'): '指尖滤波',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingertip Offset'): '指尖偏移',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Fingertip v2'): '指尖 v2',
    # props.py:GTR_Magnet, props.py:GTR_Settings, ui/panels.py:237
    ('GuitarRig', 'Fingertips'): '指尖',
    # props.py:GTR_Guitar, ui/panels.py:116
    ('GuitarRig', 'Fit'): '适配方式',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Fit Scale'): '适配缩放',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Flip Facing'): '翻转朝向',
    # ops/guitar.py:GTR_OT_flip_frame
    ('GuitarRig', 'Flip Frame'): '翻转坐标系',
    # ops/guitar.py:GTR_OT_flip_frame, ui/panels.py:109
    ('GuitarRig', 'Flip X'): '翻转 X',
    # ops/guitar.py:GTR_OT_flip_frame, ui/panels.py:110
    ('GuitarRig', 'Flip Z'): '翻转 Z',
    # core/modes.py:21, props.py:GTR_RangeOverride, props.py:GTR_Settings
    ('GuitarRig', 'Follow'): '跟随',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Forearm'): '前臂',
    # ui/panels.py:525
    ('GuitarRig', 'Frame {frame}: {mode}'): '第 {frame} 帧：{mode}',
    # ui/panels.py:527
    ('GuitarRig', 'Frame {frame}: {mode} (range {range_number})'): '第 {frame} 帧：{mode}（区间 {range_number}）',
    # ops/bake.py:238
    ('GuitarRig', 'Frame {frame}: {name} {value}.'): '第 {frame} 帧：{name} {value}。',
    # core/solver.py:390
    ('GuitarRig', 'Frame {frame}: {summary}.'): '第 {frame} 帧：{summary}。',
    # ui/panels.py:699
    ('GuitarRig', 'Frame {frame}: {value}'): '第 {frame} 帧：{value}',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Fretboard Edge'): '指板边缘',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Fretboard Plane'): '指板平面',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Fretboard surface, normal +Z: the fretting hand snaps onto it (SAO magnet 3)'): '指板表面，法线 +Z：按弦手会吸附到该平面（SAO 磁铁 3）',
    # props.py:GTR_Prep
    ('GuitarRig', 'Fretting Fingers'): '按弦手指',
    # props.py:GTR_Settings
    ('GuitarRig', 'Fretting Wrist'): '按弦手腕',
    # ui/panels.py:585
    ('GuitarRig', 'Fretting wrist'): '按弦手腕',
    # core/mount.py:57
    ('GuitarRig', 'GTR_ROOT has a negative (mirroring) scale: use Flip X or Flip Z instead of a negative scale.'): 'GTR_ROOT 存在负（镜像）缩放：请使用“翻转 X”或“翻转 Z”，不要使用负缩放。',
    # core/baker.py:126
    ('GuitarRig', 'GTR_ROOT has constraints, which act on top of its baked keys.'): 'GTR_ROOT 带有约束，它们会叠加在烘焙关键帧之上生效。',
    # core/baker.py:122
    ('GuitarRig', 'GTR_ROOT has delta transforms: clear them (Object properties > Transform > Delta Transform) before baking.'): 'GTR_ROOT 存在增量变换：请在烘焙前清除（物体属性 > 变换 > 增量变换）。',
    # ops/guitar.py:117, ops/guitar.py:527
    ('GuitarRig', 'GTR_ROOT has no meshes below it: normalise the guitar first.'): 'GTR_ROOT 下没有网格物体：请先规范化吉他坐标系。',
    # ops/mount.py:73
    ('GuitarRig', 'GTR_ROOT is animated: its animation moves it back on the next frame change.'): 'GTR_ROOT 带有动画：切帧时会将其移回原动画位置。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Gain'): '增益',
    # ops/bake.py:223
    ('GuitarRig', 'Go to worst frame #{rank} by {measure}: {description}'): '按“{measure}”跳转到第 {rank} 差帧：{description}',
    # ui/panels.py:GTR_PT_guitar
    ('GuitarRig', 'Guitar'): '吉他',
    # props.py:GTR_Settings
    ('GuitarRig', 'Guitar Cutoff (Hz)'): '吉他截止频率 (Hz)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Guitar Keys'): '吉他关键帧',
    # props.py:GTR_Guitar, props.py:GTR_Settings
    ('GuitarRig', 'Guitar Root'): '吉他根物体',
    # ops/guitar.py:243
    ('GuitarRig', 'Guitar frame found ({confidence} confidence); the guitar is {length:.2f} m long. Check the axes, then load a preset.'): '已识别吉他坐标系（置信度：{confidence}），吉他总长 {length:.2f} m。请检查坐标轴，然后加载预设。',
    # ui/panels.py:GTR_PT_main
    ('GuitarRig', 'GuitarRig'): 'GuitarRig',
    # core/bonemap.py:SLOTS, props.py:GTR_Magnet
    ('GuitarRig', 'Hand'): '手',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Hand Offset'): '手部偏移',
    # props.py:GTR_Settings
    ('GuitarRig', 'Handedness'): '惯用手',
    # props.py:GTR_Settings
    ('GuitarRig', 'Hands'): '生效手部',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Head'): '头部',
    # ui/panels.py:226
    ('GuitarRig', 'Height'): '身高',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Height (m)'): '身高 (m)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Hide Meshes While Baking'): '烘焙时隐藏网格',
    # props.py:GTR_Guitar, ui/panels.py:22
    ('GuitarRig', 'High'): '高',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Hips'): '臀部',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far a hand point was behind a barrier plane before it was clamped'): '手部参考点在被限位前深入阻挡面后方的距离',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far a solved wrist ended from its target'): '求解后的手腕最终偏离目标点的距离',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the chest collider pushed a wrist'): '胸部碰撞体将手腕推离的距离',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the fretting wrist turned away from the mocap'): '按弦手腕偏离原始动捕的转动角度',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the neck aim turned the guitar from its mount'): '琴颈瞄准使吉他偏离挂载位的摆动角度',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'How far the solve moved a wrist target from the mocap wrist'): '求解将手腕目标从动捕手腕移动的距离',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Hysteresis'): '滞回',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'IK Miss'): 'IK 偏差',
    # ui/panels.py:234
    ('GuitarRig', 'IK chain L / R'): '左右 IK 链',
    # ui/panels.py:360
    ('GuitarRig', 'In Follow mode the neck swings toward the magenta aim point on the fretting hand; Align mode switches the aim off.'): '在跟随模式下，琴颈会朝按弦手上的品红色瞄准点摆动；对齐模式则会关闭琴颈瞄准。',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Index'): '食指',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Distal'): '食指远节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Intermediate'): '食指中节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Index Proximal'): '食指近节',
    # props.py:GTR_Prep
    ('GuitarRig', 'Intensity'): '强度',
    # props.py:GTR_Settings
    ('GuitarRig', 'Interpolation'): '插值方式',
    # props.py:GTR_Settings
    ('GuitarRig', 'Iterations'): '迭代次数',
    # props.py:GTR_Prep
    ('GuitarRig', 'Joint Margin'): '关节余量',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('GuitarRig', 'Jump to Worst Frame'): '跳转到最差帧',
    # core/baker.py:980
    ('GuitarRig', 'Kept the refine actions with your keys ({names}) with a fake user.'): '已为包含你关键帧的精修动作（{names}）添加伪用户并保留。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Keys'): '关键帧',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Kind'): '类型',
    # ui/panels.py:219
    ('GuitarRig', 'L {left}, R {right}'): '左 {left}，右 {right}',
    # ui/panels.py:223
    ('GuitarRig', 'L {left}, R {right} ({estimated} estimated)'): '左 {left}，右 {right}（{estimated} 个为估算）',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Landmark A'): '标定点 A',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Landmark B'): '标定点 B',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Landmark Confidence'): '标定点置信度',
    # props.py:GTR_Guitar, ui/panels.py:138
    ('GuitarRig', 'Landmarks'): '标定点',
    # ui/panels.py:137
    ('GuitarRig', 'Landmarks ({count} missing)'): '标定点（缺少 {count} 个）',
    # props.py:GTR_Prep
    ('GuitarRig', 'Lead (frames)'): '提前量（帧）',
    # ops/setup.py:17
    ('GuitarRig', 'Leave Edit Mode first'): '请先退出编辑模式',
    # core/bonemap.py:318, props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'Left'): '左',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left Arm'): '左臂',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Left Axis Rotation'): '左手轴向旋转',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Left Chain Length (m)'): '左链长度 (m)',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left Fingers'): '左手手指',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Forearm'): '左前臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Hand'): '左手',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Left IK Chain'): '左 IK 链',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Forearm'): '左 IK 前臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Hand'): '左 IK 手',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left IK Upper Arm'): '左 IK 上臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Distal'): '左手食指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Intermediate'): '左手食指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Index Proximal'): '左手食指近节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Distal'): '左手中指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Intermediate'): '左手中指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Middle Proximal'): '左手中指近节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Distal'): '左手无名指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Intermediate'): '左手无名指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Ring Proximal'): '左手无名指近节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Upper Arm'): '左上臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Left Upper Leg'): '左大腿',
    # ui/panels.py:571
    ('GuitarRig', 'Left wrist'): '左手腕',
    # props.py:GTR_Settings
    ('GuitarRig', 'Left-Handed'): '左利手',
    # ui/panels.py:111
    ('GuitarRig', 'Length'): '长度',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Length (m)'): '长度 (m)',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Line'): '直线',
    # props.py:GTR_Settings
    ('GuitarRig', 'Linear'): '线性',
    # ops/guitar.py:GTR_OT_load_preset
    ('GuitarRig', 'Load Preset'): '加载预设',
    # ops/guitar.py:GTR_OT_load_preset_file
    ('GuitarRig', 'Load Preset File'): '加载预设文件',
    # ui/panels.py:454
    ('GuitarRig', "Load a preset for SAO's magnets, or add your own. They act in list order."): '加载预设以获取 SAO 磁铁，或手动添加自定义磁铁。磁铁按列表顺序依次生效。',
    # ui/panels.py:343
    ('GuitarRig', 'Load a preset for a first estimate, or pose the guitar on the character (move and rotate GTR_ROOT) and capture it.'): '可先加载预设作为初始估计，或直接在角色身上摆好吉他（移动和旋转 GTR_ROOT）后捕获挂载。',
    # ops/mount.py:36, ops/rig.py:35
    ('GuitarRig', 'Load a preset or capture the mount first'): '请先加载预设或捕获挂载',
    # core/solver.py:585
    ('GuitarRig', 'Load a preset or capture the mount first.'): '请先加载预设或捕获挂载。',
    # ui/panels.py:159
    ('GuitarRig', 'Load a preset to place the landmarks, or Auto-Place them on the neck and body the add-on finds, then check them on the guitar.'): '加载预设以放置标定点，或在插件检测到的琴颈与琴体上执行“自动放置”，然后对照吉他模型检查。',
    # ops/guitar.py:342
    ('GuitarRig', 'Loaded {name}: fitted to the {method} (×{length:.2f} long, ×{width:.2f} wide, ×{depth:.2f} deep). Check the landmarks.'): '已加载 {name}：按{method}适配（长 ×{length:.2f}、宽 ×{width:.2f}、厚 ×{depth:.2f}）。请检查标定点。',
    # props.py:GTR_Guitar, ui/panels.py:22
    ('GuitarRig', 'Low'): '低',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Lower fretboard edge (-Y) near the neck/body joint: start of the neck axis the aim swings (SAO reference_origin)'): '靠近琴颈/琴体连接处的指板下缘（-Y）：琴颈瞄准摆动轴线的起点（SAO reference_origin）',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Lower fretboard edge at the nut: end of the aimed neck axis (SAO reference_point)'): '上弦枕处的指板下缘：琴颈瞄准轴线的终点（SAO reference_point）',
    # presets/bone_maps.json
    ('GuitarRig', 'MMD (Japanese names)'): 'MMD（日文骨骼名）',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', "Magnet 3 uses SAO's offset_fingertip (v1), which min.js runs through the same code as v2: it is fingertip v2 without push-only."): '磁铁 3 使用 SAO 的 offset_fingertip (v1)，min.js 中它与 v2 走相同代码：即未开启“仅推离”的指尖 v2。',
    # presets/ukulele.json
    ('GuitarRig', 'Magnet 6, the nut barrier, is only in the ukulele scene: its neck is short enough for the fretting hand to slide past the nut.'): '磁铁 6（上弦枕阻挡面）仅存在于尤克里里场景：尤克里里琴颈较短，按弦手容易滑过上弦枕。',
    # core/solver.py:142
    ('GuitarRig', 'Magnet {name} is missing a landmark and was skipped.'): '磁铁 {name} 缺少标定点，已跳过。',
    # core/presets.py:325
    ('GuitarRig', 'Magnet {name}: there is no {landmark} landmark.'): '磁铁 {name}：找不到标定点 {landmark}。',
    # core/presets.py:336
    ('GuitarRig', 'Magnet {name}: unknown setting {key!r} ignored.'): '磁铁 {name}：已忽略未知设置 {key!r}。',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file, ui/panels.py:GTR_PT_magnets
    ('GuitarRig', 'Magnets'): '磁铁',
    # ops/mount.py:142
    ('GuitarRig', 'Map the fretting hand bone first'): '请先映射按弦手骨骼',
    # ops/setup.py:45
    ('GuitarRig', 'Mapped {found} of {slots_count} bones ({source}). Check the map, then calibrate.'): '已映射 {found}/{slots_count} 根骨骼（{source}）。请检查映射，然后执行校准。',
    # ui/panels.py:175
    ('GuitarRig', 'Matched: {source}'): '匹配结果：{source}',
    # props.py:GTR_Settings
    ('GuitarRig', 'Max Swing'): '最大摆角',
    # ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Measure'): '指标',
    # props.py:GTR_Guitar, ui/panels.py:22
    ('GuitarRig', 'Medium'): '中',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Metres per Unit'): '每单位米数',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Middle'): '中指',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Distal'): '中指远节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Intermediate'): '中指中节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Middle Proximal'): '中指近节',
    # presets/bone_maps.json
    ('GuitarRig', 'Mixamo'): 'Mixamo',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings, ui/panels.py:565
    ('GuitarRig', 'Mode'): '模式',
    # core/baker.py:553
    ('GuitarRig', 'Modes: {ranges} (* range override). The filters restarted at the {changes} changes, where the neck aim fades over {fade_frames} frames.'): '模式分段：{ranges}（* 表示区间覆盖）。滤波器已在 {changes} 处模式切换时重置，琴颈瞄准在每处切换用 {fade_frames} 帧平滑过渡。',
    # ops/guitar.py:GTR_OT_load_preset, ops/guitar.py:GTR_OT_load_preset_file, props.py:GTR_Settings, ui/panels.py:334
    ('GuitarRig', 'Mount'): '挂载',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Offset (m)'): '挂载偏移 (m)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Preset'): '挂载来源预设',
    # props.py:GTR_Settings
    ('GuitarRig', 'Mount Rotation'): '挂载旋转',
    # ui/panels.py:GTR_PT_mount
    ('GuitarRig', 'Mount and Wrist'): '挂载与手腕',
    # ops/mount.py:111
    ('GuitarRig', 'Mount captured at frame {mount_frame}: the guitar origin is {distance:.1f} cm from the chest bone.'): '已于第 {mount_frame} 帧捕获挂载：吉他原点距胸骨 {distance:.1f} cm。',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Move Magnet'): '移动磁铁',
    # ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'Name'): '名称',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap, props.py:GTR_Guitar, ui/panels.py:118
    ('GuitarRig', 'Neck'): '琴颈',
    # props.py:GTR_Settings, ui/panels.py:351
    ('GuitarRig', 'Neck Aim'): '琴颈瞄准',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Neck Found'): '已找到琴颈',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Neck Pivot'): '琴颈枢轴',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Neck Swing'): '琴颈摆动',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Neck end of the strum line (SAO magnet 0)'): '扫弦线的琴颈端（SAO 磁铁 0）',
    # ui/panels.py:582
    ('GuitarRig', 'Neck swing'): '琴颈摆动',
    # core/autoland.py:163
    ('GuitarRig', 'Neck {length:.0f} cm from the {start} to the nut, {width:.1f} cm wide at the nut; fretboard tilted {tilt:+.1f}°.'): '琴颈从{start}到上弦枕长 {length:.0f} cm，上弦枕处宽 {width:.1f} cm；指板倾角 {tilt:+.1f}°。',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Neck/Body Barrier'): '琴颈/琴体阻挡面',
    # props.py:GTR_Settings
    ('GuitarRig', 'Negative'): '负方向',
    # core/autoland.py:114
    ('GuitarRig', 'No body was found under the neck: the Neck/Body Barrier and the strum line are placed from where the neck narrows. Check them.'): '琴颈下方未检测到琴体：琴颈/琴体阻挡面和扫弦线将按琴颈收窄处放置。请检查确认。',
    # core/calibrate.py:261
    ('GuitarRig', 'No finger bones on the {hand_name} hand: fingertip v2 is off there and only the palm margin applies.'): '{hand_name}手没有手指骨骼：该手已关闭指尖 v2，仅应用手掌余量。',
    # ui/panels.py:696
    ('GuitarRig', 'No frame has any {measure}'): '没有任何帧存在{measure}',
    # ops/bake.py:231
    ('GuitarRig', 'No frame of the bake has a {name} above 0.'): '烘焙中没有帧的{name}大于 0。',
    # core/baker.py:946
    ('GuitarRig', 'No frame of {first}-{last} needed a re-clamp (tolerance {tolerance:.1f} mm).'): '第 {first}-{last} 帧中没有需要重新限位的帧（容差 {tolerance:.1f} mm）。',
    # core/baker.py:948
    ('GuitarRig', 'No frames to re-clamp.'): '没有可重新限位的帧。',
    # core/bonemap.py:259
    ('GuitarRig', "No humanoid chest bone found: the guitar will mount on '{bone}'. Check Chest (Mount), and capture the mount again if you change it."): '未找到人形胸骨：吉他将挂载在“{bone}”上。请检查“胸骨（挂载）”，如作修改请重新捕获挂载。',
    # core/calibrate.py:218
    ('GuitarRig', 'No left middle-finger proximal bone: the palm length is taken from the hand bone.'): '未找到左手中指近节骨骼：将使用手部骨骼长度作为手掌长度。',
    # core/calibrate.py:228
    ('GuitarRig', 'No left upper-leg bone: the spine length is measured from the hips instead.'): '未找到左大腿骨骼：将改从臀部起测量脊柱长度。',
    # core/calibrate.py:224
    ('GuitarRig', 'No neck bone: the spine length is measured up to the head instead.'): '未找到颈部骨骼：将改测至头部作为脊柱长度。',
    # core/presets.py:289
    ('GuitarRig', 'No neck found on the guitar: the landmarks are fitted to the bounding box. Check them.'): '吉他上未找到琴颈：标定点已按包围盒适配。请检查确认。',
    # core/presets.py:290
    ('GuitarRig', 'No neck found on the preset reference: the landmarks are fitted to the bounding box. Check them.'): '预设参考模型上未找到琴颈：标定点已按包围盒适配。请检查确认。',
    # core/guitar_frame.py:703
    ('GuitarRig', 'No neck found: preset landmarks are fitted to the bounding box and need checking.'): '未找到琴颈：预设标定点已按包围盒适配，需要手动检查。',
    # core/autoland.py:104
    ('GuitarRig', 'No neck was found on the guitar: place the landmarks by hand, or load the preset and check them.'): '吉他上未找到琴颈：请手动放置标定点，或加载预设后再检查。',
    # core/prepjob.py:163
    ('GuitarRig', 'No twist bone between the {side} forearm and hand: Roll is off there.'): '{side}前臂与手之间未找到扭转骨骼：该侧已关闭扭转分配。',
    # props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'None'): '无',
    # core/landmarks.py:ROLES
    ('GuitarRig', "Normal +X: holds the picking hand's position along the strings (SAO magnet 1)"): '法线 +X：控制拨弦手沿琴弦方向的位置（SAO 磁铁 1）',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Normal +X: the fretting hand stays on the headstock side of the neck/body joint (SAO magnet 4)'): '法线 +X：使按弦手保持在琴颈/琴体连接处靠琴头一侧（SAO 磁铁 4）',
    # core/landmarks.py:ROLES
    ('GuitarRig', "Normal +Z: the picking hand's fingertips stay above it (SAO magnet 2)"): '法线 +Z：使拨弦手指尖保持在该平面上方（SAO 磁铁 2）',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('GuitarRig', 'Normalise Frame'): '规范化坐标系',
    # ui/panels.py:323, ui/panels.py:498, ui/panels.py:622
    ('GuitarRig', 'Normalise the guitar and calibrate first'): '请先规范化吉他坐标系并校准角色',
    # ops/guitar.py:155, ops/mount.py:33, ops/rig.py:32
    ('GuitarRig', 'Normalise the guitar first'): '请先规范化吉他坐标系',
    # core/solver.py:583, ops/mount.py:20
    ('GuitarRig', 'Normalise the guitar first.'): '请先规范化吉他坐标系。',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Not Placed'): '未放置',
    # props.py:GTR_Settings
    ('GuitarRig', 'Not Set'): '未设置',
    # ui/panels.py:208
    ('GuitarRig', 'Not calibrated'): '未校准',
    # ui/panels.py:MOUNT_TEXT
    ('GuitarRig', 'Not set'): '未设置',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Nut'): '上弦枕',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Nut Barrier'): '上弦枕阻挡面',
    # ui/panels.py:371
    ('GuitarRig', 'Offset'): '偏移',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Offset (m)'): '偏移 (m)',
    # props.py:GTR_Magnet
    ('GuitarRig', 'One Euro'): 'One Euro',
    # props.py:GTR_Settings, ui/panels.py:641
    ('GuitarRig', 'One Euro Magnets'): 'One Euro 磁铁',
    # ui/panels.py:647
    ('GuitarRig', "One-euro filters: minimum cutoff (Hz), beta and derivative cutoff (Hz), with SAO's values by default. Lower cutoffs smooth more and lag more."): 'One Euro 滤波器：最小截止频率 (Hz)、beta 与导数截止频率 (Hz)，默认为 SAO 数值。截止频率越低越平滑，但滞后越大。',
    # ops/bake.py:232
    ('GuitarRig', 'Only {ranked_count} frames have a {name} above 0.'): '只有 {ranked_count} 帧的{name}大于 0。',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Optional, normal -X: the fretting hand stays on the body side of the nut (SAO magnet 6, ukulele)'): '可选，法线 -X：使按弦手保持在上弦枕靠琴体一侧（SAO 磁铁 6，尤克里里）',
    # ui/panels.py:540
    ('GuitarRig', 'Options'): '选项',
    # ops/prep.py:GTR_OT_toggle_prep
    ('GuitarRig', 'Original'): '原始动作',
    # ui/panels.py:244
    ('GuitarRig', "Overlay: red X (character's left), green Y (up), blue Z (forward); yellow and orange dots are fingertips, magenta is the neck-aim point."): '叠加层：红色 X（角色左侧）、绿色 Y（上方）、蓝色 Z（前方）；黄色与橙色圆点为指尖，品红色为琴颈瞄准点。',
    # ui/panels.py:228
    ('GuitarRig', 'Palm'): '手掌',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Palm Length (m)'): '手掌长度 (m)',
    # props.py:GTR_Settings
    ('GuitarRig', 'Palm Margin (m)'): '手掌余量 (m)',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Palm Ratio'): '手掌比例',
    # props.py:GTR_Settings, ui/panels.py:459
    ('GuitarRig', 'Pass-Through'): '直通',
    # ui/panels.py:458
    ('GuitarRig', 'Pass-Through ({hands})'): '直通（{hands}）',
    # ui/panels.py:591
    ('GuitarRig', 'Passes'): '迭代轮数',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Peak (m)'): '峰值 (m)',
    # ops/setup.py:14
    ('GuitarRig', 'Pick the character armature first'): '请先选择角色骨架',
    # ops/mount.py:18, rig/build.py:238
    ('GuitarRig', 'Pick the character armature first.'): '请先选择角色骨架。',
    # core/prepjob.py:292
    ('GuitarRig', 'Pick the character first.'): '请先选择角色。',
    # ui/panels.py:73
    ('GuitarRig', 'Pick the retargeted character'): '请选择已完成重定向的角色',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Fingers'): '拨弦手指',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Strength'): '拨弦手指强度',
    # props.py:GTR_Prep
    ('GuitarRig', 'Picking Wrist'): '拨弦手腕',
    # ops/mount.py:GTR_OT_place_on_mount
    ('GuitarRig', 'Place on Mount'): '放置到挂载位',
    # ui/panels.py:LANDMARK_TEXT
    ('GuitarRig', 'Placed by the preset fit'): '按预设适配放置',
    # props.py:GTR_Magnet, ui/panels.py:387
    ('GuitarRig', 'Plane'): '平面',
    # core/landmarks.py:ROLES
    ('GuitarRig', 'Plane through the lower fretboard edge, normal +Y: the fretting hand stays above it (SAO magnet 5)'): '穿过指板下缘的平面，法线 +Y：使按弦手保持在该边缘上方（SAO 磁铁 5）',
    # core/baker.py:573
    ('GuitarRig', 'Played back within {error:.2f} mm of the solve.'): '回放结果与求解偏差在 {error:.2f} mm 以内。',
    # core/baker.py:568
    ('GuitarRig', 'Played back, the bake is {error:.1f} mm from the solve at frame {error_frame}: something acts on top of the keys (constraints, drivers, other NLA tracks above the bake).'): '第 {error_frame} 帧回放结果与求解相差 {error:.1f} mm：烘焙关键帧之上叠加了其他影响（约束、驱动器或位于烘焙上方的 NLA 轨道）。',
    # presets/acoustic.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the acoustic_guitar prop; placement.scale 0.088 makes 1 unit 0.008 m."): '点位数据来自 SAO，使用 acoustic_guitar 道具的 GLB 单位；placement.scale 为 0.088，使 1 单位等于 0.008 m。',
    # presets/bass.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the bass_guitar prop; placement.scale 5.5599 makes 1 unit 0.505447 m."): '点位数据来自 SAO，使用 bass_guitar 道具的 GLB 单位；placement.scale 为 5.5599，使 1 单位等于 0.505447 m。',
    # presets/strat.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the stratocaster_guitar prop; placement.scale 8.8 makes 1 unit 0.8 m."): '点位数据来自 SAO，使用 stratocaster_guitar 道具的 GLB 单位；placement.scale 为 8.8，使 1 单位等于 0.8 m。',
    # presets/ukulele.json
    ('GuitarRig', "Positions are SAO's, in GLB units of the ukulele prop; placement.scale 2.2 makes 1 unit 0.2 m."): '点位数据来自 SAO，使用 ukulele 道具的 GLB 单位；placement.scale 为 2.2，使 1 单位等于 0.2 m。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Positive'): '正方向',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Power'): '幂次',
    # ui/panels.py:GTR_PT_prep
    ('GuitarRig', 'Prep'): '预处理',
    # props.py:GTR_Prep
    ('GuitarRig', 'Prep Report'): '预处理报告',
    # props.py:GTR_Prep
    ('GuitarRig', 'Prep Serial'): '预处理序号',
    # core/prepjob.py:57
    ('GuitarRig', 'Prep supports MMD models (MMD Tools) in this version'): '当前版本的预处理仅支持 MMD 模型（MMD Tools）',
    # core/prepjob.py:394
    ('GuitarRig', 'Prepped frames {start}-{end} ({count} frames) in {elapsed:.1f} s: {bones} bones keyed on the GuitarPrep layer.'): '已预处理第 {start}-{end} 帧（共 {count} 帧），耗时 {elapsed:.1f} 秒：已在 GuitarPrep 图层为 {bones} 根骨骼打帧。',
    # props.py:GTR_Guitar, props.py:GTR_Settings, ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'Preset'): '预设',
    # props.py:GTR_Guitar
    ('GuitarRig', 'Preset Fit'): '预设适配',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Preset ID'): '预设 ID',
    # ui/panels.py:MOUNT_TEXT
    ('GuitarRig', 'Preset estimate'): '预设估计值',
    # ui/panels.py:331
    ('GuitarRig', 'Preset estimate ({preset})'): '预设估计值（{preset}）',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Push Only'): '仅推离',
    # props.py:GTR_Settings
    ('GuitarRig', 'Radius (m)'): '半径 (m)',
    # ui/panels.py:271
    ('GuitarRig', 'Range'): '幅度',
    # ui/panels.py:515
    ('GuitarRig', 'Range Overrides'): '区间覆盖',
    # ui/panels.py:515
    ('GuitarRig', 'Range Overrides ({count})'): '区间覆盖（{count}）',
    # ops/bake.py:GTR_OT_jump_worst_frame
    ('GuitarRig', 'Rank'): '名次',
    # ops/bake.py:GTR_OT_reclamp
    ('GuitarRig', 'Re-clamp'): '重新限位',
    # props.py:GTR_Settings
    ('GuitarRig', 'Re-clamp Tolerance (m)'): '重新限位容差 (m)',
    # core/baker.py:770
    ('GuitarRig', 'Re-clamp restores the contacts that smoothing loosened.'): '执行“重新限位”可恢复被平滑松动的接触约束。',
    # core/baker.py:951
    ('GuitarRig', 'Re-clamped {frames_count} frames: the left hand on {left_count}, the right hand on {right_count}. The deepest was {depth:.1f} mm ({side} hand, frame {frame}).'): '已重新限位 {frames_count} 帧：左手 {left_count} 帧，右手 {right_count} 帧。最大深入 {depth:.1f} mm（{side}手，第 {frame} 帧）。',
    # ui/panels.py:417
    ('GuitarRig', 'Reach'): '作用距离',
    # props.py:GTR_Settings
    ('GuitarRig', 'Reach Clamp'): '伸展限制',
    # ops/guitar.py:GTR_OT_normalize_frame
    ('GuitarRig', 'Real Length (m)'): '真实长度 (m)',
    # ui/panels.py:503
    ('GuitarRig', 'Rebuild Rig'): '重建绑定',
    # props.py:GTR_Settings
    ('GuitarRig', 'Relax'): '松弛系数',
    # ops/bake.py:GTR_OT_remove_bake
    ('GuitarRig', 'Remove Bake'): '移除烘焙',
    # ops/magnets.py:GTR_OT_magnet_remove
    ('GuitarRig', 'Remove Magnet'): '移除磁铁',
    # ops/prep.py:GTR_OT_remove_prep
    ('GuitarRig', 'Remove Prep'): '移除预处理',
    # ops/rig.py:GTR_OT_range_remove
    ('GuitarRig', 'Remove Range Override'): '移除区间覆盖',
    # core/baker.py:978
    ('GuitarRig', 'Removed the bake. Actions removed: {count}.'): '已移除烘焙。共删除动作：{count}。',
    # ops/rig.py:92
    ('GuitarRig', 'Removed the helper rig.'): '已移除辅助绑定。',
    # core/prepjob.py:611
    ('GuitarRig', 'Removed the prep. Actions removed: {count}.'): '已移除预处理。共删除动作：{count}。',
    # ops/guitar.py:302
    ('GuitarRig', 'Removed the {label} landmark: the {name} preset does not use it.'): '已移除标定点“{label}”：{name} 预设不使用该标定点。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Rig Armature'): '绑定骨架',
    # props.py:GTR_Settings
    ('GuitarRig', 'Rig Collection'): '绑定集合',
    # core/bonemap.py:318, props.py:GTR_Fingertip, props.py:GTR_Magnet, props.py:GTR_Settings
    ('GuitarRig', 'Right'): '右',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right Arm'): '右臂',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Right Axis Rotation'): '右手轴向旋转',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Right Chain Length (m)'): '右链长度 (m)',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right Fingers'): '右手手指',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Forearm'): '右前臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Hand'): '右手',
    # ui/panels.py:SLOT_GROUPS
    ('GuitarRig', 'Right IK Chain'): '右 IK 链',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Forearm'): '右 IK 前臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Hand'): '右 IK 手',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right IK Upper Arm'): '右 IK 上臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Distal'): '右手食指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Intermediate'): '右手食指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Index Proximal'): '右手食指近节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Distal'): '右手中指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Intermediate'): '右手中指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Middle Proximal'): '右手中指近节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Distal'): '右手无名指远节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Intermediate'): '右手无名指中节',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Ring Proximal'): '右手无名指近节',
    # props.py:GTR_Settings
    ('GuitarRig', 'Right Root Bias'): '右臂根部偏置',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Upper Arm'): '右上臂',
    # core/bonemap.py:SLOTS, props.py:GTR_BoneMap
    ('GuitarRig', 'Right Upper Leg'): '右大腿',
    # ui/panels.py:571
    ('GuitarRig', 'Right wrist'): '右手腕',
    # props.py:GTR_Settings
    ('GuitarRig', 'Right-Handed'): '右利手',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify (deform bones)'): 'Rigify（变形骨骼）',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify (generated rig)'): 'Rigify（生成的绑定）',
    # presets/bone_maps.json
    ('GuitarRig', 'Rigify metarig names'): 'Rigify 元骨骼命名（metarig）',
    # props.py:GTR_Fingertip, props.py:GTR_Magnet
    ('GuitarRig', 'Ring'): '无名指',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Distal'): '无名指远节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Intermediate'): '无名指中节',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Ring Proximal'): '无名指近节',
    # ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Role'): '角色',
    # ui/panels.py:291
    ('GuitarRig', 'Roll and Safety'): '扭转分配与安全限位',
    # props.py:GTR_Prep
    ('GuitarRig', 'Roll to Twist Bone'): '扭转分配到扭转骨',
    # core/prepjob.py:568
    ('GuitarRig', 'Roll: the {side} twist bone turns {low:.0f}° to {high:.0f}° (1st to 99th percentile); the hand keeps its pose.'): '扭转分配：{side}扭转骨骼转动范围为 {low:.0f}° 至 {high:.0f}°（第 1 至 99 百分位）；手部姿态保持不变。',
    # props.py:GTR_Magnet, ui/panels.py:337, ui/panels.py:372
    ('GuitarRig', 'Rotation'): '旋转',
    # props.py:GTR_Settings, ui/panels.py:643
    ('GuitarRig', 'Rotation Magnets'): '旋转磁铁',
    # props.py:GTR_Settings
    ('GuitarRig', 'SAO Default'): 'SAO 默认',
    # ui/panels.py:WRIST_TEXT
    ('GuitarRig', 'SAO default'): 'SAO 默认',
    # presets/ukulele.json
    ('GuitarRig', "SAO's string plane point is the strum line's start; only its height above the fretboard matters."): 'SAO 的琴弦平面参考点取自扫弦线起点；起作用的只是它高于指板的高度。',
    # ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'Save Preset'): '保存预设',
    # ops/guitar.py:468
    ('GuitarRig', 'Saved the preset to {path}.'): '已将预设保存到 {path}。',
    # ops/bake.py:GTR_OT_show_diagnostics
    ('GuitarRig', 'Select Curves'): '选择曲线',
    # ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Select Landmark'): '选择标定点',
    # ui/panels.py:104
    ('GuitarRig', 'Select the guitar meshes (or the empty they hang from), then Normalise Frame.'): '请选中吉他网格（或其父级空物体），然后点击“规范化坐标系”。',
    # ops/guitar.py:188
    ('GuitarRig', 'Select the guitar meshes first'): '请先选中吉他网格',
    # ops/guitar.py:202
    ('GuitarRig', 'Select the guitar meshes first.'): '请先选中吉他网格。',
    # ops/bake.py:270
    ('GuitarRig', 'Selected {name}: its curves are in the Graph Editor.'): '已选中 {name}：可在曲线编辑器中查看其曲线。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Shorter Way'): '较短路径',
    # props.py:GTR_Settings
    ('GuitarRig', 'Show Magnets'): '显示磁铁',
    # ops/rig.py:GTR_OT_clear_solve
    ('GuitarRig', 'Show Mocap'): '显示动捕',
    # ops/prep.py:GTR_OT_toggle_prep, ui/panels.py:300
    ('GuitarRig', 'Show Original'): '显示原始动作',
    # props.py:GTR_Settings
    ('GuitarRig', 'Show Overlay'): '显示叠加层',
    # props.py:GTR_Settings
    ('GuitarRig', 'Showing a Solve'): '正在显示求解结果',
    # core/prepjob.py:237
    ('GuitarRig', 'Showing the original mocap: the GuitarPrep layer is muted.'): '当前显示原始动捕：GuitarPrep 图层已静音。',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Side'): '左右侧',
    # props.py:GTR_Prep
    ('GuitarRig', 'Smallest Finger Move'): '最小手指动作',
    # props.py:GTR_Prep
    ('GuitarRig', 'Smallest Stroke'): '最小拨弦幅度',
    # ops/bake.py:GTR_OT_smooth_bake, props.py:GTR_Settings
    ('GuitarRig', 'Smooth'): '平滑',
    # core/baker.py:751
    ('GuitarRig', "Smoothed the solve's correction on {smoothed} arm curves at {cutoff:g} Hz"): '已按 {cutoff:g} Hz 平滑 {smoothed} 条手臂曲线的求解修正量',
    # core/baker.py:755
    ('GuitarRig', 'Smoothed {smoothed} arm curves at {cutoff:g} Hz'): '已按 {cutoff:g} Hz 平滑 {smoothed} 条手臂曲线',
    # core/baker.py:755
    ('GuitarRig', 'Smoothed {smoothed} guitar curves at {cutoff:g} Hz'): '已按 {cutoff:g} Hz 平滑 {smoothed} 条吉他曲线',
    # core/baker.py:768
    ('GuitarRig', "Smoothing the arm keys also smooths away the prep's quick motion: use Smooth Correction to keep it."): '直接平滑手臂关键帧也会抹平预处理的快速动作：请改用“修正量”平滑模式以保留细节。',
    # ui/panels.py:276
    ('GuitarRig', 'Snap'): '锐化',
    # ui/panels.py:422, ui/panels.py:GTR_PT_solve
    ('GuitarRig', 'Solve'): '求解',
    # ops/rig.py:GTR_OT_solve_frame
    ('GuitarRig', 'Solve Frame'): '求解当前帧',
    # ui/panels.py:600
    ('GuitarRig', 'Solve Frame shows the solved arms until the frame changes.'): '“求解当前帧”会展示求解后的双臂，直到切换帧为止。',
    # props.py:GTR_Settings
    ('GuitarRig', 'Solve Serial'): '求解序号',
    # core/diagnostics.py:METRICS
    ('GuitarRig', 'Solve passes on the frames whose neck aim or wrists had not settled'): '琴颈瞄准或手腕尚未收敛帧的求解轮数',
    # props.py:GTR_Settings
    ('GuitarRig', 'Solved Frame'): '已求解帧',
    # props.py:GTR_BoneMap, props.py:GTR_Fingertip
    ('GuitarRig', 'Source'): '来源',
    # ui/panels.py:231
    ('GuitarRig', 'Spine'): '脊柱',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Spine Length (m)'): '脊柱长度 (m)',
    # props.py:GTR_Calibration
    ('GuitarRig', 'Spine Ratio'): '脊柱比例',
    # props.py:GTR_RangeOverride, props.py:GTR_Settings, ui/panels.py:387
    ('GuitarRig', 'Start'): '起始',
    # presets/strat.json, props.py:GTR_Settings
    ('GuitarRig', 'Stratocaster'): 'Stratocaster 电吉他',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'String Plane'): '琴弦平面',
    # core/guitar_frame.py:693
    ('GuitarRig', 'String face from: {cues}.'): '琴弦面判断依据：{cues}。',
    # props.py:GTR_Prep
    ('GuitarRig', 'Strokes'): '拨弦动作',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Line A'): '扫弦线 A',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Line B'): '扫弦线 B',
    # core/landmarks.py:ROLES, ops/guitar.py:GTR_OT_select_landmark
    ('GuitarRig', 'Strum Position'): '扫弦位置',
    # props.py:GTR_Prep, ui/panels.py:286
    ('GuitarRig', 'Swing'): '摆臂',
    # ops/bake.py:255, ops/guitar.py:158, ops/guitar.py:184
    ('GuitarRig', 'Switch to Object Mode first'): '请先切换到物体模式',
    # ops/mount.py:39, ops/prep.py:38, ops/rig.py:18
    ('GuitarRig', 'Switch to Object or Pose Mode first'): '请先切换到物体模式或姿态模式',
    # core/baker.py:353
    ('GuitarRig', 'The GuitarPrep layer is muted (Show Original): the bake read the mocap without the prep.'): 'GuitarPrep 图层已静音（显示原始动作）：本次烘焙读取的是未经预处理的原始动捕。',
    # core/baker.py:563
    ('GuitarRig', 'The IK missed its target on {misses_count} frames ({frames}): check the arm bones for IK locks, limits or stretch.'): '有 {misses_count} 帧的 IK 偏离目标（{frames}）：请检查手臂骨骼的 IK 锁定、限位或拉伸设置。',
    # core/baker.py:543
    ('GuitarRig', 'The Max Swing limit acted on {count} frames.'): '最大摆角限制在 {count} 帧上生效。',
    # core/baker.py:746
    ('GuitarRig', 'The arm cutoff, {cutoff:g} Hz, is above what {fps:g} frames/s can show: nothing changed'): '手臂截止频率 {cutoff:g} Hz 高于 {fps:g} 帧/秒所能表示的上限：未作修改',
    # core/calibrate.py:173
    ('GuitarRig', 'The armature object has a mirroring (negative) scale; rotations may be wrong.'): '骨架物体存在镜像（负）缩放；旋转计算可能出错。',
    # core/calibrate.py:176
    ('GuitarRig', 'The armature object has a non-uniform scale; apply it for reliable rotations.'): '骨架物体存在非均匀缩放；请先应用缩放以确保旋转可靠。',
    # rig/build.py:243
    ('GuitarRig', 'The armature uses the iTaSC IK solver: switch it to Standard (Armature properties > Inverse Kinematics).'): '该骨架正在使用 iTaSC IK 求解器：请切换为标准（Standard）求解器（骨架属性 > 反向动力学）。',
    # ui/panels.py:597
    ('GuitarRig', 'The arms show a solve whose details were lost (undo or reload): solve the frame again, or show the mocap.'): '双臂当前显示的求解详情已丢失（撤销或重新加载导致）：请重新求解当前帧，或切回显示动捕。',
    # ops/guitar.py:161, ops/guitar.py:191
    ('GuitarRig', 'The bake animates GTR_ROOT: remove the bake first'): '烘焙结果正在驱动 GTR_ROOT 动画：请先移除烘焙',
    # core/prepjob.py:401
    ('GuitarRig', 'The bake still holds the arms solved from the mocap before this prep: bake again.'): '当前烘焙仍是基于本次预处理前的动捕求解的：请重新烘焙。',
    # core/prepjob.py:240
    ('GuitarRig', 'The bake was made before this prep: bake again.'): '当前烘焙早于本次预处理生成：请重新烘焙。',
    # core/prepjob.py:241
    ('GuitarRig', 'The bake was made from a prep that has been removed: bake again.'): '当前烘焙所依赖的预处理已被移除：请重新烘焙。',
    # core/prepjob.py:614
    ('GuitarRig', 'The bake was made from a prep: bake again.'): '当前烘焙基于预处理生成：请重新烘焙。',
    # core/autoland.py:129
    ('GuitarRig', 'The body is short next to the neck: check the strum line.'): '琴体相对于琴颈偏短：请检查扫弦线位置。',
    # core/calibrate.py:238
    ('GuitarRig', "The character is {height:.2f} m tall. GuitarRig works in metres: check the object scale and the scene's unit scale."): '角色身高为 {height:.2f} m。GuitarRig 按米制工作：请检查物体缩放和场景单位缩放。',
    # core/mount.py:28, core/prepjob.py:128, core/solver.py:588
    ('GuitarRig', 'The chest bone is not mapped, or not in the armature.'): '胸骨未映射，或不在当前骨架中。',
    # core/baker.py:539
    ('GuitarRig', 'The chest collider acted on {count} frames.'): '胸部碰撞体在 {count} 帧上生效。',
    # ui/panels.py:428
    ('GuitarRig', 'The filter acts from frame to frame when baking: Solve Frame shows a frame unfiltered.'): '滤波器仅在烘焙时逐帧生效：“求解当前帧”显示的是未滤波的单帧结果。',
    # core/baker.py:342, core/prepjob.py:310
    ('GuitarRig', 'The frame range is empty.'): '帧范围为空。',
    # ui/panels.py:376
    ('GuitarRig', 'The fretting wrist turns Wrist Blend of the way from the mocap to this rotation on the guitar. To set it, pose the hand on the neck and capture it.'): '按弦手腕会按“手腕混合”的比例从原始动捕转向吉他上的该目标旋转。要设置此项，请先在琴颈上摆好手部姿势并捕获。',
    # core/baker.py:746
    ('GuitarRig', 'The guitar cutoff, {cutoff:g} Hz, is above what {fps:g} frames/s can show: nothing changed'): '吉他截止频率 {cutoff:g} Hz 高于 {fps:g} 帧/秒所能表示的上限：未作修改',
    # core/autoland.py:139
    ('GuitarRig', 'The guitar frame has low confidence: check its axes first.'): '吉他坐标系的置信度较低：请先检查坐标轴方向。',
    # ops/guitar.py:248
    ('GuitarRig', 'The guitar is {length:.2f} m long: use Real Length to scale it to real size.'): '当前吉他长度为 {length:.2f} m：请使用“真实长度”将其缩放到真实尺寸。',
    # core/presets.py:286
    ('GuitarRig', 'The guitar or the preset reference has no extent along an axis.'): '吉他或预设参考模型在某个坐标轴上的尺寸为零。',
    # core/presets.py:297
    ('GuitarRig', "The guitar's proportions differ a lot from the preset's; check the landmarks."): '吉他比例与所选预设差异较大；请检查标定点。',
    # rig/build.py:298
    ('GuitarRig', 'The helper rig could not be built.'): '无法构建辅助绑定。',
    # ui/panels.py:506
    ('GuitarRig', 'The helper rig does not match the character or its bone map: build it again.'): '辅助绑定与当前角色或其骨骼映射不匹配：请重新构建绑定。',
    # core/calibrate.py:86
    ('GuitarRig', 'The hips and head, or the two upper arms, are at the same place in rest pose.'): '静置姿态下臀部与头部重合，或两侧上臂位置重合。',
    # core/calibrate.py:202
    ('GuitarRig', 'The index fingers sit behind the ring fingers relative to the detected facing (Z): left and right may be swapped in the bone map. Check the overlay, and use Flip Facing if the frame is wrong.'): '相对于检测到的朝向 (Z)，食指位于无名指后方：骨骼映射中的左右侧可能反了。请查看叠加层，若朝向相反请勾选“翻转朝向”。',
    # core/prepjob.py:591
    ('GuitarRig', 'The joint clamp held the {side} fingers on {hit_count} frames ({frames}).'): '关节限位在 {hit_count} 帧上限制了{side}手指（{frames}）。',
    # core/baker.py:535
    ('GuitarRig', 'The largest wrist correction was {distance:.1f} cm (frame {frame}).'): '最大手腕修正距离为 {distance:.1f} cm（第 {frame} 帧）。',
    # ui/panels.py:467
    ('GuitarRig', "The magnets act on the slow part of these wrists' path, and the quick strokes ride on top, kept out of the barriers. Without it, a strum-line magnet takes back most of a stroke."): '磁铁仅作用于这些手腕路径的低速部分，快速拨弦动作叠加在上方并由阻挡面防止穿模。如果不开启直通，扫弦线磁铁会抵消大部分拨弦幅度。',
    # core/guitar_frame.py:636
    ('GuitarRig', 'The meshes are flat or a line: they do not look like a guitar.'): '所选网格呈平面或直线状：看起来不像吉他。',
    # core/guitar_frame.py:632
    ('GuitarRig', 'The meshes have no faces to measure.'): '所选网格没有可供测量的面。',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', 'The mount is only a starting guess: pose the guitar on the character and use Capture Mount.'): '预设挂载仅为初始估计：请在角色身上摆好吉他后点击“捕获挂载”。',
    # core/baker.py:558
    ('GuitarRig', 'The neck aim did not settle on {unconverged_count} frames ({frames}): raise Iterations or lower Relax.'): '琴颈瞄准在 {unconverged_count} 帧上未收敛（{frames}）：请调高迭代次数或调低松弛系数。',
    # core/solver.py:726
    ('GuitarRig', 'The neck aim had not settled after {count} iterations: raise Iterations, or lower Relax if the guitar oscillates.'): '经过 {count} 次迭代后琴颈瞄准仍未收敛：请调高迭代次数；如果吉他来回抖动，请调低松弛系数。',
    # core/solver.py:722
    ('GuitarRig', 'The neck aim was limited to {limit:.0f}° (Max Swing): the fretting hand is far from the neck.'): '琴颈瞄准已被限制在 {limit:.0f}°（最大摆角）：按弦手距离琴颈较远。',
    # core/solver.py:598
    ('GuitarRig', 'The neck is not aimed: the Neck Pivot or Nut landmark is missing.'): '未启用琴颈瞄准：缺少“琴颈枢轴”或“上弦枕”标定点。',
    # core/autoland.py:126
    ('GuitarRig', 'The neck or the body has no length along X: check the guitar frame (Flip X).'): '琴颈或琴体沿 X 轴长度为零：请检查吉他坐标系（翻转 X）。',
    # core/prepjob.py:232
    ('GuitarRig', 'The prep covers frames {first}-{last} only, and the bake range is {start}-{end}: Apply Prep again.'): '预处理仅覆盖第 {first}-{last} 帧，而烘焙范围为 {start}-{end}：请重新应用预处理。',
    # core/autoland.py:144, ops/guitar.py:126
    ('GuitarRig', 'The preset has an unknown landmark role {role!r}.'): '预设包含未知的标定点角色 {role!r}。',
    # ops/guitar.py:315
    ('GuitarRig', 'The preset has no {label} landmark: add it by hand.'): '该预设不包含“{label}”标定点：请手动添加。',
    # ui/panels.py:346
    ('GuitarRig', 'The preset mount is only an estimate: Place on Mount, adjust GTR_ROOT on the character, then Capture Mount.'): '预设挂载仅为初始估计：请点击“放置到挂载位”，在角色身上调整 GTR_ROOT 后点击“捕获挂载”。',
    # ops/guitar.py:326
    ('GuitarRig', 'The preset mount is only an estimate: pose the guitar on the character and use Capture Mount.'): '预设挂载仅为初始估计：请在角色身上摆好吉他后点击“捕获挂载”。',
    # core/presets.py:156
    ('GuitarRig', 'The preset {name} is malformed: {detail}.'): '预设 {name} 格式错误：{detail}。',
    # core/presets.py:143
    ('GuitarRig', 'The preset {name} is not valid JSON: {reason}.'): '预设 {name} 不是有效的 JSON：{reason}。',
    # core/baker.py:541
    ('GuitarRig', 'The reach clamp acted on {count} frames.'): '伸展限制在 {count} 帧上生效。',
    # ops/mount.py:109
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again, then capture the mount again.'): '自上次校准以来绑定或骨骼映射已变更：请重新校准，然后重新捕获挂载。',
    # ops/mount.py:163
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again, then capture the wrist offset again.'): '自上次校准以来绑定或骨骼映射已变更：请重新校准，然后重新捕获手腕偏移。',
    # ops/mount.py:70, ops/rig.py:63
    ('GuitarRig', 'The rig or bone map changed since calibration: calibrate again.'): '自上次校准以来绑定或骨骼映射已变更：请重新校准。',
    # ui/panels.py:215
    ('GuitarRig', 'The rig or bone map changed: calibrate again'): '绑定或骨骼映射已变更：请重新校准',
    # ops/rig.py:134
    ('GuitarRig', 'The rig shows no solve'): '当前未显示求解结果',
    # core/prepjob.py:228
    ('GuitarRig', 'The settings changed since the prep was applied: Apply Prep again.'): '自上次应用预处理以来设置已更改：请重新应用预处理。',
    # core/calibrate.py:90
    ('GuitarRig', 'The shoulder line is parallel to the hips-to-head line in rest pose.'): '静置姿态下双肩连线与臀部到头部的连线平行。',
    # core/guitar_frame.py:700
    ('GuitarRig', 'The string face could not be told from the geometry: check that +Z points out of the strings, and use Flip Z if not.'): '无法从几何体判断琴弦朝向：请检查 +Z 是否垂直琴弦向外，若相反请点击“翻转 Z”。',
    # core/solver.py:717
    ('GuitarRig', 'The {name} IK misses its target by {error:.1f} mm: check the arm bones for IK locks, limits or stretch.'): '{name}侧 IK 偏离目标 {error:.1f} mm：请检查手臂骨骼的 IK 锁定、限位或拉伸设置。',
    # core/prepjob.py:561
    ('GuitarRig', 'The {name} elbow was too straight to swing on {count} frames ({frames}): only the shoulder turned.'): '{name}肘在 {count} 帧上伸得过直而无法参与摆臂（{frames}）：仅肩部进行了转动。',
    # core/prepjob.py:586
    ('GuitarRig', 'The {name} fingers: {moves} moves snapped.'): '{name}手手指：已锐化 {moves} 次动作。',
    # core/prepjob.py:552
    ('GuitarRig', "The {name} hand's turns above {cutoff:g} Hz: {before:.1f}° → {after:.1f}° RMS, speed {speed_before:.0f} → {speed_after:.0f}°/s (95th percentile)"): '{name}手高于 {cutoff:g} Hz 的转动：{before:.1f}° → {after:.1f}° RMS，转速 {speed_before:.0f} → {speed_after:.0f}°/s（第 95 百分位）',
    # core/autoland.py:107
    ('GuitarRig', 'The {name} preset has no neck measurements to place landmarks from.'): '{name} 预设缺少可用于放置标定点的琴颈测量数据。',
    # ops/guitar.py:543
    ('GuitarRig', 'The {name} preset has no {label} landmark: add it by hand.'): '{name} 预设不包含“{label}”标定点：请手动添加。',
    # ops/guitar.py:337
    ('GuitarRig', 'The {name} preset is not verified against its source: check it.'): '{name} 预设尚未与源文件核验：请自行检查确认。',
    # core/autoland.py:118
    ('GuitarRig', "The {name} preset was saved without its guitar's heel: the Neck/Body Barrier and the strum line are placed from where the neck narrows. Check them, or save the preset again."): '{name} 预设保存时未记录吉他琴踵数据：琴颈/琴体阻挡面和扫弦线已按琴颈收窄处放置。请检查确认，或重新保存预设。',
    # core/solver.py:712
    ('GuitarRig', "The {name} wrist target was out of reach: it was kept within {reach_clamp:.1%} of the arm length, or the mocap wrist's distance if that is further."): '{name}手腕目标超出伸展范围：已限制在臂长的 {reach_clamp:.1%} 以内（若原动捕手腕更远则取动捕距离）。',
    # core/prepjob.py:534
    ('GuitarRig', "The {name} wrist's travel above {cutoff:g} Hz: {before:.1f} → {after:.1f} cm RMS (99th percentile {peak_before:.1f} → {peak_after:.1f} cm)"): '{name}手腕高于 {cutoff:g} Hz 的位移：{before:.1f} → {after:.1f} cm RMS（第 99 百分位 {peak_before:.1f} → {peak_after:.1f} cm）',
    # rig/build.py:195
    ('GuitarRig', 'The {side_name} IK chain is not mapped to existing bones: check the bone map.'): '{side_name} IK 链未映射到存在的骨骼：请检查骨骼映射。',
    # rig/build.py:199
    ('GuitarRig', 'The {side_name} IK forearm is not below the IK upper arm: check the bone map.'): '{side_name} IK 前臂不是 IK 上臂的子级：请检查骨骼映射。',
    # rig/build.py:203
    ('GuitarRig', 'The {side_name} IK hand is not below the IK forearm, so the IK would not move it: check the bone map.'): '{side_name} IK 手不是 IK 前臂的子级，IK 将无法驱动它：请检查骨骼映射。',
    # core/solver.py:789
    ('GuitarRig', 'The {side} IK does not reproduce the current pose: the elbow is {elbow:.1f} mm and the wrist {wrist:.1f} mm off. Check the arm bones for IK locks, limits or stretch.'): '{side}侧 IK 无法准确复现当前姿态：肘部偏差 {elbow:.1f} mm，手腕偏差 {wrist:.1f} mm。请检查手臂骨骼的 IK 锁定、限位或拉伸设置。',
    # rig/build.py:263
    ('GuitarRig', 'The {side} arm has its own IK ({constraints}): mute it while you solve, or the pole target is ignored.'): '{side}臂本身带有 IK 约束（{constraints}）：求解时请将其静音，否则极向目标会被忽略。',
    # core/prepjob.py:134
    ('GuitarRig', "The {side} arm's bones are not mapped as a chain: check the bone map."): '{side}臂骨骼未映射为连续父子链：请检查骨骼映射。',
    # core/prepjob.py:580
    ('GuitarRig', "The {side} fingers' presses and releases: {before:.0f} → {after:.0f} frames from 10 % to 90 % (median of {count}); {moves} moves snapped."): '{side}手手指按压与抬起：从 10% 到 90% 耗时 {before:.0f} → {after:.0f} 帧（{count} 次的中位数）；已锐化 {moves} 次动作。',
    # core/calibrate.py:248
    ('GuitarRig', 'The {side} forearm and hand start at the same place in rest pose.'): '静置姿态下{side}前臂与手的起点重合。',
    # core/prepjob.py:167
    ('GuitarRig', 'The {side} thumb or index finger is missing: Swing is off.'): '缺少{side}拇指或食指骨骼：已关闭摆臂功能。',
    # core/prepjob.py:471
    ('GuitarRig', "The {side} twist bone's fixed axis is {angle:.0f}° off the forearm: Roll turns it about the forearm."): '{side}扭转骨骼的固定轴与前臂偏离 {angle:.0f}°：扭转分配将改为绕前臂轴旋转它。',
    # ops/guitar.py:434
    ('GuitarRig', 'There are no landmarks to save.'): '没有可保存的标定点。',
    # ops/bake.py:184
    ('GuitarRig', 'There is no bake'): '当前没有烘焙结果',
    # core/baker.py:682
    ('GuitarRig', 'There is no bake to smooth.'): '没有可平滑的烘焙结果。',
    # ops/rig.py:86
    ('GuitarRig', 'There is no helper rig'): '当前没有辅助绑定',
    # props.py:GTR_Fingertip
    ('GuitarRig', 'Tip'): '指尖点',
    # ui/panels.py:268
    ('GuitarRig', 'Tools'): '工具',
    # props.py:GTR_Settings
    ('GuitarRig', 'Top (m)'): '上端 (m)',
    # presets/ukulele.json, props.py:GTR_Settings
    ('GuitarRig', 'Ukulele'): '尤克里里',
    # presets/bone_maps.json
    ('GuitarRig', 'Unreal Mannequin (UE4)'): 'Unreal Mannequin (UE4)',
    # presets/bone_maps.json
    ('GuitarRig', 'Unreal Mannequin (UE5)'): 'Unreal Mannequin (UE5)',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Unsettled'): '未收敛',
    # ops/magnets.py:GTR_OT_magnet_move
    ('GuitarRig', 'Up'): '上移',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Upper Arm'): '上臂',
    # core/bonemap.py:SLOTS
    ('GuitarRig', 'Upper Leg'): '大腿',
    # props.py:GTR_Magnet
    ('GuitarRig', 'Use Default Rotation'): '使用默认旋转',
    # props.py:GTR_Settings
    ('GuitarRig', 'Use Scene Range'): '使用场景范围',
    # core/bonemap.py:106
    ('GuitarRig', 'VRM humanoid'): 'VRM 人形骨骼',
    # presets/bone_maps.json
    ('GuitarRig', 'VRoid / VRM (J_Bip)'): 'VRoid / VRM (J_Bip)',
    # props.py:GTR_Settings
    ('GuitarRig', 'World'): '世界空间',
    # props.py:GTR_Settings, ui/panels.py:364
    ('GuitarRig', 'Wrist'): '手腕',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Blend'): '手腕混合',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Capture Frame'): '手腕捕获帧',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Wrist Correction'): '手腕修正量',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Corrections'): '手腕修正量',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Filter'): '手腕滤波',
    # props.py:GTR_Settings
    ('GuitarRig', 'Wrist Offset'): '手腕偏移',
    # core/diagnostics.py:METRICS, ops/bake.py:GTR_OT_jump_worst_frame, props.py:GTR_Settings
    ('GuitarRig', 'Wrist Turn'): '手腕转动',
    # ops/mount.py:165
    ('GuitarRig', 'Wrist offset captured at frame {wrist_frame}: the solve turns the fretting wrist {wrist_blend:.0%} of the way to this rotation on the guitar.'): '已于第 {wrist_frame} 帧捕获手腕偏移：求解时按弦手腕将向吉他上的该目标旋转混合 {wrist_blend:.0%}。',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'X (char. left)'): 'X（角色左侧）',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'X (headstock)'): 'X（琴头方向）',
    # presets/strat.json
    ('GuitarRig', "XR Animator's Stratocaster scene (guitar_collection_v9.1/scene - stratocaster guitar.json)"): 'XR Animator 的 Stratocaster 电吉他场景（guitar_collection_v9.1/scene - stratocaster guitar.json）',
    # presets/acoustic.json
    ('GuitarRig', "XR Animator's acoustic guitar scene (guitar_collection_v9.1/scene.json)"): 'XR Animator 的木吉他场景（guitar_collection_v9.1/scene.json）',
    # presets/bass.json
    ('GuitarRig', "XR Animator's bass guitar scene (guitar_collection_v9.1/scene - bass guitar.json)"): 'XR Animator 的电贝斯场景（guitar_collection_v9.1/scene - bass guitar.json）',
    # presets/ukulele.json
    ('GuitarRig', "XR Animator's ukulele scene (guitar_collection_v9.1/scene - ukulele.json)"): 'XR Animator 的尤克里里场景（guitar_collection_v9.1/scene - ukulele.json）',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'Y'): 'Y',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'Y (up)'): 'Y（上方）',
    # props.py:GTR_Settings
    ('GuitarRig', 'Yaw Direction'): '偏航方向',
    # ui/panels.py:AXIS_NAMES
    ('GuitarRig', 'Z (forward)'): 'Z（前方）',
    # ui/panels.py:GUITAR_AXIS_NAMES
    ('GuitarRig', 'Z (strings)'): 'Z（琴弦面）',
    # props.py:GTR_Settings
    ('GuitarRig', 'active_magnet_index'): '活动磁铁索引',
    # props.py:GTR_Settings
    ('GuitarRig', 'active_range_index'): '活动区间索引',
    # core/autoland.py:166
    ('GuitarRig', 'body'): '琴体',
    # props.py:GTR_Character
    ('GuitarRig', 'bone_map'): '骨骼映射',
    # ops/guitar.py:345
    ('GuitarRig', 'bounds'): '包围盒',
    # props.py:GTR_Character
    ('GuitarRig', 'calibration'): '校准',
    # core/solver.py:379
    ('GuitarRig', 'chest collider {distance:.1f} cm'): '胸部碰撞体 {distance:.1f} cm',
    # core/solver.py:375, ui/overlay.py:313, ui/panels.py:421, ui/panels.py:580
    ('GuitarRig', 'clamp'): '限位',
    # ops/guitar.py:GTR_OT_load_preset_file, ops/guitar.py:GTR_OT_save_preset
    ('GuitarRig', 'filter_glob'): '文件筛选',
    # props.py:GTR_Calibration
    ('GuitarRig', 'fingerprint'): '指纹',
    # props.py:GTR_Calibration
    ('GuitarRig', 'fingertips'): '指尖',
    # core/presets.py:182
    ('GuitarRig', 'format {format} is newer than this add-on reads ({supported})'): '预设格式版本 {format} 高于当前插件支持的版本（{supported}）',
    # core/bonemap.py:106
    ('GuitarRig', 'generic names'): '通用骨骼命名',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'headstock set-back'): '琴头后倾',
    # core/autoland.py:166
    ('GuitarRig', 'heel'): '琴踵',
    # core/guitar_frame.py:41
    ('GuitarRig', 'high'): '高',
    # props.py:GTR_Settings
    ('GuitarRig', 'index.js'): 'index.js',
    # props.py:GTR_Guitar
    ('GuitarRig', 'landmark_messages'): '标定点消息',
    # core/calibrate.py:260, core/solver.py:61, rig/build.py:32
    ('GuitarRig', 'left'): '左',
    # core/guitar_frame.py:41
    ('GuitarRig', 'low'): '低',
    # props.py:GTR_Settings
    ('GuitarRig', 'magnets'): '磁铁',
    # core/guitar_frame.py:41
    ('GuitarRig', 'medium'): '中',
    # props.py:GTR_Calibration, props.py:GTR_Guitar
    ('GuitarRig', 'messages'): '消息',
    # props.py:GTR_Settings
    ('GuitarRig', 'min.js'): 'min.js',
    # presets/acoustic.json, presets/bass.json, presets/strat.json, presets/ukulele.json
    ('GuitarRig', 'mocap_factor settings are ignored: they only matter for external VMC input.'): '已忽略 mocap_factor 设置：该参数仅对外部 VMC 输入有效。',
    # ui/panels.py:570
    ('GuitarRig', 'moved {moved:.1f} cm'): '移动了 {moved:.1f} cm',
    # ui/panels.py:569
    ('GuitarRig', 'moved {moved:.1f} cm, reach clamped'): '移动了 {moved:.1f} cm（受伸展限制）',
    # ops/guitar.py:345
    ('GuitarRig', 'neck'): '琴颈',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'neck position'): '琴颈位置',
    # core/solver.py:385
    ('GuitarRig', 'neck swung {angle:.1f}°'): '琴颈摆动 {angle:.1f}°',
    # core/bonemap.py:106
    ('GuitarRig', 'no match'): '无匹配',
    # props.py:GTR_Settings
    ('GuitarRig', 'prep'): '预处理',
    # props.py:GTR_Settings
    ('GuitarRig', 'range_overrides'): '区间覆盖',
    # core/calibrate.py:260, core/solver.py:61, rig/build.py:32
    ('GuitarRig', 'right'): '右',
    # core/guitar_frame.py:CUE_TITLES
    ('GuitarRig', 'strings'): '琴弦',
    # ui/panels.py:588
    ('GuitarRig', 'turned {angle:.1f}°'): '转动了 {angle:.1f}°',
    # ui/panels.py:585
    ('GuitarRig', 'turned {angle:.1f}°, yaw constrained'): '转动了 {angle:.1f}°（偏航受约束）',
    # ui/panels.py:421, ui/panels.py:580
    ('GuitarRig', 'weight {weight:.2f}'): '权重 {weight:.2f}',
    # ui/panels.py:582
    ('GuitarRig', '{angle:.1f}°, limited'): '{angle:.1f}°（受限）',
    # ui/panels.py:227
    ('GuitarRig', '{arm_len:.3f} m  ×{ratio_arm:.3f}'): '{arm_len:.3f} m  ×{ratio_arm:.3f}',
    # ops/guitar.py:283
    ('GuitarRig', '{axis} flipped by hand.'): '已手动翻转 {axis} 轴。',
    # core/diagnostics.py:233
    ('GuitarRig', '{count:.0f} passes'): '{count:.0f} 轮',
    # ui/panels.py:591
    ('GuitarRig', '{count}, not settled'): '{count}（未收敛）',
    # ui/panels.py:574
    ('GuitarRig', '{distance:.1f} cm'): '{distance:.1f} cm',
    # ui/panels.py:422
    ('GuitarRig', '{distance:.1f} cm away, {state}'): '相距 {distance:.1f} cm，{state}',
    # core/calibrate.py:268
    ('GuitarRig', '{estimated} fingertip(s) estimated from the finger joints because the bone tails look unreliable.'): '因骨骼末端位置不可靠，已根据手指关节估算了 {estimated} 个指尖位置。',
    # core/baker.py:548
    ('GuitarRig', '{first}-{last} {mode}'): '{first}-{last} {mode}',
    # core/baker.py:299
    ('GuitarRig', '{frames} and {count} more'): '{frames} 以及其余 {count} 帧',
    # ui/panels.py:226
    ('GuitarRig', '{height:.3f} m'): '{height:.3f} m',
    # core/autoland.py:181
    ('GuitarRig', '{label} is off the end of the guitar: check the strum line.'): '“{label}”超出了吉他末端：请检查扫弦线。',
    # ui/panels.py:155
    ('GuitarRig', '{landmark}  (missing)'): '{landmark}（缺失）',
    # ui/panels.py:156
    ('GuitarRig', '{landmark}  (optional)'): '{landmark}（可选）',
    # ui/panels.py:234
    ('GuitarRig', '{left:.3f} / {right:.3f} m'): '{left:.3f} / {right:.3f} m',
    # ui/panels.py:111
    ('GuitarRig', '{length_m:.3f} m'): '{length_m:.3f} m',
    # ui/panels.py:116
    ('GuitarRig', '{method}  ×{length:.2f} ×{width:.2f} ×{depth:.2f}'): '{method}  ×{length:.2f} ×{width:.2f} ×{depth:.2f}',
    # ui/panels.py:564
    ('GuitarRig', '{mode} (range {range_number})'): '{mode}（区间 {range_number}）',
    # core/baker.py:106
    ('GuitarRig', "{name} has constraints ({constraints}) that act on top of the baked keys: the baked arm will differ from the solve. Mute them, or bake the rig's FK controls."): '{name} 带有叠加在烘焙关键帧之上的约束（{constraints}）：烘焙后的手臂将与求解结果不同。请将其静音，或改烘焙绑定的 FK 控制器。',
    # ops/guitar.py:500
    ('GuitarRig', '{name} is hidden or in an excluded collection.'): '{name} 已隐藏或位于被排除的集合中。',
    # ops/bake.py:262
    ('GuitarRig', '{name} is hidden or in an excluded collection: unhide it to see its curves.'): '{name} 已隐藏或位于被排除的集合中：请取消隐藏以查看其曲线。',
    # core/baker.py:285
    ('GuitarRig', '{name} is in NLA tweak mode: leave it in the NLA editor first.'): '{name} 正处于 NLA 调整模式：请先在 NLA 编辑器中退出该模式。',
    # core/solver.py:373
    ('GuitarRig', '{name} {state}'): '{name} {state}',
    # ui/panels.py:706
    ('GuitarRig', "{name}'s curves hold every frame: each wrist's correction (cm) and IK miss (mm), each magnet's distance d (cm, negative behind a plane) and weight w, the neck swing and the fretting wrist's turn (°). They show the solve, before any Smooth or Re-clamp."): '{name} 的曲线记录了每一帧的求解信息：双手手腕修正量 (cm) 与 IK 偏差 (mm)、各磁铁的距离 d（cm，平面后方为负）与权重 w、琴颈摆动角度以及按弦手腕转动角度 (°)。这些数据反映的是平滑或重新限位之前的求解结果。',
    # ui/overlay.py:315
    ('GuitarRig', '{name}: {state}'): '{name}：{state}',
    # ops/bake.py:69
    ('GuitarRig', '{operation} cancelled at frame {frame}: nothing was changed.'): '{operation}已在第 {frame} 帧取消：未做任何更改。',
    # ops/bake.py:86
    ('GuitarRig', '{operation} failed at frame {frame}: {error}'): '{operation}在第 {frame} 帧失败：{error}',
    # ops/bake.py:97
    ('GuitarRig', '{operation}: frame {frame} ({progress:.0%}). Esc to cancel.'): '{operation}：第 {frame} 帧（{progress:.0%}）。按 Esc 取消。',
    # ui/panels.py:228
    ('GuitarRig', '{palm_len:.3f} m  ×{ratio_palm:.3f}'): '{palm_len:.3f} m  ×{ratio_palm:.3f}',
    # ui/panels.py:417
    ('GuitarRig', '{reach:.3f} m on this character'): '在此角色上为 {reach:.3f} m',
    # core/prepjob.py:158
    ('GuitarRig', '{requirement}: no MMD finger bones (人指１…) were found on the {side} hand.'): '{requirement}：在{side}手上未找到 MMD 手指骨骼（人指１等）。',
    # core/bonemap.py:321
    ('GuitarRig', "{side_name} IK chain: '{name}' is not below '{name2}'."): '{side_name} IK 链：“{name}”不是“{name2}”的子级。',
    # core/bonemap.py:326
    ('GuitarRig', "{side_name} IK hand '{name}' is not below the IK forearm '{name2}'."): '{side_name} IK 手“{name}”不是 IK 前臂“{name2}”的子级。',
    # core/solver.py:382
    ('GuitarRig', '{side} wrist moved {moved:.1f} cm'): '{side}手腕移动了 {moved:.1f} cm',
    # core/solver.py:387
    ('GuitarRig', '{side} wrist turned {angle:.1f}°'): '{side}手腕转动了 {angle:.1f}°',
    # ui/panels.py:231
    ('GuitarRig', '{spine_len:.3f} m  ×{ratio_spine:.3f}'): '{spine_len:.3f} m  ×{ratio_spine:.3f}',
    # ui/panels.py:530
    ('GuitarRig', '{status}, neck aim fading ({weight:.2f})'): '{status}，琴颈瞄准过渡中（{weight:.2f}）',
    # core/guitar_frame.py:549, core/guitar_frame.py:559
    ('GuitarRig', '{strings_count} long thin parts'): '{strings_count} 个细长部件',
    # core/bonemap.py:315
    ('GuitarRig', "{title} '{name}' is not a child of '{name2}'."): '{title}“{name}”不是“{name2}”的子级。',
    # core/calibrate.py:167
    ('GuitarRig', '{title} is not mapped to a bone.'): '{title}尚未映射到骨骼。',
    # core/bonemap.py:303
    ('GuitarRig', '{title} is not mapped.'): '{title}尚未映射。',
    # core/bonemap.py:305
    ('GuitarRig', "{title}: there is no bone '{name}'."): '{title}：找不到骨骼“{name}”。',
    # ui/panels.py:123, ui/panels.py:242
    ('GuitarRig', '{x:+.2f}  {y:+.2f}  {z:+.2f}'): '{x:+.2f}  {y:+.2f}  {z:+.2f}',
}
