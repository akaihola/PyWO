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

"""pywo - package containing Python Window Organizer."""

import logging


__author__ = "Wojciech 'KosciaK' Pietrzok, Antti Kaihola"
__credits__ = ["Wojciech 'KosciaK' Pietrzok", 
               "Antti Kaihola"]
__license__ = 'GPL'
__version__ = "0.3.0"
__maintainer__ = "Wojciech 'KosciaK' Pietrzok"
__email__ = 'kosciak@kosciak.net'


class NullHandler(logging.Handler):

    """logging.Handler that does not emit anything."""

    def emit(self, record):
        """Just pass."""
        pass


# set NullHandler for whole pywo.* loggers hierarchy
logging.getLogger('pywo').addHandler(NullHandler())

