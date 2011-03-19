#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from Xlib import Xutil

from tests import mock_Xlib
from tests.test_common import TestMockedCore
from tests.test_common import DESKTOPS, DESKTOP_WIDTH, DESKTOP_HEIGHT, VIEWPORTS
from tests.test_common import WIN_X, WIN_Y, WIN_WIDTH, WIN_HEIGHT
from pywo.core import Position, Geometry, State, Type, Window, WindowManager
from pywo.core.xlib import XObject


class TestWindowManager(TestMockedCore):

    def test_singleton(self):
        self.assertEqual(self.WM, WindowManager())
        self.assertTrue(self.WM == WindowManager())

    def test_name(self):
        self.assertEqual(self.WM.name, 'mock-wm')

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
        self.assertEqual(self.WM.desktops, DESKTOPS)
        # TODO: add/remove_desktop

    def test_desktop_size(self):
        self.assertEqual(self.WM.desktop_size.width, 
                         DESKTOP_WIDTH * VIEWPORTS[0])
        self.assertEqual(self.WM.desktop_size.height, 
                         DESKTOP_HEIGHT * VIEWPORTS[1])

    def test_desktop_layout(self):
        self.assertEqual(self.WM.desktop_layout, 
                         (0, self.WM.desktops, 1, 0))
        # TODO: change number of desktops and check again

    def test_viewports(self):
        self.assertEqual(self.WM.viewport_position, Position(0, 0))
        # TODO: test set_viewport_position()
        # TODO: changing desktop_size (and number of viewports)

    def test_workarea_geometry(self):
        # No panels!
        self.assertEqual(self.WM.workarea_geometry, 
                         Geometry(0, 0, DESKTOP_WIDTH, DESKTOP_HEIGHT))

    def test_active_window(self):
        win = self.WM.active_window()
        self.assertEqual(win, self.win)
        # create new window, and check if new is active
        new_win = self.map_window(name='Test Window 2')
        self.assertNotEqual(new_win, self.win)
        # close second window, check if first is active
        new_win.close()
        win = self.WM.active_window()
        self.assertEqual(win, self.win)
        # close all windows, check if active is None
        self.win.close()
        win = self.WM.active_window()
        self.assertEqual(win, None)

    def test_windows(self):
        # only one window
        self.assertEqual(self.WM.windows(), [self.win])
        self.assertEqual(self.WM.windows_ids(), [self.win.id])
        self.assertEqual(self.WM.windows(stacking=False), [self.win])
        self.assertEqual(self.WM.windows_ids(stacking=False), [self.win.id])
        # create window
        new_win = self.map_window(name='Test Window 2')
        # check order (newest/on top first, so same order)
        self.assertEqual(self.WM.windows(), 
                         [new_win, self.win])
        self.assertEqual(self.WM.windows_ids(), 
                         [new_win.id, self.win.id])
        self.assertEqual(self.WM.windows(stacking=False), 
                         [new_win, self.win])
        self.assertEqual(self.WM.windows_ids(stacking=False), 
                         [new_win.id, self.win.id])
        # activate older, order should differ
        self.win.activate()
        self.assertEqual(self.WM.windows(), 
                         [self.win, new_win])
        self.assertEqual(self.WM.windows_ids(), 
                         [self.win.id, new_win.id])
        self.assertEqual(self.WM.windows_ids(stacking=False), 
                         [new_win.id, self.win.id])
        self.assertEqual(self.WM.windows(stacking=False), 
                         [new_win, self.win])

    def test_windows_filter(self):
        def fullscreen_filter(window):
            return State.FULLSCREEN in window.state

        windows = self.WM.windows(filter=fullscreen_filter)
        self.assertEqual(len(windows), 0)
        self.win.fullscreen(1)
        windows = self.WM.windows(filter=fullscreen_filter)
        self.assertEqual(len(windows), 1)


