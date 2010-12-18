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

"""actions - core PyWO actions classes and functions."""

import logging
import os.path
import sys

from core import Window, WindowManager


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


WM = WindowManager()

TYPE = 1
STATE = 2


class ActionException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Action(object):

    _ACTIONS = {} # {action.name: action, }
    _LOADED = False

    def __init__(self, action, name,
                 check=[], unshade=False):
        self.name = name
        self.args = action.func_code.co_varnames[1:action.func_code.co_argcount]
        if action.func_defaults:
            self.obligatory_args = self.args[:-len(action.func_defaults)]
        else:
            self.obligatory_args = self.args
        self.__action = action
        self.__check = check
        self.__unshade = unshade
        self.__doc__ = action.__doc__

    def __call__(self, win, **kwargs):
        if self.__check:
            self.__check_type_state(win)
        if self.__unshade:
            win.shade(win.MODE_UNSET)
            win.flush()
        self.__action(win, **kwargs)
        # history
        # _GRIDED ??

    def __check_type_state(self, win):
        type = win.type
        if TYPE in self.__check and \
           (Window.TYPE_DESKTOP in type or \
            Window.TYPE_DOCK in type or \
            Window.TYPE_SPLASH in type):
            error = "Can't perform %s on window of this type." % self.name
            raise ActionException(error)

        state = win.state
        if STATE in self.__check and \
           (Window.STATE_FULLSCREEN in state or \
            (Window.STATE_MAXIMIZED_HORZ in state and \
             Window.STATE_MAXIMIZED_VERT in state)):
            error = "Can't perform %s on maximized/fullscreen window." % self.name
            raise ActionException(error)


def register(name, check=[], unshade=False):
    """Register function as PyWO action with given name."""
    def register_action(action):
        doc = action.__doc__
        action = Action(action, name, check, unshade)
        Action._ACTIONS[name] = action
        return action
    name = name.lower()
    return register_action


@register(name='debug', check=[TYPE])
def _debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    logging.info('-= Window Manager =-')
    WindowManager().debug_info()
    logging.info('-= Current Window =-')
    win.debug_info()
    logging.info('-= Move with same geometry =-')
    geo =  win.geometry
    win.set_geometry(geo)
    win.sync()
    logging.info('New geometry=%s' % win.geometry)
    logging.info('-= End of debug =-')


def __load():
    """Autodiscover actions."""
    path = os.path.dirname(os.path.abspath(__file__))
    modules = [file[0:-3] for file in os.listdir(path) 
                          if file.endswith('.py')]
    for module in modules:
        __import__('actions.%s' % module)
    Action._LOADED = True


def get(name):
    """Return action with given name."""
    if not Action._LOADED:
        __load()
    return Action._ACTIONS.get(name.lower(), None)


def all():
    """Return set of all actions."""
    if not Action._LOADED:
        __load()
    return Action._ACTIONS.values()


def get_args(action, config, section=None, options=None):
    # FIXME: --widths, --heights don't work right now, 
    #        --sizes is used instead (from options, or default from section)
    kwargs = {}
    for arg in action.args:
        for obj in [options, section, config]:
            value = getattr(obj, arg, None)
            if value is not None:
                kwargs[arg] = value
                break
    return kwargs


def perform(args, config, options={}, win_id=0):
    if not options.action and len(args) == 0:
        raise ActionException('No ACTION provided')
    name = options.action or args.pop(0)
    action = get(name)
    if not action:
        raise ActionException('Invalid ACTION name: %s' % name)
    need_section = 'direction' in action.args or \
                   'position' in action.args or \
                   'gravity' in action.args
    if need_section and (args or options.section):
        name = options.section or args.pop(0)
        section = config.section(name)
        if not section:
            raise ActionException('Invalid SECTION name: %s' % name)
    else:
        section = None

    missing_args = []
    for arg in action.obligatory_args:
        if not getattr(options, arg):
            missing_args.append(arg.upper())
    if need_section and not section and missing_args:
        raise ActionException('Missing %s' % ', '.join(missing))

    if win_id or options.win_id:
        # TODO: try/except invalid options.win_id, or non existatn Window
        window = Window(win_id or int(options.win_id, 0))
    elif args:
        # TODO: check system encoding?
        args = [arg.decode('utf-8') for arg in args]
        match = u' '.join(args)
        windows = WM.windows(lambda window: Window.TYPE_NORMAL in window.type,
                             match=match)
        try:
            window = windows[0]
        except:
            raise ActionException('No WINDOW matching name: %s' % match)
    else:
        window = WM.active_window()

    kwargs = get_args(action, config, section, options)
    logging.debug('%s(%s)' % 
                  (action.name, 
                  ', '.join(['%s=%s' % (key, str(value)) 
                             for key, value in kwargs.items()])))
    action(window, **kwargs)


