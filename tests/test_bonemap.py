import unittest
from types import SimpleNamespace

import rigs
from guitar_rig.core import bonemap

FINGER_WORDS = {"index": "Index", "middle": "Middle", "ring": "Ring"}


def vroid_vrm_names():
    """VRM humanoid name -> VRoid bone name."""
    names = {"hips": "J_Bip_C_Hips", "spine": "J_Bip_C_Spine", "chest": "J_Bip_C_Chest",
             "upperChest": "J_Bip_C_UpperChest", "neck": "J_Bip_C_Neck", "head": "J_Bip_C_Head"}
    for vrm_side, s in (("left", "L"), ("right", "R")):
        names.update({f"{vrm_side}UpperLeg": f"J_Bip_{s}_UpperLeg", f"{vrm_side}UpperArm": f"J_Bip_{s}_UpperArm",
                      f"{vrm_side}LowerArm": f"J_Bip_{s}_LowerArm", f"{vrm_side}Hand": f"J_Bip_{s}_Hand"})
        for word in FINGER_WORDS.values():
            for i, phalanx in enumerate(("Proximal", "Intermediate", "Distal"), 1):
                names[f"{vrm_side}{word}{phalanx}"] = f"J_Bip_{s}_{word}{i}"
    return names


class GuessTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()

    def check(self, obj, expected, source):
        result = bonemap.guess(obj)
        for key, name in expected.items():
            self.assertEqual(result.mapping[key], name, key)
        self.assertIn(source, result.source)
        self.assertEqual([m for m in result.messages if m[0] == 'ERROR'], [])
        return result

    def assert_complete(self, result):
        self.assertEqual([key for key, name in result.mapping.items() if not name], [])

    def test_vroid(self):
        obj = rigs.vroid()
        result = self.check(obj, {
            "hips": "J_Bip_C_Hips", "chest": "J_Bip_C_Chest", "neck": "J_Bip_C_Neck", "head": "J_Bip_C_Head",
            "thigh_L": "J_Bip_L_UpperLeg", "upper_arm_L": "J_Bip_L_UpperArm", "forearm_R": "J_Bip_R_LowerArm",
            "hand_L": "J_Bip_L_Hand", "index_proximal_L": "J_Bip_L_Index1", "middle_intermediate_R": "J_Bip_R_Middle2",
            "ring_distal_R": "J_Bip_R_Ring3", "chain_upper_arm_L": "J_Bip_L_UpperArm",
            "chain_forearm_R": "J_Bip_R_LowerArm", "chain_hand_L": "J_Bip_L_Hand",
        }, "VRoid")
        self.assert_complete(result)
        self.assertEqual(result.messages, [])

    def test_chest_fallback_warns(self):
        obj = rigs.vroid(skip=("Chest",))
        result = self.check(obj, {"chest": "J_Bip_C_UpperChest"}, "VRoid")
        self.assertTrue(any(level == 'WARNING' and "chest" in text for level, text in result.messages))

    def test_mixamo(self):
        for prefix in ("mixamorig:", "mixamorig1:", ""):
            with self.subTest(prefix=prefix):
                rigs.clear_scene()
                obj = rigs.mixamo(prefix=prefix)
                n = prefix.__add__
                result = self.check(obj, {
                    "hips": n("Hips"), "chest": n("Spine1"), "neck": n("Neck"), "head": n("Head"),
                    "thigh_R": n("RightUpLeg"), "upper_arm_L": n("LeftArm"), "forearm_L": n("LeftForeArm"),
                    "hand_R": n("RightHand"), "index_distal_L": n("LeftHandIndex3"),
                    "ring_proximal_R": n("RightHandRing1"), "chain_forearm_L": n("LeftForeArm"),
                }, "Mixamo")
                self.assert_complete(result)
                self.assertEqual(result.source, "Mixamo")

    def test_rigify(self):
        obj = rigs.rigify()
        result = self.check(obj, {
            "hips": "ORG-spine", "chest": "ORG-spine.002", "neck": "ORG-spine.004", "head": "ORG-spine.006",
            "thigh_L": "ORG-thigh.L", "upper_arm_L": "ORG-upper_arm.L", "forearm_R": "ORG-forearm.R",
            "hand_L": "ORG-hand.L", "index_proximal_L": "ORG-f_index.01.L", "ring_distal_R": "ORG-f_ring.03.R",
            "chain_upper_arm_L": "upper_arm_fk.L", "chain_forearm_L": "forearm_fk.L", "chain_hand_R": "hand_fk.R",
        }, "Rigify (generated rig)")
        self.assert_complete(result)
        self.assertEqual(bonemap.chain_count(obj.data.bones, "upper_arm_fk.L", "forearm_fk.L"), 2)

    def test_mmd(self):
        for suffix in (False, True):
            with self.subTest(suffix=suffix):
                rigs.clear_scene()
                obj = rigs.mmd(suffix=suffix)

                def n(base, side='L'):
                    return f"{base}.{side}" if suffix else {'L': "左", 'R': "右"}[side] + base
                result = self.check(obj, {
                    "hips": "下半身", "chest": "上半身2", "neck": "首", "head": "頭", "thigh_L": n("足"),
                    "upper_arm_L": n("腕"), "forearm_L": n("ひじ"), "hand_R": n("手首", 'R'),
                    "index_proximal_L": n("人指１"), "middle_distal_R": n("中指３", 'R'),
                    "ring_intermediate_L": n("薬指２"), "chain_forearm_L": n("ひじ"),
                }, "MMD")
                self.assert_complete(result)
                # The arm twist bone sits between the upper arm and the elbow.
                self.assertEqual(bonemap.chain_count(obj.data.bones, n("腕"), n("ひじ")), 3)

    def test_unreal(self):
        for ue5, chest, label in ((False, "spine_02", "UE4"), (True, "spine_04", "UE5")):
            with self.subTest(label):
                rigs.clear_scene()
                obj = rigs.unreal(ue5=ue5)
                result = self.check(obj, {
                    "hips": "pelvis", "chest": chest, "neck": "neck_01", "head": "head", "thigh_L": "thigh_l",
                    "upper_arm_L": "upperarm_l", "forearm_R": "lowerarm_r", "hand_L": "hand_l",
                    "index_proximal_L": "index_01_l", "ring_distal_R": "ring_03_r",
                }, label)
                self.assert_complete(result)
                self.assertEqual(result.messages, [])
                self.assertEqual(bonemap.chain_count(obj.data.bones, "upperarm_l", "lowerarm_l"), 2)

    def test_generic_names(self):
        obj = rigs.generic()
        result = self.check(obj, {
            "hips": "Hips", "chest": "Chest", "neck": "Neck", "head": "Head",
            "thigh_L": "LeftUpperLeg", "thigh_R": "UpperLeg_R", "upper_arm_L": "LeftUpperArm",
            "upper_arm_R": "UpperArm_R", "forearm_L": "LeftLowerArm", "forearm_R": "LowerArm_R",
            "hand_L": "LeftHand", "hand_R": "Hand_R", "index_proximal_L": "LeftIndexProximal",
            "ring_distal_R": "RingDistal_R", "chain_upper_arm_R": "UpperArm_R",
        }, "generic names")
        self.assert_complete(result)
        self.assertEqual(result.messages, [])

    def test_vrm_custom_properties(self):
        obj = rigs.vroid()
        renamed = {}
        for i, bone in enumerate(list(obj.data.bones)):
            renamed[bone.name] = bone.name = f"b{i:03d}"
        for vrm_name, bone_name in vroid_vrm_names().items():
            obj.data[vrm_name] = renamed[bone_name]
        result = self.check(obj, {
            "chest": renamed["J_Bip_C_Chest"], "index_distal_R": renamed["J_Bip_R_Index3"],
            "thigh_L": renamed["J_Bip_L_UpperLeg"], "chain_forearm_L": renamed["J_Bip_L_LowerArm"],
        }, "VRM humanoid")
        self.assert_complete(result)
        self.assertEqual(result.source, "VRM humanoid")

    def test_vrm_addon_properties(self):
        names = {"hips": "Hip", "upperChest": "Chest2", "leftUpperArm": "ArmL", "rightIndexDistal": "IdxR3"}
        bones = {name: object() for name in names.values()}

        def node(bone_name):
            return SimpleNamespace(node=SimpleNamespace(bone_name=bone_name))
        vrm1 = SimpleNamespace(**{bonemap._snake(k): node(v) for k, v in names.items()}, neck=node("Missing"))
        ext = SimpleNamespace(spec_version="1.0", vrm1=SimpleNamespace(humanoid=SimpleNamespace(human_bones=vrm1)))
        obj = SimpleNamespace(data=SimpleNamespace(bones=bones, vrm_addon_extension=ext))
        self.assertEqual(bonemap.read_vrm_humanoid(obj), names)

        vrm0 = [SimpleNamespace(bone=k, node=SimpleNamespace(bone_name=v)) for k, v in names.items()]
        ext = SimpleNamespace(spec_version="0.0", vrm0=SimpleNamespace(humanoid=SimpleNamespace(human_bones=vrm0)))
        obj = SimpleNamespace(data=SimpleNamespace(bones=bones, vrm_addon_extension=ext))
        self.assertEqual(bonemap.read_vrm_humanoid(obj), names)

    def test_mmd_tools_japanese_names(self):
        obj = rigs.mmd()
        japanese = {}
        for i, bone in enumerate(list(obj.data.bones)):
            japanese[f"bone{i}"] = bone.name
            bone.name = f"bone{i}"
        by_japanese = {v: k for k, v in japanese.items()}
        original = bonemap.read_mmd_names
        bonemap.read_mmd_names = lambda arm_obj: japanese
        try:
            self.check(obj, {"chest": by_japanese["上半身2"], "forearm_L": by_japanese["左ひじ"],
                             "index_distal_R": by_japanese["右人指３"]}, "MMD")
        finally:
            bonemap.read_mmd_names = original

    def test_split_side(self):
        cases = {
            "J_Bip_L_UpperArm": 'L', "J_Bip_R_Hand": 'R', "hand.L": 'L', "DEF-upper_arm.R.001": 'R',
            "Bip01 L UpperArm": 'L', "upperarm_l": 'L', "arm_right": 'R', "LeftHand": 'L',
            "mixamorig:RightArm": 'R', "leftHand": 'L', "HandLeft": 'L', "LowerArm_R": 'R', "左腕": 'L',
            "右ひじ": 'R', "Hips": '', "Spine1": '', "Leg": '', "spine.001": '', "Relaxed": '',
        }
        for name, side in cases.items():
            self.assertEqual(bonemap.split_side(name)[0], side, name)


