"""Helpers shared by the operators."""


def target_armature(context):
    """The scene's character armature, or the active object if it is an armature."""
    obj = context.scene.gtr.armature
    if obj is None:
        active = context.active_object
        if active is not None and active.type == 'ARMATURE':
            obj = active
    return obj


def report(op, messages):
    """Report (level, text) messages; errors and warnings as warnings, the rest as info."""
    for level, text in messages:
        op.report({'WARNING'} if level in {'ERROR', 'WARNING'} else {'INFO'}, text)


def tag_redraw(context):
    screen = context.screen
    for area in (screen.areas if screen is not None else ()):
        if area.type == 'VIEW_3D':
            area.tag_redraw()
