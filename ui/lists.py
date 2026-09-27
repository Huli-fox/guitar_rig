"""UI lists: the magnets (§10)."""

import bpy

KIND_ICONS = {'LINE': 'IPO_LINEAR', 'PLANE': 'MESH_PLANE'}


class GTR_UL_magnets(bpy.types.UIList):
    """Magnets in the order they act: enabled toggle, name, hand, and whether a plane is a barrier."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.prop(item, "name", text="", emboss=False, icon=KIND_ICONS.get(item.kind, 'NONE'))
        barrier = item.kind == 'PLANE' and not item.crossable
        row.label(text=("Barrier  " if barrier else "") + ("Left" if item.hand == 'L' else "Right"))


CLASSES = (GTR_UL_magnets,)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
