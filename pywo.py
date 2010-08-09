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

import itertools
import logging
import operator
import time
import sys

from core import Gravity, Size, Geometry, Window, WindowManager
from events import KeyPressEventHandler
from config import Config
from reposition import reposition_resize, shrink_window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.0.1"


# TODO: move it somewhere
format = '%(levelname)s:%(filename)s(%(lineno)d):%(funcName)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)
logging.getLogger().setLevel(logging.DEBUG)


def expand(win, direction):
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle),
                               vertical_first=CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


def shrink(win, direction):
    border = shrink_window(win, direction.invert(), sticky=False,
                           vertical_first=CONFIG.settings['vertical_first'])
    logging.debug(border)
    win.move_resize(border, direction)


def move(win, direction):
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
    # TODO: move checking state to handler!
    state = win.state
    if Window.STATE_MAXIMIZED_VERT in state and \
       Window.STATE_MAXIMIZED_VERT in state:
        print "Can't put maximized window!"
        return
    
    #win.shade(0) # TODO: not sure...
    workarea = wm.workarea_geometry
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
    sizes.sort()
    if new_size in sizes[len(sizes)/2:] and \
       new_size != sizes[len(sizes)/2]:
        sizes.reverse()
    sizes = sizes[sizes.index(new_size)+1:] + \
             sizes[:sizes.index(new_size)+1]
    return itertools.cycle(sizes)

def grid(win, position, gravity, sizes, cycle='width'):
    # TODO: move checking state and resetting to handler
    win.reset() 
    win.sync() 
    workarea = wm.workarea_geometry
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


def print_info(win):
    win.full_info()
    geo =  win.geometry
    win.move_resize(geo)
    return geo, Gravity(0, 0)


def close():
    HANDLER.ungrab_keys(wm)
    sys.exit()


def reload():
    global HANDLER
    CONFIG.load('pyworc')
    HANDLER.ungrab_keys(wm)
    HANDLER.mappings = CONFIG.mappings.keys()
    HANDLER.numlock = CONFIG.settings['numlock']
    HANDLER.grab_keys(wm)


ACTIONS = {'float': move,
           'expand': expand,
           'shrink': shrink,
           'put': put,
           'grid': grid,
           'reload': reload,
           'exit': close,
           'debug': print_info}

wm = WindowManager()
print 'WindowManager:', wm.name
print 'Desktops:', wm.desktops, 'current:', wm.desktop
print 'Desktop size:', wm.desktop_size
print 'Viewport:', wm.viewport
print 'Workarea:', wm.workarea_geometry
print '---------------------'
print wm.active_window().geometry
print '---------------------'


CONFIG = Config()
GRIDED = {}

def handle(event):
    logging.debug('type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, event.keycode, event.modifiers))
    window = wm.active_window()
    print window.name
    data = CONFIG.mappings[event.modifiers, event.keycode]
    logging.info([str(e) for e in data])
    if not (event.modifiers, event.keycode) in CONFIG.mappings:
        logging.error('Unrecognized key!')
        return
    action = data[0]
    if action in ['exit', 'reload']:
        ACTIONS[action]()
        return
    if Window.TYPE_NORMAL not in window.type:
        #TODO: decide where to perform window type checking
        logging.error('Only normal windows!')
        return
    if action != 'grid':
        GRIDED['id'] = None
    ACTIONS[action](window, *data[1:])
    wm.flush()

HANDLER = KeyPressEventHandler(CONFIG.mappings.keys(), 
                               CONFIG.settings['numlock'], 
                               handle)
HANDLER.grab_keys(wm)

