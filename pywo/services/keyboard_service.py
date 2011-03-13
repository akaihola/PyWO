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
from pywo.core.events import KeyHandler


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)

WM = WindowManager()


class KeyPressHandler(KeyHandler):

    """EventHandler for KeyPress events."""

    def __init__(self, config=None):
        KeyHandler.__init__(self)
        self.config = config
        self.mappings = {} # {(modifiers, keycode): (action, section), }
        if self.config:
            self.set_config(self.config)

    def key_press(self, event):
        """Event handler method for KeyPressEventHandler."""
        log.debug('%s' % (event,))
        if not (event.modifiers, event.keycode) in self.mappings:
            log.exception('Unrecognized key!')
            return
        action, section = self.mappings[event.modifiers, event.keycode]
        try:
            window = WM.active_window()
            kwargs = action.get_kwargs(self.config, section)
            action(window, **kwargs)
        except actions.ActionException, e:
            log.error(e)
        except Exception, err:
            log.exception(err)
    
    def set_config(self, config):
        self.config = config
        self.mappings.clear()
        for action in actions.manager.get_all():
            if action.need_section:
                mask = config.keys.get(action.name)
                if not mask:
                    continue
                for section in config.sections.values():
                    key = section.key
                    if key and action not in section.ignored:
                        (mod, keycode) = WM.str2modifiers_keycode(mask, key)
                        self.mappings[(mod, keycode)] = (action, section)
            else:
                key = config.keys.get(action.name)
                if key and action not in config.ignored:
                    (mod, keycode) = WM.str2modifiers_keycode(key)
                    self.mappings[(mod, keycode)] = (action, None)
        self.keys = self.mappings.keys()
        self.numlock = config.numlock
        self.capslock = config.capslock


HANDLER = KeyPressHandler()


def setup(config):
    HANDLER.set_config(config)

def start():
    log.info('Registering keyboard shortcuts')
    HANDLER.grab_keys(WM)


def stop():
    HANDLER.ungrab_keys(WM)
    log.info('Keyboard shortcuts unregistered')


