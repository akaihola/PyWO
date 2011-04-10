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

"""windows.py - classes and functions related to windows and window managers."""

import logging
import time

from Xlib import X, Xutil, Xatom

from pywo.core.basic import CustomTuple
from pywo.core.basic import Gravity, Position, Size, Geometry, Extents
from pywo.core.xlib import XObject


__author__ = "Wojciech 'KosciaK' Pietrzok, Antti Kaihola"


log = logging.getLogger(__name__)


class Type(object):

    """Enum of window, and window manager types."""

    # Window Types
    DESKTOP = XObject.atom('_NET_WM_WINDOW_TYPE_DESKTOP')
    DOCK = XObject.atom('_NET_WM_WINDOW_TYPE_DOCK')
    TOOLBAR = XObject.atom('_NET_WM_WINDOW_TYPE_TOOLBAR')
    MENU = XObject.atom('_NET_WM_WINDOW_TYPE_MENU')
    UTILITY = XObject.atom('_NET_WM_WINDOW_TYPE_UTILITY')
    SPLASH = XObject.atom('_NET_WM_WINDOW_TYPE_SPLASH')
    DIALOG = XObject.atom('_NET_WM_WINDOW_TYPE_DIALOG')
    NORMAL = XObject.atom('_NET_WM_WINDOW_TYPE_NORMAL')
    NONE = -1

    # Window manager Types
    COMPIZ = 1
    METACITY = 2
    KWIN = 3
    XFWM = 4
    OPENBOX = 5
    FLUXBOX = 6
    BLACKBOX = 7
    ICEWM = 8
    ENLIGHTMENT = 9
    WINDOW_MAKER = 10
    SAWFISH = 11
    PEKWM = 12
    UNKNOWN = -1


class Hacks(object):

    """List of hacks caused by EWMH, ICCCM implementation inconsistences."""

    DONT_TRANSLATE_COORDS = CustomTuple([Type.COMPIZ, 
                                         Type.FLUXBOX, 
                                         Type.WINDOW_MAKER])
    ADJUST_GEOMETRY = CustomTuple([Type.COMPIZ, 
                                   Type.KWIN, 
                                   Type.ENLIGHTMENT, 
                                   Type.ICEWM, 
                                   Type.BLACKBOX])
    PARENT_XY = CustomTuple([Type.FLUXBOX, 
                             Type.WINDOW_MAKER])
    CALCULATE_EXTENTS = CustomTuple([Type.BLACKBOX, 
                                     Type.ICEWM,
                                     Type.SAWFISH,
                                     Type.WINDOW_MAKER,
                                     Type.UNKNOWN])


class State(object):

    """Enum of window states."""

    # States described by EWMH
    MODAL = XObject.atom('_NET_WM_STATE_MODAL')
    STICKY = XObject.atom('_NET_WM_STATE_STICKY')
    MAXIMIZED_VERT = XObject.atom('_NET_WM_STATE_MAXIMIZED_VERT')
    MAXIMIZED_HORZ = XObject.atom('_NET_WM_STATE_MAXIMIZED_HORZ')
    MAXIMIZED = (MAXIMIZED_VERT, MAXIMIZED_HORZ)
    SHADED = XObject.atom('_NET_WM_STATE_SHADED')
    SKIP_TASKBAR = XObject.atom('_NET_WM_STATE_SKIP_TASKBAR')
    SKIP_PAGER = XObject.atom('_NET_WM_STATE_SKIP_PAGER')
    HIDDEN = XObject.atom('_NET_WM_STATE_HIDDEN')
    FULLSCREEN = XObject.atom('_NET_WM_STATE_FULLSCREEN')
    ABOVE = XObject.atom('_NET_WM_STATE_ABOVE')
    BELOW = XObject.atom('_NET_WM_STATE_BELOW')
    DEMANDS_ATTENTION = XObject.atom('_NET_WM_STATE_DEMANDS_ATTENTION')
    # Window managers specific states
    OB_UNDECORATED = XObject.atom('_OB_WM_STATE_UNDECORATED')


class Mode(object):

    """Enum of mode values. 
    
    Used while changing window's states.
    
    """

    UNSET = 0
    SET = 1
    TOGGLE = 2


