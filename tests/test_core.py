#!/usr/bin/env python

import unittest

import os
import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

import mock_Xlib
import core


class TestMocked(unittest.TestCase):

    DESKTOP_WIDTH = 800
    DESKTOP_HEIGHT = 600
    DESKTOPS = 2
    VIEWPORTS = [1, 1]
    WIN_X = 10
    WIN_Y = 10
    WIN_WIDTH = 100
    WIN_HEIGHT = 150

    def setUp(self):
        # setup Window Manager
        display = mock_Xlib.Display(screen_width=self.DESKTOP_WIDTH, 
                                    screen_height=self.DESKTOP_HEIGHT,
                                    desktops=self.DESKTOPS,
                                    viewports=self.VIEWPORTS)
        self.display = display
        core.ClientMessage = mock_Xlib.ClientMessage
        core.XObject._XObject__DISPLAY = display
        self.WM = core.WindowManager()
        # setup one Window
        geometry = mock_Xlib.Geometry(
            self.WIN_X + mock_Xlib.EXTENTS_NORMAL.left,
            self.WIN_Y + mock_Xlib.EXTENTS_NORMAL.top,
            self.WIN_WIDTH - (mock_Xlib.EXTENTS_NORMAL.left +
                              mock_Xlib.EXTENTS_NORMAL.right),
            self.WIN_HEIGHT - (mock_Xlib.EXTENTS_NORMAL.top +
                               mock_Xlib.EXTENTS_NORMAL.bottom))
        window = mock_Xlib.Window(display=self.display,
                                  class_name=['test', 'Window'], 
                                  name='Test Window',
                                  geometry=geometry)
        window.map()
        self.win = self.WM.active_window()


class TestXObject(TestMocked):

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


class TestWindowManager(TestMocked):

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
        self.assertEqual(self.WM.desktops, self.DESKTOPS)
        # TODO: add/remove_desktop

    def test_desktop_size(self):
        self.assertEqual(self.WM.desktop_size.width, 
                         self.DESKTOP_WIDTH * self.VIEWPORTS[0])
        self.assertEqual(self.WM.desktop_size.height, 
                         self.DESKTOP_HEIGHT * self.VIEWPORTS[1])
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
        self.assertEqual(self.WM.workarea_geometry.width, self.DESKTOP_WIDTH)
        self.assertEqual(self.WM.workarea_geometry.height, self.DESKTOP_HEIGHT)

    def test_active_window(self):
        win = self.WM.active_window()
        self.assertEqual(win, self.win)
        # create new window, and check if new is active
        window = mock_Xlib.Window(display=self.display,
                                  class_name=['test', 'Window'], 
                                  name='Test Window 2',
                                  geometry=mock_Xlib.Geometry(4, 19, 92, 130))
        window.map()
        win = self.WM.active_window()
        self.assertNotEqual(win, self.win)
        # close second window, check if first is active
        win.close()
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
        window = mock_Xlib.Window(display=self.display,
                                  class_name=['test', 'Window'], 
                                  name='Test Window 2',
                                  geometry=mock_Xlib.Geometry(4, 19, 92, 130))
        window.map()
        new_win = self.WM.active_window()
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


class TestWindowProperties(TestMocked):

    def test_name(self):
        self.assertEqual(self.win.name, 'Test Window')
        self.assertEqual(self.win.class_name, 'test.Window')

    def test_client_machine(self):
        self.assertEqual(self.win.client_machine, 'mock')

    def test_type(self):
        self.assertEqual(self.win.type, [self.win.TYPE_NORMAL])

    def test_state(self):
        self.assertEqual(self.win.state, [])

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
        self.assertEqual(geometry.x, self.WIN_X)
        self.assertEqual(geometry.y, self.WIN_Y)
        self.assertEqual(geometry.width, self.WIN_WIDTH)
        self.assertEqual(geometry.height, self.WIN_HEIGHT)
        # set same geometry
        self.win.set_geometry(geometry)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, self.WIN_X)
        self.assertEqual(geometry.y, self.WIN_Y)
        self.assertEqual(geometry.width, self.WIN_WIDTH)
        self.assertEqual(geometry.height, self.WIN_HEIGHT)
        # set new geometry
        self.win.set_geometry(core.Geometry(50, 75, 138, 45))
        geometry = self.win.geometry
        self.assertEqual(geometry.x, 50)
        self.assertEqual(geometry.y, 75)
        self.assertEqual(geometry.width, 138)
        self.assertEqual(geometry.height, 45)
        # TODO: test with incremental windows!

    def test_borders(self):
        # normal borders
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # borders for maximized
        self.win.maximize(1)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_MAXIMIZED.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_MAXIMIZED.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_MAXIMIZED.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_MAXIMIZED.bottom)
        # unmaximize, back to normal borders
        self.win.maximize(0)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # borders for fullscreen
        self.win.fullscreen(1)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # and back to normal borders
        self.win.fullscreen(0)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)