class TestWindowsNameMatcher(TestMockedCore):

    def test_no_match(self):
        self.map_window(name='Foo bar')
        windows = self.WM.windows(match='ABCD')
        self.assertEqual(len(windows), 0)

    def test_match(self):
        self.map_window(name='Foo')
        self.map_window(name='Foo', desktop=1)
        self.map_window(name='foo')
        self.map_window(name='Foo bar')
        self.map_window(name='Bar Foo')
        self.map_window(name='Bar Foo Baz')
        self.map_window(name='ABC')
        self.map_window(name='ABC', class_name=['foo', 'qwe'])
        self.map_window(name='ABC', class_name=['abc', 'foo'])
        windows = self.WM.windows(match='Foo')
        self.assertEqual(len(windows), 8)

    def test_match_case_insensitive(self):
        self.map_window(name='abc')
        self.map_window(name='ABC')
        self.map_window(name='XYZ')
        windows = self.WM.windows(match='ABC')
        self.assertEqual(len(windows), 2)
        windows = self.WM.windows(match='abc')
        self.assertEqual(len(windows), 2)

    def test_match_order(self):
        win1 = self.map_window(name='abc')
        win2 = self.map_window(name='ABC')
        windows = self.WM.windows(match='abc')
        self.assertEqual(windows[0], win2)
        windows = self.WM.windows(match='abc', stacking=False)
        self.assertEqual(windows[0], win2)
        win1.activate()
        windows = self.WM.windows(match='abc')
        self.assertEqual(windows[0], win1)
        windows = self.WM.windows(match='abc', stacking=False)
        self.assertEqual(windows[0], win2)

    def test_exact_match(self):
        win1 = self.map_window(name='Foo')
        win2 = self.map_window(name='Foo bar')
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win1, win2])

    def test_left_match(self):
        win1 = self.map_window(name='baz Foo bar')
        win2 = self.map_window(name='a Foo bar')
        win3 = self.map_window(name='az Foo bar')
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win2, win3, win1])

    def test_right_match(self):
        win1 = self.map_window(name='qwertyuiop Foo bazbar')
        win2 = self.map_window(name='qwertyuiop Foo a')
        win3 = self.map_window(name='qwertyuiop Foo bar')
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win2, win3, win1])

    def test_right_match(self):
        win1 = self.map_window(name='qwertyuiop Foo bazbar')
        win2 = self.map_window(name='qwertyuiop Foo a')
        win3 = self.map_window(name='qwertyuiop Foo bar')
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win2, win3, win1])

    def test_left_right_match(self):
        win1 = self.map_window(name='baz Foo a')
        win2 = self.map_window(name='baz Foo bar')
        win3 = self.map_window(name='az Foo bar')
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win1, win3, win2])

    def test_class_name_match(self):
        win1 = self.map_window(name='abc', 
                               class_name=['foo', 'bar']) # class match
        win2 = self.map_window(name='xyz', 
                               class_name=['qwe', 'asd']) # no match
        win3 = self.map_window(name='foo bar', 
                               class_name=['xyz', 'iop']) # name match
        win4 = self.map_window(name='bar foo', 
                               class_name=['foo', 'iop']) # name and class match
        windows = self.WM.windows(match='Foo')
        self.assertEqual(windows, [win4, win3, win1])

    def test_match_same_desktop_first(self):
        win1 = self.map_window(name='abc', desktop=1)
        win2 = self.map_window(name='abc')
        windows = self.WM.windows(match='abc')
        self.assertEqual(windows, [win2, win1])

    def test_match_same_viewport_first(self):
        win1 = self.map_window(name='abc', desktop=1) # other desktop
        win2 = self.map_window(name='abc') # same viewport, desktop
        win3 = self.map_window(name='abc')
        geometry = win3.geometry
        geometry.x += self.WM.workarea_geometry.width
        win3.set_geometry(geometry) # move to other viewport
        win4 = self.map_window(name='qwe abc xyz') # same viewport, desktop
        windows = self.WM.windows(match='abc')
        self.assertEqual(windows, [win2, win4, win3, win1])


