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

"""events.py - X events handling.

events module contain abstract base classes representing event handler, and
event object wrapper. These should be subclassed by concrete implementations
dealing with concrete X event types.

"""

import logging

from Xlib import X 

from core import Window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


_SUBSTRUCTURE = {True: X.SubstructureNotifyMask,
                 False: X.StructureNotifyMask}


class Event(object):

    """Abstract base class for X event wrappers."""

    def __init__(self, event):
        """
        event - raw X event object
        """
        self._event = event
        self.type = event.type

    @property
    def window_id(self):
        """Return id of the window, which is the source of the event."""
        return self._event.window.id

    @property
    def window(self):
        """Return window, which is the source of the event."""
        return Window(self.window_id)


class EventHandler(object):

    """Abstract base class for event handlers."""

    _EVENT_TYPE = Event

    def __init__(self, mask, mapping):
        """
        mask - X.EventMask
        mapping - dict of X.EventTypes and associated functions
        """
        self.mask = mask
        self.__mapping = mapping

    @property
    def types(self):
        return self.__mapping.keys()

    def handle_event(self, event):
        """Wrap raw X event into _EVENT_TYPE (Event object) and call _METHOD."""
        event = self._EVENT_TYPE(event)
        self.__mapping[event.type](event)


class KeyEvent(Event):

    """Class representing X.KeyPress and X.KeyRelease events.
    
    This event is generated if grabbed key is pressed.
    
    """

    # List of Modifiers we are interested in
    __KEY_MODIFIERS = (X.ShiftMask, X.ControlMask, X.Mod1Mask, X.Mod4Mask)

    def __init__(self, event):
        Event.__init__(self, event)
        self.modifiers, self.keycode = self.__get_modifiers_keycode(event)

    def __get_modifiers_keycode(self, event):
        """Return modifiers mask and keycode of this event."""
        keycode = event.detail
        state = event.state
        modifiers = 0
        for modifier in self.__KEY_MODIFIERS:
            if state & modifier:
                modifiers = modifiers | modifier
        return (modifiers or X.AnyModifier, keycode)


class KeyPressHandler(EventHandler):
    
    """Handler for X.KeyPress events."""

    _EVENT_TYPE = KeyEvent

    def __init__(self, key_press, keys=[], numlock=0, capslock=0):
        """
        key_press - function that will handle events 
        keys - list of (mask, keycode) pairs
        numlock - state of NumLock key (0 - OFF, 1 - OFF, 2 - IGNORE)
        capslock - state of CapsLock key
        """
        EventHandler.__init__(self, X.KeyPressMask, 
                              {X.KeyPress: key_press})
        self.keys = keys
        self.numlock = numlock
        self.capslock = capslock

    def set_keys(self, keys, numlock, capslock):
        """Set new keys list."""
        self.keys = keys
        self.numlock = numlock
        self.capslock = capslock

    def grab_keys(self, window):
        """Grab keys and start listening to window's events."""
        for mask, code in self.keys:
            window.grab_key(mask, code, self.numlock, self.capslock)
        window.listen(self)

    def ungrab_keys(self, window):
        """Ungrab keys and stop listening to window's events."""
        for mask, code in self.keys:
            window.ungrab_key(mask, code, self.numlock, self.capslock)
        window.unlisten(self)


class DestroyNotifyEvent(Event):

    """Class representing X.DestroyNotify events.
    
    This event is generated when a window is destroyed.
    
    """

    def __init__(self, event):
        Event.__init__(self, event)


class DestroyNotifyHandler(EventHandler):

    """Handler for X.DestroyNotify events."""

    def __init__(self, destroyed, children=False):
        """
        destroyed - function that will handle events
        children - False - listen for children windows' events
                   True - listen for window's events
        """
        EventHandler.__init__(self, _SUBSTRUCTURE[children],
                              {X.DestroyNotify: destroyed})


class PropertyNotifyEvent(Event):

    """Class representing X.PropertyNotify events.
    
    This event is generated when property of the window is changed.
    
    """

    NEW_VALUE = X.PropertyNewValue
    DELETED = X.PropertyDelete

    def __init__(self, event):
        Event.__init__(self, event)
        self.atom = event.atom
        self.state = event.state

    @property
    def atom_name(self):
        """Return event's atom name."""
        return Window.atom_name(self.atom)


class PropertyNotifyHandler(EventHandler):

    """Hanlder for X.PropertyNotify events."""

    _EVENT_TYPE = PropertyNotifyEvent

    def __init__(self, property):
        """
        property - function that will handle events
        """
        EventHandler.__init__(self, X.PropertyChangeMask, 
                              {X.PropertyNotify: property})

