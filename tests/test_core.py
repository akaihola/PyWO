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
from pywo import core


class TestXObject(TestMockedCore):

    def test_atom(self):
        atom = core.XObject.atom('_NET_WM_NAME')
        name = core.XObject.atom_name(atom)
        self.assertEqual(name, '_NET_WM_NAME')

    def test_str2_methods(self):
        # test if not case sensitive
        self.assertEqual(core.XObject.str2keycode('a'),
                         core.XObject.str2keycode('A'))
        self.assertEqual(core.XObject.str2modifiers('Alt'),
                         core.XObject.str2modifiers('alt'))
        self.assertEqual(core.XObject.str2modifiers('Alt'),
                         core.XObject.str2modifiers('ALT'))
        self.assertEqual(core.XObject.str2modifiers('alt'),
                         core.XObject.str2modifiers('ALT'))
        # modifiers-keycode
        modifiers = core.XObject.str2modifiers('Alt-Shift')
        keycode = core.XObject.str2keycode('A')
        modifiers_keycode = core.XObject.str2modifiers_keycode('Alt-Shift-A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        modifiers_keycode = core.XObject.str2modifiers_keycode('Alt-Shift', 'A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        # no modifiers
        modifiers = core.XObject.str2modifiers('')
        modifiers_keycode = core.XObject.str2modifiers_keycode('A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        modifiers_keycode = core.XObject.str2modifiers_keycode('', 'A')
        self.assertEqual(modifiers, modifiers_keycode[0])
        self.assertEqual(keycode, modifiers_keycode[1])
        # invalid input
        self.assertRaises(ValueError, core.XObject.str2modifiers, 'fsdfd')
        self.assertRaises(ValueError, core.XObject.str2keycode, 'Alt')
        self.assertRaises(ValueError, core.XObject.str2modifiers_keycode, 'Alt')


class TestWindowManager(TestMockedCore):

    def test_singleton(self):
        self.assertEqual(self.WM, core.WindowManager())
        self.assertTrue(self.WM == core.WindowManager())

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
        self.assertEqual(self.WM.viewport_position.x, 0)
        self.assertEqual(self.WM.viewport_position.y, 0)
        # TODO: test set_viewport_position()
        # TODO: changing desktop_size (and number of viewports)

    def test_workarea_geometry(self):
        # No panels!
        self.assertEqual(self.WM.workarea_geometry.x, 0)
        self.assertEqual(self.WM.workarea_geometry.y, 0)
        self.assertEqual(self.WM.workarea_geometry.width, DESKTOP_WIDTH)
        self.assertEqual(self.WM.workarea_geometry.height, DESKTOP_HEIGHT)

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
            return core.State.FULLSCREEN in window.state

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
        self.assertEqual(self.win.type, (core.Type.NORMAL,))

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

    def test_geometry(self):
        # initial geometry
        geometry = self.win.geometry
        self.assertEqual(geometry.x, WIN_X)
        self.assertEqual(geometry.y, WIN_Y)
        self.assertEqual(geometry.width, WIN_WIDTH)
        self.assertEqual(geometry.height, WIN_HEIGHT)
        # set same geometry
        self.win.set_geometry(geometry)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, WIN_X)
        self.assertEqual(geometry.y, WIN_Y)
        self.assertEqual(geometry.width, WIN_WIDTH)
        self.assertEqual(geometry.height, WIN_HEIGHT)
        # set new geometry
        self.win.set_geometry(core.Geometry(50, 75, 138, 45))
        geometry = self.win.geometry
        self.assertEqual(geometry.x, 50)
        self.assertEqual(geometry.y, 75)
        self.assertEqual(geometry.width, 138)
        self.assertEqual(geometry.height, 45)
        # set position to (0, 0)
        self.win.set_geometry(core.Geometry(0, 0, 138, 45))
        geometry = self.win.geometry
        self.assertEqual(geometry.x, 0)
        self.assertEqual(geometry.y, 0)
        self.assertEqual(geometry.width, 138)
        self.assertEqual(geometry.height, 45)
        # TODO: test with incremental windows!
        # TODO: test windows with maximal, and minimal size
        # TODO: test with windows with border_width > 0

    def test_extents(self):
        # normal extents
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # extents for maximized
        self.win.maximize(1)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_MAXIMIZED.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_MAXIMIZED.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_MAXIMIZED.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_MAXIMIZED.bottom)
        # unmaximize, back to normal extents
        self.win.maximize(0)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # extents for fullscreen
        self.win.fullscreen(1)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # and back to normal extents
        self.win.fullscreen(0)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)


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
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.iconify(1)
        self.assertTrue(core.State.HIDDEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.iconify(0)
        geometry = self.win.geometry
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.iconify(2)
        self.assertTrue(core.State.HIDDEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.iconify(2)
        geometry = self.win.geometry
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(geometry, win_geometry)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)

    def test_maximize(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1)
        self.assertTrue(core.State.MAXIMIZED in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_MAXIMIZED.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_MAXIMIZED.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_MAXIMIZED.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_MAXIMIZED.bottom)
        # unset maximize
        self.win.maximize(0)
        self.assertFalse(core.State.MAXIMIZED in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2)
        self.assertTrue(core.State.MAXIMIZED in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2)
        self.assertFalse(core.State.MAXIMIZED in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)

    def test_maximize_vert(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1, horz=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_VERT in self.win.state)
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
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        # unset maximize
        self.win.maximize(0, horz=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2, horz=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(core.State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, horz=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)

    def test_maximize_horz(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1, vert=False)
        self.assertTrue(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
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
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # unset maximize
        self.win.maximize(0, vert=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2, vert=False)
        self.assertTrue(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, vert=False)
        self.assertFalse(core.State.MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(core.State.MAXIMIZED_VERT in self.win.state)

    def test_shade(self):
        win_geometry = self.win.geometry
        self.assertFalse(core.State.SHADED in self.win.state)
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.win.shade(1)
        self.assertTrue(core.State.SHADED in self.win.state)
        self.assertTrue(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        self.win.shade(0)
        geometry = self.win.geometry
        self.assertFalse(core.State.SHADED in self.win.state)
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)
        self.assertEqual(geometry, win_geometry)
        self.win.shade(2)
        self.assertTrue(core.State.SHADED in self.win.state)
        self.assertTrue(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.IconicState)
        self.win.shade(2)
        self.assertFalse(core.State.SHADED in self.win.state)
        self.assertFalse(core.State.HIDDEN in self.win.state)
        self.assertEqual(self.win._win.get_wm_state().state, Xutil.NormalState)

    def test_fullscreen(self):
        win_geometry = self.win.geometry
        self.assertFalse(core.State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, 0)
        self.assertNotEqual(geometry.y, 0)
        self.assertNotEqual(geometry.width, DESKTOP_WIDTH)
        self.assertNotEqual(geometry.height, DESKTOP_HEIGHT)
        extents = self.win.extents
        self.assertNotEqual(extents.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertNotEqual(extents.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertNotEqual(extents.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertNotEqual(extents.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # set fullscreen
        self.win.fullscreen(1)
        self.assertTrue(core.State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, 0)
        self.assertEqual(geometry.y, 0)
        self.assertEqual(geometry.width, DESKTOP_WIDTH)
        self.assertEqual(geometry.height, DESKTOP_HEIGHT)
        extents = self.win.extents
        self.assertEqual(extents.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertEqual(extents.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertEqual(extents.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertEqual(extents.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # unset fullscreen
        self.win.fullscreen(0)
        self.assertFalse(core.State.FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, 0)
        self.assertNotEqual(geometry.y, 0)
        self.assertNotEqual(geometry.width, DESKTOP_WIDTH)
        self.assertNotEqual(geometry.height, DESKTOP_HEIGHT)
        self.assertEqual(win_geometry.x, geometry.x)
        self.assertEqual(win_geometry.y, geometry.y)
        self.assertEqual(win_geometry.width, geometry.width)
        self.assertEqual(win_geometry.height, geometry.height)
        extents = self.win.extents
        self.assertNotEqual(extents.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertNotEqual(extents.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertNotEqual(extents.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertNotEqual(extents.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # toggle back and forth
        self.win.fullscreen(2)
        self.assertTrue(core.State.FULLSCREEN in self.win.state)
        self.win.fullscreen(2)
        self.assertFalse(core.State.FULLSCREEN in self.win.state)

    def test_sticky(self):
        self.assertNotEqual(self.win.desktop, core.Window.ALL_DESKTOPS)
        self.win.sticky(1)
        self.assertEqual(self.win.desktop, core.Window.ALL_DESKTOPS)
        self.win.sticky(0)
        self.assertEqual(self.win.desktop, self.WM.desktop)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, core.Window.ALL_DESKTOPS)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, self.WM.desktop)

    def test_reset(self):
        self.win.maximize(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())
        self.win.fullscreen(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())
        self.win.iconify(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())
        self.win.sticky(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())
        self.win.shade(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())
        self.win.maximize(1)
        self.win.fullscreen(1)
        self.win.sticky(1)
        self.win.shade(1)
        self.win.iconify(1)
        self.assertNotEqual(self.win.state, ())
        self.win.reset()
        self.assertEqual(self.win.state, ())


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestXObject, TestWindowManager, TestWindowProperties, TestWindowState, TestWindowsNameMatcher, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