class TestWindowProperties(TestMockedCore):

    def test_name(self):
        self.assertEqual(self.win.name, 'Test Window')
        self.assertEqual(self.win.class_name, 'test.Window')

    def test_client_machine(self):
        self.assertEqual(self.win.client_machine, 'mock')

    def test_type(self):
        self.assertEqual(self.win.type, (Type.NORMAL,))

    def test_state(self):
        self.assertEqual(self.win.state, ())

    def test_desktop(self):
        # check current
        self.assertEqual(self.win.desktop, 0)
        # set current
        self.win.set_desktop(0)
        self.assertEqual(self.win.desktop, 0)
        # change to last desktop
        self.win.set_desktop(self.WM.desktops - 1)
        self.assertEqual(self.win.desktop, self.WM.desktops - 1)
        # change back to first desktop
        self.win.set_desktop(0)
        self.assertEqual(self.win.desktop, 0)
        # change to higher than number of desktops
        self.win.set_desktop(self.WM.desktops)
        self.assertEqual(self.win.desktop, self.WM.desktops - 1)
        # change to lower than 0
        self.win.set_desktop(-1)
        self.assertEqual(self.win.desktop, 0)
        # desktop_id as string
        self.win.set_desktop('0')
        self.assertEqual(self.win.desktop, 0)
        # invalid string desktop_id
        self.assertRaises(ValueError, self.win.set_desktop, 'a')
    
    def assertEqualGeometry(self, geometry, x, y, width, height):
        other = Geometry(x, y, width, height)
        self.assertEqual(geometry, other)

    def test_geometry(self):
        # initial geometry
        geometry = self.win.geometry
        self.assertEqualGeometry(geometry, WIN_X, WIN_Y, WIN_WIDTH, WIN_HEIGHT)
        # set same geometry
        self.win.set_geometry(geometry)
        geometry = self.win.geometry
        self.assertEqualGeometry(geometry, WIN_X, WIN_Y, WIN_WIDTH, WIN_HEIGHT)
        # set new geometry
        self.win.set_geometry(Geometry(50, 75, 138, 45))
        geometry = self.win.geometry
        self.assertEqualGeometry(geometry, 50, 75, 138, 45)
        # set position to (0, 0)
        self.win.set_geometry(Geometry(0, 0, 138, 45))
        geometry = self.win.geometry
        self.assertEqualGeometry(geometry, 0, 0, 138, 45)
        # TODO: test with incremental windows!
        # TODO: test windows with maximal, and minimal size
        # TODO: test with windows with border_width > 0

    def test_extents(self):
        # normal extents
        self.assertEqual(self.win.extents, mock_Xlib.EXTENTS_NORMAL)
        # extents for maximized
        self.win.maximize(1)
        self.assertEqual(self.win.extents, mock_Xlib.EXTENTS_MAXIMIZED)
        # unmaximize, back to normal extents
        self.win.maximize(0)
        self.assertEqual(self.win.extents, mock_Xlib.EXTENTS_NORMAL)
        # extents for fullscreen
        self.win.fullscreen(1)
        self.assertEqual(self.win.extents, mock_Xlib.EXTENTS_FULLSCREEN)
        # and back to normal extents
        self.win.fullscreen(0)
        self.assertEqual(self.win.extents, mock_Xlib.EXTENTS_NORMAL)


