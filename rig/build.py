"""The helper rig (§4): IK goal, pole, bend and wrist-rotation empties in a "GuitarRig" collection, a Copy Rotation
("GTR Bend") and an IK constraint on each IK forearm and a Copy Rotation constraint on each IK hand.

The constraints start at influence 0, so the character plays its own animation until a solve switches them on.
After Solve Frame they stay on to show the solved frame, and the frame-change handler switches them off again
on the next frame change. Bones between the IK upper arm and the IK forearm (twist bones such as MMD 腕捩) are
locked for IK, so the IK turns only the two bones of the bone map; `clean` restores their locks.

The bend constraint comes before the IK, so Blender applies it to the pose the IK starts from: it gives a straight
FK arm the small bend the IK needs to shorten it (ik.seed_bend), and is the identity otherwise.
"""

from dataclasses import dataclass

import bpy
from bpy.app.handlers import persistent
from mathutils import Quaternion, Vector

from ..core import bonemap, ik, keys
from ..core.bonemap import SIDES

COLLECTION_NAME = "GuitarRig"
HELPER_PROP = "gtr_helper"      # role of a helper empty
CHAIN_PROP = "gtr_chain"        # on the IK goal empties: the chain the constraints were built for
LOCK_PROP = "gtr_lock_ik"       # on locked in-between pose bones: their own IK locks
IK_NAME = "GTR IK"
BEND_NAME = "GTR Bend"
WRIST_NAME = "GTR Wrist"
CONSTRAINT_NAMES = {IK_NAME, BEND_NAME, WRIST_NAME}
IK_ITERATIONS = 500
SIDE_NAMES = {'L': "left", 'R': "right"}
HELPER_KINDS = {                # kind -> (empty display type, display size in metres, hidden)
    "IKT": ('SPHERE', 0.03, False),
    "POLE": ('CONE', 0.04, False),
    "BEND": ('PLAIN_AXES', 0.02, True),
    "WRIST_ROT": ('ARROWS', 0.06, False),
}
ROLES = tuple(f"{kind}_{side}" for kind in HELPER_KINDS for side in SIDES)


class RigError(ValueError):
    """The character is not ready for the helper rig."""


@dataclass(frozen=True)
class Chain:
    upper: str                  # IK upper arm: the root of the IK chain
    forearm: str                # IK forearm: carries the IK constraint
    hand: str                   # IK hand: carries the wrist constraint
    count: int                  # IK chain_count

    @property
    def key(self):
        return f"{self.upper}|{self.forearm}|{self.hand}|{self.count}"


def chains_from(bone_map):
    return {side: Chain(getattr(bone_map, f"chain_upper_arm_{side}"), getattr(bone_map, f"chain_forearm_{side}"),
                        getattr(bone_map, f"chain_hand_{side}"), getattr(bone_map, f"chain_count_{side}"))
            for side in SIDES}


@dataclass
class Rig:
    armature: object
    collection: object
    helpers: dict               # role -> empty
    ik: dict                    # side -> IK constraint
    bend: dict                  # side -> bend Copy Rotation constraint
    wrist: dict                 # side -> Copy Rotation constraint
    chains: dict                # side -> Chain

    def helper(self, kind, side):
        return self.helpers[f"{kind}_{side}"]

    def set_active(self, active):
        """Switch the constraints on (influence 1) or off (influence 0)."""
        value = 1.0 if active else 0.0
        for side in SIDES:
            self.ik[side].influence = value
            self.bend[side].influence = value
            self.wrist[side].influence = value


def find(settings):
    """The scene's helper rig, or None if it is missing, incomplete or built for another bone map."""
    obj, coll = settings.armature, settings.rig_collection
    if obj is None or coll is None or settings.rig_armature is not obj:
        return None
    helpers = {}
    for item in coll.objects:
        role = item.get(HELPER_PROP)
        if role in ROLES and role not in helpers:
            helpers[role] = item
    if len(helpers) != len(ROLES):
        return None
    chains = chains_from(obj.gtr_char.bone_map)
    ik_cons, bend_cons, wrist_cons = {}, {}, {}
    for side, chain in chains.items():
        forearm, hand = obj.pose.bones.get(chain.forearm), obj.pose.bones.get(chain.hand)
        if forearm is None or hand is None or helpers[f"IKT_{side}"].get(CHAIN_PROP) != chain.key:
            return None
        con = forearm.constraints.get(IK_NAME)
        if (con is None or con.type != 'IK' or con.target is not helpers[f"IKT_{side}"]
                or con.pole_target is not helpers[f"POLE_{side}"]):
            return None
        bend = forearm.constraints.get(BEND_NAME)
        if (bend is None or bend.type != 'COPY_ROTATION' or bend.target is not helpers[f"BEND_{side}"]
                or forearm.constraints.find(BEND_NAME) > forearm.constraints.find(IK_NAME)):
            return None
        wrist = hand.constraints.get(WRIST_NAME)
        if wrist is None or wrist.type != 'COPY_ROTATION' or wrist.target is not helpers[f"WRIST_ROT_{side}"]:
            return None
        ik_cons[side], bend_cons[side], wrist_cons[side] = con, bend, wrist
    return Rig(obj, coll, helpers, ik_cons, bend_cons, wrist_cons, chains)


