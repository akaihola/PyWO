#!/usr/bin/env python

import itertools
import logging
import operator
import time

from core import Gravity, Size, Geometry, Window, WindowManager
from events import KeyPressEventHandler
import config


# TODO: move it somewhere
format = '%(levelname)s:%(filename)s(%(lineno)d):%(funcName)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)
logging.getLogger().setLevel(logging.DEBUG)


#TODO: Move repositioning code to another module?
class RepositionerResizer(object):

    """RepositionerResizer finds new geometry for window when resizing, moving.

    Class must be initialized with methods returning new window's edges.

    """

    ATTRGETTERS = {'x': (operator.attrgetter('x'),
                         operator.attrgetter('x2'),
                         operator.attrgetter('width')),
                   'y': (operator.attrgetter('y'),
                         operator.attrgetter('y2'),
                         operator.attrgetter('height'))}

    def __init__(self, top, bottom, left, right):
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
        xy, xy2, size = self.ATTRGETTERS[xy_name]
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
        xy, xy2, size = self.ATTRGETTERS[xy_name]
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
    xy, xy2, size = RepositionerResizer.ATTRGETTERS[xy_name]
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
    xy, xy2, size = RepositionerResizer.ATTRGETTERS[xy_name]
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
    """Return top or left edge of new window's position."""
    xy, xy2, size = RepositionerResizer.ATTRGETTERS[xy_name]
    return min([coord for coord in insides
                      if coord > xy(current) and \
                         coord != xy2(current)] or \
               [xy(current)])

def __ins_bottom_right(current, workarea,
                          windows, insides, xy_name, 
                          sticky, insideout):
    """Return bottom or right edge of new window's position."""
    xy, xy2, size = RepositionerResizer.ATTRGETTERS[xy_name]
    return max([coord for coord in insides
                      if coord < xy2(current) and \
                         coord != xy(current)] or \
               [xy2(current)])

shrink_window = RepositionerResizer(__ins_top_left, __ins_bottom_right, 
                                    __ins_top_left, __ins_bottom_right).find 


def expand(win, direction):
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle))
    logging.debug(border)
    win.move_resize(border, direction)
    #return border, direction


def shrink(win, direction):
    border = shrink_window(win, direction.invert(), sticky=False)
    logging.debug(border)
    win.move_resize(border, direction)
    #return border, direction


def move(win, direction):
    border = reposition_resize(win, direction, 
                               sticky=(not direction.is_middle), 
                               insideout=(not direction.is_middle))
    print border
    geometry = win.geometry
    geometry.width = min(border.width, geometry.width)
    geometry.height = min(border.height, geometry.height)
    x = border.x + border.width * direction.x
    y = border.y + border.height * direction.y
    geometry.set_position(x, y, direction)
    logging.debug('x: %s, y: %s, gravity: %s' % 
                  (geometry.x, geometry.y, direction))
    win.move_resize(geometry)
    #return geometry, direction


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
    #return geometry, position


#TODO: reset GRIDED on every other function
GRIDED = {}

def __get_iterator(sizes, new_size):
    sizes.sort()
    if new_size in sizes[len(sizes)/2:] and \
       new_size != sizes[len(sizes)/2]:
        sizes.reverse()
    sizes = sizes[sizes.index(new_size)+1:] + \
             sizes[:sizes.index(new_size)+1]
    return itertools.cycle(sizes)


def grid(win, position, gravity, sizes, cycle='width'):

    class DummyWindow(object):

        """Mock Window object, only location information is needed."""
        
        gravity = Gravity(0.5, 0.5)

        def __init__(self, window, x, y, sizes, gravity):
            self.borders = window.borders
            self.desktop = window.desktop
            self.id = window.id
            width = int(workarea.width * min(sizes.width))
            height = int(workarea.height * min(sizes.height))
            self.geometry = Geometry(x, y, width, height, gravity)

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
        dummy = DummyWindow(win, x, y, sizes, gravity)
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
    win.move_resize(geometry, gravity.invert())
    #return geometry, gravity.invert()


# =========================================================================

def test(win):
    win.full_info()
    geo =  win.geometry
    win.move_resize(geo)
    return geo, Gravity(0, 0)

def exit():
    import sys
    sys.exit()

def reload():
    global KEY_MAPPING, HANDLER
    KEY_MAPPING = config.load('pyworc')
    HANDLER.ungrab_keys(wm)
    HANDLER = KeyPressEventHandler(KEY_MAPPING.keys(), handle)
    HANDLER.grab_keys(wm)


wm = WindowManager()
print 'WindowManager:', wm.name
print 'Desktops:', wm.desktops, 'current:', wm.desktop
print 'Desktop size:', wm.desktop_size
print 'Viewport:', wm.viewport
print 'Workarea:', wm.workarea_geometry
print '---------------------'
print wm.active_window().geometry
print '---------------------'

# Obsolete
FULL = 1.0
HALF = 0.5
THIRD = 1.0/3
QUARTER = 0.25

GRID3x3 = [Size([THIRD, HALF, THIRD*2], [THIRD, HALF]),
           Size([THIRD, THIRD*2, FULL], [THIRD, HALF]),
           Size([THIRD, HALF, THIRD*2], [THIRD, HALF]),
           Size([THIRD, HALF, THIRD*2], [THIRD, FULL]),
           Size([THIRD, THIRD*2, FULL], [THIRD, FULL]),
           Size([THIRD, HALF, THIRD*2], [THIRD, FULL]),
           Size([THIRD, HALF, THIRD*2], [THIRD, HALF, THIRD*2]),
           Size([THIRD, THIRD*2, FULL], [THIRD, HALF, THIRD*2]),
           Size([THIRD, HALF, THIRD*2], [THIRD, HALF, THIRD*2])]

GRID2x3 = [Size([THIRD, HALF, THIRD*2], [HALF]),
           Size([THIRD, FULL], [HALF]),
           Size([THIRD, HALF, THIRD*2], [HALF]),
           Size([THIRD, HALF, THIRD*2], [FULL]),
           Size([THIRD, THIRD*2], [FULL]),
           Size([THIRD, HALF, THIRD*2], [FULL]),
           Size([THIRD, HALF, THIRD*2], [HALF]),
           Size([THIRD, FULL], [HALF]),
           Size([THIRD, HALF, THIRD*2], [HALF])]

GRID = GRID3x3


CONFIG = config.Config()

def handle(event):
    logging.debug('type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, event.keycode, event.modifiers))
    window = wm.active_window()
    print window.name
    data = CONFIG.mappings[event.modifiers, event.keycode]
    logging.info([str(e) for e in data])
    if data[0] in ['exit', 'reload']:
        globals()[data[0]]()
        return
    if Window.TYPE_NORMAL not in window.type:
        logging.error('Only normal windows!')
        return
    if not (event.modifiers, event.keycode) in CONFIG.mappings:
        logging.error('Unrecognized key!')
        return
    globals()[data[0]](window, *data[1:])
    wm.flush()

HANDLER = KeyPressEventHandler(CONFIG.mappings.keys(), handle)
HANDLER.grab_keys(wm)
#wm.unlisten()

