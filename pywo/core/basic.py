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

"""basic.py - objects representing most basic PyWO concepts."""

import logging
import re


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class CustomTuple(tuple):

    """Tuple that allows both x in [x, y] and [x,z] in [x, y, z]"""

    def __contains__(self, item):
        if hasattr(item, '__len__'):
            return set(item) <= set(self)
        return tuple.__contains__(self, item)


class Gravity(object):

    """Gravity point as a percentage of width and height of the window."""

    # Predefined gravities, that can be used in config files
    __GRAVITIES = {}
    for xy, names in {
        (0, 0): ['TOP_LEFT', 'UP_LEFT', 'TL', 'UL', 'NW'],
        (0.5, 0): ['TOP', 'UP', 'T', 'U', 'N'],
        (1, 0): ['TOP_RIGHT', 'UP_RIGHT', 'TR', 'UR', 'NE'],
        (0, 0.5): ['LEFT', 'L', 'W'],
        (0.5, 0.5): ['MIDDLE', 'CENTER', 'M', 'C', 'NSEW', 'NSWE'],
        (1, 0.5): ['RIGHT', 'R', 'E'],
        (0, 1): ['BOTTOM_LEFT', 'DOWN_LEFT', 'BL', 'DL', 'SW'],
        (0.5, 1): ['BOTTOM', 'DOWN', 'B', 'D', 'S'],
        (1, 1): ['BOTTOM_RIGHT', 'DOWN_RIGHT', 'BR', 'DR', 'SE'],
    }.items():
        for name in names:
            __GRAVITIES[name] = xy

    def __init__(self, x, y):
        """
        x - percentage of width
        y - percentage of height
        """
        self.x = x
        self.y = y
        self.is_middle = (x == 1.0/2) and (y == 1.0/2)
        # FIXME: should is_middle be also is_diagonal?
        self.is_diagonal = (not x == 1.0/2) and (not y == 1.0/2)

    @property
    def is_top(self):
        """Return True if gravity is toward top."""
        return self.y < 1.0/2 or self.is_middle

    @property
    def is_bottom(self):
        """Return True if gravity is toward bottom."""
        return self.y > 1.0/2 or self.is_middle

    @property
    def is_left(self):
        """Return True if gravity is toward left."""
        return self.x < 1.0/2 or self.is_middle

    @property
    def is_right(self):
        """Return True if gravity is toward right."""
        return self.x > 1.0/2 or self.is_middle

    def invert(self, vertical=True, horizontal=True):
        """Invert the gravity (left becomes right, top becomes bottom)."""
        x, y = self.x, self.y
        if vertical:
            y = 1.0 - self.y
        if horizontal:
            x = 1.0 - self.x
        return Gravity(x, y)

    @staticmethod
    def parse(gravity):
        """Parse gravity string and return Gravity object.

        It can be one of predefined __GRAVITIES, or x and y values (floating
        numbers or those described in __SIZES).

        """
        if not gravity:
            return None
        if gravity in Gravity.__GRAVITIES:
            x, y = Gravity.__GRAVITIES[gravity]
            return Gravity(x, y)
        else:
            x, y = [Size.parse_value(xy) for xy in gravity.split(',')]
        return Gravity(x, y)

    def __eq__(self, other):
        return ((self.x, self.y) ==
                (other.x, other.y))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<Gravity x=%.2f, y=%.2f>' % (self.x, self.y)


class Size(object):

    """Size encapsulates width and height of the object."""

    # Pattern matching simple calculations with floating numbers
    __PATTERN = re.compile('^[ 0-9\.\+-/\*]+$')

    # Predefined sizes that can be used in config files
    __SIZES = {'FULL': '1.0',
               'HALF': '0.5',
               'THIRD': '1.0/3',
               'QUARTER': '0.25', }
    __SIZES_SHORT = {'F': '1.0',
                     'H': '0.5',
                     'T': '1.0/3',
                     'Q': '0.25', }

    def __init__(self, width, height):
        self.width = width
        self.height = height

    @classmethod
    def parse_value(cls, size_string):
        """Parse string representing width or height.

        It can be one of the predefined values, float, or expression.
        If you want to parse list of values separte them with comma.

        """
        if not size_string.strip():
            return None
        size = size_string
        for name, value in cls.__SIZES.items():
            size = size.replace(name, value)
        for name, value in cls.__SIZES_SHORT.items():
            size = size.replace(name, value)
        size = [eval(value) for value in size.split(',')
                            if value.strip() and \
                            cls.__PATTERN.match(value)]
        if size == []:
            raise ValueError('Can\'t parse: %s' % (size_string))
        if len(size) == 1:
            return size[0]
        return size
    
    @staticmethod
    def parse(width, height):
        """Parse width and height strings.
        
        Check parse_value for details.
        
        """
        width = Size.parse_value(width)
        height = Size.parse_value(height)
        if width is not None and height is not None:
            return Size(width, height)
        return None

    def __eq__(self, other):
        return ((self.width, self.height) == (other.width, other.height))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<Size width=%s, height=%s>' % (self.width, self.height)


class Position(object):

    """Position encapsulates Position of the object.

    Position coordinates starts at top-left corner of the desktop.

    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    # TODO: add parse for relative and absolute values

    def __eq__(self, other):
        return ((self.x, self.y) == (other.x, other.y))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<Position x=%s, y=%s>' % (self.x, self.y)


class Geometry(Position, Size):

    """Geometry combines Size and Position of the object.

    Position coordinates (x, y) starts at top left corner of the desktop.
    (x2, y2) are the coordinates of the bottom-right corner of the object.

    """

    # TODO: Geometry + Size, Geometry + Position, Geometry * Size

    __DEFAULT_GRAVITY = Gravity(0, 0)

    def __init__(self, x, y, width, height,
                 gravity=__DEFAULT_GRAVITY):
        Size.__init__(self, int(width), int(height))
        Position.__init__(self, int(x), int(y))
        self.set_position(x, y, gravity)

    @property
    def x2(self):
        return self.x + self.width

    @property
    def y2(self):
        return self.y + self.height

    def set_position(self, x, y, gravity=__DEFAULT_GRAVITY):
        """Set position with (x,y) as gravity point."""
        # FIXME: why x,y not position?
        self.x = int(x - self.width * gravity.x)
        self.y = int(y - self.height * gravity.y)

    # TODO: def set_size(self, size, gravity)
    #       int() !!!

    def __eq__(self, other):
        return ((self.x, self.y, self.width, self.height) ==
                (other.x, other.y, other.width, other.height))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return '<Geometry x=%s, y=%s, width=%s, height=%s, x2=%s, y2=%s>' % \
               (self.x, self.y, self.width, self.height, self.x2, self.y2)


class Extents(object):

    """Extents encapsulate Window extents (decorations)."""

    def __init__(self, left, right, top, bottom):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @property
    def horizontal(self):
        """Return sum of left and right extents."""
        return self.left + self.right

    @property
    def vertical(self):
        """Return sum of top and bottom extents."""
        return self.top + self.bottom

    def __str__(self):
        return '<Extents left=%s, right=%s, top=%s, bottom=%s>' % \
               (self.left, self.right, self.top, self.bottom)

