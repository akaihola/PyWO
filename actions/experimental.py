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

"""experimental.py - experimental PyWO actions."""

import logging

from actions import register, TYPE, STATE
from core import WM


__author__ = "Wojciech 'KosciaK' Pietrzok <kosciak@kosciak.net>"


#@register(name="spatial_switcher", check=[TYPE, STATE])
@register(name="sp", check=[TYPE, STATE])
def _spatial_switcher(win, direction):
    geometry = win.geometry
    win_center = [geometry.x + geometry.width/2, 
                  geometry.y + geometry.height/2]
    print direction
    if direction.is_top or direction.is_bottom:
        multi = [2, 1]
    else:
        multi = [1, 2]
    print multi
    windows = WM.windows(normal_on_same_filter)
    results = []
    for window in windows:
        if win.id == window.id:
            continue
        geometry = window.geometry
        center = [geometry.x + geometry.width/2, 
                  geometry.y + geometry.height/2]
        vector = [center[0] - win_center[0],
                  center[1] - win_center[1]]
        if not vector[0]:
            slope = 'undefined'
        else:
            slope = float(vector[1]) / float(vector[0])
        length = (multi[0]*vector[0]**2 + multi[1]*vector[1]**2)**0.5
        results.append((window.name, length, vector, slope))
    results.sort(key=lambda e: e[2])
    for result in results:
        print result



# TODO: new actions
#   - always on top
#   - resize (with gravity?)
#   - move (relative with gravity and +/-length)?
#   - place (absolute x,y)
#   - switch desktop/viewport
#   - move window to desktop/viewport

