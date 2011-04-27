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

"""example_actions.py - example of pywo.actions plugin."""

import logging

from pywo import actions


__author__ = "Wojciech 'KosciaK' Pietrzok"


# NOTE: Use logger in 'pywo.actions.*' hierarchy!
log = logging.getLogger('pywo.actions.' + __name__)


@actions.register('example_action')
def example_action(win, **kwargs):
    """This is an example of simple, function based action."""
    log.info('Example action: %s' % win)


class ExampleAction(actions.Action):

    """This is an example of action subclassing actions.Action."""

    def perform(self, win, **kwargs):
        log.info('ExampleAction: %s' % win)

ExampleAction('example_action_class').register()

