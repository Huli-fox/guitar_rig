"""Operators. setup: bone map and calibration; guitar: frame, presets and landmarks; mount: chest mount;
magnets: the magnet list; rig: the helper rig and Solve Frame; bake: Bake, Smooth, Re-clamp and Remove Bake."""

from . import bake, guitar, magnets, mount, rig, setup

_MODULES = (setup, guitar, mount, magnets, rig, bake)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