class Window(XObject):

    """Window object."""

    # _NET_WM_DESKTOP returns this value when in STATE_STICKY
    ALL_DESKTOPS = 0xFFFFFFFF

    def __init__(self, win_id):
        XObject.__init__(self, win_id)

    @property
    def type(self):
        """Return tuple of window's type(s)."""
        type = self.get_property('_NET_WM_WINDOW_TYPE')
        if not type:
            return CustomTuple([Type.NONE])
        return CustomTuple(type.value)

    @property
    def state(self):
        """Return tuple of window's state(s)."""
        state = self.get_property('_NET_WM_STATE')
        if not state:
            return CustomTuple()
        return CustomTuple(state.value)

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
        """Return name of window's client machine."""
        client = self._win.get_wm_client_machine()
        return client

    @property
    def desktop(self):
        """Return desktop number the window is on.

        Returns 0xFFFFFFFF when "show on all desktops"

        """
        desktop = self.get_property('_NET_WM_DESKTOP')
        if not desktop:
            return 0
        return desktop.value[0]

    def set_desktop(self, desktop_id):
        """Move window to given desktop."""
        desktop_id = int(desktop_id)
        if desktop_id < 0:
            desktop_id = 0
        event_type = self.atom('_NET_WM_DESKTOP')
        data = [desktop_id, 
                0, 0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, event_type, mask)

    def __extents(self):
        """Return raw extents info."""
        extents = self.get_property('_NET_FRAME_EXTENTS')
        if extents:
            return extents.value
        else: 
            return ()

    @property
    def extents(self):
        """Return window's extents (decorations)."""
        extents = self.__extents()
        if not extents and self.wm_type in Hacks.CALCULATE_EXTENTS:
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
            parent_border = parent_geo.border_width*2
            left = win_geo.x + border_widths
            top = win_geo.y + border_widths
            right = parent_geo.width - win_geo.width - left + parent_border
            bottom = parent_geo.height - win_geo.height - top + parent_border
            extents = (left, right, top, bottom)
        elif not extents:
            extents = (0, 0, 0, 0)
        elif Type.OPENBOX in self.wm_type and \
             State.OB_UNDECORATED in self.state:
            # TODO: recognize 'retain border when undecorated' setting
            extents = (1, 1, 1, 1) # works for retain border
            #extents = (0, 0, 0, 0) # if border is not retained
        return Extents(*extents)

    def __geometry(self):
        """Return raw geometry info (translated if needed)."""
        geometry = self._win.get_geometry()
        if self.wm_type in Hacks.PARENT_XY:
            # Hack for Fluxbox, Window Maker
            parent_geo = self._win.query_tree().parent.get_geometry()
            geometry.x = parent_geo.x
            geometry.y = parent_geo.y
        if self.wm_type not in Hacks.DONT_TRANSLATE_COORDS:
            # if neeeded translate coords and multiply them by -1
            translated = self._translate_coords(geometry.x, geometry.y)
            return (-translated.x, -translated.y, 
                    geometry.width, geometry.height)
        return (geometry.x, geometry.y, 
                geometry.width, geometry.height)

    # TODO: strut - use _NET_WM_STRUT_PARTIAL with fallback to _NET_WM_STRUT

    @property
    def geometry(self):
        """Return window's geometry.

        (x, y) coordinates are the top-left corner of the window,
        relative to the left-top corner of current viewport.
        Position and size *includes* window's extents!
        Position is translated if needed.

        """
        x, y, width, height = self.__geometry()
        extents = self.extents
        if self.wm_type in Hacks.ADJUST_GEOMETRY:
            # Used in Compiz, KWin, E16, IceWM, Blackbox
            x -= extents.left
            y -= extents.top
        # FIXME: invalid geometry if border_width > 0 in raw_geometry
        return Geometry(x, y,
                        width + extents.horizontal,
                        height + extents.vertical)

    def set_geometry(self, geometry, on_resize=Gravity(0, 0)):
        """Move or resize window using provided geometry.

        Postion and size must include window's extents. 
        Position is relative to current viewport.

        """
        # FIXME: probabely doesn't work correctly with windows with border_width
        extents = self.extents
        x = geometry.x
        y = geometry.y
        width = geometry.width - extents.horizontal
        height = geometry.height - extents.vertical
        geometry_size = (width, height)
        current = self.__geometry()
        hints = self._win.get_wm_normal_hints()
        # This is a fix for WINE, OpenOffice and KeePassX windows
        if hints and hints.win_gravity == X.StaticGravity:
            x += extents.left
            y += extents.top
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

    def moveresize(self, geometry):
        """Works like set_geometry, but using _NET_MOVERESIZE_WINDOW

        This gives finer control: 
        - it allows to use gravity, so there are no problems with static windows
        - x, y coordinates includes window's extents
        - allow to move part of the window outside the workarea, while 
          configure will resize window to fit workarea

        WARNING! It seems that x,y coords must be unsigned ints!!! 
                 So it is not possible to move window to the left viewport!
                 Not sure it it is EWMH, Xlib, or python-xlib fault...
                 But it makes _NET_MOVERESIZE_WINDOW rather useless...

        """
        # TODO: check the border_width issue
        # TODO: what about max/min/incremental size?
        event_type = self.atom('_NET_MOVERESIZE_WINDOW')
        mask = X.SubstructureRedirectMask
        flags = 1 << 8 | 1 << 9 | 1 << 10 | 1 << 11 | 1 << 13
        data = [X.NorthWestGravity | flags,
                max([0, geometry.x]),
                max([0, geometry.y]),
                geometry.width,
                geometry.height]
        self.send_event(data, event_type, mask)

    def activate(self):
        """Make this window active (and unshade, unminimize)."""
        # NOTE: In Metacity this WON'T change desktop to window's desktop!
        event_type = self.atom('_NET_ACTIVE_WINDOW')
        mask = X.SubstructureRedirectMask
        data = [0, 0, 0, 0, 0]
        self.send_event(data, event_type, mask)
        # NOTE: Previously used for activating (didn't unshade/unminimize)
        #       Need to test if setting X.Above is needed in various WMs
        #self._win.set_input_focus(X.RevertToNone, X.CurrentTime)
        #self._win.configure(stack_mode=X.Above)

    def iconify(self, mode):
        """Iconify (minimize) window."""
        state = self._win.get_wm_state().state
        if mode == 1 or \
           mode == 2 and state == Xutil.NormalState:
            set_state = Xutil.IconicState
        if mode == 0 or \
           mode == 2 and state == Xutil.IconicState:
            set_state = Xutil.NormalState
        event_type = self.atom('WM_CHANGE_STATE')
        mask = X.SubstructureRedirectMask
        data = [set_state,
                0, 0, 0, 0]
        self.send_event(data, event_type, mask)

    def maximize(self, mode,
                 vert=State.MAXIMIZED_VERT, 
                 horz=State.MAXIMIZED_HORZ):
        """Maximize window (both vertically and horizontally)."""
        data = [mode, 
                horz,
                vert,
                0, 0]
        self.__change_state(data)

    def shade(self, mode):
        """Shade window (if supported by window manager)."""
        data = [mode, 
                State.SHADED,
                0, 0, 0]
        self.__change_state(data)

    def fullscreen(self, mode):
        """Make window fullscreen (if supported by window manager)."""
        data = [mode, 
                State.FULLSCREEN,
                0, 0, 0]
        self.__change_state(data)

    def sticky(self, mode):
        """Make window fullscreen (if supported by window manager)."""
        data = [mode, 
                State.STICKY,
                0, 0, 0]
        self.__change_state(data)

    def always_above(self, mode):
        """Make window always above others (if supported by window manager)."""
        data = [mode, 
                State.ABOVE,
                0, 0, 0]
        self.__change_state(data)

    def always_below(self, mode):
        """Make window always below others (if supported by window manager)."""
        data = [mode, 
                State.BELOW,
                0, 0, 0]
        self.__change_state(data)

    def reset(self, full=False):
        """Unmaximize (horizontally and vertically), unshade, unfullscreen."""
        self.iconify(Mode.UNSET)
        self.fullscreen(Mode.UNSET)
        self.maximize(Mode.UNSET)
        self.shade(Mode.UNSET)
        if full:
            self.sticky(Mode.UNSET)
            self.always_above(Mode.UNSET)
            self.always_below(Mode.UNSET)

    def close(self):
        """Close window."""
        event_type = self.atom('_NET_CLOSE_WINDOW')
        mask = X.SubstructureRedirectMask
        data = [0, 0, 0, 0, 0]
        self.send_event(data, event_type, mask)

    def destroy(self):
        """Unmap and destroy window."""
        self._win.unmap()
        self._win.destroy()

    def __change_state(self, data):
        """Send _NET_WM_STATE event to the root window."""
        event_type = self.atom('_NET_WM_STATE')
        mask = X.SubstructureRedirectMask
        self.send_event(data, event_type, mask)

    def blink(self):
        """For 0.075 second show border around window."""
        geo = self.geometry
        self.draw_rectangle(geo.x+2, geo.y+2, geo.width-4, geo.height-4, 4)
        self.flush()
        time.sleep(0.075)
        self.draw_rectangle(geo.x+2, geo.y+2, geo.width-4, geo.height-4, 4)
        self.flush()

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return not self.id == other.id

    def __str__(self):
        return '<Window id=%s>' % (self.id,)

    def debug_info(self, logger=log):
        """Print full window's info, for debug use only."""
        win = self._win
        logger.info('ID=%s' % self.id)
        logger.info('Client_machine=%s' % self.client_machine)
        logger.info('Name=%s' % self.name)
        logger.info('Class=%s' % self.class_name)
        logger.info('Type=%s' % [self.atom_name(e) for e in self.type])
        logger.info('State=%s' % [self.atom_name(e) for e in self.state])
        logger.info('WM State=%s' % win.get_wm_state())
        logger.info('Desktop=%s' % self.desktop)
        logger.info('Extents=%s' % self.extents)
        logger.info('Extents_raw=%s' % [str(e) for e in self.__extents()])
        logger.info('Geometry=%s' % self.geometry)
        logger.info('Geometry_raw=%s' % getattr(win.get_geometry(), '_data'))
        geometry = self._win.get_geometry()
        translated = self._translate_coords(geometry.x, geometry.y)
        logger.info('Geometry_translated=%s' % getattr(translated, '_data'))
        logger.info('Parent=%s %s' % (self.parent_id, self.parent))
        logger.info('Normal_hints=%s' % getattr(win.get_wm_normal_hints(), 
                                                '_data'))
        #log.info('Hints=%s' % self._win.get_wm_hints())
        logger.info('Attributes=%s' % getattr(win.get_attributes(), '_data'))
        logger.info('Query_tree=%s' % getattr(win.query_tree(), '_data'))


