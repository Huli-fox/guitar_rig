"""User interface: sidebar panels and the viewport overlay."""

from . import overlay, panels

_MODULES = (panels, overlay)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
