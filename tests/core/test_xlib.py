#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from Xlib import Xutil

from tests import mock_Xlib
from tests.test_common import TestMockedCore
from pywo.core.basic import Geometry
from pywo.core.xlib import XObject


class TestXObject(TestMockedCore):

    def test_atom(self):
        atom = XObject.atom('_NET_WM_NAME')
        name = XObject.atom_name(atom)
        self.assertEqual(name, '_NET_WM_NAME')

    def test_str2_methods_case_sensitivity(self):
        self.assertEqual(XObject.str2keycode('a'),
                         XObject.str2keycode('A'))
        self.assertEqual(XObject.str2modifiers('Alt'),
                         XObject.str2modifiers('alt'))
        self.assertEqual(XObject.str2modifiers('Alt'),
                         XObject.str2modifiers('ALT'))
        self.assertEqual(XObject.str2modifiers('alt'),
                         XObject.str2modifiers('ALT'))

    def test_str2_methods_modifiers_keycode(self):
        modifiers = XObject.str2modifiers('Alt-Shift')
        keycode = XObject.str2keycode('A')
        modifiers_keycode = XObject.str2modifiers_keycode('Alt-Shift-A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        modifiers_keycode = XObject.str2modifiers_keycode('Alt-Shift', 'A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])

    def test_str2_methods_no_modifiers(self):
        modifiers = XObject.str2modifiers('')
        keycode = XObject.str2keycode('A')
        modifiers_keycode = XObject.str2modifiers_keycode('A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        modifiers_keycode = XObject.str2modifiers_keycode('', 'A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])

    def test_str2_methods_invalid_input(self):
        self.assertRaises(ValueError, XObject.str2modifiers, 'fsdfd')
        self.assertRaises(ValueError, XObject.str2keycode, 'Alt')
        self.assertRaises(ValueError, XObject.str2modifiers_keycode, 'Alt')

    def test_has_xinerama(self):
        self.assertEqual(XObject.has_xinerama(), True)

    def test_has_no_xinerama(self):
        self.display.extensions = []
        self.assertEqual(XObject.has_xinerama(), False)

    def test_get_xinerama_geometries(self):
        self.display.xinerama_query_screens = lambda: mock_Xlib.ScreensQuery(
            (0, 0, 640, 400),
            (640, 0, 960, 200))
        self.assertEqual(XObject.get_xinerama_geometries(),
                         [mock_Xlib.Geometry(0, 0, 640, 400),
                          mock_Xlib.Geometry(640, 0, 960, 200)])

    def test_get_no_xinerama_geometries(self):
        self.display.xinerama_query_screens = AttributeError
        self.assertEqual(XObject.get_xinerama_geometries(),
                         [mock_Xlib.Geometry(0, 0, 800, 600)])



if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestXObject, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

