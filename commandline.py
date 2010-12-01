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

"""commandline.py - parses commandline options."""

from copy import copy
import optparse
from optparse import Option, OptionParser, OptionGroup, OptionValueError
import textwrap
import sys

from core import Size, Gravity


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


# Hack for textwrap so I can use newline characters
class TextWrapperWithNewLines:
    @staticmethod
    def wrap(text, width=70, **kw):
        result = []
        for line in text.split("\n"):
            result.extend(textwrap.wrap(line, width, **kw))
        return result
    @staticmethod
    def fill(text, width=70, **kw):
        result = []
        for line in text.split("\n"):
            result.append(textwrap.fill(line, width, **kw))
        return "\n".join(result)

optparse.textwrap = TextWrapperWithNewLines()


def check_gravity(option, opt, value):
    # TODO: use gravity_callback
    try:
        return Gravity.parse(value)
    except ValueError:
        raise OptionValueError(
            'option %s: error parsing Gravity with value: %s' % (opt, value))


def size_callback(option, opt_str, value, parser):
    # TODO: use parser.largs to set .action, .section
    # TODO: -w and -h are not working... only --size (since 'size' attribute is neede by actions, not 'width' and 'height'
    try:
        if opt_str == '-w' or opt_str == '--width':
            size = Size.parse(value, '0')
        elif opt_str == '-h' or opt_str == '--height':
            size = Size.parse('0', value)
        elif opt_str == '-s' or opt_str == '--size':
            size = Size.parse(*value)
    except ValueError, TypeError:
        raise OptionValueError(
            'option %s: error parsing Size with value: %s' % (opt_str, value))
    setattr(parser.values, option.dest, size)


class GravitySizeOption(Option):
    TYPES = Option.TYPES + ('gravity',)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER['gravity'] = check_gravity


usage = '%prog [OPTIONS]\n   or: %prog ACTION [SECTION] [OPTIONS] WINDOW'
version='PyWO - Python Window Organizer 0.3'
description = version
epilog = '' 
# TODO: add some examples of usage
# TODO: add author, webpage, license info
parser = OptionParser(usage=usage, version=version,
                      #description=description,
                      conflict_handler='resolve',
                      option_class=GravitySizeOption)

parser.add_option('--actions',
                  action='store_true', dest='list_actions',
                  help='list all available ACTIONs')
parser.add_option('--debug', '--verbose',
                  action='store_true', dest='debug', default=False,
                  help='print debug informations')
parser.add_option('-c', '--config',
                  action='store', dest='config', default='~/.pyworc',
                  help='use given config FILE [default: %default]', 
                  metavar='FILE')
parser.add_option('--daemon',
                  action='store_true', dest='start_daemon', default=False,
                  help='run PyWO in daemon mode - register keyboard shortcuts, start D-Bus Service (if turned on in config file) [default: %default]')

action = OptionGroup(parser, 'Options for Actions', 
                     'If not provided, default values from config file will be used')
# TODO: use gravity_callback for gravity, direction, position (so I can use parser.values to get already parsed values)
#       if not direction: direction = gravity
#       if not position: position = gravity
#       if position and not gravity: gravity = position
#       like in config
action.add_option('-g', '--gravity',
                  action='store', dest='gravity', type='gravity',
                  help='use given gravity\nIf not set POSITION will be used')
action.add_option('-d', '--direction',
                  action='store', dest='direction', type='gravity',
                  help='use given direction\nIf not set GRAVITY will be used')
action.add_option('-p', '--position',
                  action='store', dest='position', type='gravity',
                  help='use given position\nIf not set GRAVITY will be used')
action.add_option('-w', '--width',
                  action='callback', dest='widths',
                  help='use given width sizes', type='string', 
                  callback=size_callback,
                  metavar='WIDTH')
action.add_option('-h', '--height',
                  action='callback', dest='heights', type='string', 
                  callback=size_callback,
                  help='use given height sizes',
                  metavar='HEIGHT')
action.add_option('-s', '--size',
                  action='callback', dest='sizes', nargs=2, type='string',
                  callback=size_callback,
                  help='use given sizes - combines WIDTH, and SIZE (used by grid_width, grid_heigt)',
                  metavar='SIZE')

action.add_option('-i', '--invert',
                  action='store_true', dest='invert_on_resize', default=True,
                  help='invert gravity resizing windows with incremental size [default: %default]')
action.add_option('-I', '--no-invert',
                  action='store_false', dest='invert_on_resize', 
                  help='DON\'T invert gravity resizing windows with incremental size')
action.add_option('-V', '--vertical-first',
                  action='store_true', dest='vertical_first', default=True,
                  help='[default: %default]')
action.add_option('-H', '--horizontal-first',
                  action='store_false', dest='vertical_first')
parser.add_option_group(action)

gravity = OptionGroup(parser, 'GRAVITY',
                      '''\
Predefined names:
  TOP_LEFT, TL, UP_LEFT, UL, NW = 0,0
  TOP, T, UP, U, N = 0.5,0
  TOP_RIGHT, TR, UP_RIGHT, UR, NE = 1,0
  LEFT, L = 0,0.5
  MIDDLE, M, CENTER, C = 0.5,0.5
  RIGHT, R = 1,0.5
  BOTTOM_LEFT, BL, DOWN_LEFT, DL, SW = 0,1
  BOTTOM, B, DOWN, D = 0.5,1
  BOTTOM_RIGHT, BR, DOWN_RIGHT, DR, SE = 1,1
Custom Gravity:
  Provide values from 0.0 to 1.0 for x, and y. 
  Example: --gravity FULL,THIRD*2 --position 0.5,1.0/3*2''')
parser.add_option_group(gravity)

w_h = OptionGroup(parser, 'WIDTH, HEIGHT',
                  '''\
Predefined names:
  QUARTER, Q = 0.25
  THIRD, T = 1.0/3
  HALF, H  = 0.5
  FULL, F = 1
Custom size:
  Provide value from 0.0 to 1.0 
  Example: --width THIRD*2 --height 1.0/3*2''')
parser.add_option_group(w_h)

size = OptionGroup(parser, 'SIZE',
                   '''\
SIZE combines WIDTH and HEIGHT in one option. 
Example: --size H T*2''')
parser.add_option_group(size)

window = OptionGroup(parser, 'WINDOW',
                     '''\
Title of the window. You can use part of window's title - PyWO will try to find \
best match. Windows on current desktop/viewport have higher priority.''')
parser.add_option_group(window)



def parse_args(args=sys.argv[1:]):
    return parser.parse_args(args)


def print_error(msg):
    parser.error(msg)


def print_help():
    parser.print_help()


if __name__ == '__main__':
    options, arguments = parser.parse_args()
    print options, arguments

