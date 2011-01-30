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

"""manager.py - load, and manage services."""

import logging
import os.path
import sys


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

_SERVICES = set()


def load(config):
    _SERVICES.clear()
    # import all local modules
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [filename[0:-3] for filename in os.listdir(path) 
                              if filename.endswith('_service.py')]
    for module in modules:
        module_name = 'pywo.services.%s' % module
        if getattr(config, module) or getattr(config, module_name):
            log.debug('Importing module %s' % module_name)
            __import__(module_name)
            _SERVICES.add(sys.modules[module_name])
    # TODO: use pkg_resources and pywo.actions entry point


def get_all():
    """Return set of all services."""
    return _SERVICES