def deactivate(settings):
    """Switch the constraints off and forget the shown solve; the bake tracks it muted play again."""
    settings.solve_active = False
    rig = find(settings)
    if rig is not None:
        rig.set_active(False)
    for obj in (settings.armature, settings.rig_armature):
        if obj is not None:
            keys.unmute_after_solve(obj)


# Building ------------------------------------------------------------------------------------------------------

def _between(obj, chain):
    """Pose bones strictly between the IK forearm and the IK upper arm."""
    bones = []
    pbone = obj.pose.bones[chain.forearm].parent
    while pbone is not None and pbone.name != chain.upper:
        bones.append(pbone)
        pbone = pbone.parent
    return bones


def _lock(pbone):
    if LOCK_PROP not in pbone:
        pbone[LOCK_PROP] = [int(pbone.lock_ik_x), int(pbone.lock_ik_y), int(pbone.lock_ik_z)]
    pbone.lock_ik_x = pbone.lock_ik_y = pbone.lock_ik_z = True


def remove_constraints(obj):
    """Remove the rig's constraints from every bone of `obj` and restore the IK locks the rig set."""
    for pbone in obj.pose.bones:
        for con in list(pbone.constraints):
            if con.name in CONSTRAINT_NAMES:
                pbone.constraints.remove(con)
        if LOCK_PROP in pbone:
            pbone.lock_ik_x, pbone.lock_ik_y, pbone.lock_ik_z = (bool(v) for v in pbone[LOCK_PROP])
            del pbone[LOCK_PROP]


def _metres_per_unit(scene):
    scale = scene.unit_settings.scale_length
    return scale if scale > 0.0 else 1.0


def _collection(scene, settings):
    coll = settings.rig_collection or bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
    settings.rig_collection = coll
    if coll not in scene.collection.children_recursive:
        scene.collection.children.link(coll)
    return coll


def _helper(coll, role, metres_per_bu):
    for item in coll.objects:
        if item.get(HELPER_PROP) == role:
            return item
    item = bpy.data.objects.new(role, None)
    item[HELPER_PROP] = role
    coll.objects.link(item)
    kind = role.rsplit("_", 1)[0]
    item.empty_display_type, size, hidden = HELPER_KINDS[kind]
    item.empty_display_size = size / metres_per_bu
    item.show_in_front = True
    item.hide_viewport = hidden
    item.rotation_mode = 'QUATERNION'
    return item


def _check_chain(obj, side, chain):
    side_name = SIDE_NAMES[side]
    bones = obj.data.bones
    for name in (chain.upper, chain.forearm, chain.hand):
        if not name or bones.get(name) is None:
            raise RigError(f"The {side_name} IK chain is not mapped to existing bones: check the bone map.")
    if chain.count < 2:
        raise RigError(f"The {side_name} IK forearm is not below the IK upper arm: check the bone map.")
    if not bonemap.is_ancestor(bones[chain.forearm], bones[chain.hand]):
        raise RigError(f"The {side_name} IK hand is not below the IK forearm, so the IK would not move it: check "
                       "the bone map.")


def _other_ik(obj, chain):
    """Names of enabled IK constraints on the chain's bones other than the rig's: they would join its IK tree,
    and Blender ignores the pole of a tree with more than one goal."""
    names = []
    pbone = obj.pose.bones[chain.hand]
    while pbone is not None:
        names += [f"{pbone.name}: {con.name}" for con in pbone.constraints
                  if con.type == 'IK' and con.name != IK_NAME and not con.mute and con.influence > 0.0]
        if pbone.name == chain.upper:
            break
        pbone = pbone.parent
    return names


