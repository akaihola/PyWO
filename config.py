#
# PyWO - Python Windows Organizer
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

"""config.py encapsulates dealing with configuration file."""

import logging
import re
import os
from ConfigParser import ConfigParser

from core import Size, Gravity
from core import WindowManager as WM


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


OFF = 0
ON = 1
IGNORE = 2


class Config(object):

    """Config class holding all data from configuration files."""

    # Predefined sizes that can be used in config files
    __SIZES = {'FULL': '1.0',
               'HALF': '0.5',
               'THIRD': '1.0/3',
               'QUARTER': '0.25'}

    # Predefined gravities, that can be used in config files
    __GRAVITIES = {'TOP_LEFT': Gravity(0, 0),
                   'TOP': Gravity(0.5, 0),
                   'TOP_RIGHT': Gravity(1, 0),
                   'LEFT': Gravity(0, 0.5),
                   'MIDDLE': Gravity(0.5, 0.5),
                   'RIGHT': Gravity(1, 0.5),
                   'BOTTOM_LEFT': Gravity(0, 1),
                   'BOTTOM': Gravity(0.5, 1),
                   'BOTTOM_RIGHT': Gravity(1, 1)}

    # Pattern matching simple calculations with floating numbers
    __PATTERN = re.compile('^[ 0-9\.\+-/\*]+$')

    def __init__(self):
        self.__config = ConfigParser()
        self.settings = {}
        self.mappings = {}
        self.ignore = []

    def __parse_size(self, widths, heights):
        """Parse widths and heights strings and return Size object.

        It can be float number (value will be evaluatedi, so 1.0/2 is valid) 
        or predefined value in SIZES.

        """
        for old, new in self.__SIZES.items():
            widths = widths.replace(old, new)
            heights = heights.replace(old, new)
        width = [eval(width) for width in widths.split(', ')
                             if self.__PATTERN.match(width)]
        height = [eval(height) for height in heights.split(', ')
                               if self.__PATTERN.match(height)]
        return Size(width, height)

    def __parse_gravity(self, gravity):
        """Parse gravity string and return Gravity object.

        It can be one of predefined GRAVITIES, or x and y values (floating
        numbers or those described in SIZES).

        """
        if gravity in self.__GRAVITIES:
            return self.__GRAVITIES[gravity]
        for old, new in self.__SIZES.items():
            gravity = gravity.replace(old, new)
        x, y = [eval(xy) for xy in gravity.split(', ')
                         if self.__PATTERN.match(xy)]
        return Gravity(x, y)

    def __parse_settings(self):
        """Parse SETTINGS section of the config file"""
        for key, value in self.__config.items('SETTINGS'):
            value = value.lower()
            if value in ['1', 'yes', 'on', 'true']:
                self.settings[key] = ON
            elif value == 'ignore':
                self.settings[key] = IGNORE
            else:
                self.settings[key] = OFF

    def load(self, filename='.pyworc'):
        """Load configuration file"""
        logging.info('Loading configuration file...')
        # Reset values
        self.settings = {}
        self.mappings = {}
        self.ignore = []
        # Load config file
        self.__config.read([os.path.join(os.path.dirname(__file__), 'pyworc'),
                            os.path.join(os.path.expanduser('~'), '.pyworc')])
        keys = dict(self.__config.items('KEYS'))
        self.__config.remove_section('KEYS')
        # Parse SETTINGS section
        self.__parse_settings()
        if self.__config.has_option('SETTINGS', 'layout'):
            # Load layout definition
            layout = self.__config.get('SETTINGS', 'layout')
            self.__config.read([os.path.join(os.path.dirname(__file__), layout),
                                os.path.join(os.path.expanduser('~'), layout)])
        if self.__config.has_option('SETTINGS', 'ignore_actions'):
            # Parse ignore_actions setting
            ignore = self.__config.get('SETTINGS', 'ignore_actions')
            self.ignore = ignore.split(', ')
        self.__config.remove_section('SETTINGS')
        # Parse every section
        for section in self.__config.sections():
            data = dict(self.__config.items(section))
            ignore = []
            mask_key = keys[section]
            if 'ignore_actions' in data:
                ignore = data['ignore_actions'].split(', ')
            if not (('float' in self.ignore or 'float' in ignore) and \
                    ('expand' in self.ignore or 'expand' in ignore) and \
                    ('shrink' in self.ignore or 'shrink' in ignore)):
                # No need to parse if float, expand, shrink are ignored
                direction = self.__parse_gravity(data['direction'])
            if not (('put' in self.ignore or 'put' in ignore) and \
                    ('grid' in self.ignore or 'grid' in ignore or \
                     ('grid_width' in self.ignore or \
                      'grid_width' in ignore) and \
                     ('grid_height' in self.ignore or \
                      'grid_height' in ignore))):
                # No need to parse these if put and grid are ignored
                position  = self.__parse_gravity(data['position'])
                if 'gravity' in data:
                    gravity = self.__parse_gravity(data['gravity'])
                else:
                    gravity = position
                sizes = self.__parse_size(data['widths'], data['heights'])

            # Parse put, grid actions if not ignored
            if not ('put' in self.ignore or 'put' in ignore):
                key = WM.str2keycode(keys['put'], mask_key)
                self.mappings[key] = ['put', [position]]
            if not ('grid' in self.ignore or 'grid' in ignore or \
                    'grid_width' in ignore or 'grid_width' in ignore):
                key = WM.str2keycode(keys['grid_width'], mask_key)
                self.mappings[key] = ['grid', 
                                     [position, gravity, sizes, 'width']]
            if not ('grid' in self.ignore or 'grid' in ignore or \
                    'grid_height' in self.ignore or 'grid_height' in ignore):
                key = WM.str2keycode(keys['grid_height'], mask_key)
                self.mappings[key] = ['grid', 
                                     [position, gravity, sizes, 'height']]

            # Parse float, expand, shrink actions if not ignored
            if not ('float' in self.ignore or 'float' in ignore):
                key = WM.str2keycode(keys['float'], mask_key)
                self.mappings[key] = ['float', [direction]]
            if not ('expand' in self.ignore or 'expand' in ignore):
                key = WM.str2keycode(keys['expand'], mask_key)
                self.mappings[key] = ['expand', [direction]]
            if not ('shrink' in self.ignore or 'shrink' in ignore):
                key = WM.str2keycode(keys['shrink'], mask_key)
                self.mappings[key] = ['shrink', [direction]]
                self.__config.remove_section(section)

        # Parse switch, cycle if not ignored
        if not 'switch' in self.ignore:
            key = WM.str2keycode(keys['switch'])
            self.mappings[key] = ['switch_cycle', [True]]
        if not 'cycle' in self.ignore:
            key = WM.str2keycode(keys['cycle'])
            self.mappings[key] = ['switch_cycle', [False]]

        # Parse reload, exit, debug. Can not be ignored!
        key = WM.str2keycode(keys['reload'])
        self.mappings[key] = ['reload', []]
        key = WM.str2keycode(keys['exit'])
        self.mappings[key] = ['exit', []]
        key = WM.str2keycode(keys['debug'])
        self.mappings[key] = ['debug', []]
        logging.info('Configuration loaded.')


