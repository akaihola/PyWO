#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from tests.test_common import TestMockedCore
from tests.test_common import DESKTOPS, DESKTOP_WIDTH, DESKTOP_HEIGHT, VIEWPORTS
from pywo.core import Geometry, State, Type, Mode, Window
from pywo.core import filters


class TestFilters(TestMockedCore):

    def assertWindows(self, filter, windows):
        """Assert that after using given filters you get given windows."""
        filtered_windows = self.WM.windows(filter)
        filtered_windows_ids = set([win.id for win in filtered_windows])
        windows_ids = set([win.id for win in windows])
        self.assertEqual(windows_ids, filtered_windows_ids)


class TestTypeFilters(TestFilters):

    def setUp(self):
        super(TestTypeFilters, self).setUp()
        # map windows of all types
        self.normal_win = self.win
        self.desktop_win = self.map_window(type=Type.DESKTOP)
        self.dock_win = self.map_window(type=Type.DOCK)
        self.toolbar_win = self.map_window(type=Type.TOOLBAR)
        self.menu_win = self.map_window(type=Type.MENU)
        self.utility_win = self.map_window(type=Type.UTILITY)
        self.splash_win = self.map_window(type=Type.SPLASH)
        self.dialog_win = self.map_window(type=Type.DIALOG)

    def test_include_type(self):
        self.assertWindows(filters.IncludeType(Type.NORMAL, Type.UTILITY), 
                           [self.normal_win, self.utility_win])

    def test_exclude_type(self):
        self.assertWindows(filters.ExcludeType(Type.NORMAL, Type.UTILITY), 
                           [self.desktop_win, self.dock_win, self.toolbar_win,
                            self.menu_win, self.splash_win, self.dialog_win])

    def test_normal_type(self):
        self.assertWindows(filters.NORMAL_TYPE, [self.normal_win])

    def test_standard_type(self):
        self.assertWindows(filters.STANDARD_TYPE, 
                           [self.normal_win, self.dock_win, 
                            self.utility_win, self.dialog_win])


class TestStateFilters(TestFilters):

    def setUp(self):
        super(TestStateFilters, self).setUp()
        # map windows of all states
        self.no_state_win = self.win
        self.modal_win = self.map_window(modal=True)
        self.sticky_win = self.map_window()
        self.sticky_win.sticky(Mode.SET)
        self.maximized_win = self.map_window()
        self.maximized_win.maximize(Mode.SET)
        self.vert_maximized_win = self.map_window()
        self.vert_maximized_win.maximize(Mode.SET, horz=False)
        self.horz_maximized_win = self.map_window()
        self.horz_maximized_win.maximize(Mode.SET, vert=False)
        self.fullscreen_win = self.map_window()
        self.fullscreen_win.fullscreen(Mode.SET)
        self.shaded_win = self.map_window()
        self.shaded_win.shade(Mode.SET)
        self.above_win = self.map_window()
        self.above_win.always_above(Mode.SET)
        self.below_win = self.map_window()
        self.below_win.always_below(Mode.SET)
        self.iconified_win = self.map_window()
        self.iconified_win.iconify(Mode.SET)

    def test_include_state(self):
        self.assertWindows(filters.IncludeState(State.STICKY, State.FULLSCREEN),
                           [self.sticky_win, self.fullscreen_win])
        self.assertWindows(filters.IncludeState(State.MAXIMIZED),
                           [self.maximized_win])
        self.assertWindows(filters.IncludeState(State.MAXIMIZED_VERT),
                           [self.maximized_win, self.vert_maximized_win])
        self.assertWindows(filters.IncludeState(State.MAXIMIZED_HORZ),
                           [self.maximized_win, self.horz_maximized_win])
        self.assertWindows(filters.IncludeState(State.HIDDEN),
                           [self.iconified_win, self.shaded_win])

    def test_exclude_state(self):
        self.assertWindows(filters.ExcludeState(State.MAXIMIZED_VERT, State.HIDDEN),
                           [self.no_state_win, self.modal_win, self.sticky_win,
                            self.horz_maximized_win, self.fullscreen_win, 
                            self.above_win, self.below_win])

    def test_normal_state(self):
        self.assertWindows(filters.NORMAL_STATE,
                           [self.no_state_win, self.sticky_win, 
                            self.vert_maximized_win, self.horz_maximized_win, 
                            self.above_win, self.below_win])


class TestDesktopFilter(TestFilters):

    def setUp(self):
        super(TestDesktopFilter, self).setUp()
        self.desktop1_win = self.win
        self.desktop2_win = self.map_window(desktop=1)
        self.all_desktops_win = self.map_window()
        self.all_desktops_win.sticky(Mode.SET)

    def test_current(self):
        self.WM.set_desktop(0)
        self.assertWindows(filters.Desktop(), 
                           [self.desktop1_win, self.all_desktops_win])
        self.assertWindows(filters.DESKTOP,
                           [self.desktop1_win, self.all_desktops_win])
        self.WM.set_desktop(1)
        self.assertWindows(filters.Desktop(), 
                           [self.desktop2_win, self.all_desktops_win])
        self.assertWindows(filters.DESKTOP,
                           [self.desktop2_win, self.all_desktops_win])
        self.WM.set_desktop(0)
        self.assertWindows(filters.Desktop(), 
                           [self.desktop1_win, self.all_desktops_win])
        self.assertWindows(filters.DESKTOP,
                           [self.desktop1_win, self.all_desktops_win])

    def test_selected(self):
        # windows on selected desktop
        self.assertWindows(filters.Desktop(0), 
                           [self.desktop1_win, self.all_desktops_win])
        self.assertWindows(filters.Desktop(1), 
                           [self.desktop2_win, self.all_desktops_win])
        # all desktops only
        self.assertWindows(filters.Desktop(Window.ALL_DESKTOPS), 
                           [self.all_desktops_win])
        # invalid desktop number
        self.assertWindows(filters.Desktop(-1), 
                           [self.all_desktops_win])


