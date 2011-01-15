#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from tests.test_common import TestMockedCore
import actions
import core

class TestActionPut(TestMockedCore):

    def get_geometry(self, x, y):
        return core.Geometry(x, y, self.WIN_WIDTH, self.WIN_HEIGHT)

    def test_position(self):
        action = actions.get('put')
        position = core.Gravity.parse('TOP_LEFT')
        action(self.win, position=position)
        geometry = self.get_geometry(0, 0)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('TOP')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH/2-self.WIN_WIDTH/2, 0)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('TOP_RIGHT')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH-self.WIN_WIDTH, 0)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('LEFT')
        action(self.win, position=position)
        geometry = self.get_geometry(0, self.DESKTOP_HEIGHT/2-self.WIN_HEIGHT/2)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('MIDDLE')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH/2-self.WIN_WIDTH/2, 
                                     self.DESKTOP_HEIGHT/2-self.WIN_HEIGHT/2)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('RIGHT')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH-self.WIN_WIDTH, 
                                     self.DESKTOP_HEIGHT/2-self.WIN_HEIGHT/2)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('BOTTOM_LEFT')
        action(self.win, position=position)
        geometry = self.get_geometry(0, self.DESKTOP_HEIGHT-self.WIN_HEIGHT)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('BOTTOM')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH/2-self.WIN_WIDTH/2, 
                                     self.DESKTOP_HEIGHT-self.WIN_HEIGHT)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('BOTTOM_RIGHT')
        action(self.win, position=position)
        geometry = self.get_geometry(self.DESKTOP_WIDTH-self.WIN_WIDTH, 
                                     self.DESKTOP_HEIGHT-self.WIN_HEIGHT)
        self.assertEqual(self.win.geometry, geometry)

    def test_position_gravity(self):
        action = actions.get('put')
        position = core.Gravity.parse('MIDDLE')
        gravity = core.Gravity.parse('TOP_RIGHT')
        action(self.win, position=position, gravity=gravity)
        geometry = self.get_geometry(self.DESKTOP_WIDTH/2-self.WIN_WIDTH, 
                                     self.DESKTOP_HEIGHT/2)
        self.assertEqual(self.win.geometry, geometry)
        position = core.Gravity.parse('TOP')


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestActionPut, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

