"""Operators. setup: bone map and calibration."""

from . import setup

_MODULES = (setup,)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
