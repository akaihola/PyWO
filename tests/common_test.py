#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from tests import Xlib_mock

from pywo.core import xlib
from pywo import core


DESKTOP_WIDTH = 800
DESKTOP_HEIGHT = 600
DESKTOPS = 2
VIEWPORTS = [2, 1]

EXTENSIONS = ['XINERAMA', ]

WIN_NAME = 'Test Window'
WIN_CLASS_NAME = ['test', 'Window']
WIN_X = 10
WIN_Y = 10
WIN_WIDTH = 100
WIN_HEIGHT = 150


class MockedXlibTests(unittest.TestCase):

    def setUp(self):
        # setup Window Manager
        display = Xlib_mock.Display(screen_width=DESKTOP_WIDTH, 
                                    screen_height=DESKTOP_HEIGHT,
                                    desktops=DESKTOPS,
                                    viewports=VIEWPORTS,
                                    extensions=EXTENSIONS)
        self.display = display
        xlib.ClientMessage = Xlib_mock.ClientMessage
        xlib.XObject._XObject__DISPLAY = display
        self.WM = core.WindowManager()
        self.win = self.map_window()

    def map_window(self, 
                   type=core.Type.NORMAL,
                   modal=False,
                   name=WIN_NAME, class_name=WIN_CLASS_NAME,
                   x=WIN_X, y=WIN_Y, 
                   width=WIN_WIDTH, height=WIN_HEIGHT,
                   desktop=0):
        geometry = Xlib_mock.Geometry(
            x + Xlib_mock.EXTENTS_NORMAL.left,
            y + Xlib_mock.EXTENTS_NORMAL.top,
            width - (Xlib_mock.EXTENTS_NORMAL.left +
                     Xlib_mock.EXTENTS_NORMAL.right),
            height - (Xlib_mock.EXTENTS_NORMAL.top +
                      Xlib_mock.EXTENTS_NORMAL.bottom))
        window = Xlib_mock.Window(display=self.display,
                                  type=[type],
                                  modal=modal,
                                  name=name,
                                  class_name=class_name,
                                  geometry=geometry)
        window.map()
        win = core.Window(window.id)
        win.set_desktop(desktop)
        return win

