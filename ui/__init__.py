"""User interface: sidebar panels, lists and the viewport overlay."""

from . import lists, overlay, panels

_MODULES = (lists, panels, overlay)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
