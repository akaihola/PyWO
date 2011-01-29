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

"""filters.py - window filters."""

import logging

from pywo.core import Window, WindowManager, Type, State


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class IncludeType(object):

    """Return only windows with specified type."""

    def __init__(self,
                 desktop=False, dock=False, 
                 toolbar=False, menu=False,
                 utility=False, splash=False,
                 dialog=False, normal=False):
        self.allowed_types = []
        if desktop:
            self.allowed_types.append(Type.DESKTOP)
        if dock:
            self.allowed_types.append(Type.DOCK)
        if toolbar:
            self.allowed_types.append(Type.TOOLBAR)
        if menu:
            self.allowed_types.append(Type.MENU)
        if utility:
            self.allowed_types.append(Type.UTILITY)
        if splash:
            self.allowed_types.append(Type.SPLASH)
        if dialog:
            self.allowed_types.append(Type.DIALOG)
        if normal:
            self.allowed_types.append(Type.NORMAL)

    def __call__(self, window):
        type = window.type
        for allowed_type in self.allowed_types:
            if allowed_type in type:
                return True
        return False

NORMAL_TYPE = IncludeType(normal=True)


class ExcludeType(object):
    def __init__(self,
                 desktop=False, dock=False, 
                 toolbar=False, menu=False,
                 utility=False, splash=False,
                 dialog=False, normal=False):
        self.not_allowed_types = []
        if desktop:
            self.not_allowed_types.append(Type.DESKTOP)
        if dock:
            self.not_allowed_types.append(Type.DOCK)
        if toolbar:
            self.not_allowed_types.append(Type.TOOLBAR)
        if menu:
            self.not_allowed_types.append(Type.MENU)
        if utility:
            self.not_allowed_types.append(Type.UTILITY)
        if splash:
            self.not_allowed_types.append(Type.SPLASH)
        if dialog:
            self.not_allowed_types.append(Type.DIALOG)
        if normal:
            self.not_allowed_types.append(Type.NORMAL)

    def __call__(self, window):
        type = window.type
        for not_allowed_type in self.not_allowed_types:
            if not_allowed_type in type:
                return False
        return True


class IncludeState(object):

    """Return only windows with specified state."""

    def __init__(self,
                 modal=False, sticky=False,
                 maximized=False, maximized_vert=False, maximized_horz=False,
                 fullscreen=False,
                 shaded=False, hidden=False, 
                 skip_pager=False, skip_taskbar=False,
                 demands_attention = False):
        self.allowed_states = []
        if modal:
            self.allowed_states.append(State.MODAL)
        if sticky:
            self.allowed_states.append(State.STICKY)
        if maximized or maximized_vert:
            self.allowed_states.append(State.MAXIMIZED_VERT)
        if maximized or maximized_horz:
            self.allowed_states.append(State.MAXIMIZED_HORZ)
        if fullscreen:
            self.allowed_states.append(State.FULLSCREEN)
        if shaded:
            self.allowed_states.append(State.SHADED)
        if hidden:
            self.allowed_states.append(State.HIDDEN)
        if skip_pager:
            self.allowed_states.append(State.SKIP_PAGER)
        if skip_taskbar:
            self.allowed_states.append(State.SKIP_TASKBAR)
        if demands_attention:
            self.allowed_states.append(State.DEMANDS_ATTENTION)

    def __call__(self, window):
        for state in window.state:
            if state in self.allowed_states:
                return True
        return False


class ExcludeState(object):

    """Return only windows without specified type."""

    def __init__(self,
                 modal=False, sticky=False,
                 maximized=False, maximized_vert=False, maximized_horz=False,
                 fullscreen=False,
                 shaded=False, hidden=False, 
                 skip_pager=False, skip_taskbar=False,
                 demands_attention = False):
        self.modal = modal
        self.sticky = sticky
        self.maximized = maximized
        self.maximized_vert = maximized_vert
        self.maximized_horz = maximized_horz
        self.fullscreen = fullscreen
        self.shaded = shaded
        self.hidden = hidden
        self.skip_pager = skip_pager
        self.skip_taskbar = skip_taskbar
        self.demands_attention = demands_attention

    def __call__(self, window):
        state = window.state
        if self.modal and State.MODAL in state:
            return False
        if self.sticky and State.STICKY in state:
            return False
        if self.maximized and \
           State.MAXIMIZED_VERT in state and State.MAXIMIZED_HORZ in state:
            return False
        if self.maximized and State.MAXIMIZED_VERT in state:
            return False
        if self.maximized and State.MAXIMIZED_HORZ in state:
            return False
        if self.fullscreen and State.FULLSCREEN in state:
            return False
        if self.shaded and State.SHADED in state:
            return False
        if self.hidden and State.HIDDEN in state:
            return False
        if self.skip_pager and State.SKIP_PAGER in state:
            return False
        if self.skip_taskbar and State.SKIP_TASKBAR in state:
            return False
        if self.demands_attention and State.DEMANDS_ATTENTION in state:
            return False
        return True

NORMAL_STATE = ExcludeState(modal=True, shaded=True, hidden=True, 
                            maximized=True, fullscreen=True)

class Desktop(object):

    """Return only windows on specified (or current) desktop."""

    def __init__(self, desktop=None):
        self.desktop = desktop

    def __call__(self, window):
        if self.desktop is None:
            self.desktop = WindowManager().desktop
        desktop = self.desktop
        win_desktop = window.desktop
        return win_desktop == desktop or \
               win_desktop == Window.ALL_DESKTOPS

DESKTOP = Desktop()


class Workarea(Desktop):

    """Return only windows on current workarea."""

    def __init__(self):
        Desktop.__init__(self)
        self.workarea = None

    def __call__(self, window):
        if not Desktop.__call__(self, window):
            return False
        if self.workarea is None:
            self.workarea = WindowManager().workarea_geometry
        geometry = window.geometry
        return geometry.x < self.workarea.x2 and \
               geometry.x2 > self.workarea.x and \
               geometry.y < self.workarea.y2 and \
               geometry.y2 > self.workarea.y

WORKAREA = Workarea()


class AND(object):

    """Combine filters."""

    def __init__(self, *filters):
        self.filters = filters

    def __call__(self, window):
        for filter in self.filters:
            if not filter(window):
                return False
        return True

NORMAL = AND(NORMAL_TYPE, NORMAL_STATE)

NORMAL_ON_WORKAREA = AND(NORMAL_TYPE, NORMAL_STATE, WORKAREA)