def rest_pole_angle(obj, chain, char_frame):
    """The pole angle that puts the pole behind the elbow (§4): see ik.rest_pole_angle."""
    bones = obj.data.bones
    upper, forearm = bones[chain.upper], bones[chain.forearm]
    axes = upper.matrix_local.to_3x3().normalized()
    backward = char_frame @ Vector((0.0, 0.0, -1.0))
    return ik.rest_pole_angle(axes.col[0], axes.col[2], forearm.tail_local - upper.head_local, backward)


def build(context, settings):
    """Create the helper rig for the scene's character (§4), replacing an older one. Returns (Rig, messages);
    raises RigError. The constraints start switched off; solver.check_rig puts the empties on the current pose.
    """
    obj = settings.armature
    if obj is None:
        raise RigError("Pick the character armature first.")
    cal = obj.gtr_char.calibration
    if not cal.is_valid:
        raise RigError("Calibrate the character first.")
    if obj.pose.ik_solver != 'LEGACY':
        raise RigError("The armature uses the iTaSC IK solver: switch it to Standard (Armature properties > "
                       "Inverse Kinematics).")
    chains = chains_from(obj.gtr_char.bone_map)
    for side, chain in chains.items():
        _check_chain(obj, side, chain)

    for other in (settings.rig_armature, obj):
        if other is not None and other.type == 'ARMATURE':
            remove_constraints(other)
    settings.solve_active = False
    scene = context.scene
    coll = _collection(scene, settings)
    helpers = {role: _helper(coll, role, _metres_per_unit(scene)) for role in ROLES}
    char_frame = Quaternion(cal.char_frame)
    messages = []
    for side, chain in chains.items():
        for pbone in _between(obj, chain):
            _lock(pbone)
        others = _other_ik(obj, chain)
        if others:
            messages.append(('WARNING', f"The {SIDE_NAMES[side]} arm has its own IK ({', '.join(others)}): mute it "
                                        "while you solve, or the pole target is ignored."))
        helpers[f"IKT_{side}"][CHAIN_PROP] = chain.key

        forearm = obj.pose.bones[chain.forearm]
        con = forearm.constraints.new('COPY_ROTATION')
        con.name = BEND_NAME
        con.target = helpers[f"BEND_{side}"]
        con.mix_mode = 'AFTER'         # the forearm's world rotation, then the bend in its own frame
        con.target_space = con.owner_space = 'WORLD'
        con.influence = 0.0

        con = forearm.constraints.new('IK')
        con.name = IK_NAME
        con.target = helpers[f"IKT_{side}"]
        con.pole_target = helpers[f"POLE_{side}"]
        con.pole_angle = rest_pole_angle(obj, chain, char_frame)
        con.chain_count = chain.count
        con.use_tail = True
        con.use_stretch = False
        con.use_rotation = False
        con.iterations = IK_ITERATIONS
        con.influence = 0.0

        con = obj.pose.bones[chain.hand].constraints.new('COPY_ROTATION')
        con.name = WRIST_NAME
        con.target = helpers[f"WRIST_ROT_{side}"]
        con.mix_mode = 'REPLACE'
        con.target_space = con.owner_space = 'WORLD'
        con.influence = 0.0
    settings.rig_armature = obj
    rig = find(settings)
    if rig is None:
        raise RigError("The helper rig could not be built.")
    return rig, messages


def clean(settings):
    """Remove the helper rig: the constraints (restoring the IK locks), the helper empties, and the GuitarRig
    collection if nothing else is left in it."""
    for obj in (settings.rig_armature, settings.armature):
        if obj is not None and obj.type == 'ARMATURE':
            remove_constraints(obj)
            keys.unmute_after_solve(obj)
    coll = settings.rig_collection
    if coll is not None:
        for item in list(coll.objects):
            if item.get(HELPER_PROP) in ROLES:
                bpy.data.objects.remove(item)
        if not coll.objects and not coll.children:
            bpy.data.collections.remove(coll)
    settings.rig_collection = None
    settings.rig_armature = None
    settings.solve_active = False


# Frame changes -------------------------------------------------------------------------------------------------

@persistent
def _frame_change_pre(scene, depsgraph=None):
    """Switch the constraints off when the frame leaves the solved frame the rig shows."""
    settings = getattr(scene, "gtr", None)
    if settings is not None and settings.solve_active and scene.frame_current != settings.solve_frame:
        deactivate(settings)


def register():
    bpy.app.handlers.frame_change_pre.append(_frame_change_pre)


def unregister():
    if _frame_change_pre in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(_frame_change_pre)
