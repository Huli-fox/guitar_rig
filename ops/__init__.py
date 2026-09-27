"""Operators. setup: bone map and calibration; guitar: frame, presets and landmarks; mount: chest mount;
magnets: the magnet list; rig: the helper rig and Solve Frame."""

from . import guitar, magnets, mount, rig, setup

_MODULES = (setup, guitar, mount, magnets, rig)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
