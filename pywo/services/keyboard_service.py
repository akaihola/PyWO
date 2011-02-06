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

from pywo import actions
from pywo.core import WindowManager
from pywo.events import KeyHandler


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()

MAPPINGS = {} # {(modifiers, keycode): (action, args), }

class KeyPressHandler(KeyHandler):

    """EventHandler for KeyPress events."""

    def key_press(self, event):
        """Event handler method for KeyPressEventHandler."""
        log.debug('EVENT: type=%s, window=%s, keycode=%s, modifiers=%s' %
                  (event.type, event.window_id, 
                   event.keycode, event.modifiers))
        if not (event.modifiers, event.keycode) in MAPPINGS:
            log.excetpion('Unrecognized key!')
            return
        window = WM.active_window()
        action, kwargs = MAPPINGS[event.modifiers, event.keycode]
        try:
            action(window, **kwargs)
        except actions.ActionException, e:
            log.error(e)
        except Exception, err:
            log.exception(err)


HANDLER = KeyPressHandler()


def setup(config):
    MAPPINGS.clear()
    for action in actions.manager.get_all():
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
    log.info('Registering keyboard shortcuts')
    HANDLER.grab_keys(WM)


def stop():
    HANDLER.ungrab_keys(WM)
    log.info('Keyboard shortcuts unregistered')


