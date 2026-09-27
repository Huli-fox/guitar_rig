"""Synthetic humanoid armatures for the tests: VRoid, Mixamo, Rigify, MMD, Unreal and generic names.

Joints are given in the character frame (x: toward the character's left, y: up, z: forward) in metres, and
each rig maps them into its own armature axes and units, so all rigs have the same body in world space.
"""

import math
import zlib

import bpy
import numpy as np
from mathutils import Matrix, Vector

from guitar_rig.core import bake

BODY_JOINTS = {
    "hips": (0.0, 1.00, 0.0),
    "spine": (0.0, 1.08, 0.0),
    "chest": (0.0, 1.20, -0.01),
    "upper_chest": (0.0, 1.32, -0.01),
    "neck": (0.0, 1.45, 0.0),
    "neck_mid": (0.0, 1.50, 0.005),
    "head": (0.0, 1.55, 0.0),
    "head_top": (0.0, 1.75, 0.0),
}
# Left side; the right side mirrors x.
SIDE_JOINTS = {
    "shoulder": (0.03, 1.40, 0.0),
    "upper_arm": (0.17, 1.40, 0.0),
    "upper_arm_mid": (0.31, 1.40, 0.0),
    "forearm": (0.45, 1.40, 0.0),
    "forearm_mid": (0.575, 1.40, 0.0),
    "hand": (0.70, 1.40, 0.0),
    "hand_end": (0.78, 1.40, 0.0),
    "index_proximal": (0.79, 1.40, 0.025),
    "index_intermediate": (0.835, 1.40, 0.025),
    "index_distal": (0.86, 1.40, 0.025),
    "index_tip": (0.882, 1.40, 0.025),
    "middle_proximal": (0.795, 1.40, 0.0),
    "middle_intermediate": (0.845, 1.40, 0.0),
    "middle_distal": (0.875, 1.40, 0.0),
    "middle_tip": (0.899, 1.40, 0.0),
    "ring_proximal": (0.787, 1.40, -0.022),
    "ring_intermediate": (0.832, 1.40, -0.022),
    "ring_distal": (0.860, 1.40, -0.022),
    "ring_tip": (0.881, 1.40, -0.022),
    "thigh": (0.09, 0.95, 0.0),
    "knee": (0.09, 0.52, 0.01),
    "ankle": (0.09, 0.08, -0.02),
    "toe": (0.09, 0.0, 0.12),
}
# Joints that an A-pose turns down about the upper-arm joint.
ARM_JOINTS = frozenset(k for k in SIDE_JOINTS if k not in {"shoulder", "upper_arm", "thigh", "knee", "ankle", "toe"})
FINGERS = ("index", "middle", "ring")

# Expected measurements of this body, in metres.
ARM_LEN = 0.53          # |upper_arm - hand|
PALM_LEN = 0.095        # |hand - middle_proximal|
SPINE_LEN = 0.50        # neck height above the thigh joint
CHAIN_LEN = 0.53        # 0.28 + 0.25
HEIGHT = 1.75

# Character frame -> armature axes.
BLENDER_AXES = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))   # faces -Y, Z up
Y_UP_AXES = Matrix.Identity(3)                                                  # faces +Z, Y up (FBX)
# Armature object matrices: an FBX import (Y-up data turned upright, centimetres), and an Unreal import
# turned to face +X.
FBX_OBJECT = Matrix.Rotation(math.pi / 2.0, 4, 'X') @ Matrix.Scale(0.01, 4)
UE_OBJECT = Matrix.Rotation(math.pi / 2.0, 4, 'Z') @ Matrix.Scale(0.01, 4)


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for arm in list(bpy.data.armatures):
        bpy.data.armatures.remove(arm)
    bpy.context.scene.unit_settings.scale_length = 1.0


def pseudo_roll(name):
    """A repeatable roll angle per bone name."""
    return math.radians(zlib.crc32(name.encode("utf-8")) % 360 - 180)


