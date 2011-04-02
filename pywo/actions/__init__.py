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

"""actions - core PyWO actions classes and functions.

PyWO uses pkg_resources for actions plugins discovery. 
When writing your own actions please use 'pywo.actions' entry point group, 
and use module name as an value for entry point. 
Check /examples/plugins/actions for an example of third-party actions plugin.

"""

import logging

from pywo.core import Window, WindowManager, Type, State, Mode
from pywo.core import filters
from pywo.actions import manager


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()

TYPE_FILTER = filters.STANDARD_TYPE
STATE_FILTER = filters.ExcludeState(State.MAXIMIZED, State.FULLSCREEN)
TYPE_STATE_FILTER = filters.AND(TYPE_FILTER, STATE_FILTER)


class ActionException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class Action(object):

    """Base class for all PyWO actions.
    
    Actions should be treated as callable.

    One instance of the Action will be created and used for all calls. 
    Since PyWO is a multithreaded app Action objects should be stateless.

    """

    # TODO: implement pre and post action_hooks

    def __init__(self, name='', doc='', filter=None, unshade=False):
        self.name = name
        self.__doc__ = doc or self.__doc__
        self.__filter = filter or filters.ALL_FILTER
        self.__unshade = unshade
        args = self.perform.func_code.co_varnames
        self.args = args[2:self.perform.func_code.co_argcount] 
        self.obligatory_args = self.args[:-len(self.perform.func_defaults or [])]

    def perform(self, win, **kwargs):
        """Perform action on window and with given arguments.
        
        This method must be implemented by Action subclasses.
        
        """
        raise NotImplementedError()

    @property
    def optional_args(self):
        """Return list of optional arguments."""
        optional_args = [arg for arg in self.args 
                             if arg not in self.obligatory_args]
        return optional_args

    @property
    def need_section(self):
        return 'direction' in self.args or \
               'position' in self.args or \
               'gravity' in self.args

    def get_kwargs(self, config, section=None, options=None):
        kwargs = {}
        for arg in self.args:
            for obj in [options, section, config]:
                value = getattr(obj, arg, None)
                if value is not None:
                    kwargs[arg] = value
                    break
        return kwargs

    def __call__(self, win, **kwargs):
        """Perform action on window and with given arguments."""
        log.debug('%s win=%s, kwargs={%s}' % 
                  (self, win,
                  ', '.join(["'%s':%s" % (key, value) 
                             for key, value in kwargs.items()])))
        self.check_filter(win)
        self.pre_perform(win, **kwargs)
        try:
            self.perform(win, **kwargs)
        except Exception, e:
            log.exception('Exception %s while performing %s' % (e, self))
        self.post_perform(win, **kwargs)

    def check_filter(self, win):
        """Check if window matches filter."""
        if not self.__filter(win):
            error = "Can't perform %s on this window." % self.name
            raise ActionException(error)

    def pre_perform(self, win, *args, **kwargs):
        """Called before performing an action."""
        # TODO: call pre_action_hooks
        if self.__unshade:
            win.shade(Mode.UNSET)
            win.flush()

    def post_perform(self, win, *args, **kwargs):
        """Called after performing an action."""
        win.sync()
        # TODO: call post_action_hooks

    def register(self):
        """Register instance of Action as PyWO action."""
        manager.register(self)

    def __str__(self):
        return "<Action '%s'>" % (self.name,)


class SimpleActionWrapper(Action):

    """Wrapper for simple function based actions."""

    def __init__(self, action, name, filter=None, unshade=False):
        Action.__init__(self, name=name, filter=filter, unshade=unshade)
        self.args = action.func_code.co_varnames[1:action.func_code.co_argcount]
        self.obligatory_args = self.args[:-len(action.func_defaults or [])]
        self.__doc__ = action.__doc__
        self.__action = action

    def perform(self, win, **kwargs):
        """Perform action on window and with given arguments."""
        self.__action(win, **kwargs)


def register(name, filter=filters.ALL_FILTER, unshade=False):
    """Register function or Action subclass as PyWO action with given name."""
    def register_action(action):
        """Registers action."""
        if isinstance(action, type) and issubclass(action, Action):
            action = action(name=name, filter=filter, unshade=unshade)
        elif callable(action):
            action = SimpleActionWrapper(action, name.lower(), filter, unshade)
        manager.register(action)
        return action
    return register_action


@register(name='debug')
def _debug_info(win):
    """Print debug info about Window Manager, and current Window."""
    log.info('-= Window Manager =-')
    WindowManager().debug_info(log)
    log.info('-= Current Window =-')
    win.debug_info(log)
    log.info('-= Move with same geometry =-')
    geo =  win.geometry
    win.set_geometry(geo)
    win.sync()
    log.info('New geometry=%s' % win.geometry)
    log.info('-= End of debug =-')



def perform(options, args, config, win_id=0):
    """Perform action based on options and args returned by parser."""
    if not options.action and not args:
        raise ActionException('No ACTION provided')
    name = options.action or args.pop(0)
    name = config.alias(name)
    action = manager.get(name)
    if not action:
        raise ActionException('Invalid ACTION name: %s' % name)
    if action.need_section and options.section:
        name = options.section
        section = config.section(name)
        if not section:
            raise ActionException('Invalid SECTION name: %s' % name)
    elif action.need_section and args and config.section(args[0]):
        section = config.section(args.pop(0))
    else:
        section = None

    missing_args = []
    for arg in action.obligatory_args:
        if not getattr(options, arg):
            missing_args.append(arg.upper())
    if action.need_section and not section and missing_args:
        raise ActionException('Missing %s' % ', '.join(missing_args))

    if win_id or options.win_id:
        window_id = win_id or int(options.win_id, 0)
        window = WM.get_window(window_id)
    elif args:
        # TODO: check system encoding?
        args = [arg.decode('utf-8') for arg in args]
        match = u' '.join(args)
        windows = WM.windows(match=match)
        try:
            window = windows[0]
        except:
            raise ActionException('No WINDOW matching name: %s' % match)
    else:
        window = WM.active_window()

    kwargs = action.get_kwargs(config, section, options)
    action(window, **kwargs)

