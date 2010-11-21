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

"""actions.py - core PyWO actions."""

import itertools
import logging

from core import Gravity, Geometry, Window, WM, normal_on_same_filter
from events import PropertyNotifyHandler
from reposition import reposition_resize, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


ACTIONS = {} # {action.name: action, }

_GRIDED = {} # change to HISTORY

TYPE = 1
STATE = 2


class ActionException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Action(object):

    def __init__(self, name, action, 
                 check=[], unshade=False):
        self.name = name
        self.args = action.func_code.co_varnames[1:action.func_code.co_argcount]
        self.__action = action
        self.__check = check
        self.__unshade = unshade

    def __call__(self, win, **kwargs):
        if self.__check:
            self.__check_type_state(win)
        if self.__unshade:
            win.shade(win.MODE_UNSET)
            win.flush()
        self.__action(win, **kwargs)
        # history
        # _GRIDED ??

    def __check_type_state(self, win):
        type = win.type
        if TYPE in self.__check and \
           (Window.TYPE_DESKTOP in type or \
            Window.TYPE_DOCK in type or \
            Window.TYPE_SPLASH in type):
            error_msg = "Can't perform action on window of this type."
            raise ActionException(error_msg)

        state = win.state
        if STATE in self.__check and \
           (Window.STATE_FULLSCREEN in state or \
            (Window.STATE_MAXIMIZED_HORZ in state and \
             Window.STATE_MAXIMIZED_VERT in state)):
            error_msg = "Can't perform action on maximized/fullscreen window."
            raise ActionException(error_msg)


def register_action(name, check=[], unshade=False):
    """Register function as PyWO action with given name."""
    def register(action):
        action = Action(name, action, check, unshade)
        ACTIONS[name] = action
        return action
    return register


@register_action(name='expand', check=[TYPE, STATE], unshade=True)
def _expand(win, direction, vertical_first=True):
    """Expand window in given direction."""
    _GRIDED['id'] = None
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle),
                               vertical_first=vertical_first)
    logging.debug(border)
    win.move_resize(border, direction)


@register_action(name='shrink', check=[TYPE, STATE], unshade=True)
def _shrink(win, direction, vertical_first=True):
    """Shrink window in given direction."""
    _GRIDED['id'] = None
    border = shrink_window(win, direction.invert(), 
                           sticky=True,
                           vertical_first=vertical_first)
    logging.debug(border)
    win.move_resize(border, direction)


@register_action(name='float', check=[TYPE, STATE], unshade=True)
def _move(win, direction, vertical_first):
    """Move window in given direction."""
    _GRIDED['id'] = None
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle), 
                               insideout=(not direction.is_middle),
                               vertical_first=vertical_first)
    geometry = win.geometry
    geometry.width = min(border.width, geometry.width)
    geometry.height = min(border.height, geometry.height)
    x = border.x + border.width * direction.x
    y = border.y + border.height * direction.y
    geometry.set_position(x, y, direction)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, direction))
    win.move_resize(geometry)


@register_action(name='put', check=[TYPE, STATE], unshade=True)
def _put(win, position):
    """Put window in given position (without resizing)."""
    _GRIDED['id'] = None
    workarea = WM.workarea_geometry
    geometry = win.geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    geometry.set_position(x, y, position)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, position))
    win.move_resize(geometry)


class _DummyWindow(object):

    """Dummy Window object, only geometry information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, workarea, window, x, y, sizes, gravity):
        self.borders = window.borders
        self.desktop = window.desktop
        self.id = window.id
        width = int(workarea.width * min(sizes.width))
        height = int(workarea.height * min(sizes.height))
        self.geometry = Geometry(x, y, width, height, gravity)


def __grid(win, position, gravity, sizes, invert_on_resize, cycle):
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
    workarea = WM.workarea_geometry
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
    if invert_on_resize: 
        gravity = gravity.invert()
    win.move_resize(geometry, gravity)


@register_action(name='grid_width', check=[TYPE])
def _grid_width(win, position, gravity, sizes, invert_on_resize=True):
    """Put window in given position and resize it (cycle widths)."""
    __grid(win, position, gravity, sizes, invert_on_resize, 'width')

@register_action(name='grid_height', check=[TYPE])
def _grid_height(win, position, gravity, sizes, invert_on_resize=True):
    """Put window in given position and resize it (cycle heights)."""
    __grid(win, position, gravity, sizes, invert_on_resize, 'height')


@register_action(name='maximize', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize window."""
    state = win.state
    if mode == Window.MODE_TOGGLE and \
       Window.STATE_MAXIMIZED_HORZ in state and \
       Window.STATE_MAXIMIZED_VERT in state:
        mode = Window.MODE_UNSET
    elif mode == Window.MODE_TOGGLE:
        mode = Window.MODE_SET
    if Window.STATE_FULLSCREEN in state:
        win.fullscreen(win.MODE_UNSET)
    win.maximize(mode)

