#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from tests.test_common import TestMockedCore
from tests.test_common import DESKTOP_WIDTH, DESKTOP_HEIGHT

from pywo import core
from pywo.actions import resizer


TOP_LEFT = core.Gravity.parse('NW')
TOP = core.Gravity.parse('N')
TOP_RIGHT = core.Gravity.parse('NE')
LEFT = core.Gravity.parse('W')
ALL = core.Gravity.parse('MIDDLE')
RIGHT = core.Gravity.parse('E')
BOTTOM_LEFT = core.Gravity.parse('SW')
BOTTOM = core.Gravity.parse('S')
BOTTOM_RIGHT = core.Gravity.parse('SE')


class TestExpandWindow(TestMockedCore):

    def setUp(self):
        TestMockedCore.setUp(self)
        self.resize = resizer.expand_window

    def test_empty_desktop(self):
        geometry = self.win.geometry
        resized = self.resize(self.win, TOP_LEFT)
        self.assertEqual(resized.x, 0)
        self.assertEqual(resized.y, 0)
        self.assertEqual(resized.x2, geometry.x2)
        self.assertEqual(resized.y2, geometry.y2)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, TOP)
        self.assertEqual(resized.x, geometry.x)
        self.assertEqual(resized.y, 0)
        self.assertEqual(resized.x2, geometry.x2)
        self.assertEqual(resized.y2, geometry.y2)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, TOP_RIGHT)
        self.assertEqual(resized.x, geometry.x)
        self.assertEqual(resized.y, 0)
        self.assertEqual(resized.x2, DESKTOP_WIDTH)
        self.assertEqual(resized.y2, geometry.y2)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, LEFT)
        self.assertEqual(resized.x, 0)
        self.assertEqual(resized.y, geometry.y)
        self.assertEqual(resized.x2, geometry.x2)
        self.assertEqual(resized.y2, geometry.y2)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, ALL)
        self.assertEqual(resized.x, 0)
        self.assertEqual(resized.y, 0)
        self.assertEqual(resized.x2, DESKTOP_WIDTH)
        self.assertEqual(resized.y2, DESKTOP_HEIGHT)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, RIGHT)
        self.assertEqual(resized.x, geometry.x)
        self.assertEqual(resized.y, geometry.y)
        self.assertEqual(resized.x2, DESKTOP_WIDTH)
        self.assertEqual(resized.y2, geometry.y2)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, BOTTOM_LEFT)
        self.assertEqual(resized.x, 0)
        self.assertEqual(resized.y, geometry.y)
        self.assertEqual(resized.x2, geometry.x2)
        self.assertEqual(resized.y2, DESKTOP_HEIGHT)
        self.win.set_geometry(geometry)

        resized = self.resize(self.win, BOTTOM_RIGHT)
        self.assertEqual(resized.x, geometry.x)
        self.assertEqual(resized.y, geometry.y)
        self.assertEqual(resized.x2, DESKTOP_WIDTH)
        self.assertEqual(resized.y2, DESKTOP_HEIGHT)

    def test_maximal_size(self):
        max_geometry = core.Geometry(0, 0, DESKTOP_WIDTH, DESKTOP_HEIGHT)
        self.win.set_geometry(max_geometry)
        resized = self.resize(self.win, ALL)
        self.assertEqual(resized.x, 0)
        self.assertEqual(resized.y, 0)
        self.assertEqual(resized.x2, DESKTOP_WIDTH)
        self.assertEqual(resized.y2, DESKTOP_HEIGHT)


class TestShrinkWindow(TestMockedCore):

    def setUp(self):
        TestMockedCore.setUp(self)
        self.resize = resizer.shrink_window

    def test_empty_desktop(self):
        geometry = self.win.geometry
        resized = self.resize(self.win, TOP_LEFT)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, TOP)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, TOP_RIGHT)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, LEFT)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, ALL)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, RIGHT)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, BOTTOM_LEFT)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, BOTTOM)
        self.assertEqual(resized, geometry)
        resized = self.resize(self.win, BOTTOM_RIGHT)
        self.assertEqual(resized, geometry)


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestExpandWindow, 
                  TestShrinkWindow]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