class WindowManager(XObject):
    
    """Window Manager (or root window in X programming terms).
    
    WindowManager's self._win refers to the root window.
    It is a Singleton.

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
        manager.update_type()
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
    def type(self):
        """Return tuple of window manager's type(s)."""
        return self.wm_type
    
    def update_type(self):
        """Update window manager's type."""
        recognize = {'compiz': Type.COMPIZ, 'metacity': Type.METACITY,
                     'kwin': Type.KWIN, 'xfwm': Type.XFWM, 
                     'openbox': Type.OPENBOX, 'fluxbox': Type.FLUXBOX,
                     'blackbox': Type.BLACKBOX, 'icewm': Type.ICEWM,
                     'e1': Type.ENLIGHTMENT, 'sawfish': Type.SAWFISH,
                     'window maker': Type.WINDOW_MAKER, 'pekwm': Type.PEKWM,
                    }
        name = self.name.lower()
        XObject.set_wm_type(Type.UNKNOWN)
        for name_part, wm_type in recognize.items():
            if name_part in name:
                XObject.set_wm_type(wm_type)

    @property
    def desktops(self):
        """Return number of desktops."""
        # _NET_NUMBER_OF_DESKTOPS, CARDINAL/32
        number = self.get_property('_NET_NUMBER_OF_DESKTOPS')
        if not number:
            return 1
        return number.value[0]

    @property
    def desktop_names(self):
        """Return list of desktop names."""
        # _NET_DESKTOP_NAMES, UTF8_STRING[]
        names = self.get_property('_NET_DESKTOP_NAMES')
        if not names:
            return []
        return names.value.decode('utf-8').split('\x00')[:-1]

    # TODO: set_desktop_name ???
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
        event_type = self.atom('_NET_CURRENT_DESKTOP')
        data = [desktop_id, 
                0, 0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, event_type, mask)

    @property
    def desktop_size(self):
        """Return Size of current desktop."""
        # _NET_DESKTOP_GEOMETRY width, height, CARDINAL[2]/32
        geometry = self.get_property('_NET_DESKTOP_GEOMETRY').value
        return Size(geometry[0], geometry[1])

    # TODO: set_desktop_size?!?, or set_viewports(columns, rows)

    @property
    def desktop_layout(self):
        """Return desktops layout, as set by pager."""
        # _NET_DESKTOP_LAYOUT, orientation, columns, rows, starting_corner 
        #                      CARDINAL[4]/32
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
        # NOTE: this will return geometry for first, not current!
        #       what about all workareas, not only the current one?
        # TODO: multi monitor support by returning workarea for current monitor?
        return Geometry(workarea[0], workarea[1], 
                        workarea[2], workarea[3])

    # TODO: Consider change of method name
    def nearest_screen_geometry(self, geometry):
        """Return geometry of the screen best matching the given rectangle"""
        screens_by_intersection = ((screen & geometry, screen)
                                   for screen in self.get_xinerama_geometries())
        screens_by_area = ((intersection.area, screen)
                           for intersection, screen in screens_by_intersection
                           if intersection)
        largest_area, screen = sorted(screens_by_area)[-1]
        return screen & self.workarea_geometry

    @property
    def viewport_position(self):
        """Return position of current viewport. 

        If desktop is large it might be divided into several viewports.

        """
        # _NET_DESKTOP_VIEWPORT x, y, CARDINAL[][2]/32
        viewport = self.get_property('_NET_DESKTOP_VIEWPORT').value
        # TODO: Might not work correctly on all WMs
        return Position(viewport[0], viewport[1])

    def set_viewport_position(self, x, y):
        """Change current viewport."""
        event_type = self.atom('_NET_DESKTOP_VIEWPORT')
        data = [x, 
                y, 
                0, 0, 0]
        mask = X.PropertyChangeMask
        self.send_event(data, event_type, mask)

    # TODO: set_viewport(viewport) similar to set_desktop(desktop)
    # TODO: viewport_layout

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

    @staticmethod
    def get_window(window_id):
        """Return Window with given id."""
        window = Window(window_id)
        return window

    def windows_ids(self, stacking=True):
        """Return list of all windows' ids (newest/on top first)."""
        if stacking:
            windows_ids = self.get_property('_NET_CLIENT_LIST_STACKING').value
        else:
            windows_ids = self.get_property('_NET_CLIENT_LIST').value
        windows_ids.reverse()
        return windows_ids

    def windows(self, filter=None, match='', stacking=True):
        """Return list of all windows (newest/on top first)."""
        # TODO: regexp matching?
        windows_ids = self.windows_ids(stacking)
        windows = [Window(win_id) for win_id in windows_ids]
        if filter:
            windows = [window for window in windows if filter(window)]
        if match:
            windows = self.__name_matcher(windows, match)
        return windows

    def __name_matcher(self, windows, match):
        """Filter and sort windows with matching name or class name."""
        match = match.strip().lower()
        # TODO: match.decode('utf-8') if not unicode
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
                window.desktop == Window.ALL_DESKTOPS):
                points += 50
                if geometry.x < workarea.x2 and \
                   geometry.x2 > workarea.x and \
                   geometry.y < workarea.y2 and \
                   geometry.y2 > workarea.y:
                    points += 100
            return (window, points)
        windows = map(mapper, windows)
        windows.sort(key=lambda win: win[1], reverse=True)
        windows = [win for win, points in windows if points]
        return windows

    def unregister_all(self):
        """Unregister all event handlers for all windows."""
        self._unregister_all()

    def __str__(self):
        return '<WindowManager id=%s>' % (self.id,)

    def debug_info(self, logger=log):
        """Print full windows manager's info, for debug use only."""
        logger.info('WindowManager=%s' % self.name)
        logger.info('Desktops=%s, current=%s' % (self.desktops, self.desktop))
        logger.info('Names=[%s]' % ', '.join(self.desktop_names))
        logger.info('Layout: orientation=%s, cols=%s, rows=%s, corner=%s' % \
                    self.desktop_layout)
        logger.info('Desktop=%s' % self.desktop_size)
        logger.info('Viewport=%s' % self.viewport_position)
        logger.info('Workarea=%s' % self.workarea_geometry)