@register_action(name='maximize_vert', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize vertically window."""
    win.fullscreen(win.MODE_UNSET)
    win.maximize(mode, horz=False)

@register_action(name='maximize_horz', check=[TYPE], unshade=True)
def _maximize(win, mode=Window.MODE_TOGGLE):
    """Maximize vertically window."""
    win.fullscreen(win.MODE_UNSET)
    win.maximize(mode, vert=False)


@register_action(name='shade', check=[TYPE])
def _shade(win, mode=Window.MODE_TOGGLE):
    """Shade window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(win.MODE_UNSET)
    win.shade(mode)


@register_action(name='fullscreen', check=[TYPE], unshade=True)
def _fullscreen(win, mode=Window.MODE_TOGGLE):
    """Fullscreen window."""
    #win.maximize(win.MODE_UNSET)
    win.fullscreen(mode)


@register_action(name='sticky', check=[TYPE])
def _sticky(win, mode=Window.MODE_TOGGLE):
    """Change sticky (stay on all desktops/viewports) property."""
    win.sticky(mode)


@register_action(name='activate', check=[TYPE], unshade=True)
def _activate(win, mode=Window.MODE_TOGGLE):
    """Activate window.
    
    Unshade, unminimize and switch to it's desktop/viewport.
    
    """
    win.activate()


@register_action(name="close", check=[TYPE])
def _close(win):
    """Close window."""
    win.close()


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
            win.move_resize(active_geo)
            active.move_resize(win_geo)
            if keep_active:
                win.activate()

    property_handler = PropertyNotifyHandler(active_changed)
    if _switch_cycle:
        WM.unlisten(property_handler)
        _switch_cycle = False
    else:
        WM.listen(property_handler)
        _switch_cycle = True

@register_action(name='switch', check=[TYPE])
def _switch(win):
    """Switch placement of windows (keep focus on the same window)."""
    __switch_cycle(win, True)

@register_action(name='cycle', check=[TYPE])
def _cycle(win):
    """Switch contents of windows (focus on new window)."""
    __switch_cycle(win, False)


@register_action(name='blink', check=[TYPE, STATE])
def _blink(win):
    """Blink window (show border around window)."""
    win.blink()


@register_action(name='debug', check=[TYPE])
def _debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    logging.info('-= Window Manager =-')
    WM.debug_info()
    logging.info('-= Current Window =-')
    win.debug_info()
    logging.info('-= Move with same geometry =-')
    geo =  win.geometry
    win.move_resize(geo)
    win.sync()
    logging.info('New geometry=%s' % win.geometry)
    logging.info('-= End of debug =-')


# TODO: new actions
#   - always on top
#   - resize (with gravity?)
#   - move (relative with gravity and +/-length)?
#   - place (absolute x,y)
#   - switch desktop/viewport
#   - move window to desktop/viewport

#@register_action(name="spatial_switcher", check=[TYPE, STATE])
@register_action(name="sp", check=[TYPE, STATE])
def _spatial_switcher(win, direction):
    geometry = win.geometry
    win_center = [geometry.x + geometry.width/2, 
                  geometry.y + geometry.height/2]
    print direction
    if direction.is_top or direction.is_bottom:
        multi = [2, 1]
    else:
        multi = [1, 2]
    print multi
    windows = WM.windows(normal_on_same_filter)
    results = []
    for window in windows:
        if win.id == window.id:
            continue
        geometry = window.geometry
        center = [geometry.x + geometry.width/2, 
                  geometry.y + geometry.height/2]
        vector = [center[0] - win_center[0],
                  center[1] - win_center[1]]
        if not vector[0]:
            slope = 'undefined'
        else:
            slope = float(vector[1]) / float(vector[0])
        length = (multi[0]*vector[0]**2 + multi[1]*vector[1]**2)**0.5
        results.append((window.name, length, vector, slope))
    results.sort(key=lambda e: e[2])
    for result in results:
        print result


