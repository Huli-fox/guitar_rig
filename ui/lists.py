"""UI lists: the magnets and the range overrides (§10)."""

import bpy

from ..i18n import CONTEXT, iface, mark

KIND_ICONS = {'LINE': 'IPO_LINEAR', 'PLANE': 'MESH_PLANE'}


class GTR_UL_magnets(bpy.types.UIList):
    """Magnets in the order they act: enabled toggle, name, hand, and whether a plane is a barrier."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="", text_ctxt=CONTEXT)
        row.prop(item, "name", text="", emboss=False, icon=KIND_ICONS.get(item.kind, 'NONE'), text_ctxt=CONTEXT)
        barrier = item.kind == 'PLANE' and not item.crossable
        if barrier:
            text = mark('Barrier — Left') if item.hand == 'L' else mark('Barrier — Right')
        else:
            text = "Left" if item.hand == 'L' else "Right"
        row.label(text=iface(text), translate=False)


class GTR_UL_ranges(bpy.types.UIList):
    """Frame ranges solved in another mode; lower entries win where ranges overlap."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index=0):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="", text_ctxt=CONTEXT)
        sub = row.row(align=True)
        sub.active = item.enabled
        sub.alert = item.frame_end < item.frame_start
        sub.prop(item, "frame_start", text="", text_ctxt=CONTEXT)
        sub.prop(item, "frame_end", text="", text_ctxt=CONTEXT)
        sub.prop(item, "mode", text="", text_ctxt=CONTEXT)


CLASSES = (GTR_UL_magnets, GTR_UL_ranges)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
