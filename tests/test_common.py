#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from tests import mock_Xlib

from pywo.core import xlib
from pywo import core


DESKTOP_WIDTH = 800
DESKTOP_HEIGHT = 600
DESKTOPS = 2
VIEWPORTS = [2, 1]

WIN_NAME = 'Test Window'
WIN_CLASS_NAME = ['test', 'Window']
WIN_X = 10
WIN_Y = 10
WIN_WIDTH = 100
WIN_HEIGHT = 150


class TestMockedCore(unittest.TestCase):

    def setUp(self):
        # setup Window Manager
        display = mock_Xlib.Display(screen_width=DESKTOP_WIDTH, 
                                    screen_height=DESKTOP_HEIGHT,
                                    desktops=DESKTOPS,
                                    viewports=VIEWPORTS)
        self.display = display
        xlib.ClientMessage = mock_Xlib.ClientMessage
        xlib.XObject._XObject__DISPLAY = display
        self.WM = core.WindowManager()
        self.win = self.map_window()

    def map_window(self, 
                   type=core.Type.NORMAL,
                   name=WIN_NAME, class_name=WIN_CLASS_NAME,
                   x=WIN_X, y=WIN_Y, 
                   width=WIN_WIDTH, height=WIN_HEIGHT,
                   desktop=0):
        geometry = mock_Xlib.Geometry(
            x + mock_Xlib.EXTENTS_NORMAL.left,
            y + mock_Xlib.EXTENTS_NORMAL.top,
            width - (mock_Xlib.EXTENTS_NORMAL.left +
                     mock_Xlib.EXTENTS_NORMAL.right),
            height - (mock_Xlib.EXTENTS_NORMAL.top +
                      mock_Xlib.EXTENTS_NORMAL.bottom))
        window = mock_Xlib.Window(display=self.display,
                                  type=[type],
                                  name=name,
                                  class_name=class_name,
                                  geometry=geometry)
        window.map()
        win = core.Window(window.id)
        win.set_desktop(desktop)
        return win

