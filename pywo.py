#!/usr/bin/env python
#
# PyWO - Python Windows Organizer
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

"""pywo.py is the main module for PyWO."""

import itertools
import collections
import logging
from logging.handlers import RotatingFileHandler
import operator
import time
import sys

from core import Gravity, Size, Geometry, Window, WindowManager
from events import KeyPressHandler, PropertyNotifyHandler
from config import Config
from reposition import reposition_resize, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.2"


WM = WindowManager()
CONFIG = Config()
GRIDED = {}

def expand(win, direction):
    """Expand window in given direction."""
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle),
                               vertical_first=CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


def shrink(win, direction):
    """Shrink window in given direction."""
    border = shrink_window(win, direction.invert(), sticky=True,
                           vertical_first=CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


def move(win, direction):
    """Move window in given direction."""
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle), 
                               insideout=(not direction.is_middle),
                               vertical_first=CONFIG.settings['vertical_first'])
    geometry = win.geometry
    geometry.width = min(border.width, geometry.width)
    geometry.height = min(border.height, geometry.height)
    x = border.x + border.width * direction.x
    y = border.y + border.height * direction.y
    geometry.set_position(x, y, direction)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, direction))
    win.move_resize(geometry)


def put(win, position):
    """Put window in given position (without resizing)."""
    workarea = WM.workarea_geometry
    geometry = win.geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    geometry.set_position(x, y, position)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, position))
    win.move_resize(geometry)


class DummyWindow(object):

    """Mock Window object, only location information is needed."""
    
    gravity = Gravity(0.5, 0.5)

    def __init__(self, workarea, window, x, y, sizes, gravity):
        self.borders = window.borders
        self.desktop = window.desktop
        self.id = window.id
        width = int(workarea.width * min(sizes.width))
        height = int(workarea.height * min(sizes.height))
        self.geometry = Geometry(x, y, width, height, gravity)

def __get_iterator(sizes, new_size):
    """Prepare cycle iterator for window sizes."""
    sizes.sort()
    if new_size in sizes[len(sizes)/2:] and \
       new_size != sizes[len(sizes)/2]:
        sizes.reverse()
    sizes = sizes[sizes.index(new_size)+1:] + \
             sizes[:sizes.index(new_size)+1]
    return itertools.cycle(sizes)

def grid(win, position, gravity, sizes, cycle='width'):
    """Put window in given position and resize it."""
    win.reset() 
    win.sync() 
    workarea = WM.workarea_geometry
    x = workarea.x + workarea.width * position.x
    y = workarea.y + workarea.height * position.y
    heights = [int(workarea.height * height) for height in sizes.height]
    widths = [int(workarea.width * width) for width in sizes.width]
    if GRIDED and win.id == GRIDED['id'] and \
       GRIDED['placement'] == (position, gravity):
        old = win.geometry
        if cycle == 'width':
            new_width = GRIDED['width'].next()
            new_height = old.height + \
                         min(abs(old.height - height) for height in heights)
        elif cycle == 'height':
            new_height = GRIDED['height'].next()
            new_width = old.width + \
                        min(abs(old.width - width) for width in widths)
    else:
        dummy = DummyWindow(workarea, win, x, y, sizes, gravity)
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
        GRIDED['id'] = win.id
        GRIDED['width'] = __get_iterator(widths, new_width)
        GRIDED['height'] = __get_iterator(heights, new_height)
        GRIDED['placement'] = (position, gravity)
    geometry = Geometry(x, y, new_width, new_height, gravity)
    logging.debug('width: %s, height: %s' % (geometry.width, geometry.height))
    if CONFIG.settings['invert_on_resize']: win.move_resize(geometry,
                                                            gravity.invert())
    else: win.move_resize(geometry, gravity)


def switch_cycle(win, keep_active):
    
    def active_changed(event):
        if event.atom_name == '_NET_ACTIVE_WINDOW':
            WM.unlisten(property_handler)
            active = WM.active_window()
            win.move_resize(active.geometry)
            active.move_resize(win.geometry)
            if keep_active:
                win.activate()

    property_handler = PropertyNotifyHandler(active_changed)
    WM.listen(property_handler)


def debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    logging.info('----------==========----------')
    logging.info('WindowManager=%s' % WM.name)
    logging.info('Desktops=%s current=%s' % (WM.desktops, WM.desktop))
    logging.info('Desktop=%s' % WM.desktop_size)
    logging.info('Viewport=%s' % WM.viewport)
    logging.info('Workarea=%s' % WM.workarea_geometry)
    win.full_info()
    geo =  win.geometry
    win.move_resize(geo)
    win.sync()
    logging.info('New geometry=%s' % win.geometry)
    logging.info('----------==========----------')


def close():
    """Ungrab keys and exit PyWO."""
    HANDLER.ungrab_keys(WM)
    logging.info('Exiting....')
    sys.exit()


def reload():
    """Reload configuration file."""
    global HANDLER
    CONFIG.load('pyworc')
    HANDLER.ungrab_keys(WM)
    HANDLER.set_keys(CONFIG.mappings.keys(), CONFIG.settings['numlock'])
    HANDLER.grab_keys(WM)


ACTIONS = {'float': move,
           'expand': expand,
           'shrink': shrink,
           'put': put,
           'grid': grid,
           'switch_cycle': switch_cycle,
           'reload': reload,
           'exit': close,
           'debug': debug_info}


def key_press(event):
    """Event handler method for KeyPressEventHandler."""
    logging.debug('EVENT: type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, event.keycode, event.modifiers))
    if not (event.modifiers, event.keycode) in CONFIG.mappings:
        logging.error('Unrecognized key!')
        return
    window = WM.active_window()
    logging.debug(window.name)
    action, args = CONFIG.mappings[event.modifiers, event.keycode]
    logging.debug('%s%s' % 
                  (action, 
                  ['%s: %s' % (a.__class__.__name__, str(a)) for a in args]))
    if action in ['exit', 'reload']:
        try:
            ACTIONS[action]()
        except Exception, err:
            logging.exception(err)
        return
    type = window.type
    if (Window.TYPE_DESKTOP in type or \
        Window.TYPE_DOCK in type or \
        Window.TYPE_SPLASH in type):
        logging.error("Can't %s window like this!" % action)
        return
    state = window.state
    if action in ['float', 'expand', 'shrink', 'put'] and \
       (Window.STATE_FULLSCREEN in state or \
        (Window.STATE_MAXIMIZED_HORZ in state and \
         Window.STATE_MAXIMIZED_VERT in state)):
        logging.error("Can't %s window in fullscreen or maximized mode" % action)
        return
    if action != 'grid':
        GRIDED['id'] = None
    try:
        window.shade(window.MODE_UNSET)
        ACTIONS[action](window, *args)
    except Exception, err:
        logging.exception(err)
    WM.flush()


HANDLER = KeyPressHandler(key_press)

def start():
    """Setup and start PyWO."""
    logging.debug('>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<')
    logging.info('Starting PyWO...')
    CONFIG.load()
    HANDLER.set_keys(CONFIG.mappings.keys(), CONFIG.settings['numlock'])
    HANDLER.grab_keys(WM)
    logging.info('PyWO ready and running!')


if __name__ == '__main__':
    # Setup logging ...
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    format = '%(levelname)s: %(filename)s %(funcName)s(%(lineno)d): %(message)s'
    rotating = RotatingFileHandler('/tmp/PyWO.log', 'a', 1024*50, 2)
    rotating.setFormatter(logging.Formatter(format))
    rotating.setLevel(logging.DEBUG)
    logger.addHandler(rotating)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    # ... and start PyWO
    start()

