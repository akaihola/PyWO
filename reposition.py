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

"""reposition.py provides methods used to find new geometry for window."""

import logging
import operator

from core import Window, WM, normal_on_same_filter


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


_ATTRGETTERS = {'x': (operator.attrgetter('x'),
                      operator.attrgetter('x2'),
                      operator.attrgetter('width')),
                'y': (operator.attrgetter('y'),
                      operator.attrgetter('y2'),
                      operator.attrgetter('height'))}

class RepositionerResizer(object):

    """RepositionerResizer finds new geometry for window when resizing, moving.

    Class must be initialized with methods returning new window's edges.

    """

    def __init__(self, top, bottom, left, right):
        """top,bottom,left,right - methods returning window's edge coordinate.
        
        These methods must take arguments:
        current - current window geometry
        workarea - workarea geometry
        windows - list of window's geometries
        insides - list of coordinates of inside windows edges
        axis - name of axis ('x', or 'y')
        sticky
        insideout
        
        """
        self.find_top = top
        self.find_bottom = bottom
        self.find_left = left
        self.find_right = right
        self._top_left = {'y': top, 'x': left}
        self._bottom_right = {'y': bottom, 'x': right}

    def __call__(self, win, direction, 
             sticky=False, insideout=False, vertical_first=True):
        """Return new geometry for the window."""
        #TODO: add limit? and use limit geometry instead of workarea?
        current = win.geometry
        workarea = WM.workarea_geometry
        windows = [window.geometry for window in WM.windows(normal_on_same_filter) 
                                    if window.id != win.id]
        order = [['x', 'y'], ['y', 'x']]
        for axis in order[vertical_first]:
            self.__horizontal_vertical(axis, 
                                       current, workarea, windows, 
                                       direction, sticky, insideout)
        return current

    def __axis_filter(self, windows, current, workarea, 
                      axis, sticky=False):
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

    def __insides_coords(self, windows, current, axis):
        """Return list of coordinates of window's edges inside current one.

        It contains both left/right, top/bottom edge's coordinates.

        """
        xy, xy2, size = _ATTRGETTERS[axis]
        top_left = [xy(other) for other in windows
                              if xy(current) <= xy(other) <= xy2(current)]
        bottom_right = [xy2(other) for other in windows 
                                   if xy(current) <= xy2(other) <= xy2(current)]
        return (top_left or []) + (bottom_right or [])

    def __horizontal_vertical(self, axis,
                              current, workarea, windows,
                              direction, sticky, insideout):
        """Set left and right, or bottom and top edges of new window's position."""
        xy, xy2, size = _ATTRGETTERS[axis]
        # TODO: use only getattr instead of _ATTRGETTERS
        opposite_axis = {'x':'y', 'y':'x'}[axis]
        size = {'x':'width', 'y':'height'}[axis]
        setattr(current, axis, 
                max(xy(current), xy(workarea)))
        setattr(current, size, 
                min(xy2(current), xy2(workarea)) - xy(current))
        horz_vert = self.__axis_filter(windows, current, workarea, 
                                       opposite_axis, sticky)
        insides = self.__insides_coords(horz_vert, current, axis)
        if (axis == 'x' and direction.is_left) or \
           (axis == 'y' and direction.is_top):
            old_xy = xy(current)
            setattr(current, axis, 
                    self._top_left[axis](current, workarea,
                                         horz_vert, insides, axis, 
                                         sticky, insideout))
            setattr(current, size, 
                    getattr(current, size) + (old_xy - xy(current)))
        if (axis == 'x' and direction.is_right) or \
           (axis == 'y' and direction.is_bottom):
            setattr(current, size, 
                    self._bottom_right[axis](current, workarea,
                                             horz_vert, insides, axis, 
                                             sticky, insideout) - xy(current))


def __top_left(current, workarea,
               windows, insides, axis,
               sticky, insideout):
    """Return top or left edge of new window's position."""
    xy, xy2, size = _ATTRGETTERS[axis]
    adjecent = [xy2(other) for other in windows 
                             if (not sticky and \
                                 xy2(other) <= xy(current)) or \
                                xy2(other) < xy(current)]
    others = [xy(workarea)] + (adjecent or [])
    if sticky:
        opposite = [xy(other) for other in windows 
                        if xy(workarea) < xy(other) < xy(current)]
        others += opposite or []
    output = max(others)
    if insideout:
        inside = max([coord for coord in insides
                          if coord < xy2(current)] or \
                     [xy(workarea)])
        if inside - size(current) > output:
            output = inside - size(current)
    return output

def __bottom_right(current, workarea,
                   windows, insides, axis,
                   sticky, insideout):
    """Return bottom or right edge of new window's position."""
    #TODO: merge with __top_left() method
    xy, xy2, size = _ATTRGETTERS[axis]
    adjecent = [xy(other) for other in windows 
                          if (not sticky and \
                              xy2(current) <= xy(other)) or \
                             xy2(current) < xy(other)]
    others = [xy2(workarea)] + (adjecent or [])
    if sticky:
        opposite = [xy2(other) for other in windows 
                        if xy2(current) < xy2(other) < xy2(workarea)]
        others += opposite or []
    output = min(others)
    if insideout:
        inside = min([coord for coord in insides
                          if coord > xy(current)] or \
                     [xy2(workarea)])
        if inside + size(current) < output:
            output = inside + size(current)
    return output

reposition_resize = RepositionerResizer(__top_left, __bottom_right,
                                        __top_left, __bottom_right)


def __ins_top_left(current, workarea,
                 windows, insides, axis, 
                 sticky, insideout):
    """Return top or left edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[axis]
    return min([coord for coord in insides
                      if coord > xy(current) and \
                         coord != xy2(current)] or \
               [xy(current)])

def __ins_bottom_right(current, workarea,
                          windows, insides, axis, 
                          sticky, insideout):
    """Return bottom or right edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[axis]
    return max([coord for coord in insides
                      if coord < xy2(current) and \
                         coord != xy(current)] or \
               [xy2(current)])

shrink_window = RepositionerResizer(__ins_top_left, __ins_bottom_right, 
                                    __ins_top_left, __ins_bottom_right)


