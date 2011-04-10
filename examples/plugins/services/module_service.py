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

"""module_service.py - example of pywo.service plugin."""

import logging
import threading

from pywo.core import WindowManager
from pywo.core.events import PropertyNotifyHandler

__author__ = "Wojciech 'KosciaK' Pietrzok"


# NOTE: Use logger in 'pywo.services.*' hierarchy!
log = logging.getLogger('pywo.services.' + __name__)


def active_window_changed(event):
    if event.atom_name == '_NET_ACTIVE_WINDOW':
        log.info('Active window changed to: %s' % WM.active_window().name)

WM = WindowManager()
HANDLER = PropertyNotifyHandler(active_window_changed)


def setup(config):
    log.debug('Setting up module_service')


def start():
    log.info('Starting module_service example')
    WM.register(HANDLER)


def stop():
    log.info('Starting module_service example')
    WM.unregister(HANDLER)

