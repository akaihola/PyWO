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

"""pywo.py - main module for PyWO."""

import atexit
import logging
from logging.handlers import RotatingFileHandler
import signal
import sys
import threading
import time

from core import WM
from events import KeyPressHandler
from config import CONFIG
from actions import ACTIONS, register_action, ActionException


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.3"


SERVICES = []

def register_services():
    global SERVICES
    SERVICES = []
    if CONFIG.keyboard_service:
        import keyboard_service
        SERVICES.append(keyboard_service)
    if CONFIG.dbus_service:
        import dbus_service
        SERVICES.append(dbus_service)


def setup_loggers():
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


def start():
    """Setup and start all services."""
    CONFIG.load('.pyworc')
    register_services()
    for service in SERVICES:
        service.start()
    logging.info('PyWO ready and running!')
    while len(threading.enumerate()) > 1: 
        time.sleep(0.1)


def stop():
    """Stop all services."""
    for service in SERVICES:
        service.stop()


@register_action(name='reload')
def reload(*args):
    """Stop services, reload configuration file, and start again."""
    # TODO: add filepath as argument so it is possible to source any file as command
    logging.info('Reloading PyWO...')
    stop()
    start()


@register_action(name='exit')
def exit_pywo(*args):
    """Stop sevices, and exit PyWO."""
    logging.info('Exiting PyWO...')
    stop()


#atexit.register(stop)

def interrupt_handler(signal, frame):
    logging.error('Interrupted!')
    stop()

signal.signal(signal.SIGINT, interrupt_handler)

if __name__ == '__main__':
    setup_loggers()
    logging.info('Starting PyWO...')
    start()

