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

from core import WM, Window
from config import CONFIG
from actions import ACTIONS, ActionException


def get_args(action, config, section=None):
    kwargs = {}
    for arg in action.args:
        if section:
            value = getattr(section, arg, getattr(config, arg, None))
        else:
            value = getattr(config, arg, None)
        if value:
            kwargs[arg] = value
    return kwargs


class DBusService(dbus.service.Object):

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='si', out_signature='s')
    def PerformCommand(self, command, win_id):
        logging.debug('DBUS: command="%s", win_id=%s' % (command, win_id))
        cmd = command.strip().split(' ')
        try:
            action = ACTIONS[cmd[0]]
        except:
            logging.error('Unrecognized action: %s' % cmd[0])
            return 'Unrecognized action: %s' % cmd[0]

        if ('direction' in action.args or \
            'position' in action.args or \
            'gravity' in action.args) and \
           len(cmd) > 1 and \
           cmd[1] in CONFIG.sections:
            section = CONFIG.sections[cmd[1]]
            match = u' '.join(cmd[2:])
        elif ('direction' in action.args or \
              'position' in action.args or \
              'gravity' in action.args) and \
             len(cmd) > 1 and \
             cmd[1] not in CONFIG.sections:
            logging.error('Unrecognized section: %s' % cmd[1])
            return 'Unrecognized section: %s' % cmd[1]
        elif ('direction' in action.args or \
              'position' in action.args or \
              'gravity' in action.args):
            logging.error('No section specified')
            return 'No section specified'
        else:
            section = None
            match = u' '.join(cmd[1:])

        if win_id > 0:
            window = Window(win_id)
        elif match:
            try:
                windows = WM.windows(lambda window: 
                                            Window.TYPE_NORMAL in window.type,
                                     match=match)
                window = windows[0]
            except:
                logging.error('Can\'t find window matching: %s' % match)
                return 'Can\'t find window matching: %s' % match
        else:
            window = WM.active_window()

        logging.debug(window.name)
        kwargs = get_args(action, CONFIG, section)
        logging.debug('%s(%s)' % 
                      (action.name, 
                      ', '.join(['%s=%s' % (key, str(value)) 
                                 for key, value in kwargs.items()])))
        try:
            action(window, **kwargs)
        except ActionException, e:
            logging.error(e)
        except Exception, e:
            logging.exception(e)
            return e
        WM.flush()
        return ''

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def Commands(self):
        return ACTIONS

    @dbus.service.method("net.kosciak.PyWO", 
                         in_signature='', out_signature='as')
    def Sections(self):
        return CONFIG.sections

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
object = DBusService(session_bus, "/net/kosciak/PyWO")

import gobject
gobject.threads_init()
loop = gobject.MainLoop()


def start():
    logging.info('Starting PyWO D-Bus Service')
    t = threading.Thread(target=loop.run)
    t.start()

def stop():
    loop.quit()
    logging.info('PyWO D-Bus Service stopped')

