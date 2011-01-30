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

"""services - core PyWO services classes and functions."""

import logging


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


log = logging.getLogger(__name__)


class Service(object):

    """Service interface.

    Service can be a class or module that provide these three functions.
    You can't rely on the order of services to be loaded, started, or stopped.

    """

    def setup(confif):
        """Setup service using provided Config instance.

        Class will be initialized (or module loaded) only once, 
        while restart service will be stopped, set up with new config, 
        and started again.
        
        """
        raise NotImplementedError()

    def start():
        """Start service.

        If needed new thread should be started and main loop entered.
        All EventHandlers should be registered while started.

        """
        raise NotImplementedError()

    def stop():
        """Stop service and cleanup all used resources.

        All threads should be stopped. 
        All registered EventHandlers should be unregistered.
        If PyWO is closed normally (not using KILL signal) all services will be
        stopped, so there's no need to use other means of resource cleaning 
        (for example registering atexit function).

        """
        raise NotImplementedError()

