"""Magnet list operators (§10): gtr.magnet_add, gtr.magnet_remove and gtr.magnet_move."""

import bpy
from bpy.props import EnumProperty

from .common import tag_redraw


def _unique_name(items, base):
    names = {item.name for item in items}
    if base not in names:
        return base
    number = 2
    while f"{base} {number}" in names:
        number += 1
    return f"{base} {number}"


class GTR_OT_magnet_add(bpy.types.Operator):
    """Add a magnet after the active one. Magnets act in list order"""

    bl_idname = "gtr.magnet_add"
    bl_label = "Add Magnet"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        settings = context.scene.gtr
        items = settings.magnets
        item = items.add()
        item.name = _unique_name(items, "Magnet")
        index = min(settings.active_magnet_index + 1, len(items) - 1) if len(items) > 1 else 0
        items.move(len(items) - 1, index)
        settings.active_magnet_index = index
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_magnet_remove(bpy.types.Operator):
    """Remove the active magnet"""

    bl_idname = "gtr.magnet_remove"
    bl_label = "Remove Magnet"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        return 0 <= settings.active_magnet_index < len(settings.magnets)

    def execute(self, context):
        settings = context.scene.gtr
        settings.magnets.remove(settings.active_magnet_index)
        settings.active_magnet_index = max(0, min(settings.active_magnet_index, len(settings.magnets) - 1))
        tag_redraw(context)
        return {'FINISHED'}


class GTR_OT_magnet_move(bpy.types.Operator):
    """Move the active magnet up or down the list. Magnets act in list order"""

    bl_idname = "gtr.magnet_move"
    bl_label = "Move Magnet"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(name="Direction", items=(('UP', "Up", ""), ('DOWN', "Down", "")))

    @classmethod
    def poll(cls, context):
        settings = context.scene.gtr
        return 0 <= settings.active_magnet_index < len(settings.magnets)

    def execute(self, context):
        settings = context.scene.gtr
        index = settings.active_magnet_index
        target = index - 1 if self.direction == 'UP' else index + 1
        if not 0 <= target < len(settings.magnets):
            return {'CANCELLED'}
        settings.magnets.move(index, target)
        settings.active_magnet_index = target
        tag_redraw(context)
        return {'FINISHED'}


CLASSES = (GTR_OT_magnet_add, GTR_OT_magnet_remove, GTR_OT_magnet_move)
register, unregister = bpy.utils.register_classes_factory(CLASSES)
