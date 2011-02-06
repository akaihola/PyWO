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

"""grid_actions.py - PyWO actions - placing windows on grid."""

import itertools
import logging

from pywo.actions import register, TYPE_FILTER
from pywo.core import Gravity, Geometry, Size, WindowManager
from pywo.resizer import expand_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()

NO_SIZE = Size(0, 0)
_GRIDED = {} # change to HISTORY


class _DummyWindow(object):

    """Dummy Window object, only geometry information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, workarea, window, x, y, widths, heights, gravity):
        self.extents = window.extents
        self.desktop = window.desktop
        self.id = window.id
        self.geometry = Geometry(x, y, min(widths), min(heights), gravity)


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

    win.reset()
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


