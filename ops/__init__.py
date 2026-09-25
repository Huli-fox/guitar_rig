"""Operators. setup: bone map and calibration; guitar: frame, presets and landmarks; mount: chest mount."""

from . import guitar, mount, setup

_MODULES = (setup, guitar, mount)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
