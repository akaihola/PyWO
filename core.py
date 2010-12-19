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

"""core.py - an abstract layer between Xlib and the rest of aplication.

core module (with events module) encapsulates all comunication with X Server.
It contains objects representing Window Manager, Windows, and other basic
concepts needed for repositioning and resizing windows (size, position,
borders, gravity, etc).

"""

import logging
import re
import time
import threading

from Xlib import X, Xutil, XK, Xatom, error
from Xlib.protocol.event import ClientMessage
from Xlib.display import Display


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


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
        return '(%.2f, %.2f)' % (self.x, self.y)


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
        string = 'width: %s, height: %s' 
        return string % (self.width, self.height)


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
        string = 'x: %s, y: %s' 
        return string % (self.x, self.y)


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
        string = 'x: %s, y: %s, width: %s, height: %s, x2: %s, y2: %s' 
        return string % (self.x, self.y, 
                         self.width, self.height, 
                         self.x2, self.y2)


class Borders(object):

    """Borders encapsulate Window borders (frames/decorations)."""

    def __init__(self, left, right, top, bottom):
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @property
    def horizontal(self):
        """Return sum of left and right borders."""
        return self.left + self.right

    @property
    def vertical(self):
        """Return sum of top and bottom borders."""
        return self.top + self.bottom

    def __str__(self):
        string = 'left: %s, right: %s, top: %s, bottom %s' 
        return string % (self.left, self.right, self.top, self.bottom)


class EventDispatcher(object):

    """Checks the event queue and dispatches events to correct handlers.

    EventDispatcher will run in separate thread.
    The self.__handlers attribute holds all registered EventHnadlers,
    it has structure as follows:
    self.__handlers = {win_id: {event_type: handler}} 
    That's why there can be only one handler per window/event_type.

    """

    def __init__(self, display):
        # What about integration with gobject?
        # gobject.io_add_watch(root.display, gobject.IO_IN, handle_xevent)
        self.__display = display
        self.__root = display.screen().root
        self.__handlers = {} # {window.id: {handler.type: [handler, ], }, }
        self.__thread = None

    def run(self):
        """Perform event queue checking.

        Every 50ms check event queue for pending events and dispatch them.
        If there's no registered handlers stop running.

        """
        logging.debug('EventDispatcher started')
        while self.__handlers:
            while self.__display.pending_events():
                # Dispatch all pending events if present
                self.__dispatch(self.__display.next_event())
            time.sleep(0.05)
        logging.debug('EventDispatcher stopped')

    def __get_masks(self, window_id):
        """Return event type masks for given window."""
        masks = set()
        for type_handlers in self.__handlers.get(window_id, {}).values():
            masks.update(set(handler.mask for handler in type_handlers))
        return masks

    def register(self, window, handler):
        """Register event handler and return new window's event mask."""
        logging.debug('Registering %s (mask=%s, types=%s) for %s' %
                      (handler.__class__.__name__, 
                       handler.mask, handler.types, window.id))
        window_handlers = self.__handlers.setdefault(window.id, {})
        for type in handler.types:
            type_handlers = window_handlers.setdefault(type, [])
            type_handlers.append(handler)
        if not self.__thread or \
           (self.__thread and not self.__thread.isAlive()):
            # start new thread only if needed
            self.__thread = threading.Thread(name='EventDispatcher', 
                                 target=self.run)
            self.__thread.start()
        return self.__get_masks(window.id)

    def unregister(self, window=None, handler=None):
        """Unregister event handler and return new window's event mask.
        
        If window is None all handlers for all windows will be unregistered.
        If handler is None all handlers for this window will be unregistered.
        
        """
        if not window:
            logging.debug('Unregistering all handlers for all windows')
            self.__handlers.clear()
            return []
        if not window.id in self.__handlers:
            logging.error('No handlers registered for window %s' % window.id)
        elif not handler and window.id in self.__handlers:
            logging.debug('Unregistering all handlers for window %s' % 
                          (window.id))
            del self.__handlers[window.id]
        elif window.id in self.__handlers:
            logging.debug('Unregistering %s (mask=%s, types=%s) for %s' %
                          (handler.__class__.__name__, 
                           handler.mask, handler.types, window.id))
            window_handlers = self.__handlers[window.id]
            for type in handler.types:
                type_handlers = window_handlers.setdefault(type, [])
                if handler in type_handlers:
                    type_handlers.remove(handler)
                if not type_handlers:
                    del window_handlers[type]
        if not self.__handlers.setdefault(window.id, {}):
            del self.__handlers[window.id]
        return self.__get_masks(window.id)

    def __dispatch(self, event):
        """Dispatch raw X event to correct handler."""
        if hasattr(event, 'window') and \
           event.window.id in self.__handlers:
            # Try window the event is reported on (if present)
            handlers = self.__handlers[event.window.id]
        elif hasattr(event, 'event') and \
             event.event.id in self.__handlers:
            # Try window the event is reported for (if present)
            handlers = self.__handlers[event.event.id]
        elif self.__root in self.__handlers:
            # Try root window
            handlers = self.__handlers[self.__root]
        else:
            logging.error('No handler for this event')
            return
        if not event.type in handlers:
            # Just skip unwanted events types
            return
        for handler in handlers[event.type]:
            handler.handle_event(event)


