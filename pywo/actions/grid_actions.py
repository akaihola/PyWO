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

from pywo.core import Gravity, Geometry, Size, Position, WindowManager
from pywo.actions import Action, TYPE_FILTER
from pywo.actions.resizer import expand_window


__author__ = "Wojciech 'KosciaK' Pietrzok"


log = logging.getLogger(__name__)

WM = WindowManager()

NO_SIZE = Size(0, 0)

CYCLE_WIDTH = 0
CYCLE_HEIGHT = 1


class DummyWindow(object):

    """Dummy Window object, only geometry information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, window, position, size, gravity):
        self.extents = window.extents
        self.desktop = window.desktop
        self.id = window.id
        self.geometry = Geometry(position.x, position.y, 
                                 min(size.width), min(size.height), 
                                 gravity)


def absolute_position(workarea, position):
    """Return Position on viewport."""
    return Position(workarea.x + workarea.width * position.x,
                    workarea.y + workarea.height * position.y)


def absolute_size(win, workarea, size, width, height):
    """Return Size containing sorted lists of absolute sizes."""
    widths = width.width or size.width or float(win.width)/workarea.width
    heights = height.height or size.height or float(win.height)/workarea.height
    try:
        widths = set([min([width * workarea.width, workarea.width]) 
                     for width in widths])
    except TypeError:
        widths = [min([widths * workarea.width, workarea.width])]
    try:
        heights = set([min([height * workarea.height, workarea.height]) 
                      for height in heights])
    except TypeError:
        heights = [min([heights * workarea.height, workarea.height])]
    return Size(sorted(widths), sorted(heights))


def get_iterator(sizes, new_size):
    """Prepare cycle iterator for window sizes."""
    if new_size in sizes[len(sizes)/2:] and \
       new_size != sizes[len(sizes)/2]:
        sizes.reverse()
    sizes = sizes[sizes.index(new_size):] + \
            sizes[:sizes.index(new_size)]
    return itertools.cycle(sizes)


class GeometryCycler(object):

    """Cycle window geometry."""

    def __init__(self, win, position, gravity, size, width, height, cycle):
        self.win_id = win.id
        self.args = (position, gravity, size, width, height) # TODO: remove me!?
        self.gravity = gravity
        workarea = WM.workarea_geometry
        self.position = absolute_position(workarea, position)
        self.sizes = absolute_size(win, workarea, size, width, height)
        dummy = DummyWindow(win, self.position, self.sizes, self.gravity)
        max_geo = expand_window(dummy, dummy.gravity,
                                sticky=False, vertical_first=cycle)
        widths = []
        for width in self.sizes.width:
            if max_geo.width - width >= 0 and \
               self.position.x - width * position.x >= max_geo.x and \
               self.position.x + width * (1 - position.x) <= max_geo.x2:
                widths.append(width)
        heights = []
        for height in self.sizes.height:
            if max_geo.height - height >= 0 and \
               self.position.y - height * position.y >= max_geo.y and \
               self.position.y + height * (1 - position.y) <= max_geo.y2:
                heights.append(height)
        width = max(widths)
        height = max(heights)
        self.sizes_iterator = Size(get_iterator(self.sizes.width, width),
                                   get_iterator(self.sizes.height, height))
        [self.sizes_iterator.height, self.sizes_iterator.width][cycle].next()
        self.previous = Geometry(self.position.x, self.position.y,
                                 width, height, self.gravity)

    def next(self, cycle):
        """Return new window geometry."""
        if cycle == CYCLE_WIDTH:
            width = self.sizes_iterator.width.next()
            height = self.previous.height
        if cycle == CYCLE_HEIGHT:
            width = self.previous.width
            height = self.sizes_iterator.height.next()
        self.previous = Size(width, height)
        return Geometry(self.position.x, self.position.y, 
                        width, height, self.gravity)


class GridAction(Action):

    """Put window on given position and resize it according to grid layout."""

    __cycler = None

    def __init__(self, name, doc, cycle):
        Action.__init__(self, name=name, doc=doc, 
                        filter=TYPE_FILTER, unshade=False)
        self.cycle = cycle

    def perform(self, win, position, gravity=None,
                size=NO_SIZE, width=NO_SIZE, height=NO_SIZE,
                invert_on_resize=True):
        win.reset()
        win.sync() 
        gravity = gravity or position
        geometry = self.get_geometry(win, position, gravity,
                                     size, width, height, self.cycle)
        log.debug('Setting %s' % (geometry,))
        if invert_on_resize: 
            gravity = gravity.invert()
        win.set_geometry(geometry, gravity)

    @classmethod
    def get_geometry(cls, win, position, gravity, 
                     size, width, height, cycle):
        """Return new window geometry from GeometryCycler."""
        # TODO: this should be done in action_hook,
        #       here only existence of cycle should be checked
        # NOTE: it seems window.id are reused, when you create new window 
        #       just after closing previous it might get the same id!
        if not cls.__cycler or \
           not win.id == cls.__cycler.win_id or \
           not (position, gravity, size, width, height) == cls.__cycler.args:
            cls.__cycler = GeometryCycler(win, position, gravity, 
                                          size, width, height, cycle)
        return cls.__cycler.next(cycle)


GridAction('grid_width', 
           "Put window in given position and resize it (cycle widths).",
           CYCLE_WIDTH).register()

GridAction('grid_height', 
           "Put window in given position and resize it (cycle heights).",
           CYCLE_HEIGHT).register()