class RigBuilder:
    def __init__(self, name, axes=BLENDER_AXES, unit=1.0, a_pose=0.0, rolled=False):
        self.name = name
        self.axes = axes
        self.unit = unit
        self.a_pose = a_pose
        self.rolled = rolled
        self.specs = {}

    def point(self, x, y, z):
        """Armature-space position of a character-frame point given in metres."""
        return (self.axes @ Vector((x, y, z))) * self.unit

    def joint(self, key, side=""):
        if not side:
            return self.point(*BODY_JOINTS[key])
        p = Vector(SIDE_JOINTS[key])
        if self.a_pose and key in ARM_JOINTS:
            pivot = Vector(SIDE_JOINTS["upper_arm"])
            p = pivot + Matrix.Rotation(-self.a_pose, 3, 'Z') @ (p - pivot)
        if side == 'R':
            p.x = -p.x
        return self.point(*p)

    def resolve(self, p):
        if isinstance(p, str):
            return self.joint(p)
        if isinstance(p, tuple) and len(p) == 2 and isinstance(p[0], str):
            return self.joint(*p)
        return Vector(p)

    def add(self, name, head, tail, parent=None, connect=False, roll=None, **flags):
        self.specs[name] = dict(head=head, tail=tail, parent=parent, connect=connect, roll=roll, flags=flags)

    def set_tail(self, name, tail):
        self.specs[name]["tail"] = tail

    def build(self, matrix_world=None):
        arm = bpy.data.armatures.new(self.name)
        obj = bpy.data.objects.new(self.name, arm)
        bpy.context.scene.collection.objects.link(obj)
        if matrix_world is not None:
            obj.matrix_world = matrix_world
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        try:
            edit_bones = arm.edit_bones
            for name, spec in self.specs.items():
                eb = edit_bones.new(name)
                eb.head = self.resolve(spec["head"])
                eb.tail = self.resolve(spec["tail"])
                if spec["roll"] is not None:
                    eb.roll = spec["roll"]
                elif self.rolled:
                    eb.roll = pseudo_roll(name)
            for name, spec in self.specs.items():
                eb = edit_bones[name]
                if spec["parent"]:
                    eb.parent = edit_bones[spec["parent"]]
                    eb.use_connect = spec["connect"]
                for key, value in spec["flags"].items():
                    setattr(eb, key, value)
        finally:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.update()
        return obj


def add_arm(b, side, parent, shoulder, upper_arm, forearm, hand, fingers):
    """Shoulder, arm and fingers; `fingers` maps a finger to its (proximal, intermediate, distal) names."""
    b.add(shoulder, ("shoulder", side), ("upper_arm", side), parent)
    b.add(upper_arm, ("upper_arm", side), ("forearm", side), shoulder, True)
    b.add(forearm, ("forearm", side), ("hand", side), upper_arm, True)
    b.add(hand, ("hand", side), ("hand_end", side), forearm, True)
    for finger, (proximal, intermediate, distal) in fingers.items():
        b.add(proximal, (f"{finger}_proximal", side), (f"{finger}_intermediate", side), hand)
        b.add(intermediate, (f"{finger}_intermediate", side), (f"{finger}_distal", side), proximal, True)
        b.add(distal, (f"{finger}_distal", side), (f"{finger}_tip", side), intermediate, True)


def add_leg(b, side, parent, thigh, shin, foot):
    b.add(thigh, ("thigh", side), ("knee", side), parent)
    b.add(shin, ("knee", side), ("ankle", side), thigh, True)
    b.add(foot, ("ankle", side), ("toe", side), shin, True)


def add_spine(b, names, parent=None, last_tail="head_top"):
    """A connected chain through [(bone name, head joint)], ending at `last_tail`."""
    for i, (name, head) in enumerate(names):
        tail = names[i + 1][1] if i + 1 < len(names) else last_tail
        b.add(name, head, tail, parent, connect=parent is not None and i > 0)
        parent = name


def finger_tip_extension(b, finger, side):
    """A point beyond the fingertip, along the distal segment (for tip and end bones)."""
    tip, distal = b.joint(f"{finger}_tip", side), b.joint(f"{finger}_distal", side)
    return tip + (tip - distal) * 0.5