class XObject(object):

    """Abstract base class for classes communicating with X Server.

    Encapsulates common methods for communication with X Server.

    """

    # TODO: setting Display, not only default one
    __DISPLAY = Display()
    __EVENT_DISPATCHER = EventDispatcher(__DISPLAY)
    __BAD_ACCESS = error.CatchError(error.BadAccess)

    # List of recognized key modifiers
    __KEY_MODIFIERS = {'Alt': X.Mod1Mask,
                       'Ctrl': X.ControlMask,
                       'Shift': X.ShiftMask,
                       'Super': X.Mod4Mask,
                       'NumLock': X.Mod2Mask,
                       'CapsLock': X.LockMask}

    __KEYCODES = {}

    def __init__(self, win_id=None):
        """
        win_id - id of the window to be created, if no id assume it's 
                 Window Manager (root window)
        """
        self.__root = self.__DISPLAY.screen().root
        self._root_id = self.__root.id
        if win_id and win_id != self.__root.id:
            # Normal window
            # FIXME: Xlib.error.BadWindow if invalid win_id is provided!
            self._win = self.__DISPLAY.create_resource_object('window', win_id)
            self.id = win_id
        else:
            # WindowManager, act as root window
            self._win = self.__root 
            self.id = self._win.id

    @classmethod
    def atom(cls, name):
        """Return atom with given name."""
        return cls.__DISPLAY.intern_atom(name)

    @classmethod
    def atom_name(cls, atom):
        """Return atom's name."""
        return cls.__DISPLAY.get_atom_name(atom)

    def get_property(self, name):
        """Return property (None if there's no such property)."""
        atom = self.atom(name)
        property = self._win.get_full_property(atom, 0)
        return property

    def send_event(self, data, type, mask):
        """Send event to the root window."""
        event = ClientMessage(
                    window=self._win,
                    client_type=type,
                    data=(32, (data)))
        self.__root.send_event(event, event_mask=mask)

    def listen(self, event_handler):
        """Register new event handler and update event mask."""
        masks = self.__EVENT_DISPATCHER.register(self, event_handler)
        self.__set_event_mask(masks)

    def unlisten(self, event_handler=None):
        """Unregister event handler(s) and update event mask.
        
        If event_handler is None all handlers will be unregistered.

        """
        masks = self.__EVENT_DISPATCHER.unregister(self, event_handler)
        self.__set_event_mask(masks)

    def _unlisten_all(self):
        """Unregister all event handlers for all windows."""
        masks = self.__EVENT_DISPATCHER.unregister()
        self.__set_event_mask(masks)

    def __set_event_mask(self, masks):
        """Update event mask."""
        event_mask = 0
        logging.debug('Setting %s masks for window %s' % 
                      ([str(e) for e in masks], self.id))
        for mask in masks:
            event_mask = event_mask | mask
        self._win.change_attributes(event_mask=event_mask)

    def __grab_key(self, keycode, modifiers):
        """Grab key."""
        self._win.grab_key(keycode, modifiers, 
                           1, X.GrabModeAsync, X.GrabModeAsync,
                           onerror=self.__BAD_ACCESS)
        self.sync()
        if self.__BAD_ACCESS.get_error():
            logging.error("Can't use %s" % 
                              self.keycode2str(modifiers, keycode))

    def grab_key(self, modifiers, keycode, numlock, capslock):
        """Grab key.

        Grab key alone, with CapsLock on and/or with NumLock on.

        """
        if numlock in [0, 2] and capslock in [0, 2]:
            self.__grab_key(keycode, modifiers)
        if numlock in [0, 2] and capslock in [1, 2]:
            self.__grab_key(keycode, modifiers | X.LockMask)
        if numlock in [1, 2] and capslock in [0, 2]:
            self.__grab_key(keycode, modifiers | X.Mod2Mask)
        if numlock in [1, 2] and capslock in [1, 2]:
            self.__grab_key(keycode, modifiers | X.LockMask | X.Mod2Mask)

    def ungrab_key(self, modifiers, keycode, numlock, capslock):
        """Ungrab key.

        Ungrab key alone, with CapsLock on and/or with NumLock on.

        """
        if numlock in [0, 2] and capslock in [0, 1]:
            self._win.ungrab_key(keycode, modifiers)
        if numlock in [0, 2] and capslock in [1, 2]:
            self._win.ungrab_key(keycode, modifiers | X.LockMask)
        if numlock in [1, 2] and capslock in [0, 2]:
            self._win.ungrab_key(keycode, modifiers | X.Mod2Mask)
        if numlock in [1, 2] and capslock in [1, 2]:
            self._win.ungrab_key(keycode, modifiers | X.LockMask | X.Mod2Mask)

    def draw_rectangle(self, x, y, width, height, line):
        color = self.__DISPLAY.screen().black_pixel
        gc = self.__root.create_gc(line_width=line,
                                   #join_style=X.JoinRound,
                                   foreground=color,
                                   function=X.GXinvert,
                                   subwindow_mode=X.IncludeInferiors,)
        self.__root.rectangle(gc, x, y, width, height)

    def _translate_coords(self, x, y):
        """Return translated coordinates.
        
        Untranslated coordinates are relative to window.
        Translated coordinates are relative to desktop.

        """
        return self._win.translate_coords(self.__root, x, y)

    @classmethod
    def str2modifiers(cls, masks, splitted=False):
        # TODO: Check this part... not sure why it looks like that...
        if not splitted:
            masks = masks.split('-')
        modifiers = 0
        if len(masks) > 0:
            for mask in masks:
                if not mask:
                    continue
                mask = mask.capitalize()
                if mask not in cls.__KEY_MODIFIERS.keys():
                    raise ValueError('Invalid modifier: %s' % mask)
                modifiers = modifiers | cls.__KEY_MODIFIERS[mask]

        return modifiers or X.AnyModifier

    @classmethod
    def str2keycode(cls, key):
        keysym = XK.string_to_keysym(key)
        keycode = cls.__DISPLAY.keysym_to_keycode(keysym)
        cls.__KEYCODES[keycode] = key
        if keycode == 0:
            raise ValueError('No key specified!')
        return keycode

    @classmethod
    def str2modifiers_keycode(cls, code, key=''):
        """Convert key as string(s) into (modifiers, keycode) pair.
        
        There must be both modifier(s) and key persent. If you send both
        modifier(s) and key in one string, they must be separated using '-'. 
        Modifiers must be separated using '-'.
        Keys are case insensitive.
        If you want to use upper case use Shift modifier.
        Only modifiers defined in __KEY_MODIFIERS are valid.
        For example: "Ctrl-A", "Super-Alt-x"
        
        """
        if key:
            code = '-'.join([code,key])
        code = code.split('-')
        key = code[-1]
        masks = code[:-1]
        
        modifiers = cls.str2modifiers(masks, True)
        keycode = cls.str2keycode(key)
        return (modifiers, keycode)

    @classmethod
    def keycode2str(cls, modifiers, keycode):
        """Convert key as (modifiers, keycode) pair into string.
        
        Works ONLY for already registered keycodes!
        
        """
        key = []
        for name, code in cls.__KEY_MODIFIERS.items():
            if modifiers & code:
                key.append(name)

        key.append(cls.__KEYCODES[keycode])
        return '-'.join(key)

    @classmethod
    def flush(cls):
        """Flush request queue to X Server."""
        cls.__DISPLAY.flush()

    @classmethod
    def sync(cls):
        """Flush request queue to X Server, wait until server processes them."""
        cls.__DISPLAY.sync()


