#!/usr/bin/env python
#
# Copyright 2010, Wojciech 'KosciaK' Pietrzok
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""pywo.py is the main module for PyWO."""

import itertools
import logging
from logging.handlers import RotatingFileHandler
import operator
import time
import sys

from core import Gravity, Size, Geometry, Window, WindowManager
from events import KeyPressEventHandler
from config import Config
from reposition import reposition_resize, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.1"


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
    border = shrink_window(win, direction.invert(), sticky=False,
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
    # TODO: move checking state to handler!
    state = win.state
    if Window.STATE_MAXIMIZED_VERT in state and \
       Window.STATE_MAXIMIZED_VERT in state:
        logging.warning("Can't put maximized window!")
        return
    
    #win.shade(0) # TODO: not sure...
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
    # TODO: move checking state and resetting to handler
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
    if CONFIG.settings['invert_on_resize']:
        win.move_resize(geometry, gravity.invert())
    else:
        win.move_resize(geometry, gravity)


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
    HANDLER.keys = CONFIG.mappings.keys()
    HANDLER.numlock = CONFIG.settings['numlock']
    HANDLER.grab_keys(WM)


ACTIONS = {'float': move,
           'expand': expand,
           'shrink': shrink,
           'put': put,
           'grid': grid,
           'reload': reload,
           'exit': close,
           'debug': debug_info}


def handle(event):
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
    if Window.TYPE_NORMAL not in window.type:
        #TODO: decide where to perform window type checking
        logging.error('Only normal windows!')
        return
    if action != 'grid':
        GRIDED['id'] = None
    try:
        ACTIONS[action](window, *args)
    except Exception, err:
        logging.exception(err)
    WM.flush()

HANDLER = KeyPressEventHandler(None, None, handle)

def start():
    """Start PyWO."""
    logging.debug('>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<')
    logging.info('Starting PyWO...')
    CONFIG.load()
    HANDLER.keys = CONFIG.mappings.keys()
    HANDLER.numlock = CONFIG.settings['numlock']
    HANDLER.grab_keys(WM)
    logging.info('PyWO ready and running!')


if __name__ == '__main__':
    #logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    format = '%(levelname)s: %(filename)s %(funcName)s(%(lineno)d): %(message)s'
    rotating = RotatingFileHandler('/tmp/PyWO.log', 'a', 1024*50, 2, 'UTF-8')
    rotating.setFormatter(logging.Formatter(format))
    rotating.setLevel(logging.DEBUG)
    logger.addHandler(rotating)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    start()

