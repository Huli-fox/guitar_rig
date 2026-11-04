# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Huli-fox <chmy2015@163.com>
#
# GuitarRig is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# GuitarRig is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""GuitarRig: bake guitar-playing arm and hand motion onto a retargeted character.

A port of the XR Animator / System Animator Online (SAO) guitar constraint system: a chest-mounted
guitar aimed at the fretting hand, with wrist targets pulled onto guitar landmarks ("magnets").
"""

from . import i18n, ops, props, rig, ui

_MODULES = (i18n, props, rig, ops, ui)


def register():
    for module in _MODULES:
        module.register()


def unregister():
    for module in reversed(_MODULES):
        module.unregister()
