"""Xlib related mock objects.

To be used for testing purposes by emulating Xlib and Window Managers behaviour.
Only methods used by PyWO will be implemented!
It should be enough to just change the core.XObject._XObject__DISPLAY 
to new mock instance, and change core.ClientMessage.

First phase is to write working, testable generic behaviour of mock environment, 
next create emulation of concrete Window Managers to test all the hacks prepared
for them.

"""


import collections
import random

from Xlib import X, XK, Xatom, Xutil, protocol, error
import Xlib.display


class Value(object):

    """Simple wrapper for get_full_property()"""

    def __init__(self, value):
        self.value = value


class Geometry(object):

    """Simple wrapper for get_geometry()"""

    def __init__(self, x, y, width, height,
                 depth=32, border_width=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.depth = depth
        self.border_width = border_width


class TranslateCoords(object):

    """Simple wrapper for translate_coords()"""

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Extents(object):
    
    """Simple wrapper for extents."""


    def __init__(self, left, right, top, bottom):
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom

# Extents constants
EXTENTS_NORMAL = Extents(4, 4, 19, 1)
#EXTENTS_SHADED = Extents(4, 4, 19, 1)
EXTENTS_MAXIMIZED = Extents(0, 0, 19, 1)
EXTENTS_FULLSCREEN = Extents(0, 0, 0, 0)


class NormalHints(object):

    """Simple wrapper fot get_wm_normal_hints()"""

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

class QueryTree(object):

    """Simple wrapper for query_tree()"""

    def __init__(self, parent, root, children):
        self.parent = parent
        self.root = root
        self.children = children


class ClientMessage(object):

    """Xlib.protocol.event.ClientMessage mock."""

    def __init__(self, window, client_type, data):
        self.window = window
        self.client_type = client_type
        self.data = data


class Display(Xlib.display.Display):

    """Xlib.display.Display mock."""

    def __init__(self, screen_width, screen_height, 
                 desktops=1, viewports=[1,1]):
        Xlib.display.Display.__init__(self)
        self.screen_width = screen_width
        self.screen_height = screen_height
        # list of all created windows, oldest first
        self.all_windows = []
        # stack of mapped windows
        self.windows_stack = collections.deque()
        self.root_id = Xlib.display.Display.screen(self).root.id
        self.root = RootWindow(self, desktops, viewports)

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
        screen.width_in_pixels = self.screen_width
        screen.height_in_pixels = self.screen_height
        return screen

    def send_event(self, dest, event, event_mask, propagate, onerror):
        # ROOT related
        if dest == self.root and  \
           event.client_type == self.intern_atom('_NET_CURRENT_DESKTOP'):
            desktop = event.data[1][0]
            desktop = max(desktop, 0)
            desktop = min(desktop, 
                          dest._prop('_NET_NUMBER_OF_DESKTOPS')[0] - 1)
            dest._prop('_NET_CURRENT_DESKTOP', [desktop])
        if dest == self.root and \
           event.client_type == self.intern_atom('_NET_NUMBER_OF_DESKTOPS'):
            desktops = max(1, event.data[1][0])
            event.window._set_desktops(desktops)
        if dest == self.root and \
           event.client_type == self.intern_atom('_NET_DESKTOP_VIEWPORT'):
            # TODO: set proper x, y
            pass
        # Window related
        if event.client_type == self.intern_atom('_NET_ACTIVE_WINDOW'):
            if event.window in self.windows_stack:
                self.windows_stack.remove(event.window)
                self.windows_stack.append(event.window)
            # TODO: change viewport, uniconify, unshade
        if event.client_type == self.intern_atom('_NET_WM_DESKTOP'):
            desktop = event.data[1][0]
            desktop = max(desktop, 0)
            desktop = min(desktop, 
                          self.root._prop('_NET_NUMBER_OF_DESKTOPS')[0] - 1)
            event.window._prop('_NET_WM_DESKTOP', [desktop])
        if event.client_type == self.intern_atom('WM_CHANGE_STATE') and \
           event.data[1][0] == Xutil.IconicState:
            # set WM_STATE, _NET_WM_STATE
            pass
        if event.client_type == self.intern_atom('_NET_WM_STATE'):
            mode = event.data[1][0]
            atom = event.data[1][1]
            atom2 = event.data[1][2]
            event.window._set_state(atom, mode)
            if atom2:
                event.window._set_state(atom2, mode)
        if event.client_type == self.intern_atom('_NET_CLOSE_WINDOW'):
            event.window.destroy()

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
            for win in self.all_windows:
                if win.id == id:
                    return win
            raise error.BadWindow() # Window with this id not found
        else:
            # only need to return windows
            raise NotImplementedError()


class AbstractWindow(object):
#class AbstractWindow(Xlib.display.Window):

    def __init__(self, display, id=None):
        self.display = display
        while not id and \
              id not in self.display.all_windows:
            id = random.randint(1000, self.display.root_id + 10000)
        self.id = id
        self.properties = {}
        self.display.all_windows.append(self)

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

    def __init__(self, display,
                 name,
                 geometry, 
                 class_name=None, 
                 extents=EXTENTS_NORMAL, 
                 normal_hints=HINTS_NORMAL,
                 type=[]):
        AbstractWindow.__init__(self, display)
        # Always place windows on FIRST desktop
        desktop = 0
        properties = {
            Xatom.WM_CLIENT_MACHINE: 'mock',
            self.atom('_NET_WM_NAME'): name,
            self.atom('_NET_WM_ICON_NAME'): name,
            Xatom.WM_NAME: name,
            Xatom.WM_ICON_NAME: name,
            self.atom('_NET_WM_WINDOW_TYPE'): type or \
                                              self.atom('_NET_WM_TYPE_NORMAL'),
            self.atom('_NET_WM_STATE'): [],
            self.atom('WM_STATE'): [Xutil.NormalState, X.NONE],
            self.atom('_NET_WM_WINDOW_TYPE'): 
                [self.atom('_NET_WM_WINDOW_TYPE_NORMAL'),],
            self.atom('_NET_WM_DESKTOP'): desktop,
            self.atom('_NET_FRAME_EXTENTS'): [extents.left, extents.right,
                                                 extents.top, extents.bottom],
        }
        self.properties.update(properties)
        if class_name:
            self.properties[Xatom.WM_CLASS] = class_name
        self.current_geometry = geometry
        self.normal_geometry = geometry
        self.normal_hints = normal_hints

    def map(self, onerror=None):
        self.display.windows_stack.append(self)

    def unmap(self, onerror=None):
        if self in self.display.windows_stack:
            self.display.windows_stack.remove(self)

    def destroy(self, onerror=None):
        self.unmap()
        self.display.all_windows.remove(self)

    def get_wm_transient_for(self):
        # Parent window
        return None

    def get_wm_client_machine(self):
        return self.get_full_property(Xatom.WM_CLIENT_MACHINE, 0).value

    def get_wm_class(self):
        return self.get_full_property(Xatom.WM_CLASS, 0).value

    def get_geometry(self):
        return self.current_geometry

    def _get_extents(self):
        return Extents(*self._prop('_NET_FRAME_EXTENTS'))

    def translate_coords(self, src_window, x, y):
        # Now it works like in Metacity
        extents = self._get_extents()
        return TranslateCoords((x - extents.left) * -1, 
                               (y - extents.top) * -1)

    def query_tree(self):
        return QueryTree(parent=self.display.root,
                         root=self.display.root,
                         children=[])

    def get_wm_normal_hints(self):
        return self.normal_hints

    def get_attributes(self):
        # Only need in debug_info, no need to implemet it
        raise None

    def change_attributes(self, onerror=None, **keys):
        # used to set event_mask
        pass

    def configure(self, onerror=None, **keys):
        x = self.geometry.x
        y = self.geometry.y
        width = self.normal_geometry.width
        height = selg.normal_geometry.height
        hints = self.normal_hints
        if hints.win_gravity == X.StaticGravity:
            x -= self.extents.left
            y -= self.extents.top
        # Reduce size to maximal allowed value
        width = min([width, hints.max_width or width])
        height = min([height, hints.max_height or height])
        # Don't try to set size lower then minimal
        width = max([width, hints.min_width or width])
        height = max([height, hints.min_height or height])
        # Set correct size if it is incremental, take base in account
        if hints and hints.width_inc: 
            if hints.base_width:
                base = hints.base_width
            else:
                base = width % hints.width_inc
            width = ((width - base) / hints.width_inc) * hints.width_inc
            width += base
            if hints.min_width and width < hints.min_width:
                width += hints.width_inc
        if hints and hints.height_inc:
            if hints.base_height:
                base = hints.base_height
            else:
                base = height % hints.height_inc
            height = ((height - base) / hints.height_inc) * hints.height_inc
            height += base
            if hints.height_inc and height < hints.min_height:
                height += hints.height_inc
        geometry = Geometry(x, y, width, height, 
                            border_width=self.normal_geometry.border_width)
        # FIXME: not exactly... when maximized keep normal width, height?
        #        it is possible to configure maxed_vert/horz
        self.normal_geometry = geometry
        self.current_geometry = geometry

    def grab_key(self, key, modifiers, 
                 owner_events, pointer_mode, keyboard_mode, 
                 onerror=None):
        pass

    def ungrab_key(self, key, modifiers, onerror = None):
        pass

    def _set_state(self, atom, mode):
        state = self._prop('_NET_WM_STATE')
        if atom == self.atom('_NET_WM_STATE_HIDDEN'):
            # Just ignore setting HIDDEN
            return
        elif atom == self.atom('_NET_WM_STATE_STICKY') and \
           atom not in state and (mode == 1 or mode ==2):
            self._prop('_NET_WM_DESKTOP', [0xFFFFFFFF])
        elif atom == self.atom('_NET_WM_STATE_STICKY') and \
           atom in state and (mode == 0 or mode ==2):
            desktop = self.display.root._prop('_NET_CURRENT_DESKTOP')
            self._prop('_NET_WM_DESKTOP', desktop)
        elif atom == self.atom('_NET_WM_STATE_MAXIMIZED_HORZ'):
            geometry = Geometry(x=0, y=self.current_geometry.y,
                                width=self.root.screen_width,
                                height=self.current_geometry.height,
                                border_width=self.current_geometry.border_width)
            self.current_geometry = geometry
        elif atom == self.atom('_NET_WM_STATE_MAXIMIZED_VERT'):
            geometry = Geometry(x=self.current_geometry.x, y=0,
                                width=self.current_geometry.width,
                                height=self.root.screen_height,
                                border_width=self.current_geometry.border_width)
            self.current_geometry = geometry
        elif atom == self.atom('_NET_WM_STATE_FULLSCREEN'):
            geometry = Geometry(x=0, y=0,
                                width=self.root.screen_width,
                                height=self.root.screen_height,
                                border_width=self.current_geometry.border_width)
            self.current_geometry = geometry
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


class RootWindow(AbstractWindow):

    def __init__(self, display,
                 desktops=1, viewports=[1,1]):
        AbstractWindow.__init__(self, display, display.root_id)
        self.screen_width = display.screen_width
        self.screen_height = display.screen_height
        supporting_id = self.__supporting('mock-wm')
        properties = {
            # 1 desktop, 1 viewport
            self.atom('_NET_SUPPORTING_WM_CHECK'): [supporting_id],
            self.atom('_NET_CURRENT_DESKTOP'): [0],
            self.atom('_NET_DESKTOP_LAYOUT'): [0, 0, 1, 0],
            self.atom('_NET_DESKTOP_VIEWPORT'): [0, 0],
            self.atom('_NET_WORKAREA'): [0, 0, 
                                         self.screen_width, self.screen_height],
            self.atom('_NET_DESKTOP_GEOMETRY'): [self.screen_width * viewports[0],
                                                 self.screen_height * viewports[1]],
        }
        self.properties.update(properties)
        self._set_desktops(desktops)

    def __supporting(self, name):
        win = Window(self.display, name, Geometry(-100, -100, 1, 1, 0))
        return win.id


    def get_full_property(self, property, type, sizehint=10):
        if property == self.atom('_NET_CLIENT_LIST_STACKING'):
            return Value([win.id for win in self.display.windows_stack])
        if property == self.atom('_NET_CLIENT_LIST'):
            return Value([win.id for win in self.display.all_windows
                                 if win in self.windows_stack])
        if property == self.atom('_NET_ACTIVE_WINDOW'):
            if not self.display.windows_stack:
                return None
            active = self.display.windows_stack.pop()
            self.display.windows_stack.append(active)
            return Value([active.id])
        if property == self.atom('_NET_WORKAREA'):
            desktops = self._prop('_NET_NUMBER_OF_DESKTOPS')[0]
            return Value(self._prop('_NET_WORKAREA') * desktops)
        return AbstractWindow.get_full_property(self, property, type, sizehint)

    def send_event(self, event, event_mask=0, propagate=0, onerror=None):
        self.display.send_event(self, event, event_mask, propagate, onerror)

    def create_gc(self, **keys):
        raise NotImplementedError()

    def _set_desktops(self, desktops):
        self._prop('_NET_NUMBER_OF_DESKTOPS', [desktops])
        for win in self.display.windows_stack:
            desktop = win._prop('_NET_WM_DESKTOP')
            if desktop > desktops -1:
                win._prop('_NET_WM_DESKTOP', desktops -1)



# TODO: Use Xvfb to run different window managers headless for tests

