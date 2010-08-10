#
# Copyright 2010, Wojciech 'KosciaK' Pietrzok
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""config.py encapsulates dealing with configuration file."""

import logging
import re
import os
from ConfigParser import ConfigParser

from core import Size, Gravity, WindowManager


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
        self.settings = {}
        self.mappings = {}
        self.__config.read([os.path.join(os.path.dirname(__file__), 'pyworc'),
                            os.path.join(os.path.expanduser('~'), '.pyworc')])
        keys = dict(self.__config.items('KEYS'))
        self.__config.remove_section('KEYS')
        self.__parse_settings()
        if self.__config.has_option('SETTINGS', 'layout'):
            layout = self.__config.get('SETTINGS', 'layout')
            self.__config.read(os.path.join(os.path.dirname(__file__), layout))
        self.__config.remove_section('SETTINGS')
        for section in self.__config.sections():
            data = dict(self.__config.items(section))
            direction = self.__parse_gravity(data['direction'])
            position  = self.__parse_gravity(data['position'])
            if 'gravity' in data:
                gravity = self.__parse_gravity(data['gravity'])
            else:
                gravity = position
            sizes = self.__parse_size(data['widths'], data['heights'])
            mask_key = keys[section]
            mask_code = WindowManager.str2keycode(keys['put'], mask_key)
            self.mappings[mask_code] = ['put', [position]]
            mask_code = WindowManager.str2keycode(keys['grid_width'], mask_key)
            self.mappings[mask_code] = ['grid', 
                                        [position, gravity, sizes, 'width']]
            mask_code = WindowManager.str2keycode(keys['grid_height'], mask_key)
            self.mappings[mask_code] = ['grid', 
                                        [position, gravity, sizes, 'height']]
            mask_code = WindowManager.str2keycode(keys['float'], mask_key)
            self.mappings[mask_code] = ['float', [direction]]
            mask_code = WindowManager.str2keycode(keys['expand'], mask_key)
            self.mappings[mask_code] = ['expand', [direction]]
            mask_code = WindowManager.str2keycode(keys['shrink'], mask_key)
            self.mappings[mask_code] = ['shrink', [direction]]
            self.__config.remove_section(section)

        mask_code = WindowManager.str2keycode(keys['reload'])
        self.mappings[mask_code] = ['reload', []]
        mask_code = WindowManager.str2keycode(keys['exit'])
        self.mappings[mask_code] = ['exit', []]
        mask_code = WindowManager.str2keycode(keys['debug'])
        self.mappings[mask_code] = ['debug', []]
        logging.info('Configuration loaded.')


