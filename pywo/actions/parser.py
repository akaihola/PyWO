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

"""parser.py - parses actions from commandline."""

import logging
from optparse import OptionParser, OptionValueError
import sys

from pywo.core import Size, Gravity, Position
from pywo import actions


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class ParserException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Parser(OptionParser):

    """OptionParser that raises exception on errors."""

    def error(self, msg):
        raise ParserException(msg)


def largs_callback(option, opt_str, value, parser):
    """Set action adn section options."""
    # FIXME: this callback is not called if 'action section' without other options!
    if parser.largs and not parser.values.action:
        setattr(parser.values, 'action', parser.largs.pop(0))
    if parser.largs and not parser.values.section:
        setattr(parser.values, 'section', parser.largs.pop(0))


def gravity_callback(option, opt_str, value, parser):
    """Parse gravity option to Gravity."""
    largs_callback(option, opt_str, value, parser)
    try:
        gravity = Gravity.parse(value)
    except ValueError:
        msg = 'option %s: error parsing Gravity value: %s' % (opt_str, value)
        raise OptionValueError(msg)
    setattr(parser.values, option.dest, gravity)
    if option.dest == 'gravity' and not parser.values.position:
        setattr(parser.values, 'position', gravity)
    if option.dest == 'gravity' and not parser.values.direction:
        setattr(parser.values, 'direction', gravity)
    if option.dest == 'position' and not parser.values.gravity:
        setattr(parser.values, 'gravity', gravity)


def size_callback(option, opt_str, value, parser):
    """Parse width, height, size options to Size."""
    largs_callback(option, opt_str, value, parser)
    # TODO: allow relative size, and absolute size
    try:
        if option.dest == 'width':
            width = Size.parse_value(value)
            size = Size(width, 0)
        elif option.dest == 'height':
            height = Size.parse_value(value)
            size = Size(0, height)
        elif option.dest == 'size':
            size = Size.parse(*value)
    except (ValueError, TypeError):
        msg = 'option %s: error parsing Size value: %s' % (opt_str, value)
        raise OptionValueError(msg)
    setattr(parser.values, option.dest, size)


def position_callback(option, opt_str, value, parser):
    """Parse x, y, coords options to Position."""
    largs_callback(option, opt_str, value, parser)
    # TODO: parse it to int, might be relative size
    try:
        if option.dest == 'x':
            size = Position(value, 0)
        elif option.dest == 'y':
            size = Position(0, value)
        elif option.dest == 'coords':
            size = Position(*value)
    except (ValueError, TypeError):
        msg = 'option %s: error parsing Position value: %s' % (opt_str, value)
        raise OptionValueError(msg)
    setattr(parser.values, option.dest, size)


parser = Parser(conflict_handler='resolve')
parser.set_defaults(action=None, section=None)

parser.add_option('--id',
                  action='store', dest='win_id', default='', 
                  help='perform action on window with given ID',
                  metavar='ID')

parser.add_option('-a', '--add', '--set', '--on',
                  action='store_const', const=1, dest='mode', default=2,
                  help='actions\'s MODE [default: toggle]')
parser.add_option('-r', '--remove', '--unset', '--off',
                  action='store_const', const=0, dest='mode', default=2,
                  help='actions\'s MODE [default: toggle]')
                  
parser.add_option('-g', '--gravity',
                  action='callback', dest='gravity', type='string',
                  callback=gravity_callback,
                  help='window\'s gravity\nIf not set POSITION will be used')
parser.add_option('-d', '--direction',
                  action='callback', dest='direction', type='string',
                  callback=gravity_callback,
                  help='direction of an action\nIf not set GRAVITY will be used')
parser.add_option('-p', '--position',
                  action='callback', dest='position', type='string',
                  callback=gravity_callback,
                  help='window\'s position on screen\nIf not set GRAVITY will be used')

parser.add_option('-w', '--width',
                  action='callback', dest='width', type='string',
                  callback=size_callback,)
parser.add_option('-h', '--height',
                  action='callback', dest='height', type='string', 
                  callback=size_callback,)
parser.add_option('-s', '--size',
                  action='callback', dest='size', type='string',
                  callback=size_callback, nargs=2,
                  help='[default: current size]',
                  metavar='WIDTH HEIGHT')

'''
# TODO: To be used with move, resize actions
parser.add_option('-x',
                  action='callback', dest='x', type='string',
                  callback=position_callback,)
parser.add_option('-y',
                  action='callback', dest='y', type='string',
                  callback=position_callback,)
parser.add_option('-c', '--coords',
                  action='callback', dest='coords', type='string',
                  callback=position_callback, nargs=2,
                  metavar='X Y')
'''

parser.add_option('-i', '--invert',
                  action='store_true', dest='invert_on_resize', default=True,
                  help='invert gravity when resizing windows with incremental size [default: %default]')
parser.add_option('-I', '--no-invert',
                  action='store_false', dest='invert_on_resize', 
                  help='DON\'T invert gravity when resizing windows with incremental size')

parser.add_option('-V', '--vertical-first',
                  action='store_true', dest='vertical_first', default=True,
                  help='[default: %default]')
parser.add_option('-H', '--horizontal-first',
                  action='store_false', dest='vertical_first')


def parse_args(args=sys.argv[1:]):
    return parser.parse_args(args)


