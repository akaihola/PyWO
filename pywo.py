#!/usr/bin/env python
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

"""pywo.py is the main module for PyWO."""

import itertools
import logging
from logging.handlers import RotatingFileHandler
import sys

from core import WindowManager
from events import KeyPressHandler
from config import Config
from actions import ACTIONS, register_action


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.3"


WM = WindowManager()
CONFIG = Config()


@register_action('exit')
def _close(*args):
    """Ungrab keys and exit PyWO."""
    HANDLER.ungrab_keys(WM)
    logging.info('Exiting....')
    sys.exit()


@register_action('reload')
def _reload(*args):
    """Reload configuration file."""
    global HANDLER
    CONFIG.load('pyworc')
    HANDLER.ungrab_keys(WM)
    HANDLER.set_keys(CONFIG.mappings.keys(), 
                     CONFIG.numlock,
                     CONFIG.capslock)
    HANDLER.grab_keys(WM)



def key_press(event):
    """Event handler method for KeyPressEventHandler."""
    logging.debug('EVENT: type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, event.keycode, event.modifiers))
    if not (event.modifiers, event.keycode) in CONFIG.mappings:
        logging.error('Unrecognized key!')
        return
    window = WM.active_window()
    logging.debug(window.name)
    action, args = CONFIG.mappings[event.modifiers, event.keycode]
    logging.debug('%s%s' % 
                  (action, 
                  ['%s: %s' % (a.__class__.__name__, str(a)) for a in args]))
    try:
        window.shade(window.MODE_UNSET)
        ACTIONS[action](window, *args)
    except Exception, err:
        logging.exception(err)
    WM.flush()


HANDLER = KeyPressHandler(key_press)

def start():
    """Setup and start PyWO."""
    logging.debug('>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<')
    logging.info('Starting PyWO...')
    CONFIG.load()
    HANDLER.set_keys(CONFIG.mappings.keys(), 
                     CONFIG.numlock,
                     CONFIG.capslock)
    HANDLER.grab_keys(WM)
    logging.info('PyWO ready and running!')


if __name__ == '__main__':
    # Setup logging ...
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    format = '%(levelname)s: %(filename)s %(funcName)s(%(lineno)d): %(message)s'
    rotating = RotatingFileHandler('/tmp/PyWO.log', 'a', 1024*50, 2)
    rotating.setFormatter(logging.Formatter(format))
    rotating.setLevel(logging.DEBUG)
    logger.addHandler(rotating)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    # ... and start PyWO
    start()

