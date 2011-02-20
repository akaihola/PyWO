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

from pywo import services


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


# NOTE: Use logger in 'pywo.services.*' hierarchy!
log = logging.getLogger('pywo.services.' + __name__)


class Clock(services.Service):

    def __init__(self):
        self.timer = None
        self.minutes = 0

    def setup(self, config):
        log.debug('Setting up clock')
        self.minutes = 0
        self.timer = threading.Timer(60, self._show_time)

    def start(self):
        log.info('Starting clock')
        self.timer.start()

    def stop(self):
        log.info('Stopping clock')
        self.timer.cancel()

    def _show_time(self):
        self.minutes += 1
        log.info('You are using PyWO for %s minute(s)' % self.minutes)
        self.timer = threading.Timer(60, self._show_time)
        self.timer.start()


