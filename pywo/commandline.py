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

import logging
import optparse
from optparse import OptionParser, OptionGroup
import textwrap
import sys

from pywo import actions
import pywo.actions.parser


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


# Hack for textwrap so newline characters can be used
class TextWrapperWithNewLines:

    """TextWrapper that keeps newline characters."""

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


usage = '%prog [OPTIONS]\n   or: %prog ACTION [SECTION] [OPTIONS] [WINDOW NAME]'
version = 'PyWO - Python Window Organizer 0.3'
description = version
epilog = '' 
# TODO: add some examples of usage
# TODO: add author, webpage, license info
# TODO: store parser in threading.local to make it thread safe?
parser = OptionParser(usage=usage, version=version,
                      #description=description,
                      conflict_handler='resolve')
parser.set_defaults(action=None, section=None)

#
# Commandline options
#
parser.add_option('--help-more',
                  action='store_true', dest='help_more',
                  help='list all available ACTIONs')
parser.add_option('--debug', '--verbose',
                  action='store_true', dest='debug', default=False,
                  help='print debug informations')
parser.add_option('--config',
                  action='store', dest='config', default='~/.pyworc',
                  help='use given config FILE [default: %default]', 
                  metavar='FILE')
parser.add_option('--daemon',
                  action='store_true', dest='start_daemon', default=False,
                  help='run PyWO in daemon mode [default: %default]')
parser.add_option('--windows',
                  action='store_true', dest='list_windows', default=False,
                  help='list all windows: <id> <desktop> <state> <name>')
#parser.add_option('--desktops',
#                  action='store_true', dest='list_desktops', default=False,
#                  help='list dekstops') # TODO output format


#
# Group of options related to actions
#
action = OptionGroup(parser, 'Options for Actions', 
                     'If not provided, default values from config file will be used')

for option in pywo.actions.parser.parser.option_list:
    # NOTE: just copy options from actions.parser
    action.add_option(option)
parser.add_option_group(action)


#
# Groups for --help-more
#
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

window = OptionGroup(parser, 'WINDOW',
                     '''\
Title of the window. You can use part of window's title - PyWO will try to find \
best match. Windows on current desktop/viewport have higher priority.''')



def parse_args(args=sys.argv[1:]):
    return parser.parse_args(args)


def print_error(msg):
    parser.error(msg)


def print_help():
    parser.print_help()


def print_help_more(config):
    list = []
    for action in sorted(actions.manager.get_all(), 
                         key=lambda action: action.name):
        line = '%s\n  %s\n  %s' %  (action.name, 
                         (action.__doc__ or '').split('\n')[0],
                         ', '.join(action.obligatory_args).upper())
        if action.obligatory_args and action.optional_args:
            line += ', '
        if action.optional_args:
            line += '[%s]' % ', '.join(action.optional_args).upper()
        list.append(line)
    actions_list = OptionGroup(parser, 'ACTION', '\n'.join(list))
    parser.add_option_group(actions_list)
    sections_list = OptionGroup(parser, 'SECTION', 
                                '\n'.join(sorted(config.sections, reverse=True)))
    parser.add_option_group(sections_list)
    parser.add_option_group(gravity)
    parser.add_option_group(w_h)
    parser.add_option_group(window)
    parser.print_help()

