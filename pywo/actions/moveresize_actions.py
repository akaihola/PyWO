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

"""moveresize_actions.py - PyWO actions - moving and resizing windows."""

import logging

from pywo.core import WindowManager
from pywo.actions import register, TYPE_STATE_FILTER
from pywo.actions.resizer import expand_window, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()


@register(name='expand', filter=TYPE_STATE_FILTER, unshade=True)
def _expand(win, direction, vertical_first=True):
    """Expand window in given direction."""
    geometry = expand_window(win, direction, 
                             sticky=(not direction.is_middle),
                             vertical_first=vertical_first)
    log.debug('Setting %s' % (geometry,))
    win.set_geometry(geometry, direction)


@register(name='shrink', filter=TYPE_STATE_FILTER, unshade=True)
def _shrink(win, direction, vertical_first=True):
    """Shrink window in given direction."""
    geometry = shrink_window(win, direction.invert(), 
                             vertical_first=vertical_first)
    log.debug('Setting %s' % (geometry,))
    win.set_geometry(geometry, direction)


@register(name='float', filter=TYPE_STATE_FILTER, unshade=True)
def _move(win, direction, vertical_first=True):
    """Move window in given direction."""
    border = expand_window(win, direction, 
                           sticky=(not direction.is_middle), 
                           insideout=(not direction.is_middle),
                           vertical_first=vertical_first)
    geometry = win.geometry
    geometry.width = min(border.width, geometry.width)
    geometry.height = min(border.height, geometry.height)
    x = border.x + border.width * direction.x
    y = border.y + border.height * direction.y
    geometry.set_position(x, y, direction)
    log.debug('Setting %s' % (geometry,))
    win.set_geometry(geometry)


@register(name='put', filter=TYPE_STATE_FILTER, unshade=True)
def _put(win, position, gravity=None):
    """Put window in given position (without resizing)."""
    gravity = gravity or position
    workarea = WM.workarea_geometry
    geometry = win.geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    geometry.set_position(x, y, gravity)
    log.debug('Setting %s' % (geometry,))
    win.set_geometry(geometry)


# TODO: new actions
#   - resize (with gravity?)
#   - move (relative with gravity and +/-length)?
#   - place (absolute x,y)

