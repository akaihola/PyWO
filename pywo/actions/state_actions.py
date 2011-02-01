#
# PyWO - Python Window Organizer
# Copyright 2010, Wojciech 'KosciaK' Pietrzok
#
# This file is part of PyWO.
#
# PyWO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyWO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyWO.  If not, see <http://www.gnu.org/licenses/>.
#

"""state.py - PyWO actions - changing windows state."""

import logging

from pywo.actions import register, TYPE_FILTER, TYPE_STATE_FILTER
from pywo.core import WindowManager, State, Mode


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


@register(name='iconify', filter=TYPE_FILTER, unshade=True)
def _iconify(win, mode=Mode.TOGGLE):
    """Iconify (minimize) window."""
    win.iconify(mode)


@register(name='maximize', filter=TYPE_FILTER, unshade=True)
def _maximize(win, mode=Mode.TOGGLE):
    """Maximize window."""
    state = win.state
    if mode == Mode.TOGGLE and \
       State.MAXIMIZED_HORZ in state and State.MAXIMIZED_VERT in state:
        mode = Mode.UNSET
    elif mode == Mode.TOGGLE:
        mode = Mode.SET
    if State.FULLSCREEN in state:
        win.fullscreen(win.MODE_UNSET)
    win.maximize(mode)

@register(name='maximize_vert', filter=TYPE_FILTER, unshade=True)
def _maximize_vert(win, mode=Mode.TOGGLE):
    """Maximize vertically window."""
    win.maximize(mode, horz=False)

@register(name='maximize_horz', filter=TYPE_FILTER, unshade=True)
def _maximize_horz(win, mode=Mode.TOGGLE):
    """Maximize vertically window."""
    win.maximize(mode, vert=False)


@register(name='shade', filter=TYPE_FILTER)
def _shade(win, mode=Mode.TOGGLE):
    """Shade window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(win.MODE_UNSET)
    win.shade(mode)


@register(name='fullscreen', filter=TYPE_FILTER, unshade=True)
def _fullscreen(win, mode=Mode.TOGGLE):
    """Fullscreen window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(mode)


@register(name='sticky', filter=TYPE_FILTER)
def _sticky(win, mode=Mode.TOGGLE):
    """Change sticky (stay on all desktops/viewports) property."""
    win.sticky(mode)


@register(name='above', filter=TYPE_FILTER)
def _above(win, mode=Mode.TOGGLE):
    """Always on top."""
    win.always_below(Mode.UNSET)
    win.always_above(mode)


@register(name='below', filter=TYPE_FILTER)
def _below(win, mode=Mode.TOGGLE):
    """Always on bottom."""
    win.always_above(Mode.UNSET)
    win.always_below(mode)


@register(name='activate', filter=TYPE_FILTER, unshade=True)
def _activate(win):
    """Activate window.
    
    Unshade, unminimize and switch to it's desktop/viewport.
    
    """
    WM = WindowManager()
    desktop = win.desktop
    if desktop != WM.desktop:
        WM.set_desktop(desktop)
    win.activate()


@register(name="close", filter=TYPE_FILTER)
def _close(win):
    """Close window."""
    win.close()


@register(name='blink', filter=TYPE_STATE_FILTER)
def _blink(win):
    """Blink window (show border around window)."""
    win.blink()


# TODO: new actions
#   - always on top
#   - switch desktop/viewport
#   - move window to desktop/viewport 
#     (with or without following - switching to that desktop/viewport)

