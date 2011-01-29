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

"""services - provides services autodiscovery.

All services must provide three functions:
setup(config) - setup service using provided Config instance;
start() - start service. New thread should be started, and main loop provided;
stop() - stop service. All EventHandlers should be unregistered, thread stopped.

"""

import logging
import os.path
import sys


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


def all(config):
    """Return all services."""
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [filename[0:-3] for filename in os.listdir(path) 
                              if filename.endswith('_service.py')]
    log.debug('Found services: %s' % ', '.join(modules))
    services = []
    for module in modules:
        if getattr(config, module):
            __import__('pywo.services.%s' % module)
            services.append(sys.modules['pywo.services.%s' % module])
    return services

