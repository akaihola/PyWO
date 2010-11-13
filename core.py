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

from Xlib import X, XK, Xatom, protocol, error
from Xlib.display import Display


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


class Gravity(object):

    """Gravity point as a percentage of width and height of the window."""

    def __init__(self, x, y):
        """
        x - percentage of width
        y - percentage of height
        """
        self.x = x
        self.y = y
        self.is_middle = (x == 1.0/2) and (y == 1.0/2)


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
        if vertical:
            y = 1.0 - self.y
        if horizontal:
            x = 1.0 - self.x
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

    def __init__(self, width, height):
        self.width = width
        self.height = height

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

    __DEFAULT_GRAVITY = Gravity(0, 0)

    def __init__(self, x, y, width, height,
                 gravity=__DEFAULT_GRAVITY):
        Size.__init__(self, int(width), int(height))
        x = int(x) - self.width * gravity.x
        y = int(y) - self.height * gravity.y
        Position.__init__(self, x, y)

    @property
    def x2(self):
        return self.x + self.width

    @property
    def y2(self):
        return self.y + self.height

    def set_position(self, x, y, gravity=__DEFAULT_GRAVITY):
        """Set position with (x,y) as gravity point."""
        self.x = x - self.width * gravity.x
        self.y = y - self.height * gravity.y

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
        self.__handlers = {} # {window.id: {handler.type: handler, }, }

    def run(self):
        """Perform event queue checking.

        Every 50ms check event queue for pending events and dispatch them.
        If there's no registered handlers stop running.

        """
        logging.debug('EventDispatcher started')
        while self.__handlers:
            time.sleep(0.05)
            while self.__display.pending_events():
                # Dispatch all pending events if present
                self.__dispatch(self.__display.next_event())
        logging.debug('EventDispatcher stopped')

    def register(self, window, handler):
        """Register event handler and return new window's event mask."""
        logging.debug('Registering %s (mask=%s, types=%s) for %s' %
                      (handler.__class__.__name__, 
                       handler.mask, handler.types, window.id))
        started = len(self.__handlers)
        if not window.id in self.__handlers:
            self.__handlers[window.id] = {}
        for type in handler.types:
            self.__handlers[window.id][type] = handler
        if not started:
            t = threading.Thread(target=self.run)
            t.start()
        return set([handler.mask 
                    for handler in self.__handlers[window.id].values()])

    def unregister(self, window, handler=None):
        """Unregister event handler and return new window's event mask.
        
        If handler is None all handlers will be unregistered.
        
        """
        if not handler and window.id in self.__handlers:
            logging.debug('Unregistering all handlers for window %s' % 
                          (window.id))
            self.__handlers[window.id] = {}
        elif window.id in self.__handlers:
            logging.debug('Unregistering %s (mask=%s, types=%s) for %s' %
                          (handler.__class__.__name__, 
                           handler.mask, handler.types, window.id))
            for type in handler.types:
                if type in self.__handlers[window.id]:
                    del self.__handlers[window.id][type]
        if not self.__handlers[window.id]:
            del self.__handlers[window.id]
            return []
        return set([handler.mask 
                    for handler in self.__handlers[window.id].values()])

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
            # Just skip unwanted events' types
            return
        handlers[event.type].handle_event(event)


