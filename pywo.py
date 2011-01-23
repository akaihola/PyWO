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

import logging
from logging.handlers import RotatingFileHandler

import actions
import commandline
from config import Config
from core import Window, WindowManager
from services import daemon
import filters


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"
__version__ = "0.3"


def setup_loggers(debug=False):
    """Setup file, and console loggers."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    format = '%(levelname)s: %(filename)s(%(lineno)d) %(funcName)s: %(message)s'
    rotating = RotatingFileHandler('/tmp/PyWO.log', 'a', 1024*50, 2)
    rotating.setFormatter(logging.Formatter(format))
    rotating.setLevel(logging.DEBUG)
    logger.addHandler(rotating)
    console = logging.StreamHandler()
    if debug:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)
    logger.addHandler(console)


if __name__ == '__main__':
    # parse commandline
    try:
        (options, args) = commandline.parse_args()
    except commandline.ParserException, e:
        commandline.print_error(str(e))
    # setup loggers
    setup_loggers(options.debug)

    config = Config(options.config)

    if options.start_daemon:
        logging.info('Starting PyWO...')
        daemon.setup(config)
        daemon.start(loop=True)
    elif options.list_windows:
        WM = WindowManager()
        windows = WM.windows(filters.NORMAL_TYPE)
        for window in windows:
            geometry = window.geometry
            state = window.state
            win_desktop = window.desktop
            desktop = [win_desktop, -1][Window.STATE_STICKY in state or \
                                        win_desktop == Window.ALL_DESKTOPS]
            if Window.STATE_HIDDEN in state and \
               not Window.STATE_SHADED in state:
                state_flags = 'i'
            elif Window.STATE_FULLSCREEN in state:
                state_flags = 'F'
            elif Window.STATE_MAXIMIZED_HORZ in state and \
                 Window.STATE_MAXIMIZED_VERT in state:
                state_flags = 'M'
            elif Window.STATE_MAXIMIZED_VERT in state:
                state_flags = 'V'
            elif Window.STATE_MAXIMIZED_HORZ in state:
                state_flags = 'H'
            else:
                state_flags = ' '
            state_flags += [' ', 's'][Window.STATE_SHADED in state]# and \
                                      #not Window.STATE_HIDDEN in state]
            print '%s %s %s %s' % (window.id, desktop, state_flags, window.name)
    elif args or options.action:
        try:
            actions.perform(args, config, options)
        except actions.ActionException, e:
            # TODO: What about other exceptions?
            #       parser exceptions?
            commandline.print_error(e)
    elif options.help_more:
        commandline.print_help_more(config)
    else:
        commandline.print_help()

