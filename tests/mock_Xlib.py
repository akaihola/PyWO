"""Xlib related mock objects.

To be used for testing purposes by emulating Xlib behaviour.
Only methods used by PyWO will be implemented!
It should be enough to just change the core.XObject._XObject__DISPLAY 
to mock instance.

"""


import collections

from Xlib import X, XK, Xatom, protocol, error
import Xlib.display


class Value(object):

    """Simple wrapper for get_full_property()"""

    def __init__(self, value):
        self.value = value


class Geometry(object):

    def __init__(self, x, y, width, height,
                 depth=32, border_width=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.depth = depth
        self.border_width = border_width


class Extents(object):

    def __init__(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

# Extents constants
EXTENTS_NORMAL = Extents(4, 4, 19, 1)
EXTENTS_SHADED = None # TODO: check values
EXTENTS_MAXIMIZED = None
EXTENTS_FULLSCREEN = None


class NormalHints(object):

    def __init__(self,
                 base_width=0, base_height=0,
                 width_inc=0, height_inc=0,
                 min_width=0, min_height=0,
                 max_width=0, max_height=0,
                 win_gravity=X.NorthWestGravity):
        self.base_width = base_width
        self.base_height = base_height
        self.width_inc = width_inc
        self.height_inc = height_inc
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height
        self.win_gravity = win_gravity

# NormalHints constants
HINTS_NORMAL = NormalHints()
HINTS_TERMINAL = NormalHints(2, 2, # base_*
                             7, 15, # *_inc
                             30, 32, # min_*
                             0, 0) # max_*


class Display(Xlib.display.Display):

    def __init__(self):
        Xlib.display.Display.__init__(self)
        root_id = Xlib.display.Display.screen(self).root.id
        self.root = RootWindow(self, root_id)
        self.windows_stack = collections.deque()

    def intern_atom(self, name, only_if_exists=0):
        # Just delegate to real Display
        return Xlib.display.Display.intern_atom(self, name, only_if_exists)

    def get_atom_name(self, atom):
        # Just delegate to real Display
        return Xlib.display.Display.get_atom_name(self, atom)

    def keysym_to_keycode(self, keysym):
        # Just delegate to real Display
        return Xlib.display.Display.keysym_to_keycode(self, keysym)

    def screen(self, sno=None):
        screen = Xlib.display.Display.screen(self, sno)
        screen.root = self.root
        return screen

    def send_event(self, dest, event, event_mask, propagate, onerror):
        # ROOT related
        if dest == self.root and  \
           event.client_type == self.atom('_NET_CURRENT_DESKTOP'):
            desktop = data[1][0]
            desktop = max(desktop, 0)
            desktop = min(dekstop, dest._prop('_NET_NUMBER_OF_DESKTOPS')[0])
            dest._prop('_NET_CURRENT_DESKTOP', [desktop])
        if dest == self.root and \
           event.client_type == self.atom('_NET_NUMBER_OF_DESKTOPS'):
            number = data[1][0]
            dest._prop('_NET_NUMBER_OF_DESKTOPS', [number])
        if dest == self.root and \
           event.client_type == self.atom('_NET_DESKTOP_VIEWPORT'):
            # TODO: set proper x, y
            pass
        # Window related
        if event.client_type == self.atom('_NET_ACTIVE_WINDOW'):
            if event.window in self.windows_stack:
                self.windows_stack.remove(event.window)
                self.windows_stack.append(event.window)
            # TODO: change viewport, uniconify, unshade
        if event.client_type == self.atom('WM_CHANGE_STATE') and \
           event.data[1][0] == Xutil.IconicState:
            # set WM_STATE, _NET_WM_STATE
            pass
        if event.client_type == self.atom('_NET_WM_STATE'):
            mode = data[1][0]
            atom = data[1][1]
            atom2 = data[1][2]
            event.window._set_state(atom, mode)
            if atom2:
                event.window._set_state(atom2, mode)
        if event.client_type == self.atom('_NET_CLOSE_WINDOW'):
            if event.window in self.windows_stack:
                self.windows_stack.remove(win)

    def flush(self):
        # No need to flush or sync, incoming events are processed as they come
        pass

    def sync(self):
        # No need to flush or sync, incoming events are processed as they come
        pass

    def pending_events(self):
        # No events support for now
        return 0

    def next_event(self):
        # This method should block when there are no events, but just return None
        return None

    def create_resource_object(self, type, id):
        if type == 'window':
            if id == self.root.id:
                return self.root
            for win in self.windows_stack:
                if win.id == id:
                    return win
            raise error.BadWindow() # Window with this id not found
        else:
            # only need to return windows
            raise NotImplementedError()


#class AbstractWindow(Xlib.display.Window):
class AbstractWindow(object):

    def __init__(self, display, id):
        self.display = display
        self.id = id
        self.properties = {}

    def get_full_property(self, property, type, sizehint=10):
        value = self.properties.get(property, None)
        if value:
            return Value(value)
        return None

    def atom(self, name):
        return self.display.intern_atom(name)

    def _prop(self, name, value=None):
        atom = self.atom(name)
        if not value:
            return self.properties.get(atom, None)
        self.properties[atom] = value


class Window(AbstractWindow):

    def __init__(self, display, id,
                 class_name, name,
                 geometry, 
                 extents=EXTENTS_NORMAL, 
                 normal_hints=HINTS_NORMAL):
        AbstractWindow.__init__(self, display, id)
        # Always place windows on current desktop
        desktop = self.display.root._prop('_NET_CURRENT_DESKTOP')
        properties = {
            Xatom.WM_CLIENT_MACHINE: 'mock',
            Xatom.WM_CLASS: class_name,
            self.atom('_NET_WM_NAME'): name,
            self.atom('_NET_WM_ICON_NAME'): name,
            Xatom.WM_NAME: name,
            Xatom.WM_ICON_NAME: name,
            self.atom('_NET_WM_STATE'): [],
            self.atom('WM_STATE'): [Xutil.NormalState, X.NONE],
            self.atom('_NET_WM_WINDOW_TYPE'): 
                [self.atom('_NET_WM_WINDOW_TYPE_NORMAL'),],
            self.atom('_NET_WM_DESKTOP'): desktop,
            self.atom('_NET_WM_FRAME_EXTENTS'): [extents.left, extents.right,
                                                 extents.top, extents.bottom],
        }
        self.properties.update(properties)
        self.geometry = geometry
        self.normal_hints = normal_hints

    def get_wm_transient_for(self):
        # Parent window
        return None

    def get_wm_client_machine(self):
        return self.get_full_property(Xatom.WM_CLIENT_MACHINE).value

    def get_wm_class(self):
        return self.get_full_property(Xatom.WM_CLASS).value

    def get_geometry(self):
        return geometry

    def translate_coords(self, src_window, x, y):
        # No translation, just return current geometry
        return self.geometry

    def query_tree(self):
        # TODO: parent=self.display.root, root=self.display.root, children=[]
        raise NotImplementedError()

    def get_wm_normal_hints(self):
        return self.normal_hints

    def get_attributes(self):
        # Only need in debug_info
        raise None

    def change_attributes(self, onerror=None, **keys):
        # used to set event_mask
        pass

    def configure(self, onerror=None, **keys):
        # TODO: x, y, width, height, border_width?
        #       use self.normal_hints to check proper values
        pass

    def grab_key(self, key, modifiers, 
                 owner_events, pointer_mode, keyboard_mode, 
                 onerror=None):
        pass

    def ungrab_key(self, key, modifiers, onerror = None):
        pass

    def _set_state(self, atom, mode):
        # TODO: prevent changing STATE_HIDDEN?
        state = self._prop('_NET_WM_STATE')
        if atom == self.atom('_NET_WM_STATE_STICKY') and \
           atom not in state and (mode == 1 or mode ==2):
            self._prop('_NET_WM_DESKTOP', [0xFFFFFFFF])
        elif atom == self.atom('_NET_WM_STATE_STICKY') and \
           atom in state and (mode == 0 or mode ==2):
            desktop = self.display.root._prop('_NET_CURRENT_DESKTOP')
            self._prop('_NET_WM_DESKTOP', desktop)
        if atom and atom in state:
            if mode == 0 or mode == 2:
                state.remove(atom)
        elif atom and atom not in state:
            if mode == 1 or mode == 2:
                state.append(atom)
        self._set_extents()

    def _set_extents(self):
        state = self._prop('_NET_WM_STATE')
        if self.atom('_NET_WM_STATE_FULLSCREEN') in state:
            self.extents = EXTENTS_FULLSCREEN
        elif self.atom('_NET_WM_STATE_MAXIMIZED_HORZ') in state and \
           self.atom('_NET_WM_STATE_MAXIMIZED_VERT') in state:
            self.extents = EXTENTS_MAXIMIZED
        else:
            self.extents = EXTENTS_NORMAL
        if self.atom('_NET_WM_STATE_SHADED') in state:
            self.extents = EXTENTS_SHADED



class RootWindow(AbstractWindow):

    def __init__(self, display, id):
        AbstractWindow.__init__(self, display, id)
        properties = {
            # 1 desktop, 1 viewport
            self.atom('_NET_SUPPORTING_WM_CHECK'): None, #TODO: ???
            self.atom('_NET_NUMBER_OF_DESKTOPS'): [1],
            self.atom('_NET_CURRENT_DESKTOP'): [0],
            self.atom('_NET_DESKTOP_LAYOUT'): [0, 0, 1, 0],
            # TODO: make it dynamic for viewport changing
            self.atom('_NET_DESKTOP_GEOMETRY'): [1024, 768],
            self.atom('_NET_DESKTOP_VIEWPORT'): [0, 0],
            # TODO: change to emulate panels, dynamic based on desktop geometry?
            self.atom('_NET_WORKAREA'): [0, 0, 1024, 768],
        }
        self.properties.update(properties)

    def get_full_property(self, property, type, sizehint=10):
        if property == self.atom('_NET_CLIENT_LIST_STACKING'):
            return Value(self.display.windows_stack)
        if property == self.atom('_NET_ACTIVE_WINDOW'):
            active= self.display.windows_stack.pop()
            self.display.windows_stack.append(active)
            return Value(active)
        if property == self.atom('_NET_WORKAREA'):
            desktops = self._prop('_NET_NUMBER_OF_DESKTOPS')
            return Value(self._prop('_NET_WORKAREA') * desktops)
        return AbstractWindow.get_full_property(self, property, type, sizehint)

    def send_event(self, event, event_mask=0, propagate=0, onerror=None):
        self.display.send_event(self, event, event_mask, propagate, onerror)

    def create_gc(self, **keys):
        raise NotImplementedError()


# TODO: Use Xvfb to run different window managers headless for tests

