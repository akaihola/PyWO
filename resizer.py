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

"""resizer.py provides methods used to find new geometry for window."""

import logging
import operator

from core import Window, WindowManager, normal_on_same_filter


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


WM = WindowManager()

_ATTRGETTERS = {'x': (operator.attrgetter('x'),
                      operator.attrgetter('x2'),
                      operator.attrgetter('width')),
                'y': (operator.attrgetter('y'),
                      operator.attrgetter('y2'),
                      operator.attrgetter('height'))}

class Resizer(object):

    """Resizer finds new geometry for window.

    Class must be initialized with methods returning new window's edges.

    """

    def __init__(self, top_left, bottom_right):
        """top_left ,bottom_right - methods returning window's edge coordinate.
        
        These methods must accept arguments:
        current - current window geometry
        workarea - workarea geometry
        windows - list of window's geometries
        axis - name of axis ('x', or 'y')
        sticky
        insideout
        
        """
        self.__top_left = top_left
        self.__bottom_right = bottom_right

    def __call__(self, win, direction, 
                 sticky=True, insideout=False, vertical_first=True):
        """Return new geometry for the window."""
        #TODO: add limit? and use limit geometry instead of workarea?
        current = win.geometry
        workarea = WM.workarea_geometry
        windows = [window.geometry for window in WM.windows(normal_on_same_filter) 
                                   if window.id != win.id]
        axis_order = [['x', 'y'], ['y', 'x']]
        for axis in axis_order[vertical_first]:
            self.__horizontal_vertical(axis, 
                                       current, workarea, windows, 
                                       direction, sticky, insideout)
        return current

    def __windows_in_axis(self, windows, current, 
                          axis, sticky=True):
        """Return geometries of windows placed in x or y axis to current window.

        Return windows which at least one edge is between right/left or
        top/bottom edge of current window, or current window is between
        other window's edges.

        """
        xy, xy2, size = _ATTRGETTERS[axis]
        return [other for other in windows
                if (sticky and \
                    (xy(current) <= xy(other) <= xy2(current) or \
                     xy(current) <= xy2(other) <= xy2(current))) or \
                   (xy(current) <= xy(other) < xy2(current) or \
                    xy(current) < xy2(other) <= xy2(current)) or \
                   xy(other) < xy(current) < xy2(other)]

    def __horizontal_vertical(self, axis,
                              current, workarea, windows,
                              direction, sticky, insideout):
        """Set left and right, or top and bottom edges of new window's position."""
        xy, xy2, size = _ATTRGETTERS[axis]
        # TODO: use only getattr instead of _ATTRGETTERS
        opposite_axis = ['x', 'y'][axis == 'x']
        size = {'x':'width', 'y':'height'}[axis]
        setattr(current, axis, 
                max(xy(current), xy(workarea)))
        setattr(current, size, 
                min(xy2(current), xy2(workarea)) - xy(current))
        in_axis = self.__windows_in_axis(windows, current, 
                                         opposite_axis, sticky)
        if (axis == 'x' and direction.is_left) or \
           (axis == 'y' and direction.is_top):
            new_xy = self.__top_left(current, workarea, in_axis, 
                                     axis, sticky, insideout)
            setattr(current, size, xy2(current) - new_xy)
            setattr(current, axis, new_xy)
        if (axis == 'x' and direction.is_right) or \
           (axis == 'y' and direction.is_bottom):
            new_xy2 = self.__bottom_right(current, workarea, in_axis, 
                                          axis, sticky, insideout)
            setattr(current, size, new_xy2 - xy(current))


def __top_left(current, workarea, windows, 
               axis, sticky, insideout):
    """Return top or left edge of new window's position."""
    xy, xy2, size = _ATTRGETTERS[axis]
    result = [xy(workarea)]
    result += [xy2(other) for other in windows
                         if xy2(other) < xy(current) or \
                            (not sticky and xy2(other) <= xy(current))]
    if sticky:
        result += [xy(other) for other in windows
                   if xy(workarea) < xy(other) < xy(current)]
    if insideout:
        result += [xy(other) - size(current) for other in windows
                   if xy(current) <= xy(other) < xy2(current) and \
                      xy(other) - size(current) > xy(workarea)]
        result += [xy2(other) - size(current) for other in windows
                   if xy(current) <= xy2(other) < xy2(current) and \
                      xy2(other) - size(current) > xy(workarea)]
    return max(result)

def __bottom_right(current, workarea, windows, 
                   axis, sticky, insideout):
    """Return bottom or right edge of new window's position."""
    xy, xy2, size = _ATTRGETTERS[axis]
    result = [xy2(workarea)]
    result += [xy(other) for other in windows
               if xy(other) > xy2(current) or \
                  (not sticky and xy(other) >= xy2(current))]
    if sticky:
        result += [xy2(other) for other in windows
                   if xy2(current) < xy2(other) < xy2(workarea)]
    if insideout:
        result += [xy(other) + size(current) for other in windows
                   if xy(current) < xy(other) <= xy2(current) and \
                      xy(other) + size(current) < xy2(workarea)]
        result += [xy2(other) + size(current) for other in windows
                   if xy(current) < xy2(other) <= xy2(current) and \
                      xy2(other) + size(current) < xy2(workarea)]
    return min(result)

expand_window = Resizer(__top_left, __bottom_right)


def __ins_top_left(current, workarea, windows, 
                   axis, sticky, insideout):
    """Return top or left edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[axis]
    result = [xy(other) for other in windows
               if xy(current) < xy(other) < xy2(current)]
    result += [xy2(other) for other in windows
               if xy(current) < xy2(other) < xy2(current)]
    result = result or [xy(current)]
    return min(result)

def __ins_bottom_right(current, workarea, windows, 
                       axis, sticky, insideout):
    """Return bottom or right edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[axis]
    result = [xy(other) for other in windows
              if xy(current) < xy(other) < xy2(current)]
    result += [xy2(other) for other in windows
               if xy(current) < xy2(other) < xy2(current)]
    result = result or [xy2(current)]
    return max(result)

shrink_window = Resizer(__ins_top_left, __ins_bottom_right) 

