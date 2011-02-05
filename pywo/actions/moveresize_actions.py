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

"""moveresize.py - PyWO actions -  moving and resizing windows."""

import itertools
import logging

from pywo.actions import register, TYPE_FILTER, TYPE_STATE_FILTER
from pywo.core import Gravity, Geometry, Size, WindowManager
from pywo.events import PropertyNotifyHandler
from pywo.resizer import expand_window, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()

_GRIDED = {} # change to HISTORY

@register(name='expand', filter=TYPE_STATE_FILTER, unshade=True)
def _expand(win, direction, vertical_first=True):
    """Expand window in given direction."""
    _GRIDED['id'] = None
    border = expand_window(win, direction, 
                           sticky=(not direction.is_middle),
                           vertical_first=vertical_first)
    log.debug(border)
    win.set_geometry(border, direction)


@register(name='shrink', filter=TYPE_STATE_FILTER, unshade=True)
def _shrink(win, direction, vertical_first=True):
    """Shrink window in given direction."""
    _GRIDED['id'] = None
    border = shrink_window(win, direction.invert(), 
                           vertical_first=vertical_first)
    log.debug(border)
    win.set_geometry(border, direction)


@register(name='float', filter=TYPE_STATE_FILTER, unshade=True)
def _move(win, direction, vertical_first=True):
    """Move window in given direction."""
    _GRIDED['id'] = None
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
    log.debug('x: %s, y: %s, gravity: %s' % 
              (geometry.x, geometry.y, direction))
    win.set_geometry(geometry)


@register(name='put', filter=TYPE_STATE_FILTER, unshade=True)
def _put(win, position, gravity=None):
    """Put window in given position (without resizing)."""
    _GRIDED['id'] = None
    gravity = gravity or position
    workarea = WM.workarea_geometry
    geometry = win.geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    geometry.set_position(x, y, gravity)
    log.debug('x: %s, y: %s, gravity: %s' % 
              (geometry.x, geometry.y, gravity))
    win.set_geometry(geometry)


class _DummyWindow(object):

    """Dummy Window object, only geometry information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, workarea, window, x, y, widths, heights, gravity):
        self.extents = window.extents
        self.desktop = window.desktop
        self.id = window.id
        self.geometry = Geometry(x, y, min(widths), min(heights), gravity)

NO_SIZE = Size(0, 0)

def __grid(win, position, gravity, 
           size, width, height, 
           invert_on_resize=True, cycle='width'):
    """Put window in given position and resize it."""
    # FIXME: there's something wrong... 
    #        open terminal, grid left, close terminal, 
    #        open terminal, grid left -> wrong size!

    def get_iterator(sizes, new_size):
        """Prepare cycle iterator for window sizes."""
        sizes.sort()
        if new_size in sizes[len(sizes)/2:] and \
           new_size != sizes[len(sizes)/2]:
            sizes.reverse()
        sizes = sizes[sizes.index(new_size)+1:] + \
                 sizes[:sizes.index(new_size)+1]
        return itertools.cycle(sizes)

    win.reset() # TODO: is it necessary
    win.sync() 
    workarea = WM.workarea_geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    if not size and (width == NO_SIZE or height == NO_SIZE):
        # Use current window's size if no size provided
        geometry = win.geometry
        size = Size(float(geometry.width) / workarea.width,
                    float(geometry.height) / workarea.height)
    size = size or NO_SIZE
    try:
        widths = [int(workarea.width * width) 
                  for width in (width.width or size.width)]
    except TypeError:
        widths = [int(workarea.width * (width.width or size.width))]
    try:
        heights = [int(workarea.height * height) 
                   for height in (height.height or size.height)]
    except TypeError:
        heights = [int(workarea.height * (height.height or size.height))]
    if _GRIDED and win.id == _GRIDED['id'] and \
       _GRIDED['placement'] == (position, gravity):
        old = win.geometry
        if cycle == 'width':
            new_width = _GRIDED['width'].next()
            new_height = old.height + \
                         min(abs(old.height - height) for height in heights)
        elif cycle == 'height':
            new_height = _GRIDED['height'].next()
            new_width = old.width + \
                        min(abs(old.width - width) for width in widths)
    else:
        dummy = _DummyWindow(workarea, win, x, y, widths, heights, gravity)
        border = expand_window(dummy, dummy.gravity,
                               sticky = False,
                               vertical_first=(cycle is 'height'))
        #FIXME: max() might get empty sequence! --width F+H
        #       maybe use current geometry as default in such situation?
        new_width = max([width for width in widths 
                               if border.width - width >= 0 and \
                                  x - width * position.x >= border.x and \
                                  x + width * (1 - position.x) <= border.x2])
        new_height = max([height for height in heights 
                                 if border.height - height >= 0 and \
                                    y - height * position.y >= border.y and \
                                    y + height * (1 - position.y) <= border.y2])
        _GRIDED['id'] = win.id
        _GRIDED['width'] = get_iterator(widths, new_width)
        _GRIDED['height'] = get_iterator(heights, new_height)
        _GRIDED['placement'] = (position, gravity)
    geometry = Geometry(x, y, new_width, new_height, gravity)
    log.debug('width: %s, height: %s' % (geometry.width, geometry.height))
    if invert_on_resize: 
        gravity = gravity.invert()
    win.set_geometry(geometry, gravity)


@register(name='grid_width', filter=TYPE_FILTER)
def _grid_width(win, position, gravity, 
                size=None, width=NO_SIZE, height=NO_SIZE, 
                invert_on_resize=True):
    """Put window in given position and resize it (cycle widths)."""
    __grid(win, position, gravity, 
           size, width, height, invert_on_resize, 'width')

@register(name='grid_height', filter=TYPE_FILTER)
def _grid_height(win, position, gravity, 
                 size=None, width=NO_SIZE, height=NO_SIZE, 
                 invert_on_resize=True):
    """Put window in given position and resize it (cycle heights)."""
    __grid(win, position, gravity, 
           size, width, height, invert_on_resize, 'height')


# TODO: move to separate module, 
#       make it Action subclass and __call__ after choosing second window
def __switch_cycle(win, keep_active):
    """Switch contents/placement of windows."""
    _GRIDED['id'] = None
    _switch_cycle = False
    
    def active_changed(event):
        if event.atom_name == '_NET_ACTIVE_WINDOW':
            WM.unlisten(property_handler)
            _switch_cycle = False
            active = WM.active_window()
            active_geo, win_geo = active.geometry, win.geometry
            win.set_geometry(active_geo)
            active.set_geometry(win_geo)
            if keep_active:
                win.activate()

    property_handler = PropertyNotifyHandler(active_changed)
    if _switch_cycle:
        WM.unlisten(property_handler)
        _switch_cycle = False
    else:
        WM.listen(property_handler)
        _switch_cycle = True

@register(name='switch', filter=TYPE_FILTER)
def _switch(win):
    """Switch placement of windows (keep focus on the same window)."""
    __switch_cycle(win, True)

@register(name='cycle', filter=TYPE_FILTER)
def _cycle(win):
    """Switch contents of windows (focus on new window)."""
    __switch_cycle(win, False)


# TODO: new actions
#   - resize (with gravity?)
#   - move (relative with gravity and +/-length)?
#   - place (absolute x,y)

