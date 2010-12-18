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
import dbus.service

import actions
import commandline
from core import Window, WindowManager


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


WM = WindowManager()


class DBusService(dbus.service.Object):

    CONFIG = None

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='si', out_signature='s')
    def PerformAction(self, command, win_id):
        logging.debug('DBUS: command="%s", win_id=%s' % (command, win_id))
        try:
            (options, args) = commandline.parse_args(command.split())
        except commandline.ParserException, e:
            logging.error('ParserException: %s' % e)
            return 'ERROR: %s' % e
        try:
            actions.perform(args, self.CONFIG, options, win_id)
            WM.flush()
            return ''
        except actions.ActionException, e:
            logging.error('ActionException: %s' % e)
            return 'ERROR: %s' % e

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='a(ssasas)')
    def GetActions(self):
        return [(action.name, (action.__doc__ or '').split('\n')[0],
                 action.args, action.obligatory_args) for action in actions.all()]

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def GetSections(self):
        return self.CONFIG.sections.keys()

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='s', out_signature='a(is)')
    def GetWindows(self, match):
        windows = WM.windows(lambda window: 
                                    Window.TYPE_NORMAL in window.type,
                             match=match)
        return [(win.id, win.name) for win in windows]

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='i', out_signature='a(issi(ii)(ii))')
    def GetWindowInfo(self, win_id):
        win = Window(win_id)
        geometry = win.geometry
        return [(win.id, 
                 win.class_name, win.name,
                 win.desktop
                 (geometry.x, geometry.y),
                 (geometry.width, geometry.height)) for win in windows]

    # TODO: GetDesktops
    # TODO: GetDesktopInfo


DBusGMainLoop(set_as_default=True)
session_bus = dbus.SessionBus()
name = dbus.service.BusName("net.kosciak.PyWO", session_bus)
service = DBusService(session_bus, "/net/kosciak/PyWO")

import gobject
gobject.threads_init()
loop = gobject.MainLoop()

def setup(config):
    service.CONFIG = config

def start():
    logging.info('Starting PyWO D-Bus Service')
    thread = threading.Thread(name='D-Bus Service', target=loop.run)
    thread.start()

def stop():
    loop.quit()
    logging.info('PyWO D-Bus Service stopped')