def vroid(name="VRoid", matrix_world=None, unit=1.0, a_pose=0.0, rolled=False, skip=()):
    """VRoid Studio export (J_Bip names), T-pose, zero roll."""
    b = RigBuilder(name, unit=unit, a_pose=a_pose, rolled=rolled)
    c = "J_Bip_C_"
    spine = [(c + bone, joint) for bone, joint in (("Hips", "hips"), ("Spine", "spine"), ("Chest", "chest"),
                                                   ("UpperChest", "upper_chest"), ("Neck", "neck"), ("Head", "head"))
             if bone not in skip]
    add_spine(b, spine)
    shoulder_parent = next(n for n, _ in reversed(spine) if n.endswith(("UpperChest", "Chest", "Spine")))
    for side in "LR":
        p = f"J_Bip_{side}_"
        fingers = {f: tuple(f"{p}{f.title()}{i}" for i in (1, 2, 3)) for f in FINGERS}
        add_arm(b, side, shoulder_parent, p + "Shoulder", p + "UpperArm", p + "LowerArm", p + "Hand", fingers)
        add_leg(b, side, c + "Hips", p + "UpperLeg", p + "LowerLeg", p + "Foot")
    return b.build(matrix_world)


def mixamo(name="Mixamo", prefix="mixamorig:"):
    """Mixamo FBX import: Y-up centimetre data under a turned, 0.01-scaled object, rolled bones, sideways
    distal tails (no automatic bone orientation) and end bones."""
    b = RigBuilder(name, axes=Y_UP_AXES, unit=100.0, rolled=True)
    n = prefix.__add__
    add_spine(b, [(n("Hips"), "hips"), (n("Spine"), "spine"), (n("Spine1"), "chest"), (n("Spine2"), "upper_chest"),
                  (n("Neck"), "neck"), (n("Head"), "head")])
    b.add(n("HeadTop_End"), "head_top", b.point(0.0, 1.75, 0.05), n("Head"), True)
    for side, word in (('L', "Left"), ('R', "Right")):
        s = n(word)
        fingers = {f: tuple(f"{s}Hand{f.title()}{i}" for i in (1, 2, 3)) for f in FINGERS}
        add_arm(b, side, n("Spine2"), s + "Shoulder", s + "Arm", s + "ForeArm", s + "Hand", fingers)
        for f in FINGERS:
            distal = fingers[f][2]
            b.set_tail(distal, b.joint(f"{f}_distal", side) + b.point(0.0, 0.02, 0.0))
            b.add(f"{s}Hand{f.title()}4", (f"{f}_tip", side), finger_tip_extension(b, f, side), distal)
        add_leg(b, side, n("Hips"), s + "UpLeg", s + "Leg", s + "Foot")
    return b.build(FBX_OBJECT)


def rigify(name="Rigify"):
    """Generated Rigify rig: ORG and DEF chains, torso controls, and an FK arm chain whose bones use Rigify-like
    inheritance options (no rotation inheritance, aligned/average/no scale, non-local location)."""
    b = RigBuilder(name, rolled=True)
    b.add("root", b.point(0.0, 0.0, 0.0), b.point(0.0, 0.0, -0.3))
    joints = ("hips", "spine", "chest", "upper_chest", "neck", "neck_mid", "head")
    add_spine(b, [("ORG-spine" + (f".{i:03d}" if i else ""), j) for i, j in enumerate(joints)], "root")
    add_spine(b, [("DEF-spine" + (f".{i:03d}" if i else ""), j) for i, j in enumerate(joints)], "root")
    b.add("torso", "hips", b.point(0.0, 1.0, -0.3), "root")
    b.add("hips", "spine", "hips", "torso")
    b.add("chest", "chest", "upper_chest", "torso")
    b.add("neck", "neck", "head", "ORG-spine.003")
    b.add("head", "head", "head_top", "neck")
    for side in "LR":
        fingers = {f: tuple(f"ORG-f_{f}.{i:02d}.{side}" for i in (1, 2, 3)) for f in FINGERS}
        add_arm(b, side, "ORG-spine.003", f"ORG-shoulder.{side}", f"ORG-upper_arm.{side}",
                f"ORG-forearm.{side}", f"ORG-hand.{side}", fingers)
        add_leg(b, side, "ORG-spine", f"ORG-thigh.{side}", f"ORG-shin.{side}", f"ORG-foot.{side}")
        b.add(f"DEF-upper_arm.{side}", ("upper_arm", side), ("upper_arm_mid", side), f"ORG-shoulder.{side}")
        b.add(f"DEF-upper_arm.{side}.001", ("upper_arm_mid", side), ("forearm", side), f"DEF-upper_arm.{side}", True)
        b.add(f"DEF-forearm.{side}", ("forearm", side), ("forearm_mid", side), f"DEF-upper_arm.{side}.001", True)
        b.add(f"DEF-forearm.{side}.001", ("forearm_mid", side), ("hand", side), f"DEF-forearm.{side}", True)
        b.add(f"DEF-hand.{side}", ("hand", side), ("hand_end", side), f"DEF-forearm.{side}.001", True)
        b.add(f"MCH-upper_arm_parent.{side}", ("upper_arm", side), ("upper_arm_mid", side), f"ORG-shoulder.{side}",
              use_inherit_rotation=False, inherit_scale='NONE')
        b.add(f"upper_arm_fk.{side}", ("upper_arm", side), ("forearm", side), f"MCH-upper_arm_parent.{side}",
              inherit_scale='ALIGNED')
        b.add(f"forearm_fk.{side}", ("forearm", side), ("hand", side), f"upper_arm_fk.{side}", True)
        b.add(f"MCH-hand_fk.{side}", ("hand", side), ("hand_end", side), f"forearm_fk.{side}", True,
              inherit_scale='AVERAGE')
        b.add(f"hand_fk.{side}", ("hand", side), ("hand_end", side), f"MCH-hand_fk.{side}",
              use_local_location=False)
    return b.build()