class TestWindowState(TestMockedCore):

    def test_close(self):
        win = self.WM.active_window()
        self.assertTrue(win is not None)
        # close window (this is the only one)
        win.close()
        win = self.WM.active_window()
        self.assertTrue(win is None)

    def test_activate(self):
        # create window
        new_win = self.map_window(name='Test Window 2')
        self.assertNotEqual(self.WM.active_window(), self.win)
        self.win.activate()
        self.assertEqual(self.WM.active_window(), self.win)

    def test_iconify(self):
        win_geometry = self.win.geometry
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.iconify(1)
        self.assertTrue(State.HIDDEN in self.win.state)
        self.assertEqual(self.win.geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.iconify(0)
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win.geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.iconify(2)
        self.assertTrue(State.HIDDEN in self.win.state)
        self.assertEqual(self.win.geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.iconify(2)
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win.geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)

    def test_maximize(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # set maximize
        self.win.maximize(1)
        self.assertTrue(State.MAXIMIZED in self.win.state)
        self.assertTrue(State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_MAXIMIZED)
        # unset maximize
        self.win.maximize(0)
        self.assertFalse(State.MAXIMIZED in self.win.state)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # toggle back and forth
        self.win.maximize(2)
        self.assertTrue(State.MAXIMIZED in self.win.state)
        self.assertTrue(State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2)
        self.assertFalse(State.MAXIMIZED in self.win.state)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)

    def test_maximize_vert(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # set maximize
        self.win.maximize(1, horz=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, workarea.x)
        self.assertEqual(geometry.y, workarea.y)
        self.assertNotEqual(geometry.width, workarea.width)
        self.assertEqual(geometry.height, workarea.height)
        self.assertEqual(win_geometry.x, geometry.x)
        self.assertNotEqual(win_geometry.y, geometry.y)
        self.assertEqual(win_geometry.width, geometry.width)
        self.assertNotEqual(win_geometry.height, geometry.height)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # unset maximize
        self.win.maximize(0, horz=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # toggle back and forth
        self.win.maximize(2, horz=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, horz=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)

    def test_maximize_horz(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # set maximize
        self.win.maximize(1, vert=False)
        self.assertTrue(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, workarea.x)
        self.assertNotEqual(geometry.y, workarea.y)
        self.assertEqual(geometry.width, workarea.width)
        self.assertNotEqual(geometry.height, workarea.height)
        self.assertNotEqual(win_geometry.x, geometry.x)
        self.assertEqual(win_geometry.y, geometry.y)
        self.assertNotEqual(win_geometry.width, geometry.width)
        self.assertEqual(win_geometry.height, geometry.height)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # unset maximize
        self.win.maximize(0, vert=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_NORMAL)
        # toggle back and forth
        self.win.maximize(2, vert=False)
        self.assertTrue(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, vert=False)
        self.assertFalse(State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(State.MAXIMIZED_VERT in self.win.state)

    def test_shade(self):
        win_geometry = self.win.geometry
        self.assertFalse(State.SHADED in self.win.state)
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.shade(1)
        self.assertTrue(State.SHADED in self.win.state)
        self.assertTrue(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        self.win.shade(0)
        geometry = self.win.geometry
        self.assertFalse(State.SHADED in self.win.state)
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.assertEqual(geometry, win_geometry)
        self.win.shade(2)
        self.assertTrue(State.SHADED in self.win.state)
        self.assertTrue(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.shade(2)
        self.assertFalse(State.SHADED in self.win.state)
        self.assertFalse(State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)

    def test_fullscreen(self):
        desktop_geometry = Geometry(0, 0, DESKTOP_WIDTH, DESKTOP_HEIGHT)
        win_geometry = self.win.geometry
        self.assertFalse(State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, desktop_geometry)
        extents = self.win.extents
        self.assertNotEqual(extents, mock_Xlib.EXTENTS_FULLSCREEN)
        # set fullscreen
        self.win.fullscreen(1)
        self.assertTrue(State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, desktop_geometry)
        extents = self.win.extents
        self.assertEqual(extents, mock_Xlib.EXTENTS_FULLSCREEN)
        # unset fullscreen
        self.win.fullscreen(0)
        self.assertFalse(State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, desktop_geometry)
        self.assertEqual(win_geometry, geometry)
        extents = self.win.extents
        self.assertNotEqual(extents, mock_Xlib.EXTENTS_FULLSCREEN)
        # toggle back and forth
        self.win.fullscreen(2)
        self.assertTrue(State.FULLSCREEN in self.win.state)
        self.win.fullscreen(2)
        self.assertFalse(State.FULLSCREEN in self.win.state)

    def test_sticky(self):
        self.assertNotEqual(self.win.desktop, Window.ALL_DESKTOPS)
        self.win.sticky(1)
        self.assertEqual(self.win.desktop, Window.ALL_DESKTOPS)
        self.win.sticky(0)
        self.assertEqual(self.win.desktop, self.WM.desktop)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, Window.ALL_DESKTOPS)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, self.WM.desktop)

    def test_reset(self):
        self.win.maximize(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        self.win.fullscreen(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        self.win.iconify(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        self.win.sticky(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        self.win.shade(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        self.win.maximize(1)
        self.win.fullscreen(1)
        self.win.sticky(1)
        self.win.shade(1)
        self.win.iconify(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset(True)
        self.assertEqual(self.win.state, ())
        # Test both - with, and without full=True


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestWindowManager, TestWindowProperties, TestWindowState, TestWindowsNameMatcher, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

