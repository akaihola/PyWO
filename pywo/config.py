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

"""config.py - loading and storing configuration data."""

import logging
import os
from ConfigParser import ConfigParser

from pywo.core import Gravity, Size


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class _Section(object):

    """Section configuration."""

    def __init__(self, config, section, key):
        self.key = key
        data = dict(config._config.items(section))
        self.ignored = set()
        if 'ignore_actions' in data:
            self.ignored.update(data.get('ignore_actions', '').split(', '))
        self.ignored.update(config.ignored)
        if 'grid' in self.ignored:
            self.ignored.update('grid_width', 'grid_height')

        self.gravity = Gravity.parse(data.get('gravity', ''))
        self.direction = Gravity.parse(data.get('direction', ''))
        if not self.direction:
            self.direction = self.gravity
        self.position  = Gravity.parse(data.get('position', ''))
        if not self.position:
            self.position = self.gravity
        elif self.position and not self.gravity:
            self.gravity = self.position
        self.size = Size.parse(data.get('widths', ''), 
                               data.get('heights', ''))


class Config(object):

    """Config class holding all data from configuration files."""

    OFF = 0
    ON = 1
    IGNORE = 2

    def __init__(self, filename=''):
        self._config = ConfigParser()
        self.keys = {} # {'action_name': 'key', }
        self.ignored = set()
        self.sections = {} # {section.name: section, }
        self.aliases = {} # {alias: section|action, }
        self.filename = filename
        self.load(filename)

    def __parse_settings(self):
        """Parse SETTINGS section of the config file"""
        for key, value in self._config.items('SETTINGS'):
            value = value.lower()
            if value in ['1', 'yes', 'on', 'true']:
                setattr(self, key, self.ON)
            elif value == 'ignore':
                setattr(self, key, self.IGNORE)
            elif value:
                setattr(self, key, self.OFF)

    def load(self, filename):
        """Load configuration file"""
        log.debug('Loading configuration file %s' % filename)
        self.filename = filename
        # Load config file (load default first)
        self._config.read(
            [os.path.join('/', 'etc', 'pywo', 'pyworc'),
             os.path.join(os.path.dirname(__file__), '..', 'etc', 'pyworc'),
             os.path.join(os.path.expanduser('~'), '.config', 'pywo', 'pyworc'),
             os.path.join(os.path.expanduser('~'), '.pyworc')])
        # Get keys settings
        self.keys = dict(self._config.items('KEYS'))
        self._config.remove_section('KEYS')
        # Get aliases
        self.aliases = dict(self._config.items('ALIASES'))
        self.aliases = dict([[alias, name.lower()] for alias, name 
                                                   in self.aliases.items()])
        self._config.remove_section('ALIASES')
        # Parse SETTINGS section
        if self._config.has_option('SETTINGS', 'layout'):
            # Load layout definition
            layout = self._config.get('SETTINGS', 'layout')
            self._config.read(
                [os.path.join('/', 'etc', 'pywo', 'layouts', layout),
                 os.path.join('/', 'etc', 'pywo', layout),
                 os.path.join(os.path.dirname(__file__), '..', 'etc', layout),
                 os.path.join(os.path.dirname(__file__), '..', 'etc', 
                              'layouts', layout),
                 os.path.join(os.path.expanduser('~'), '.config', 
                              'pywo', 'layouts', layout),
                 os.path.join(os.path.expanduser('~'), '.config', 
                              'pywo', layout),
                 os.path.join(os.path.expanduser('~'), layout)])
            self._config.remove_option('SETTINGS', 'layout')
        self.ignored = set()
        if self._config.has_option('SETTINGS', 'ignore_actions'):
            # Parse ignore_actions setting
            ignored = self._config.get('SETTINGS', 'ignore_actions')
            self.ignored = set(ignored.split(', '))
            self._config.remove_option('SETTINGS', 'ignore_actions')
        if 'grid' in self.ignored:
            self.ignored.update('grid_width', 'grid_height')
        self.__parse_settings()
        self._config.remove_section('SETTINGS')
        # Parse every section
        self.sections = {}
        for section in self._config.sections():
            key = self.keys.pop(section, None)
            try:
                self.sections[section.lower()] = _Section(self, section, key)
            except Exception, e:
                log.exception('Invalid section %s: %s', (section, e))
            self._config.remove_section(section)

        log.debug('Loaded configuration file')

    def section(self, name):
        """Return Section with given name."""
        name = self.alias(name)
        return self.sections.get(name.lower(), None)

    def alias(self, name):
        """Return real action or section name for alias.

        If name is not an alias return original name.

        """
        return self.aliases.get(name, name)

