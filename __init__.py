"""GuitarRig: bake guitar-playing arm and hand motion onto a retargeted character.

A port of the XR Animator / System Animator Online (SAO) guitar constraint system: a chest-mounted
guitar aimed at the fretting hand, with wrist targets pulled onto guitar landmarks ("magnets").
"""

from . import ops, props, rig, ui

_MODULES = (props, rig, ops, ui)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
