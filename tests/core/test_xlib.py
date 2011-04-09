#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from Xlib import Xutil

from tests import mock_Xlib
from tests.test_common import TestMockedCore
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


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestXObject, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

