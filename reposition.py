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

from core import Window, WindowManager


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
        xy_name - name of axis ('x', or 'y')
        sticky
        insideout
        
        """
        self.find_top = top
        self.find_bottom = bottom
        self.find_left = left
        self.find_right = right

    def __main_filter(self, window):
        """Filters hidden, maximized, shaded, fullscreen, not normal windows. 

        Can be used with WindowManager.windows() method.

        """
        state = window.state
        return Window.TYPE_NORMAL in window.type and \
               Window.STATE_SHADED not in state and \
               Window.STATE_HIDDEN not in state and \
               Window.STATE_FULLSCREEN not in state and \
               not (Window.STATE_MAXIMIZED_VERT in state and \
                    Window.STATE_MAXIMIZED_HORZ in state)

    def __axis_filter(self, windows, current, workarea, 
                      xy_name, sticky=False):
        """Return windows placed in x or y axis to current window.

        Return windows which at least one edge is between right/left or
        top/bottom edge of current window, or current window is between
        other window's edges.

        """
        xy, xy2, size = _ATTRGETTERS[xy_name]
        return [other for other in windows
                if xy(other) < xy2(workarea) and \
                   xy2(other) > xy(workarea) and \
                   (sticky and \
                    (xy(current) <= xy(other) <= xy2(current) or \
                     xy(current) <= xy2(other) <= xy2(current))) or \
                   (xy(current) <= xy(other) < xy2(current) or \
                    xy(current) < xy2(other) <= xy2(current)) or \
                   xy(other) < xy(current) < xy2(other)]

    def __insides_coords(self, windows, current, xy_name):
        """Return list of coordinates of window's edges inside current one.

        It contains both left/right, top/bottom edge's coordinates.

        """
        xy, xy2, size = _ATTRGETTERS[xy_name]
        top_left = [xy(other) for other in windows
                              if xy(current) <= xy(other) <= xy2(current)]
        bottom_right = [xy2(other) for other in windows 
                                   if xy(current) <= xy2(other) <= xy2(current)]
        return (top_left or []) + (bottom_right or [])

    def __vertical(self, win, current, workarea,
                   windows, direction, sticky, insideout):
        """Return top, and bottom edge of new window's position."""
        current.y = max(current.y, workarea.y)
        current.height = min(current.y2, workarea.y2) - current.y
        vertical = self.__axis_filter(windows, current, workarea, 'x', sticky)
        insides = self.__insides_coords(vertical, current, 'y')
        if direction.is_top:
            old_y = current.y
            current.y = self.find_top(current, workarea,
                                      vertical, insides, 'y', 
                                      sticky, insideout)
            current.height = current.height + (old_y - current.y)
        if direction.is_bottom:
            current.height = self.find_bottom(current, workarea,
                                              vertical, insides, 'y', 
                                              sticky, insideout) - current.y

    #TODO: merge _vertical and _horizontal methods
    def __horizontal(self, win, current, workarea,
                     windows, direction, sticky, insideout):
        """Return left, and right edge of new window's position."""
        current.x = max(current.x, workarea.x)
        current.width = min(current.x2, workarea.x2) - current.x
        horizontal = self.__axis_filter(windows, current, workarea, 'y', sticky)
        insides = self.__insides_coords(horizontal, current, 'x')
        if direction.is_left:
            old_x = current.x
            current.x = self.find_left(current, workarea,
                                       horizontal, insides, 'x', 
                                       sticky, insideout)
            current.width = current.width + (old_x - current.x)
        if direction.is_right:
            current.width = self.find_right(current, workarea,
                                            horizontal, insides, 'x', 
                                            sticky, insideout) - current.x

    #FIXME: I don't like name `find` for the method...
    def find(self, win, direction, 
             sticky=False, insideout=False, vertical_first=True):
        """Return new geometry for the window."""
        #TODO: add limit? and use limit geometry instead of workarea?
        current = win.geometry
        wm = WindowManager()
        workarea = wm.workarea_geometry
        windows = [window.geometry for window in wm.windows(self.__main_filter)
                                   if window.id != win.id and \
                                      window.desktop == win.desktop]


        order = {True: [self.__vertical, self.__horizontal],
                 False: [self.__horizontal, self.__vertical]}
        for method in order[vertical_first]:
            method(win, current, workarea,
                   windows, direction, sticky, insideout)
        return current


def __top_left(current, workarea,
               windows, insides, xy_name,
               sticky, insideout):
    """Return top or left edge of new window's position."""
    xy, xy2, size = _ATTRGETTERS[xy_name]
    adjecent = [xy2(other) for other in windows 
                             if xy(workarea) < xy2(other) and \
                                ((not sticky and \
                                  xy2(other) <= xy(current)) or \
                                 xy2(other) < xy(current))]
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
                   windows, insides, xy_name,
                   sticky, insideout):
    """Return bottom or right edge of new window's position."""
    #TODO: merge with __top_left() method
    xy, xy2, size = _ATTRGETTERS[xy_name]
    adjecent = [xy(other) for other in windows 
                          if xy(other) < xy2(workarea) and \
                             ((not sticky and \
                               xy2(current) <= xy(other)) or \
                              xy2(current) < xy(other))]
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
                                        __top_left, __bottom_right).find


def __ins_top_left(current, workarea,
                 windows, insides, xy_name, 
                 sticky, insideout):
    """Return top or left edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[xy_name]
    return min([coord for coord in insides
                      if coord > xy(current) and \
                         coord != xy2(current)] or \
               [xy(current)])

def __ins_bottom_right(current, workarea,
                          windows, insides, xy_name, 
                          sticky, insideout):
    """Return bottom or right edge of new window's position.
    
    Use only coordinates inside current window.
    
    """
    xy, xy2, size = _ATTRGETTERS[xy_name]
    return max([coord for coord in insides
                      if coord < xy2(current) and \
                         coord != xy(current)] or \
               [xy2(current)])

shrink_window = RepositionerResizer(__ins_top_left, __ins_bottom_right, 
                                    __ins_top_left, __ins_bottom_right).find 