class XObject(object):

    """Abstract base class for classes communicating with X Server.

    Encapsulates common methods for communication with X Server.

    """

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
        if win_id:
            # Normal window
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
        """Send event from (to?) the root window."""
        event = protocol.event.ClientMessage(
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
        if masks[0]:
            for mask in masks:
                if not mask in cls.__KEY_MODIFIERS.keys():
                    continue
                modifiers = modifiers | cls.__KEY_MODIFIERS[mask]
        else:
            modifiers = X.AnyModifier

        return modifiers

    @classmethod
    def str2keycode(cls, key):
        keysym = XK.string_to_keysym(key)
        keycode = cls.__DISPLAY.keysym_to_keycode(keysym)
        cls.__KEYCODES[keycode] = key
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

    # List of window managers that don't need position translation
    __DONT_TRANSLATE = ['compiz']
    __ADJUST_GEOMETRY = ['compiz', 'kwin', 'e16', 
                         'icewm', 'blackbox', 'fvwm',]
                         #'fluxbox',]

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
    STATE_STICKY = XObject.atom('_NET_WM_STATE_STICKY') # 262
    STATE_MAXIMIZED_VERT = XObject.atom('_NET_WM_STATE_MAXIMIZED_VERT') # 263
    STATE_MAXIMIZED_HORZ = XObject.atom('_NET_WM_STATE_MAXIMIZED_HORZ') # 264
    STATE_SHADED = XObject.atom('_NET_WM_STATE_SHADED') # 321
    STATE_SKIP_TASKBAR = XObject.atom('_NET_WM_STATE_SKIP_TASKBAR') # 322
    STATE_SKIP_PAGER = XObject.atom('_NET_WM_STATE_SKIP_PAGER') # 323
    STATE_HIDDEN = XObject.atom('_NET_WM_STATE_HIDDEN') # 324
    STATE_FULLSCREEN = XObject.atom('_NET_WM_STATE_FULLSCREEN') # 265
    STATE_ABOVE = XObject.atom('_NET_WM_STATE_ABOVE') # 325
    STATE_BELOW = XObject.atom('_NET_WM_STATE_BELOW') # 326
    STATE_DEMANDS_ATTENTION = XObject.atom('_NET_WM_STATE_DEMANDS_ATTENTION') # 327

    # Mode values (for maximize and shade functions)
    MODE_UNSET = 0
    MODE_SET = 1
    MODE_TOGGLE = 2

    def __init__(self, win_id):
        XObject.__init__(self, win_id)
        self.__translate_coords, self.__adjust_geometry = self.__check()

    def __check(self):
        """Check if position should be translated or adjusted."""
        name = WindowManager().name.lower()
        translate_coords = name not in Window.__DONT_TRANSLATE
        adjust_geometry = name in Window.__ADJUST_GEOMETRY
        return (translate_coords, adjust_geometry)

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
        return class_name

    @property
    def desktop(self):
        """Return desktop number the window is in."""
        desktop = self.get_property('_NET_WM_DESKTOP')
        if not desktop:
            return 0
        # returns 0xFFFFFFFF when "show on all desktops"
        return desktop.value[0]

    def __borders(self):
        """Return raw borders info."""
        extents = self.get_property('_NET_FRAME_EXTENTS')
        if not extents:
            return (0, 0, 0, 0)
        return extents.value

    @property
    def borders(self):
        """Return window's borders (frames/decorations)."""
        borders = self.__borders()
        return Borders(*borders)

    def __geometry(self):
        """Return raw geometry info (translated if needed)."""
        geometry = self._win.get_geometry()
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
        relative to the left-top corner of desktop (workarea?).
        Position and size *includes* window's borders!
        Position is translated if needed.

        """
        x, y, width, height = self.__geometry()
        left, right, top, bottom = self.__borders()
        if self.__adjust_geometry:
            x -= left
            y -= top
        return Geometry(x, y,
                        width + left + right,
                        height + top + bottom)

    def move_resize(self, geometry, on_resize=Gravity(0, 0)):
        """Move or resize window using provided geometry.

        Postion and size must include window's borders. 

        """
        left, right, top, bottom = self.__borders()
        x = geometry.x
        y = geometry.y
        width = geometry.width - (left + right)
        height = geometry.height - (top + bottom)
        geometry_size = (width, height)
        current = self.__geometry()
        hints = self._win.get_wm_normal_hints()
        # This is a fix for WINE, OpenOffice and KeePassX windows
        if hints and hints.win_gravity == X.StaticGravity:
            x += left
            y += top
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
        """Make this window active (unshade, unminimize)."""
        type = self.atom('_NET_ACTIVE_WINDOW')
        mask = X.SubstructureRedirectMask
        data = [0, 0, 0, 0, 0]
        self.send_event(data, type, mask)
        # NOTE: Previously used for activating (didn't unshade/unminimize)
        #       Need to test if setting X.Above is needed in various WMs
        #self._win.set_input_focus(X.RevertToNone, X.CurrentTime)
        #self._win.configure(stack_mode=X.Above)

    def maximize(self, mode,
                 vert=STATE_MAXIMIZED_VERT, 
                 horz=STATE_MAXIMIZED_HORZ):
        """Maximize window (both vertically and horizontally)."""
        data = [mode, 
                vert,
                horz,
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
        """For 0.25 second show borderaround window."""
        geo = self.geometry
        self.draw_rectangle(geo.x+5, geo.y+5, 
                            geo.width-10, geo.height-10, 10)
        self.flush()
        time.sleep(0.25)
        self.draw_rectangle(geo.x+5, geo.y+5, 
                            geo.width-10, geo.height-10, 10)
        self.flush()

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.id == other.id

    def full_info(self):
        """Print full window's info, for debug use only."""
        logging.info('----------==========----------')
        logging.info('ID=%s' % self.id)
        logging.info('Name=%s' % self.name)
        logging.info('Class=%s' % [str(e) for e in self.class_name])
        logging.info('Type=%s' % [str(e) for e in self.type])
        logging.info('State=%s' % [str(e) for e in self.state])
        logging.info('Desktop=%s' % self.desktop)
        logging.info('Borders=%s' % self.borders)
        logging.info('Borders_raw=%s' % [str(e) for e in self.__borders()])
        logging.info('Geometry=%s' % self.geometry)
        logging.info('Geometry_raw=%s' % self._win.get_geometry())
        logging.info('Parent=%s %s' % (self.parent_id, self.parent))
        logging.info('Normal_hints=%s' % self._win.get_wm_normal_hints())
        logging.info('Attributes=%s' % self._win.get_attributes())
        logging.info('Query_tree=%s' % self._win.query_tree())
        logging.info('----------==========----------')


class WindowManager(XObject):
    
    """Window Manager (or root window in X programming terms).
    
    WindowManager's self._win refers to the root window.
    It is Singleton.

    """

    # Instance of the WindowManager class, make it Singleton.
    __INSTANCE = None

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
        number = self.get_property('_NET_NUMBER_OF_DESKTOPS')
        if not number:
            return 1
        return number.value[0]

    @property
    def desktop(self):
        """Return current desktop number."""
        desktop = self.get_property('_NET_CURRENT_DESKTOP')
        return desktop.value[0]

    @property
    def desktop_size(self):
        """Return size of current desktop."""
        geometry = self.get_property('_NET_DESKTOP_GEOMETRY').value
        return Size(geometry[0], geometry[1])

    @property
    def workarea_geometry(self):
        """Return geometry of current workarea (desktop without panels)."""
        workarea = self.get_property('_NET_WORKAREA').value
        return Geometry(workarea[0], workarea[1], 
                        workarea[2], workarea[3])

    @property
    def viewport(self):
        """Return position of current viewport. 

        If desktop is large it might be divided into several viewports.

        """
        viewport = self.get_property('_NET_DESKTOP_VIEWPORT').value
        return Position(viewport[0], viewport[1])

    def active_window_id(self):
        """Return only id of active window."""
        win_id = self.get_property('_NET_ACTIVE_WINDOW').value[0]
        return win_id

    def active_window(self):
        """Return active window."""
        window_id = self.active_window_id()
        return Window(window_id)

    def windows_ids(self):
        """Return list of all windows' ids (with bottom-top stacking order)."""
        windows_ids = self.get_property('_NET_CLIENT_LIST_STACKING').value
        return windows_ids

    def windows(self, filter_method=None, match=''):
        """Return list of all windows (with top-bottom stacking order)."""
        windows_ids = self.windows_ids()
        windows = [Window(win_id) for win_id in windows_ids]
        if filter_method:
            return [window for window in windows if filter_method(window)]
        if match:
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
                geometry = window.geometry
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
        windows.reverse()
        return windows

WM = WindowManager()


# Predefined sizes that can be used in config files
__SIZES = {'FULL': '1.0',
           'HALF': '0.5',
           'THIRD': '1.0/3',
           'QUARTER': '0.25',
          }

# Predefined gravities, that can be used in config files
__GRAVITIES = {'TOP_LEFT': Gravity(0, 0), 'UP_LEFT': Gravity(0, 0),
               'TOP': Gravity(0.5, 0), 'UP': Gravity(0.5, 0),
               'TOP_RIGHT': Gravity(1, 0), 'UP_RIGHT': Gravity(1, 0),
               'LEFT': Gravity(0, 0.5),
               'MIDDLE': Gravity(0.5, 0.5), 'CENTER': Gravity(0.5, 0.5),
               'RIGHT': Gravity(1, 0.5),
               'BOTTOM_LEFT': Gravity(0, 1), 'DOWN_LEFT': Gravity(0, 1),
               'BOTTOM': Gravity(0.5, 1), 'DOWN': Gravity(0.5, 1),
               'BOTTOM_RIGHT': Gravity(1, 1), 'DOWN_RIGHT': Gravity(1, 1),
              }

# Pattern matching simple calculations with floating numbers
__PATTERN = re.compile('^[ 0-9\.\+-/\*]+$')


def parse_size(widths, heights):
    """Parse widths and heights strings and return Size object.

    It can be float number (value will be evaluatedi, so 1.0/2 is valid) 
    or predefined value in __SIZES.

    """
    if not widths or not heights:
        return None
    for name, value in __SIZES.items():
        widths = widths.replace(name, value)
        heights = heights.replace(name, value)
    width = [eval(width) for width in widths.split(', ') 
                         if __PATTERN.match(width)]
    height = [eval(height) for height in heights.split(', ')
                           if __PATTERN.match(height)]
    return Size(width, height)


def parse_gravity(gravity):
    """Parse gravity string and return Gravity object.

    It can be one of predefined __GRAVITIES, or x and y values (floating
    numbers or those described in __SIZES).

    """
    if not gravity:
        return None
    if gravity in __GRAVITIES:
        return __GRAVITIES[gravity]
    for name, value in __SIZES.items():
        gravity = gravity.replace(name, value)
    x, y = [eval(xy) for xy in gravity.split(', ')
                     if __PATTERN.match(xy)]
    return Gravity(x, y)