class Window(XObject):

    """Window object (X Server client?)."""

    # List of window types
    TYPE_DESKTOP = XObject.atom('_NET_WM_WINDOW_TYPE_DESKTOP')
    TYPE_DOCK = XObject.atom('_NET_WM_WINDOW_TYPE_DOCK')
    TYPE_TOOLBAR = XObject.atom('_NET_WM_WINDOW_TYPE_TOOLBAR')
    TYPE_MENU = XObject.atom('_NET_WM_WINDOW_TYPE_MENU')
    TYPE_UTILITY = XObject.atom('_NET_WM_WINDOW_TYPE_UTILITY')
    TYPE_SPLASH = XObject.atom('_NET_WM_WINDOW_TYPE_SPLASH')
    TYPE_DIALOG = XObject.atom('_NET_WM_WINDOW_TYPE_DIALOG')
    TYPE_NORMAL = XObject.atom('_NET_WM_WINDOW_TYPE_NORMAL')

    # List of window states
    STATE_MODAL = XObject.atom('_NET_WM_STATE_MODAL')
    STATE_STICKY = XObject.atom('_NET_WM_STATE_STICKY')
    STATE_MAXIMIZED_VERT = XObject.atom('_NET_WM_STATE_MAXIMIZED_VERT')
    STATE_MAXIMIZED_HORZ = XObject.atom('_NET_WM_STATE_MAXIMIZED_HORZ')
    STATE_SHADED = XObject.atom('_NET_WM_STATE_SHADED')
    STATE_SKIP_TASKBAR = XObject.atom('_NET_WM_STATE_SKIP_TASKBAR')
    STATE_SKIP_PAGER = XObject.atom('_NET_WM_STATE_SKIP_PAGER')
    STATE_HIDDEN = XObject.atom('_NET_WM_STATE_HIDDEN')
    STATE_FULLSCREEN = XObject.atom('_NET_WM_STATE_FULLSCREEN')
    STATE_ABOVE = XObject.atom('_NET_WM_STATE_ABOVE')
    STATE_BELOW = XObject.atom('_NET_WM_STATE_BELOW')
    STATE_DEMANDS_ATTENTION = XObject.atom('_NET_WM_STATE_DEMANDS_ATTENTION')

    # Mode values (for maximize and shade functions)
    MODE_UNSET = 0
    MODE_SET = 1
    MODE_TOGGLE = 2

    def __init__(self, win_id):
        XObject.__init__(self, win_id)
        # Here comes the hacks for WMs strange behaviours....
        wm_name = WindowManager().name.lower()
        if wm_name.startswith('icewm'):
            wm_name = 'icewm'
        self.__translate_coords =  \
                wm_name not in ['compiz', 'fluxbox', 'window maker', ]
        self.__adjust_geometry =  \
                wm_name in ['compiz', 'kwin', 'e16', 'icewm', 'blackbox', ]
        self.__parent_xy = wm_name in ['fluxbox', 'window maker', ]

    @property
    def type(self):
        """Return list of window's type(s)."""
        type = self.get_property('_NET_WM_WINDOW_TYPE')
        if not type:
            return [Window.TYPE_NORMAL]
        return type.value

    @property
    def state(self):
        """Return list of window's state(s)."""
        state = self.get_property('_NET_WM_STATE')
        if not state:
            return []
        return state.value

    @property
    def parent_id(self):
        """Return window's parent id."""
        parent = self._win.get_wm_transient_for()
        if parent:
            return parent.id
        else:
            return None

    @property
    def parent(self):
        """Return window's parent."""
        parent_id = self.parent_id
        if parent_id:
            return Window(parent_id)
        else:
            return None

    @property
    def name(self):
        """Return window's name."""
        name = self.get_property('_NET_WM_NAME')
        if not name:
            name = self._win.get_full_property(Xatom.WM_NAME, 0)
            if not name:        
                return ''
        return name.value

    @property
    def class_name(self):
        """Return window's class name."""
        class_name = self._win.get_wm_class()
        if class_name:
            return '.'.join(class_name)
        return ''

    @property
    def client_machine(self):
        client = self._win.get_wm_client_machine()
        return client

    @property
    def desktop(self):
        """Return desktop number the window is on."""
        desktop = self.get_property('_NET_WM_DESKTOP')
        if not desktop:
            return 0
        # returns 0xFFFFFFFF when "show on all desktops"
        return desktop.value[0]

    def set_desktop(self, desktop_id):
        """Move window to given desktop."""
        desktop_id = int(desktop_id)
        if desktop_id < 0:
            desktop_id = 0
        # TODO: check if desktop_id >= WindowManager.desktops?
        type = self.atom('_NET_WM_DESKTOP')
        data = [desktop_id, 
                0, 0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, type, mask)

    def __borders(self):
        """Return raw borders info."""
        extents = self.get_property('_NET_FRAME_EXTENTS')
        if extents:
            return extents.value
        # Hack for Blackbox, IceWM, Sawfish, Window Maker
        win = self._win
        parent = win.query_tree().parent
        if parent.id == self._root_id:
            return (0, 0, 0, 0)
        if win.get_geometry().width == parent.get_geometry().width and \
           win.get_geometry().height == parent.get_geometry().height:
            win, parent = parent, parent.query_tree().parent
        win_geo = win.get_geometry()
        parent_geo = parent.get_geometry()
        border_widths = win_geo.border_width + parent_geo.border_width
        left = win_geo.x + border_widths
        top = win_geo.y + border_widths
        right = parent_geo.width - win_geo.width - left + parent_geo.border_width*2
        bottom = parent_geo.height - win_geo.height - top + parent_geo.border_width*2
        return (left, right, top, bottom)

    @property
    def borders(self):
        """Return window's borders (frames/decorations)."""
        borders = self.__borders()
        return Borders(*borders)

    def __geometry(self):
        """Return raw geometry info (translated if needed)."""
        geometry = self._win.get_geometry()
        if self.__parent_xy:
            # Hack for Fluxbox, Window Maker
            parent_geo = self._win.query_tree().parent.get_geometry()
            geometry.x = parent_geo.x
            geometry.y = parent_geo.y
        if self.__translate_coords:
            # if neeeded translate coords and multiply them by -1
            translated = self._translate_coords(geometry.x, geometry.y)
            return (-translated.x, -translated.y, 
                    geometry.width, geometry.height)
        return (geometry.x, geometry.y, 
                geometry.width, geometry.height)

    @property
    def geometry(self):
        """Return window's geometry.

        (x, y) coordinates are the top-left corner of the window,
        relative to the left-top corner of current viewport.
        Position and size *includes* window's borders!
        Position is translated if needed.

        """
        x, y, width, height = self.__geometry()
        borders = self.borders
        if self.__adjust_geometry:
            # Used in Compiz, KWin, E16, IceWM, Blackbox
            x -= borders.left
            y -= borders.top
        return Geometry(x, y,
                        width + borders.horizontal,
                        height + borders.vertical)

    def set_geometry(self, geometry, on_resize=Gravity(0, 0)):
        """Move or resize window using provided geometry.

        Postion and size must include window's borders. 
        Position is relative to current viewport.

        """
        borders = self.borders
        x = geometry.x
        y = geometry.y
        width = geometry.width - borders.horizontal
        height = geometry.height - borders.vertical
        geometry_size = (width, height)
        current = self.__geometry()
        hints = self._win.get_wm_normal_hints()
        # This is a fix for WINE, OpenOffice and KeePassX windows
        if hints and hints.win_gravity == X.StaticGravity:
            x += borders.left
            y += borders.top
        # Reduce size to maximal allowed value
        if hints and hints.max_width: 
            width = min([width, hints.max_width])
        if hints and hints.max_height:
            height = min([height, hints.max_height])
        # Don't try to set size lower then minimal
        if hints and hints.min_width: 
            width = max([width, hints.min_width])
        if hints and hints.min_height:
            height = max([height, hints.min_height])
        # Set correct size if it is incremental, take base in account
        if hints and hints.width_inc: 
            if hints.base_width:
                base = hints.base_width
            else:
                base = current[2] % hints.width_inc
            width = ((width - base) / hints.width_inc) * hints.width_inc
            width += base
            if hints.min_width and width < hints.min_width:
                width += hints.width_inc
        if hints and hints.height_inc:
            if hints.base_height:
                base = hints.base_height
            else:
                base = current[3] % hints.height_inc
            height = ((height - base) / hints.height_inc) * hints.height_inc
            height += base
            if hints.height_inc and height < hints.min_height:
                height += hints.height_inc
        # Adjust position after size change
        if (width, height) != geometry_size:
            x = x + (geometry_size[0] - width) * on_resize.x
            y = y + (geometry_size[1] - height) * on_resize.y
        self._win.configure(x=x, y=y, width=width, height=height)

    def activate(self):
        """Make this window active (and unshade, unminimize)."""
        # NOTE: In Metacity this WON'T change desktop to window's desktop!
        type = self.atom('_NET_ACTIVE_WINDOW')
        mask = X.SubstructureRedirectMask
        data = [0, 0, 0, 0, 0]
        self.send_event(data, type, mask)
        # NOTE: Previously used for activating (didn't unshade/unminimize)
        #       Need to test if setting X.Above is needed in various WMs
        #self._win.set_input_focus(X.RevertToNone, X.CurrentTime)
        #self._win.configure(stack_mode=X.Above)

    def iconify(self):
        """Iconify (minimize) window."""
        type = self.atom('WM_CHANGE_STATE')
        mask = X.SubstructureRedirectMask
        data = [Xutil.IconicState,
                0, 0, 0, 0]
        self.send_event(data, type, mask)

    def maximize(self, mode,
                 vert=STATE_MAXIMIZED_VERT, 
                 horz=STATE_MAXIMIZED_HORZ):
        """Maximize window (both vertically and horizontally)."""
        data = [mode, 
                horz,
                vert,
                0, 0]
        self.__change_state(data)

    def shade(self, mode):
        """Shade window (if supported by window manager)."""
        data = [mode, 
                Window.STATE_SHADED,
                0, 0, 0]
        self.__change_state(data)

    def fullscreen(self, mode):
        """Make window fullscreen (if supported by window manager)."""
        data = [mode, 
                Window.STATE_FULLSCREEN,
                0, 0, 0]
        self.__change_state(data)

    def reset(self):
        """Unmaximize (horizontally and vertically), unshade, unfullscreen."""
        self.fullscreen(self.MODE_UNSET)
        self.maximize(self.MODE_UNSET)
        self.shade(self.MODE_UNSET)

    def sticky(self, mode):
        """Make window fullscreen (if supported by window manager)."""
        data = [mode, 
                Window.STATE_STICKY,
                0, 0, 0]
        self.__change_state(data)

    def close(self):
        """Close window."""
        type = self.atom('_NET_CLOSE_WINDOW')
        mask = X.SubstructureRedirectMask
        data = [0, 0, 0, 0, 0]
        self.send_event(data, type, mask)

    def __change_state(self, data):
        """Send _NET_WM_STATE event to the root window."""
        type = self.atom('_NET_WM_STATE')
        mask = X.SubstructureRedirectMask
        self.send_event(data, type, mask)

    def blink(self):
        """For 0.25 second show border around window."""
        geo = self.geometry
        self.draw_rectangle(geo.x+10, geo.y+10, 
                            geo.width-20, geo.height-20, 20)
        self.flush()
        time.sleep(0.25)
        self.draw_rectangle(geo.x+10, geo.y+10, 
                            geo.width-20, geo.height-20, 20)
        self.flush()

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.id == other.id

    def debug_info(self):
        """Print full window's info, for debug use only."""
        logging.info('ID=%s' % self.id)
        logging.info('Client_machine=%s' % self.client_machine)
        logging.info('Name=%s' % self.name)
        logging.info('Class=%s' % self.class_name)
        logging.info('Type=%s' % [self.atom_name(e) for e in self.type])
        logging.info('State=%s' % [self.atom_name(e) for e in self.state])
        logging.info('Desktop=%s' % self.desktop)
        logging.info('Borders=%s' % self.borders)
        logging.info('Borders_raw=%s' % [str(e) for e in self.__borders()])
        logging.info('Geometry=%s' % self.geometry)
        logging.info('Geometry_raw=%s' % self._win.get_geometry())
        geometry = self._win.get_geometry()
        translated = self._translate_coords(geometry.x, geometry.y)
        logging.info('Geometry_translated=%s' % translated)
        logging.info('Parent=%s %s' % (self.parent_id, self.parent))
        logging.info('Normal_hints=%s' % self._win.get_wm_normal_hints())
        logging.info('Attributes=%s' % self._win.get_attributes())
        logging.info('Query_tree=%s' % self._win.query_tree())