class ValidateTest(unittest.TestCase):
    def setUp(self):
        rigs.clear_scene()
        self.obj = rigs.vroid()
        self.bones = self.obj.data.bones
        self.mapping = bonemap.guess(self.obj).mapping

    def validate(self, **changes):
        return bonemap.validate(self.bones, dict(self.mapping, **changes))

    def test_complete_map(self):
        self.assertEqual(self.validate(), [])

    def test_optional_bones(self):
        empty = {key: "" for key, slot in bonemap.SLOT_BY_KEY.items() if not slot.required}
        self.assertEqual(self.validate(**empty), [])

    def test_missing_and_unknown_bones(self):
        messages = self.validate(hand_L="", head="Nope")
        self.assertIn(('ERROR', "Left Hand is not mapped."), messages)
        self.assertIn(('ERROR', "Head: there is no bone 'Nope'."), messages)

    def test_hierarchy(self):
        messages = self.validate(forearm_L="J_Bip_L_Shoulder")
        self.assertIn(('WARNING', "Left Forearm 'J_Bip_L_Shoulder' is not a child of 'J_Bip_L_UpperArm'."), messages)

    def test_chain(self):
        messages = self.validate(chain_upper_arm_L="J_Bip_L_Hand")
        self.assertTrue(any(level == 'ERROR' and "Left IK chain" in text for level, text in messages))

    def test_same_bone_on_both_sides(self):
        messages = self.validate(hand_R="J_Bip_L_Hand")
        self.assertTrue(any(level == 'ERROR' and "both sides" in text for level, text in messages))

    def test_chain_count(self):
        count = bonemap.chain_count
        self.assertEqual(count(self.bones, "J_Bip_L_UpperArm", "J_Bip_L_LowerArm"), 2)
        self.assertEqual(count(self.bones, "J_Bip_L_Shoulder", "J_Bip_L_LowerArm"), 3)
        self.assertEqual(count(self.bones, "J_Bip_L_LowerArm", "J_Bip_L_LowerArm"), 0)
        self.assertEqual(count(self.bones, "J_Bip_R_UpperArm", "J_Bip_L_LowerArm"), 0)
        self.assertEqual(count(self.bones, "", "J_Bip_L_LowerArm"), 0)