class TestWorkareaFilter(TestFilters):

    def setUp(self):
        super(TestWorkareaFilter, self).setUp()
        self.desktop1_viewport1_win = self.win
        self.desktop1_viewport2_win = self.map_window(x=DESKTOP_WIDTH + 50)
        self.desktop2_viewport1_win = self.map_window(desktop=1)
        self.desktop2_viewport2_win = self.map_window(desktop=1, 
                                                      x=DESKTOP_WIDTH + 50)

    def test_workarea(self):
        self.WM.set_desktop(0)
        self.assertWindows(filters.Workarea(),
                           [self.desktop1_viewport1_win])
        self.WM.set_desktop(1)
        self.assertWindows(filters.Workarea(),
                           [self.desktop2_viewport1_win])
        self.WM.set_desktop(0)
        self.assertWindows(filters.Workarea(),
                           [self.desktop1_viewport1_win])
        # TODO: not implemented yet in mock_Xlib
        #self.WM.set_viewport_position(DESKTOP_WIDTH, 0)
        #self.assertWindows(filters.Workarea(),
        #                   [self.desktop2_viewport2_win])


class TestCombinedFilters(TestFilters):

    def setUp(self):
        super(TestCombinedFilters, self).setUp()
        # types
        self.desktop_win = self.map_window(type=Type.DESKTOP)
        self.dock_win = self.map_window(type=Type.DOCK)
        self.toolbar_win = self.map_window(type=Type.TOOLBAR)
        self.menu_win = self.map_window(type=Type.MENU)
        self.utility_win = self.map_window(type=Type.UTILITY)
        self.splash_win = self.map_window(type=Type.SPLASH)
        self.dialog_win = self.map_window(type=Type.DIALOG)
        self.no_state_win = self.win
        self.modal_win = self.map_window(modal=True)
        # states
        self.sticky_win = self.map_window()
        self.sticky_win.sticky(Mode.SET)
        self.maximized_win = self.map_window()
        self.maximized_win.maximize(Mode.SET)
        self.vert_maximized_win = self.map_window()
        self.vert_maximized_win.maximize(Mode.SET, horz=False)
        self.horz_maximized_win = self.map_window()
        self.horz_maximized_win.maximize(Mode.SET, vert=False)
        self.fullscreen_win = self.map_window()
        self.fullscreen_win.fullscreen(Mode.SET)
        self.shaded_win = self.map_window()
        self.shaded_win.shade(Mode.SET)
        self.above_win = self.map_window()
        self.above_win.always_above(Mode.SET)
        self.below_win = self.map_window()
        self.below_win.always_below(Mode.SET)
        self.iconified_win = self.map_window()
        self.iconified_win.iconify(Mode.SET)
        # desktop/viewport
        self.desktop1_viewport1_win = self.win
        self.desktop1_viewport2_win = self.map_window(x=DESKTOP_WIDTH + 50)
        self.desktop2_viewport1_win = self.map_window(desktop=1)
        self.desktop2_viewport2_win = self.map_window(desktop=1, 
                                                      x=DESKTOP_WIDTH + 50)

    def test_normal(self):
        self.assertWindows(filters.NORMAL,
                           [self.win, 
                            self.sticky_win, 
                            self.vert_maximized_win, self.horz_maximized_win, 
                            self.above_win, self.below_win,
                            self.desktop1_viewport1_win, 
                            self.desktop1_viewport2_win, 
                            self.desktop2_viewport1_win, 
                            self.desktop2_viewport2_win])
        self.assertWindows(filters.NORMAL_ON_WORKAREA,
                           [self.win, 
                            self.sticky_win, 
                            self.vert_maximized_win, self.horz_maximized_win, 
                            self.above_win, self.below_win,
                            self.desktop1_viewport1_win])
        self.WM.set_desktop(1)
        self.assertWindows(filters.NORMAL_ON_WORKAREA,
                           [self.sticky_win, 
                            self.desktop2_viewport1_win])

    def test_standard(self):
        self.assertWindows(filters.STANDARD,
                           [self.win, 
                            self.dialog_win,
                            self.utility_win,
                            self.dock_win,
                            self.sticky_win, 
                            self.vert_maximized_win, self.horz_maximized_win, 
                            self.above_win, self.below_win,
                            self.desktop1_viewport1_win, 
                            self.desktop1_viewport2_win, 
                            self.desktop2_viewport1_win, 
                            self.desktop2_viewport2_win])
        self.assertWindows(filters.STANDARD_ON_WORKAREA,
                           [self.win, 
                            self.dialog_win,
                            self.utility_win,
                            self.dock_win,
                            self.sticky_win, 
                            self.vert_maximized_win, self.horz_maximized_win, 
                            self.above_win, self.below_win,
                            self.desktop1_viewport1_win])


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestTypeFilters, 
                  TestStateFilters, 
                  TestDesktopFilter, 
                  TestWorkareaFilter, 
                  TestCombinedFilters, ]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

