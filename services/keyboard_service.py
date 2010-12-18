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

"""keyboard_service.py - provides keyboard shortcuts handling."""

import logging

import actions
from core import WindowManager
from events import KeyPressHandler


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


WM = WindowManager()

MAPPINGS = {} # {(modifiers, keycode): (action, args), }

def key_press(event):
    """Event handler method for KeyPressEventHandler."""
    logging.debug('EVENT: type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, event.keycode, event.modifiers))
    if not (event.modifiers, event.keycode) in MAPPINGS:
        logging.error('Unrecognized key!')
        return
    window = WM.active_window()
    logging.debug(window.name)
    action, kwargs = MAPPINGS[event.modifiers, event.keycode]
    logging.debug('%s(%s)' % 
                  (action.name, 
                  ', '.join(['%s=%s' % (key, str(value)) 
                             for key, value in kwargs.items()])))
    try:
        action(window, **kwargs)
    except actions.ActionException, e:
        logging.error(e)
    except Exception, err:
        logging.exception(err)
    WM.flush()


HANDLER = KeyPressHandler(key_press)


def setup(config):
    MAPPINGS.clear()
    for action in actions.all():
        if 'direction' in action.args or \
           'position' in action.args or \
           'gravity' in action.args:
            mask = config.keys.get(action.name)
            if not mask:
                continue
            for section in config.sections.values():
                key = section.key
                if key and action not in section.ignored:
                    (modifiers, keycode) = WM.str2modifiers_keycode(mask, key)
                    kwargs = actions.get_args(action, config, section)
                    MAPPINGS[(modifiers, keycode)] = (action, kwargs)
        else:
            key = config.keys.get(action.name)
            if key and action not in config.ignored:
                (modifiers, keycode) = WM.str2modifiers_keycode(key)
                kwargs = actions.get_args(action, config)
                MAPPINGS[(modifiers, keycode)] = (action, kwargs)
    # set new mappings
    HANDLER.set_keys(MAPPINGS.keys(), 
                     config.numlock,
                     config.capslock)

def start():
    logging.info('Registering keyboard shortcuts')
    HANDLER.grab_keys(WM)


def stop():
    HANDLER.ungrab_keys(WM)
    logging.info('Keyboard shortcuts unregistered')


