"""Operators. setup: bone map and calibration; guitar: frame, presets and landmarks; mount: chest mount;
magnets: the magnet list; prep: the mocap prep; rig: the helper rig and Solve Frame; bake: Bake, Smooth, Re-clamp
and Remove Bake."""

from . import bake, guitar, magnets, mount, prep, rig, setup

_MODULES = (setup, guitar, mount, magnets, rig, bake, prep)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
