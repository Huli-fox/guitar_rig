"""Bone map slots and the automatic bone-map guess (§3.3).

`guess` tries, in order: VRM humanoid metadata (VRM add-on properties or legacy custom properties), the
naming conventions in presets/bone_maps.json (VRoid, Mixamo, Rigify, MMD, Unreal) and generic name endings.
The result is a proposal; the user confirms it in the Bones panel.
"""

import functools
import json
import os
import re
import unicodedata
from dataclasses import dataclass, field

SIDES = ('L', 'R')
FINGERS = ('index', 'middle', 'ring')
PHALANGES = ('proximal', 'intermediate', 'distal')
BODY_KINDS = ('hips', 'chest', 'neck', 'head')
CORE_KINDS = ('hips', 'head', 'upper_arm', 'forearm', 'hand')
# A naming convention contributes only if it finds this many of the 8 core slots; a few stray hits (a
# "Spine" or "LeftHand" bone) must not override the generic matching of the rest of the rig.
MIN_CORE_MATCHES = 6
# Chain slot kind -> the measurement slot kind it defaults to. Chain bones are the ones the IK drives; they
# differ from the measurement bones on rigs such as Rigify (FK controls versus ORG bones).
CHAIN_DEFAULTS = {'chain_upper_arm': 'upper_arm', 'chain_forearm': 'forearm', 'chain_hand': 'hand'}
# SAO mounts the guitar on MMD 上半身2, which it maps to VRM "chest"; these VRM bones are the fallbacks.
VRM_CHEST_FALLBACKS = ('upperChest', 'spine')

PRESET_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presets", "bone_maps.json")


@dataclass(frozen=True)
class Slot:
    key: str        # GTR_BoneMap property name, e.g. "upper_arm_L"
    kind: str       # side-independent kind, e.g. "upper_arm"
    side: str       # 'L', 'R', or '' for body bones
    group: str      # 'BODY', 'ARM', 'FINGERS' or 'CHAIN'
    label: str
    required: bool
    vrm: str = ""   # VRM humanoid bone name (camelCase)

    @property
    def title(self):
        side = {'L': "Left ", 'R': "Right "}.get(self.side, "")
        chain = "IK " if self.group == 'CHAIN' else ""
        return f"{side}{chain}{self.label}"


def _make_slots():
    slots = [
        Slot("hips", "hips", "", 'BODY', "Hips", True, "hips"),
        Slot("chest", "chest", "", 'BODY', "Chest (Mount)", True, "chest"),
        Slot("neck", "neck", "", 'BODY', "Neck", False, "neck"),
        Slot("head", "head", "", 'BODY', "Head", True, "head"),
    ]
    for side in SIDES:
        vrm = "left" if side == 'L' else "right"
        slots += [
            Slot(f"thigh_{side}", "thigh", side, 'BODY', "Upper Leg", False, vrm + "UpperLeg"),
            Slot(f"upper_arm_{side}", "upper_arm", side, 'ARM', "Upper Arm", True, vrm + "UpperArm"),
            Slot(f"forearm_{side}", "forearm", side, 'ARM', "Forearm", True, vrm + "LowerArm"),
            Slot(f"hand_{side}", "hand", side, 'ARM', "Hand", True, vrm + "Hand"),
        ]
        slots += [
            Slot(f"{f}_{p}_{side}", f"{f}_{p}", side, 'FINGERS', f"{f.title()} {p.title()}", False,
                 vrm + f.title() + p.title())
            for f in FINGERS for p in PHALANGES
        ]
        slots += [
            Slot(f"chain_upper_arm_{side}", "chain_upper_arm", side, 'CHAIN', "Upper Arm", True),
            Slot(f"chain_forearm_{side}", "chain_forearm", side, 'CHAIN', "Forearm", True),
            Slot(f"chain_hand_{side}", "chain_hand", side, 'CHAIN', "Hand", True),
        ]
    return tuple(slots)


