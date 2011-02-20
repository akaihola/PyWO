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

"""cycle_actions.py - PyWO actions - switch and cycle windows."""

import logging

from pywo.actions import Action, TYPE_FILTER
from pywo.core import WindowManager
from pywo.core.events import PropertyNotifyHandler


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()


class ActiveChangedEventHandler(PropertyNotifyHandler):

    """Listen for change of active window."""

    def __init__(self, action):
        PropertyNotifyHandler.__init__(self)
        self.action = action

    def property(self, event):
        if event.atom_name == '_NET_ACTIVE_WINDOW':
            active_win = WM.active_window()
            self.action(active_win)


class SwitchCycleAction(Action):

    """Switch or cycle windows."""

    def __init__(self, name, doc, keep_active):
        Action.__init__(self, name=name, doc=doc, filter=TYPE_FILTER)
        self.args = ['window']
        self.keep_active = keep_active
        self.__handler = ActiveChangedEventHandler(self)
        self.__from_win_id = 0

    def perform(self, win, **kwargs):
        """Perform action on window and with given arguments."""
        from_win = WM.get_window(self.__from_win_id)
        from_geo, to_geo = from_win.geometry, win.geometry
        from_win.set_geometry(to_geo)
        win.set_geometry(from_geo)
        if self.keep_active:
            from_win.activate()
        else:
            win.activate()
        self.__from_win_id = 0

    def __call__(self, win, **kwargs):
        active_win = WM.active_window()
        if not win == active_win:
            # TODO: What about 'switch win1' from some dbus client window?
            self.__from_win_id = active_win.id
        if self.__from_win_id:
            WM.unregister(self.__handler)
            Action.__call__(self, win)
        else:
            self.__from_win_id = win.id
            WM.register(self.__handler)


SwitchCycleAction('switch', 
                  "Switch placement of windows (keep focus on current window).",
                  True).register()

SwitchCycleAction('cycle', 
                  "Switch contents of windows (focus on new window).",
                  False).register()