def mmd(name="MMD", a_pose=math.radians(35.0), suffix=False):
    """MMD model (mmd_tools import): Japanese names, A-pose, arm and wrist twist bones, fingertip bones.
    With `suffix`, names use mmd_tools' L/R renaming (腕.L instead of 左腕)."""
    b = RigBuilder(name, a_pose=a_pose)
    b.add("センター", b.point(0.0, 0.8, 0.0), b.point(0.0, 0.9, 0.0))
    b.add("下半身", "hips", b.point(0.0, 0.9, 0.0), "センター")
    b.add("上半身", "hips", "chest", "センター")
    b.add("上半身2", "chest", "neck", "上半身", True)
    b.add("首", "neck", "head", "上半身2", True)
    b.add("頭", "head", "head_top", "首", True)
    for side, jp in (('L', "左"), ('R', "右")):
        def n(base):
            return f"{base}.{side}" if suffix else jp + base
        b.add(n("肩"), ("shoulder", side), ("upper_arm", side), "上半身2")
        b.add(n("腕"), ("upper_arm", side), ("forearm", side), n("肩"), True)
        b.add(n("腕捩"), ("upper_arm_mid", side), ("forearm", side), n("腕"))
        b.add(n("ひじ"), ("forearm", side), ("hand", side), n("腕捩"), True)
        b.add(n("手捩"), ("forearm_mid", side), ("hand", side), n("ひじ"))
        b.add(n("手首"), ("hand", side), ("hand_end", side), n("手捩"), True)
        for f, jf in (("index", "人指"), ("middle", "中指"), ("ring", "薬指")):
            names = [n(jf + digit) for digit in "１２３"]
            b.add(names[0], (f"{f}_proximal", side), (f"{f}_intermediate", side), n("手首"))
            b.add(names[1], (f"{f}_intermediate", side), (f"{f}_distal", side), names[0], True)
            b.add(names[2], (f"{f}_distal", side), (f"{f}_tip", side), names[1], True)
            b.add(n(jf + "先"), (f"{f}_tip", side), finger_tip_extension(b, f, side), names[2], True)
        add_leg(b, side, "下半身", n("足"), n("ひざ"), n("足首"))
    return b.build()


def unreal(name="UE4", ue5=False, matrix_world=UE_OBJECT):
    """Unreal mannequin: centimetres, rolled bones, twist bones beside the arm chain, facing +X in world."""
    b = RigBuilder(name, unit=100.0, rolled=True)
    b.add("root", b.point(0.0, 0.0, 0.0), b.point(0.0, 0.0, 0.3))
    b.add("pelvis", "hips", "spine", "root")
    heights = (1.08, 1.14, 1.20, 1.26, 1.32) if ue5 else (1.08, 1.20, 1.32)
    parent = "pelvis"
    for i, y in enumerate(heights):
        bone = f"spine_{i + 1:02d}"
        top = heights[i + 1] if i + 1 < len(heights) else BODY_JOINTS["neck"][1]
        b.add(bone, b.point(0.0, y, 0.0), b.point(0.0, top, 0.0), parent, connect=i > 0)
        parent = bone
    b.add("neck_01", "neck", "head", parent, True)
    b.add("head", "head", "head_top", "neck_01", True)
    for side in "LR":
        s = side.lower()
        fingers = {f: tuple(f"{f}_{i:02d}_{s}" for i in (1, 2, 3)) for f in FINGERS}
        add_arm(b, side, parent, f"clavicle_{s}", f"upperarm_{s}", f"lowerarm_{s}", f"hand_{s}", fingers)
        b.add(f"upperarm_twist_01_{s}", ("upper_arm_mid", side), ("forearm", side), f"upperarm_{s}")
        b.add(f"lowerarm_twist_01_{s}", ("forearm_mid", side), ("hand", side), f"lowerarm_{s}")
        add_leg(b, side, "pelvis", f"thigh_{s}", f"calf_{s}", f"foot_{s}")
    return b.build(matrix_world)


