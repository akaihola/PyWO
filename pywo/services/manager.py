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

from pywo.services import Service


__author__ = "Wojciech 'KosciaK' Pietrzok"


log = logging.getLogger(__name__)

__SERVICES = set()


def load_local(config):
    """Load Services from local modules."""
    log.debug('Loading local services modules...')
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [filename[0:-3] for filename in os.listdir(path) 
                              if filename.endswith('_service.py')]
    for module in modules:
        module_name = 'pywo.services.%s' % module
        if not (getattr(config, module, False) or \
                getattr(config, module_name, False)):
            continue
        log.debug("Importing <module '%s'>" % module_name)
        try:
            __import__(module_name)
            __SERVICES.add(sys.modules[module_name])
        except Exception, e:
            log.exception('Exception %s while importing <module %s>' % \
                          (e, module_name))


def load_plugins(config):
    """Load third party pywo.services plugins."""
    log.debug('Loading third-party services modules...')
    try:
        from pkg_resources import iter_entry_points
    except ImportError:
        return
    for entry_point in iter_entry_points('pywo.services'):
        if not (getattr(config, entry_point.module_name) or \
                getattr(config, entry_point.name)):
            continue
        log.debug('Loading plugin %s' % entry_point.name)
        try:
            plugin = entry_point.load()
        except Exception, e:
            log.exception('Exception %e while loading %s' % \
                          (e, entry_point.name))
            continue
        if isinstance(plugin, type) and \
           (issubclass(plugin, Service) or \
            (hasattr(plugin, 'setup') and \
             hasattr(plugin, 'start') and \
             hasattr(plugin, 'stop'))):
            # subclass of Service, or implementing all needed methods
            __SERVICES.add(plugin())
        elif hasattr(plugin, 'setup') and \
             hasattr(plugin, 'start') and \
             hasattr(plugin, 'stop'):
            # module implementing all needed functions
            __SERVICES.add(plugin)


def load(config):
    """Load Services from local modules and plugins."""
    __SERVICES.clear()
    load_local(config)
    load_plugins(config)
    log.debug('Registered %s services' % (len(__SERVICES),))


def remove(service):
    """Remove servive."""
    if service in __SERVICES:
        __SERVICES.remove(service)


def get_all():
    """Return set of all services."""
    return __SERVICES

