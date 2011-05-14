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

"""dbus_service.py - provides D-Bus service."""

import logging
import threading

# TODO: try catch imports
import dbus
from dbus.mainloop.glib import DBusGMainLoop
#from dbus.mainloop.qt import DBusQtMainLoop
import dbus.service

from pywo import actions
from pywo.core import WindowManager
from pywo.core import filters
from pywo.actions import manager
from pywo.actions import parser


__author__ = "Wojciech 'KosciaK' Pietrzok"


log = logging.getLogger(__name__)

WM = WindowManager()


class DBusService(dbus.service.Object):

    CONFIG = None

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='si', 
                         out_signature='s')
    def PerformAction(self, command, win_id):
        log.debug('DBUS: command="%s", win_id=%s' % (command, win_id))
        try:
            (options, args) = parser.parse_args(command.encode('utf-8'))
            log.info(options)
        except parser.ParserException, exc:
            log.exception('ParserException: %s' % exc)
            return 'ERROR: %s' % exc
        try:
            actions.perform(options, args, self.CONFIG, win_id)
            return ''
        except actions.ActionException, exc:
            log.exception('ActionException: %s' % exc)
            return 'ERROR: %s' % exc

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', 
                         out_signature='a(ssasasb)')
    def GetActions(self):
        return [(action.name, 
                 (action.__doc__ or '').split('\n')[0],
                 action.args, 
                 action.obligatory_args,
                 action.need_section) for action in manager.get_all()]

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def GetSections(self):
        return self.CONFIG.sections.keys()

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='s', 
                         out_signature='a(is)')
    def GetWindows(self, match):
        windows = WM.windows(filters.NORMAL_TYPE, match=match)
        return [(win.id, win.name) for win in windows]

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='i', 
                         out_signature='a(issiaiai(ii)(ii))')
    def GetWindowInfo(self, win_id):
        win = WM.get_window(win_id)
        geometry = win.geometry
        return [(win.id, 
                 win.class_name, win.name,
                 win.desktop,
                 win.type, win.state,
                 (geometry.x, geometry.y),
                 (geometry.width, geometry.height),
                )]

    # TODO: GetDesktops
    # TODO: GetDesktopInfo


dbus_loop = DBusGMainLoop(set_as_default=True)
#dbus_loop = DBusQtMainLoop(set_as_default=True)
session_bus = dbus.SessionBus(mainloop=dbus_loop)
name = dbus.service.BusName("net.kosciak.PyWO", session_bus)
service = DBusService(session_bus, "/net/kosciak/PyWO")

import gobject
gobject.threads_init()
loop = gobject.MainLoop()

# NOTE: not sure how to start Qt event loop in separate thread...
#from PyQt4 import QtCore
#loop = QtCore.QEventLoop()

def setup(config):
    service.CONFIG = config

def start():
    log.info('Starting PyWO D-Bus Service')
    thread = threading.Thread(name='D-Bus Service', target=loop.run)
    thread.start()

def stop():
    loop.quit()
    log.info('PyWO D-Bus Service stopped')