class TestWindowState(TestMocked):

    def test_close(self):
        win = self.WM.active_window()
        self.assertTrue(win is not None)
        # close window (this is the only one)
        win.close()
        win = self.WM.active_window()
        self.assertTrue(win is None)

    def test_activate(self):
        # create window
        window = mock_Xlib.Window(display=self.display,
                                  class_name=['test', 'Window'], 
                                  name='Test Window 2',
                                  geometry=mock_Xlib.Geometry(4, 19, 92, 130))
        window.map()
        new_win = self.WM.active_window()
        self.assertNotEqual(self.WM.active_window(), self.win)
        self.win.activate()
        self.assertEqual(self.WM.active_window(), self.win)

    def test_iconify(self):
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_HIDDEN in self.win.state)
        self.win.iconify()
        self.assertTrue(self.win.STATE_HIDDEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        # TODO: check self.win._win.get_wm_state() or WM_STATE property
        self.win.activate()
        geometry = self.win.geometry
        self.assertFalse(self.win.STATE_HIDDEN in self.win.state)
        self.assertEqual(geometry, win_geometry)

    def test_maximize(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1)
        self.assertTrue(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, workarea)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_MAXIMIZED.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_MAXIMIZED.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_MAXIMIZED.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_MAXIMIZED.bottom)
        # unset maximize
        self.win.maximize(0)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2)
        self.assertTrue(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)

    def test_maximize_vert(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1, horz=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, workarea.x)
        self.assertEqual(geometry.y, workarea.y)
        self.assertNotEqual(geometry.width, workarea.width)
        self.assertEqual(geometry.height, workarea.height)
        self.assertEqual(win_geometry.x, geometry.x)
        self.assertNotEqual(win_geometry.y, geometry.y)
        self.assertEqual(win_geometry.width, geometry.width)
        self.assertNotEqual(win_geometry.height, geometry.height)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        # unset maximize
        self.win.maximize(0, horz=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2, horz=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertTrue(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, horz=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)

    def test_maximize_horz(self):
        workarea = self.WM.workarea_geometry
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # set maximize
        self.win.maximize(1, vert=False)
        self.assertTrue(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, workarea.x)
        self.assertNotEqual(geometry.y, workarea.y)
        self.assertEqual(geometry.width, workarea.width)
        self.assertNotEqual(geometry.height, workarea.height)
        self.assertNotEqual(win_geometry.x, geometry.x)
        self.assertEqual(win_geometry.y, geometry.y)
        self.assertNotEqual(win_geometry.width, geometry.width)
        self.assertEqual(win_geometry.height, geometry.height)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # unset maximize
        self.win.maximize(0, vert=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry, workarea)
        self.assertEqual(geometry, win_geometry)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_NORMAL.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_NORMAL.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_NORMAL.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_NORMAL.bottom)
        # toggle back and forth
        self.win.maximize(2, vert=False)
        self.assertTrue(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)
        self.win.maximize(2, vert=False)
        self.assertFalse(self.win.STATE_MAXIMIZED_HORZ in self.win.state)
        self.assertFalse(self.win.STATE_MAXIMIZED_VERT in self.win.state)

    def test_shade(self):
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_SHADED in self.win.state)
        self.assertFalse(self.win.STATE_HIDDEN in self.win.state)
        self.win.shade(1)
        self.assertTrue(self.win.STATE_SHADED in self.win.state)
        self.assertTrue(self.win.STATE_HIDDEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry, win_geometry)
        # TODO: check self.win._win.get_wm_state() or WM_STATE property
        self.win.shade(0)
        geometry = self.win.geometry
        self.assertFalse(self.win.STATE_SHADED in self.win.state)
        self.assertFalse(self.win.STATE_HIDDEN in self.win.state)
        self.assertEqual(geometry, win_geometry)
        self.win.shade(2)
        self.assertTrue(self.win.STATE_SHADED in self.win.state)
        self.assertTrue(self.win.STATE_HIDDEN in self.win.state)
        self.win.shade(2)
        self.assertFalse(self.win.STATE_SHADED in self.win.state)
        self.assertFalse(self.win.STATE_HIDDEN in self.win.state)

    def test_fullscreen(self):
        win_geometry = self.win.geometry
        self.assertFalse(self.win.STATE_FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, 0)
        self.assertNotEqual(geometry.y, 0)
        self.assertNotEqual(geometry.width, self.DESKTOP_WIDTH)
        self.assertNotEqual(geometry.height, self.DESKTOP_HEIGHT)
        borders = self.win.borders
        self.assertNotEqual(borders.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertNotEqual(borders.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertNotEqual(borders.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertNotEqual(borders.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # set fullscreen
        self.win.fullscreen(1)
        self.assertTrue(self.win.STATE_FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertEqual(geometry.x, 0)
        self.assertEqual(geometry.y, 0)
        self.assertEqual(geometry.width, self.DESKTOP_WIDTH)
        self.assertEqual(geometry.height, self.DESKTOP_HEIGHT)
        borders = self.win.borders
        self.assertEqual(borders.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertEqual(borders.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertEqual(borders.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertEqual(borders.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # unset fullscreen
        self.win.fullscreen(0)
        self.assertFalse(self.win.STATE_FULLSCREEN in self.win.state)
        geometry = self.win.geometry
        self.assertNotEqual(geometry.x, 0)
        self.assertNotEqual(geometry.y, 0)
        self.assertNotEqual(geometry.width, self.DESKTOP_WIDTH)
        self.assertNotEqual(geometry.height, self.DESKTOP_HEIGHT)
        self.assertEqual(win_geometry.x, geometry.x)
        self.assertEqual(win_geometry.y, geometry.y)
        self.assertEqual(win_geometry.width, geometry.width)
        self.assertEqual(win_geometry.height, geometry.height)
        borders = self.win.borders
        self.assertNotEqual(borders.left, mock_Xlib.EXTENTS_FULLSCREEN.left)
        self.assertNotEqual(borders.right, mock_Xlib.EXTENTS_FULLSCREEN.right)
        self.assertNotEqual(borders.top, mock_Xlib.EXTENTS_FULLSCREEN.top)
        self.assertNotEqual(borders.bottom, mock_Xlib.EXTENTS_FULLSCREEN.bottom)
        # toggle back and forth
        self.win.fullscreen(2)
        self.assertTrue(self.win.STATE_FULLSCREEN in self.win.state)
        self.win.fullscreen(2)
        self.assertFalse(self.win.STATE_FULLSCREEN in self.win.state)

    def test_sticky(self):
        self.assertNotEqual(self.win.desktop, 0xFFFFFFFF)
        self.win.sticky(1)
        self.assertEqual(self.win.desktop, 0xFFFFFFFF)
        self.win.sticky(0)
        self.assertEqual(self.win.desktop, self.WM.desktop)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, 0xFFFFFFFF)
        self.win.sticky(2)
        self.assertEqual(self.win.desktop, self.WM.desktop)

    def test_reset(self):
        pass


class TestWindowsNameMatcher(TestMocked):

    def __init__(self):
        TestMocked.__init__(self)
        # TODO: create bunch of windows, on different desktops, viewports


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestXObject, TestWindowManager, TestWindowProperties, TestWindowState, TestWindowsNameMatcher, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