SLOTS = _make_slots()
SLOT_BY_KEY = {slot.key: slot for slot in SLOTS}
_VRM_NAMES = tuple(dict.fromkeys([slot.vrm for slot in SLOTS if slot.vrm] + list(VRM_CHEST_FALLBACKS)))


@dataclass
class Guess:
    mapping: dict                                   # slot key -> bone name ("" if not found)
    source: str                                     # conventions that contributed, for display
    messages: list = field(default_factory=list)    # (level, text); level is ERROR, WARNING or INFO


def mapping_from(bone_map):
    """{slot key: bone name} from a GTR_BoneMap, or any object with the slot attributes."""
    return {slot.key: getattr(bone_map, slot.key, "") for slot in SLOTS}


@functools.lru_cache(maxsize=1)
def load_presets():
    with open(PRESET_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def normalize(name):
    """Bone name as matched: NFKC (full-width digits become ASCII) and case-folded."""
    return unicodedata.normalize("NFKC", name).casefold()


_SEP = r"\s._\-:|"
_SIDE_RULES = (
    (re.compile("左"), 'L'),
    (re.compile("右"), 'R'),
    # A separate token: "J_Bip_L_Hand", "hand.L", "Bip01 L Hand", "upperarm_l", "arm_left".
    (re.compile(rf"(?<![^{_SEP}])(?:l|left)(?![^{_SEP}])", re.IGNORECASE), 'L'),
    (re.compile(rf"(?<![^{_SEP}])(?:r|right)(?![^{_SEP}])", re.IGNORECASE), 'R'),
    # camelCase: "LeftHand", "leftHand", "HandLeft".
    (re.compile(r"(?:Left|(?<![A-Za-z])left)(?=[A-Z0-9])|(?<=[a-z0-9])Left$"), 'L'),
    (re.compile(r"(?:Right|(?<![A-Za-z])right)(?=[A-Z0-9])|(?<=[a-z0-9])Right$"), 'R'),
)


def split_side(name):
    """(side, name without its side token); side is 'L', 'R' or ''."""
    for rx, side in _SIDE_RULES:
        m = rx.search(name)
        if m:
            return side, name[:m.start()] + " " + name[m.end():]
    return "", name


class _NameIndex:
    """Normalised bone names and aliases (mmd_tools Japanese names) -> bone names."""

    def __init__(self, arm_obj):
        self.aliases = {}
        for bone in arm_obj.data.bones:
            self.aliases.setdefault(normalize(bone.name), bone.name)
        for name, name_j in read_mmd_names(arm_obj).items():
            self.aliases.setdefault(normalize(name_j), name)
        self._stripped = {}

    def lookup(self, name, strip=None):
        table = self.aliases
        if strip:
            table = self._stripped.get(strip)
            if table is None:
                rx = re.compile(strip)
                table = {}
                for alias, bone in self.aliases.items():
                    table.setdefault(rx.sub("", alias, count=1), bone)
                self._stripped[strip] = table
        return table.get(normalize(name))


def _match_convention(conv, index):
    """{slot key: (bone name, candidate rank)} for one naming convention."""
    strip = conv.get("strip")
    if any(index.lookup(name, strip) is None for name in conv.get("requires", ())):
        return {}
    found = {}
    for slot in SLOTS:
        tokens = conv.get("sides", {}).get(slot.side, {}) if slot.side else {}
        for rank, template in enumerate(conv["slots"].get(slot.kind, ())):
            if bool(slot.side) != ("{" in template):
                continue
            try:
                name = template.format(**tokens)
            except (KeyError, IndexError):
                continue
            bone = index.lookup(name, strip)
            if bone is not None:
                found[slot.key] = (bone, rank)
                break
    return found


def _score(found):
    core = sum(1 for key in found if SLOT_BY_KEY[key].kind in CORE_KINDS)
    return core, len(found)


def _match_generic(bones, endings, taken):
    """{slot key: (bone name, rank)} from generic name endings, for bones not in `taken`.

    Each bone goes to the kind with the longest matching ending ("lowerarm" beats "arm"); each slot then
    takes its best bone: preferred ending first, then exact names, deform bones and shorter names.
    """
    best = {}
    for bone in bones:
        if bone.name in taken:
            continue
        side, rest = split_side(unicodedata.normalize("NFKC", bone.name))
        base = re.sub(r"[^0-9a-z]", "", rest.casefold())
        hit = None
        for kind, words in endings.items():
            for rank, word in enumerate(words):
                if base.endswith(word) and (hit is None or (len(word), -rank) > hit[0]):
                    hit = ((len(word), -rank), kind, rank, base == word)
        if hit is None:
            continue
        _, kind, rank, exact = hit
        if (kind in BODY_KINDS) == bool(side):
            continue
        order = (rank, not exact, not bone.use_deform, len(bone.name))
        current = best.get((kind, side))
        if current is None or order < current[0]:
            best[(kind, side)] = (order, bone.name, rank)
    return {slot.key: best[(slot.kind, slot.side)][1:] for slot in SLOTS if (slot.kind, slot.side) in best}


def guess(arm_obj):
    """Propose a bone map for the armature object `arm_obj`."""
    bones = arm_obj.data.bones
    mapping = {slot.key: "" for slot in SLOTS}
    rank = {}
    sources = []

    def take(found, label):
        used = False
        for key, (bone, r) in found.items():
            if not mapping[key]:
                mapping[key], rank[key] = bone, r
                used = True
        if used:
            sources.append(label)

    vrm = read_vrm_humanoid(arm_obj)
    if vrm:
        found = {slot.key: (vrm[slot.vrm], 0) for slot in SLOTS if slot.vrm and slot.vrm in vrm}
        if "chest" not in found:
            for r, name in enumerate(VRM_CHEST_FALLBACKS, 1):
                if name in vrm:
                    found["chest"] = (vrm[name], r)
                    break
        take(found, "VRM humanoid")

    presets = load_presets()
    index = _NameIndex(arm_obj)
    matches = [(conv, _match_convention(conv, index)) for conv in presets["conventions"]]
    matches.sort(key=lambda match: _score(match[1]), reverse=True)  # stable: JSON order breaks ties
    for conv, found in matches:
        if _score(found)[0] >= MIN_CORE_MATCHES:
            take(found, conv["label"])

    take(_match_generic(bones, presets["generic"], set(mapping.values())), "generic names")

    for slot in SLOTS:
        if slot.group == 'CHAIN' and not mapping[slot.key]:
            mapping[slot.key] = mapping[f"{CHAIN_DEFAULTS[slot.kind]}_{slot.side}"]

    messages = []
    if mapping["chest"] and rank.get("chest", 0) > 0:
        messages.append(('WARNING', f"No humanoid chest bone found: the guitar will mount on '{mapping['chest']}'. "
                                    "Check Chest (Mount), and capture the mount again if you change it."))
    messages += validate(bones, mapping)
    return Guess(mapping, ", ".join(sources) or "no match", messages)


def is_ancestor(ancestor, bone):
    """True if `ancestor` is a parent, grandparent, ... of `bone`."""
    parent = bone.parent
    while parent is not None:
        if parent.name == ancestor.name:
            return True
        parent = parent.parent
    return False


def chain_count(bones, upper, lower):
    """IK chain_count from bone `lower` up to and including `upper`; 0 if that is not a chain of 2+ bones."""
    bone = bones.get(lower) if lower else None
    if bone is None or not upper:
        return 0
    count = 1
    while bone is not None:
        if bone.name == upper:
            return count if count > 1 else 0
        bone = bone.parent
        count += 1
    return 0


def validate(bones, mapping):
    """Problems with a bone map, as (level, text) pairs."""
    messages = []

    def get(key):
        name = mapping.get(key, "")
        return bones.get(name) if name else None

    for slot in SLOTS:
        name = mapping.get(slot.key, "")
        if not name:
            if slot.required:
                messages.append(('ERROR', f"{slot.title} is not mapped."))
        elif bones.get(name) is None:
            messages.append(('ERROR', f"{slot.title}: there is no bone '{name}'."))

    for side in SIDES:
        pairs = [("upper_arm", "forearm"), ("forearm", "hand")]
        for f in FINGERS:
            pairs += [(f"{f}_proximal", f"{f}_intermediate"), (f"{f}_intermediate", f"{f}_distal")]
        for upper, lower in pairs:
            a, b = get(f"{upper}_{side}"), get(f"{lower}_{side}")
            if a is not None and b is not None and not is_ancestor(a, b):
                title = SLOT_BY_KEY[f"{lower}_{side}"].title
                messages.append(('WARNING', f"{title} '{b.name}' is not a child of '{a.name}'."))
        side_name = "Left" if side == 'L' else "Right"
        upper, lower = get(f"chain_upper_arm_{side}"), get(f"chain_forearm_{side}")
        if upper is not None and lower is not None and chain_count(bones, upper.name, lower.name) == 0:
            messages.append(('ERROR', f"{side_name} IK chain: '{lower.name}' is not below '{upper.name}'."))
        forearm, hand = get(f"chain_forearm_{side}"), get(f"chain_hand_{side}")
        if forearm is not None and hand is not None and not is_ancestor(forearm, hand):
            messages.append(('WARNING', f"{side_name} IK hand '{hand.name}' is not below the IK forearm "
                                        f"'{forearm.name}'."))

    flagged = set()
    for slot in SLOTS:
        if slot.side == 'L':
            name = mapping.get(slot.key, "")
            if name and name == mapping.get(slot.key[:-1] + 'R', ""):
                messages.append(('ERROR', f"'{name}' is mapped to both sides ({slot.title} and its right twin)."))
                flagged.add(name)
    used = {}
    for slot in SLOTS:
        name = mapping.get(slot.key, "")
        if not name or slot.group == 'CHAIN' or name in flagged:
            continue
        if name in used:
            messages.append(('WARNING', f"'{name}' is used for both {used[name]} and {slot.title}."))
        else:
            used[name] = slot.title
    return messages


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def read_vrm_humanoid(arm_obj):
    """{VRM human bone name: bone name} from the VRM add-on, or from legacy custom properties."""
    data = arm_obj.data
    found = {}
    ext = getattr(data, "vrm_addon_extension", None)
    if ext is not None:
        if not str(getattr(ext, "spec_version", "")).startswith("0"):
            human_bones = getattr(getattr(getattr(ext, "vrm1", None), "humanoid", None), "human_bones", None)
            for name in _VRM_NAMES:
                entry = getattr(human_bones, _snake(name), None)
                bone = getattr(getattr(entry, "node", None), "bone_name", "")
                if bone:
                    found[name] = bone
        if not found:
            human_bones = getattr(getattr(getattr(ext, "vrm0", None), "humanoid", None), "human_bones", None)
            for entry in human_bones or ():
                name = getattr(entry, "bone", "")
                bone = getattr(getattr(entry, "node", None), "bone_name", "")
                if name in _VRM_NAMES and bone:
                    found[name] = bone
    if not found and hasattr(data, "get"):
        # Older VRM importers store "hips": "J_Bip_C_Hips" and so on as custom properties.
        for name in _VRM_NAMES:
            value = data.get(name)
            if isinstance(value, str) and value:
                found[name] = value
    bones = data.bones
    return {name: bone for name, bone in found.items() if bones.get(bone) is not None}


def read_mmd_names(arm_obj):
    """{bone name: MMD Japanese name} from mmd_tools bone properties, when that add-on is enabled."""
    names = {}
    pose = getattr(arm_obj, "pose", None)
    for pbone in (pose.bones if pose is not None else ()):
        mmd = getattr(pbone, "mmd_bone", None)
        name_j = getattr(mmd, "name_j", "") if mmd is not None else ""
        if name_j and name_j != pbone.name:
            names[pbone.name] = name_j
    return names