class WindowManager(XObject):
    
    """Window Manager (or root window in X programming terms).
    
    WindowManager's self._win refers to the root window.
    It is Singleton.

    """

    # Instance of the WindowManager class, make it Singleton.
    __INSTANCE = None

    # Desktop orientations
    ORIENTATION_HORZ = 0 #XObject.atom('_NET_WM_ORIENTATION_HORZ')
    ORIENTATION_VERT = 1 #XObject.atom('_NET_WM_ORIENTATION_VERT')

    # Desktop starting corners
    TOPLEFT = 0 #XObject.atom('_NET_WM_TOPLEFT')
    TOPRIGHT = 1 #XObject.atom('_NET_WM_TOPRIGHT')
    BOTTOMRIGHT = 2 #XObject.atom('_NET_WM_BOTTOMRIGHT')
    BOTTOMLEFT = 3 #XObject.atom('_NET_WM_BOTTOMLEFT')

    def __new__(cls):
        if cls.__INSTANCE:
            return cls.__INSTANCE
        manager = object.__new__(cls)
        XObject.__init__(manager)
        cls.__INSTANCE = manager
        return manager

    @property
    def name(self):
        """Return window manager's name.

        '' is returned if window manager doesn't support EWMH.

        """
        win_id = self.get_property('_NET_SUPPORTING_WM_CHECK')
        if not win_id:
            return ''
        win = XObject(win_id.value[0])
        name = win.get_property('_NET_WM_NAME')
        if name:
            return name.value
        else:
            return ''

    @property
    def desktops(self):
        """Return number of desktops."""
        # _NET_NUMBER_OF_DESKTOPS, CARDINAL/32
        number = self.get_property('_NET_NUMBER_OF_DESKTOPS')
        if not number:
            return 1
        return number.value[0]

    # TODO: desktop names
    # _NET_DESKTOP_NAMES, UTF8_STRING[]

    # TODO: add_desktop, remove_desktop

    @property
    def desktop(self):
        """Return current desktop number."""
        # _NET_CURRENT_DESKTOP desktop, CARDINAL/32
        desktop = self.get_property('_NET_CURRENT_DESKTOP')
        return desktop.value[0]

    def set_desktop(self, desktop_id):
        """Change current desktop."""
        desktop_id = int(desktop_id)
        if desktop_id < 0:
            desktop_id = 0
        type = self.atom('_NET_CURRENT_DESKTOP')
        data = [desktop_id, 
                0, 0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, type, mask)

    @property
    def desktop_size(self):
        """Return size of current desktop."""
        # _NET_DESKTOP_GEOMETRY width, height, CARDINAL[2]/32
        geometry = self.get_property('_NET_DESKTOP_GEOMETRY').value
        #print geometry
        return Size(geometry[0], geometry[1])

    # TODO: set_desktop_size, or set_viewports(columns, rows)

    @property
    def desktop_layout(self):
        """Return desktops layout, as set by pager."""
        # _NET_DESKTOP_LAYOUT, orientation, columns, rows, starting_corner CARDINAL[4]/32
        layout = self.get_property('_NET_DESKTOP_LAYOUT')
        orientation, cols, rows, corner = layout.value
        desktops = self.desktops
        # NOTE: needs more testing...
        cols = cols or (desktops / rows + min([1, desktops % rows]))
        rows = rows or (desktops / cols + min([1, desktops % cols]))
        return orientation, cols, rows, corner

    @property
    def workarea_geometry(self):
        """Return geometry of current workarea (desktop without panels)."""
        # _NET_WORKAREA, x, y, width, height CARDINAL[][4]/32
        workarea = self.get_property('_NET_WORKAREA').value
        # TODO: this will return geometry for first, not current!
        # TODO: what about all workareas, not only the current one?
        #print workarea
        return Geometry(workarea[0], workarea[1], 
                        workarea[2], workarea[3])

    @property
    def viewport_position(self):
        """Return position of current viewport. 

        If desktop is large it might be divided into several viewports.

        """
        # _NET_DESKTOP_VIEWPORT x, y, CARDINAL[][2]/32
        viewport = self.get_property('_NET_DESKTOP_VIEWPORT').value
        # TODO: Might not work correctly on all WMs
        #print viewport
        return Position(viewport[0], viewport[1])

    def set_viewport_position(self, x, y):
        """Change current viewport."""
        type = self.atom('_NET_DESKTOP_VIEWPORT')
        data = [x, 
                y, 
                0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, type, mask)

    def active_window_id(self):
        """Return id of active window."""
        # _NET_ACTIVE_WINDOW, WINDOW/32
        win_id = self.get_property('_NET_ACTIVE_WINDOW')
        if win_id:
            return win_id.value[0]
        return None

    def active_window(self):
        """Return active window."""
        window_id = self.active_window_id()
        if window_id:
            return Window(window_id)
        return None

    def windows_ids(self, stacking=True):
        """Return list of all windows' ids (newest/on top first)."""
        # TODO: add sort_order argument to choose stacking, and by age ordering
        if stacking:
            windows_ids = self.get_property('_NET_CLIENT_LIST_STACKING').value
        else:
            windows_ids = self.get_property('_NET_CLIENT_LIST').value
        windows_ids.reverse()
        return windows_ids

    def windows(self, filter_method=None, match='', stacking=True):
        """Return list of all windows (newest/on top first)."""
        # TODO: regexp matching?
        windows_ids = self.windows_ids(stacking)
        windows = [Window(win_id) for win_id in windows_ids]
        if filter_method:
            windows = [window for window in windows if filter_method(window)]
        if match:
            windows = self.__name_matcher(windows, match)
        return windows

    def __name_matcher(self, windows, match):
        match = match.strip().lower()
        desktop = self.desktop
        workarea = self.workarea_geometry
        def mapper(window, points=0):
            name = window.name.lower().decode('utf-8')
            if name == match:
                points += 200
            elif match in name:
                left = name.find(match)
                right = (name.rfind(match) - len(name) + len(match)) * -1
                points += 150 - min(left, right)
            if match in window.class_name.lower():
                points += 100
            try:
                geometry = window.geometry
            except:
                return (window, 0)
            if points and \
               (window.desktop == desktop or \
                window.desktop == 0xFFFFFFFF):
                points += 50
                if geometry.x < workarea.x2 and \
                   geometry.x2 > workarea.x and \
                   geometry.y < workarea.y2 and \
                   geometry.y2 > workarea.y:
                    points += 100
            return (window, points)
        windows = map(mapper, windows)
        windows.sort(key=lambda win: win[1])
        windows = [win for win, points in windows if points]
        return windows

    def unlisten_all(self):
        """Unlisten all."""
        self._unlisten_all()

    def debug_info(self):
        """Print full windows manager's info, for debug use only."""
        logging.info('WindowManager=%s' % self.name)
        logging.info('Desktops=%s, current=%s' % (self.desktops, self.desktop))
        logging.info('Desktop=%s' % self.desktop_size)
        logging.info('Viewport=%s' % self.viewport_position)
        logging.info('Workarea=%s' % self.workarea_geometry)


def normal_on_same_filter(window):
    """Default windows filter.

    Returns normal, not hidde, not shaded, not fullscreen, not maximized,
    placed on the same desktop (or sticky), and on the same workarea.

    """
    if not Window.TYPE_NORMAL in window.type:
        return False
    WM = WindowManager()
    state = window.state
    geometry = window.geometry
    workarea = WM.workarea_geometry
    return Window.STATE_HIDDEN not in state and \
           Window.STATE_SHADED not in state and \
           Window.STATE_FULLSCREEN not in state and \
           not (Window.STATE_MAXIMIZED_VERT in state and \
                Window.STATE_MAXIMIZED_HORZ in state) and \
           (window.desktop == WM.desktop or \
            window.desktop == 0xFFFFFFFF) and \
           geometry.x < workarea.x2 and \
           geometry.x2 > workarea.x and \
           geometry.y < workarea.y2 and \
           geometry.y2 > workarea.y


# TODO: 
#    consider ability to connect to given screen (so Xvfb can be used) - Display(displayname=':0.0') 

