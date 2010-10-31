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

"""actions.py defines core PyWO actions."""

import itertools
import logging
from functools import wraps

from core import Gravity, Geometry, Window, WindowManager
from events import PropertyNotifyHandler
from config import Config
from reposition import reposition_resize, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


ACTIONS = {}

_WM = WindowManager()
_CONFIG = Config()
_GRIDED = {} # change to HISTORY


def register_action(name):
    """Register function as PyWO action with given name."""
    def register(action):
        ACTIONS[name] = action
        return action
    return register


def check_type(action):
    """Perform action only on normal windows."""
    @wraps(action)
    def check(win, *args):
        type = win.type
        if (Window.TYPE_DESKTOP in type or \
            Window.TYPE_DOCK in type or \
            Window.TYPE_SPLASH in type):
            logging.error("Can't perform action on window of this type.")
            return
        return action(win, *args)
    return check


def check_state(action):
    """Perform action only on not maximized/fullscreen windows."""
    @wraps(action)
    def check(win, *args):
        state = win.state
        if (Window.STATE_FULLSCREEN in state or \
            (Window.STATE_MAXIMIZED_HORZ in state and \
             Window.STATE_MAXIMIZED_VERT in state)):
            logging.error("Can't perform action on maximized or fullscreen window.")
            return
        return action(win, *args)
    return check


@register_action('expand')
@check_type
@check_state
def _expand(win, direction):
    """Expand window in given direction."""
    _GRIDED['id'] = None
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle),
                               vertical_first=_CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


@register_action('shrink')
@check_type
@check_state
def _shrink(win, direction):
    """Shrink window in given direction."""
    _GRIDED['id'] = None
    border = shrink_window(win, direction.invert(), sticky=True,
                           vertical_first=_CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


@register_action('float')
@check_type
@check_state
def _move(win, direction):
    """Move window in given direction."""
    _GRIDED['id'] = None
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle), 
                               insideout=(not direction.is_middle),
                               vertical_first=_CONFIG.settings['vertical_first'])
    geometry = win.geometry
    geometry.width = min(border.width, geometry.width)
    geometry.height = min(border.height, geometry.height)
    x = border.x + border.width * direction.x
    y = border.y + border.height * direction.y
    geometry.set_position(x, y, direction)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, direction))
    win.move_resize(geometry)


@register_action('put')
@check_type
@check_state
def _put(win, position):
    """Put window in given position (without resizing)."""
    _GRIDED['id'] = None
    workarea = _WM.workarea_geometry
    geometry = win.geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    geometry.set_position(x, y, position)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, position))
    win.move_resize(geometry)


class _DummyWindow(object):

    """Mock Window object, only location information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, workarea, window, x, y, sizes, gravity):
        self.borders = window.borders
        self.desktop = window.desktop
        self.id = window.id
        width = int(workarea.width * min(sizes.width))
        height = int(workarea.height * min(sizes.height))
        self.geometry = Geometry(x, y, width, height, gravity)


@register_action('grid')
@check_type
def _grid(win, position, gravity, sizes, cycle='width'):
    """Put window in given position and resize it."""

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
    workarea = _WM.workarea_geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    heights = [int(workarea.height * height) for height in sizes.height]
    widths = [int(workarea.width * width) for width in sizes.width]
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
        dummy = _DummyWindow(workarea, win, x, y, sizes, gravity)
        border = reposition_resize(dummy, dummy.gravity,
                                   vertical_first=(cycle is 'height'))
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
    logging.debug('width: %s, height: %s' % (geometry.width, geometry.height))
    if _CONFIG.settings['invert_on_resize']: 
        gravity = gravity.invert()
    win.move_resize(geometry, gravity)


@register_action('switch_cycle')
@check_type
def _switch_cycle(win, keep_active):
    _GRIDED['id'] = None
    
    def active_changed(event):
        if event.atom_name == '_NET_ACTIVE_WINDOW':
            _WM.unlisten(property_handler)
            _CONFIG.settings['switch_cycle'] = False
            active = _WM.active_window()
            active_geo, win_geo = active.geometry, win.geometry
            win.move_resize(active_geo)
            active.move_resize(win_geo)
            if keep_active:
                win.activate()

    property_handler = PropertyNotifyHandler(active_changed)
    if 'switch_cycle' in _CONFIG.settings and \
        _CONFIG.settings['switch_cycle']:
        _WM.unlisten(property_handler)
        _CONFIG.settings['switch_cycle'] = False
    else:
        _WM.listen(property_handler)
        _CONFIG.settings['switch_cycle'] = True


@register_action('debug')
@check_type
def _debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    logging.info('----------==========----------')
    logging.info('WindowManager=%s' % _WM.name)
    logging.info('Desktops=%s current=%s' % (_WM.desktops, _WM.desktop))
    logging.info('Desktop=%s' % _WM.desktop_size)
    logging.info('Viewport=%s' % _WM.viewport)
    logging.info('Workarea=%s' % _WM.workarea_geometry)
    win.full_info()
    geo =  win.geometry
    win.move_resize(geo)
    win.sync()
    logging.info('New geometry=%s' % win.geometry)
    logging.info('----------==========----------')

