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

"""manager.py - load, register, and manage actions."""

import logging
import os.path
import sys


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

_ACTIONS = {}


def register(action):
    """Register new Action object."""
    if action.name in _ACTIONS:
        log.warning('Action with name %s already registered!' % action.name)
    _ACTIONS[action.name] = action
    log.debug('Registered action %s' % action.name)


def load():
    """Load actions from modules and plugins."""
    # import all local modules
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [filename[0:-3] for filename in os.listdir(path) 
                              if filename.endswith('_actions.py')]
    for module in modules:
        module_name = 'pywo.actions.%s' % module
        if not module_name in sys.modules:
            log.debug('Importing module %s' % module_name)
            __import__(module_name)
    # TODO: use pkg_resources and pywo.actions entry point


def get(name):
    """Return action with given name or None."""
    return _ACTIONS.get(name, None)


def get_all():
    """Return set of all actions."""
    return _ACTIONS.values()