def generic(name="Generic"):
    """Names that match no convention: Unity-style on the left (LeftUpperArm), suffixed on the right
    (UpperArm_R), with twist bones."""
    b = RigBuilder(name)
    add_spine(b, [("Hips", "hips"), ("Spine", "spine"), ("Chest", "chest"), ("UpperChest", "upper_chest"),
                  ("Neck", "neck"), ("Head", "head")])
    for side, n in (('L', "Left{}".format), ('R', "{}_R".format)):
        fingers = {f: tuple(n(f.title() + p) for p in ("Proximal", "Intermediate", "Distal")) for f in FINGERS}
        add_arm(b, side, "UpperChest", n("Shoulder"), n("UpperArm"), n("LowerArm"), n("Hand"), fingers)
        b.add(n("UpperArmTwist"), ("upper_arm_mid", side), ("forearm", side), n("UpperArm"))
        add_leg(b, side, "Hips", n("UpperLeg"), n("LowerLeg"), n("Foot"))
    return b.build()


ALL_RIGS = (vroid, mixamo, rigify, mmd, unreal, generic)
RIG_UNITS = {vroid: 1.0, mixamo: 100.0, rigify: 1.0, mmd: 1.0, unreal: 100.0, generic: 1.0}


def rotate_bone(obj, name, delta_world):
    """Pose bone `name` turned by the world rotation `delta_world` about its head; its children follow."""
    bpy.context.view_layer.update()
    pbone = obj.pose.bones[name]
    mw = obj.matrix_world
    world = mw @ pbone.matrix
    pivot = Matrix.Translation(world.translation)
    target = mw.inverted() @ pivot @ delta_world.to_matrix().to_4x4() @ pivot.inverted() @ world
    parent = pbone.parent.matrix if pbone.parent is not None else None
    basis = bake.bone_pose_to_basis(pbone.bone, target, parent)
    pbone.matrix_basis = Matrix(basis[0].tolist())
    bpy.context.view_layer.update()


def pose_arrays(obj, names=None):
    """{bone name: (1, 4, 4)} armature-space pose matrices."""
    names = names if names is not None else [pbone.name for pbone in obj.pose.bones]
    return {name: np.array(obj.pose.bones[name].matrix)[None] for name in names}


def world_head(obj, name):
    bpy.context.view_layer.update()
    return (obj.matrix_world @ obj.pose.bones[name].matrix).translation


def reach(obj, upper, forearm, hand, target, bend):
    """Pose an arm by FK so that the head of `hand` is at the world point `target` (kept within 99.9 % of the
    arm's reach), the elbow bending toward the world direction `bend`. Works through twist bones between
    `upper` and `forearm`."""
    shoulder, elbow, wrist = (world_head(obj, name) for name in (upper, forearm, hand))
    l1, l2 = (elbow - shoulder).length, (wrist - elbow).length
    direction = target - shoulder
    distance = min(direction.length, 0.999 * (l1 + l2))
    direction.normalize()
    x = (l1 * l1 - l2 * l2 + distance * distance) / (2.0 * distance)
    side = bend - direction * bend.dot(direction)
    side.normalize()
    new_elbow = shoulder + direction * x + side * math.sqrt(max(l1 * l1 - x * x, 0.0))
    rotate_bone(obj, upper, (elbow - shoulder).rotation_difference(new_elbow - shoulder))
    wrist = world_head(obj, hand)
    rotate_bone(obj, forearm, (wrist - new_elbow).rotation_difference(shoulder + direction * distance - new_elbow))
