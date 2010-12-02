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
from commandline import parse_args
from core import WM, Window


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


class DBusService(dbus.service.Object):

    CONFIG = None

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='si', out_signature='s')
    def PerformCommand(self, command, win_id):
        logging.debug('DBUS: command="%s", win_id=%s' % (command, win_id))
        # TODO: try/except parser exceptions?
        (options, args) = parse_args(command)
        try:
            actions.perform(args, config, options)
            WM.flush()
            return ''
        except actions.ActionException, e:
            # TODO: What about other exceptions?
            #       parser exceptions?
            return str(e)

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def Commands(self):
        return [action.name for action in actions.all()]

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def Sections(self):
        return self.CONFIG.sections.keys()

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='s', out_signature='a(is)')
    def Windows(self, match):
        windows = WM.windows(lambda window: 
                                    Window.TYPE_NORMAL in window.type,
                             match=match)
        return [(win.id, win.name.decode('utf-8')) for win in windows]


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

