#!/usr/bin/env python

import unittest

import os
import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

import mock_Xlib
import core


class CoreTest(unittest.TestCase):

    WIDTH = 800
    HEIGHT = 600
    DESKTOPS = 2
    VIEWPORTS = [1, 1]

    def setUp(self):
        display = mock_Xlib.Display(screen_width=self.WIDTH, 
                                    screen_height=self.HEIGHT,
                                    desktops=self.DESKTOPS,
                                    viewports=self.VIEWPORTS)
        core.ClientMessage = mock_Xlib.ClientMessage
        core.XObject._XObject__DISPLAY = display
        self.WM = core.WindowManager()


class TestWindowManager(CoreTest):

    def test_singleton(self):
        self.assertEqual(self.WM, core.WindowManager())
        self.assertTrue(self.WM == core.WindowManager())

    def test_name(self):
        # TODO: need working _NET_SUPPORTING_WM_CHECK in mock!
        self.assertEqual(self.WM.name, '')

    def test_desktop(self):
        self.assertEqual(self.WM.desktop, 0)
        # change to current
        self.WM.set_desktop(0)
        self.assertEqual(self.WM.desktop, 0)
        # change to last desktop
        self.WM.set_desktop(self.WM.desktops - 1)
        self.assertEqual(self.WM.desktop, self.WM.desktops - 1)
        # change back to first desktop
        self.WM.set_desktop(0)
        self.assertEqual(self.WM.desktop, 0)
        # change to higher than number of desktops
        self.WM.set_desktop(self.WM.desktops)
        self.assertEqual(self.WM.desktop, self.WM.desktops - 1)
        # change to lower than 0
        self.WM.set_desktop(-1)
        self.assertEqual(self.WM.desktop, 0)
        # desktop_id as string
        self.WM.set_desktop('0')
        self.assertEqual(self.WM.desktop, 0)
        # invalid string desktop_id
        self.assertRaises(ValueError, self.WM.set_desktop, 'a')

    def test_desktops(self):
        self.assertEqual(self.WM.desktops, self.DESKTOPS)
        # TODO: add/remove_desktop

    def test_desktop_size(self):
        self.assertEqual(self.WM.desktop_size.width, 
                         self.WIDTH * self.VIEWPORTS[0])
        self.assertEqual(self.WM.desktop_size.height, 
                         self.HEIGHT * self.VIEWPORTS[1])
        # TODO: test with many viewports

    def test_desktop_layout(self):
        self.assertEqual(self.WM.desktop_layout, 
                         (0, self.WM.desktops, 1, 0))
        # TODO: change number of desktops and check again

    def test_viewports(self):
        self.assertEqual(self.WM.viewport_position.x, 0)
        self.assertEqual(self.WM.viewport_position.y, 0)
        # TODO: test set_viewport_position()
        # TODO: changing desktop_size (and number of viewports)

    def test_workarea_geometry(self):
        # No panels!
        self.assertEqual(self.WM.workarea_geometry.x, 0)
        self.assertEqual(self.WM.workarea_geometry.y, 0)
        self.assertEqual(self.WM.workarea_geometry.width, self.WIDTH)
        self.assertEqual(self.WM.workarea_geometry.height, self.HEIGHT)

    def test_active_window(self):
        pass

    def test_windows(self):
        pass


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestWindowManager, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

