import logging

from Xlib import X 

from core import Window


class Event(object):

    """Abstract base class for X event wrappers."""

    def __init__(self, event):
        self.event = event
        self.type = event.type

    @property
    def window_id(self):
        """Return id of the window, which is the source of the event."""
        return self.event.window.id

    @property
    def window(self):
        """Return window, which is the source of the event."""
        return Window(self.window_id)


class EventHandler(object):

    """Abstract base class for event handlers."""

    def __init__(self, mask, types):
        self.mask = mask
        self.types = types

    def handle_event(self, event):
        """Handle raw X event. 
        
        If handler_method present forward event to this method.

        """
        pass


class KeyEvent(Event):

    """Class representing X.KeyPress and X.KeyRelease events."""

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


class KeyPressEventHandler(EventHandler):
    
    """Handler for X.KeyPress events."""

    def __init__(self, keys, handler_method=None):
        EventHandler.__init__(self, X.KeyPressMask, [X.KeyPress])
        self.handler_method = handler_method
        self.keys = keys

    def grab_keys(self, window):
        """Grab keys and start listening to window's events."""
        for mask, code in self.keys:
            window.grab_key(mask, code)
        window.listen(self)

    def ungrab_keys(self, window):
        """Ungrab keys and stop listening to window's events."""
        for mask, code in self.keys:
            window.ungrab_key(mask, code)
        window.unlisten(self)

    def handle_event(self, event):
        """Wrap raw X event into KeyEvent and delegate to handler method."""
        event = KeyEvent(event)
        self.key_press(event)

    def key_press(self, event):
        """Handle key press event or delegate to handler method."""
        if self.handler_method:
            self.handler_method(event)


