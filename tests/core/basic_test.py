#!/usr/bin/env python

import unittest

import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')

from pywo.core import Gravity, Size, Position, Geometry, Extents


class SizeTests(unittest.TestCase):

    def setUp(self):
        self.HALF_FULL = Size(0.5, 1.0)

    def test_parse_value(self):
        self.assertEqual(Size.parse_value('FULL'), 1.0)
        self.assertEqual(Size.parse_value('F'), 1.0)
        self.assertEqual(Size.parse_value('1'), 1.0)
        self.assertEqual(Size.parse_value('1.0'), 1.0)
        self.assertEqual(Size.parse_value('H+H'), 1.0)
        self.assertEqual(Size.parse_value('H+0.5'), 1.0)
        self.assertEqual(Size.parse_value('0.25*4'), 1.0)
        self.assertEqual(Size.parse_value('Q*4'), 1.0)
        self.assertEqual(Size.parse_value('0.25*2+H'), 1.0)
        self.assertEqual(Size.parse_value('8*HALF/4'), 1.0)
        self.assertEqual(Size.parse_value('8*HALF/2-FULL'), 1.0)
        self.assertEqual(Size.parse_value('HALF'), 0.5)
        self.assertEqual(Size.parse_value('H'), 0.5)
        self.assertEqual(Size.parse_value('0.5'), 0.5)
        self.assertEqual(Size.parse_value('THIRD'), 1.0/3)
        self.assertEqual(Size.parse_value('T'), 1.0/3)
        self.assertEqual(Size.parse_value('QUARTER'), 0.25)
        self.assertEqual(Size.parse_value('Q'), 0.25)
        self.assertEqual(Size.parse_value('0.25'), 0.25)
        self.assertEqual(Size.parse_value('HALF,FULL'), [0.5, 1])
        self.assertEqual(Size.parse_value(''), None)
        self.assertEqual(Size.parse_value(' '), None)
        self.assertRaises(ValueError, Size.parse_value, 'fasdfa')

    def test_parse(self):
        self.assertEqual(Size.parse('', ''), None)
        self.assertEqual(Size.parse('', 'FULL'), None)
        self.assertEqual(Size.parse('HALF', ''), None)
        self.assertEqual(Size.parse('HALF', 'FULL'), self.HALF_FULL)
        self.assertEqual(Size.parse('HALF', '1'), self.HALF_FULL)
        self.assertEqual(Size.parse('HALF', '1.0'), self.HALF_FULL)
        self.assertEqual(Size.parse('HALF', 'HALF*2'), self.HALF_FULL)
        self.assertEqual(Size.parse('HALF', 'QUARTER*2+HALF'), self.HALF_FULL)
        self.assertEqual(Size.parse('1.0/2', '0.1*6-0.1+HALF'), self.HALF_FULL)
        self.assertEqual(Size.parse('HALF, FULL', '1'), Size([0.5, 1], 1))
        self.assertRaises(ValueError, Size.parse, 'tttgf', '0')

    def test_area(self):
        self.assertEqual(Size.parse('HALF', 'FULL').area, 0.5)
        self.assertEqual(Size.parse('HALF', '1').area, 0.5)
        self.assertEqual(Size.parse('HALF', '1.0').area, 0.5)
        self.assertEqual(Size.parse('HALF', 'HALF*2').area, 0.5)
        self.assertEqual(Size.parse('HALF', 'QUARTER*2+HALF').area, 0.5)
        self.assertEqual(Size.parse('1.0/2', '0.1*6-0.1+HALF').area, 0.5)
        self.assertEqual(Size(10, 10).area, 100)
        try:  # assertRaises doesn't work with properties
            Size.parse('HALF, FULL', '1').area
        except ValueError:  # "Size.area doesn't support multiple dimensions"
            pass
        else:
            raise AssertionError


class PostionTests(unittest.TestCase):

    def test_equal(self):
        self.assertEqual(Position(1, 1), Position(1.0, 1.0))
        self.assertNotEqual(Position(1, 1), Position(1, 2))
        self.assertNotEqual(Position(1, 1), Position(2, 1))


class GravityTests(unittest.TestCase):

    def setUp(self):
        self.TOP = Gravity(0.5, 0)
        self.BOTTOM = Gravity(0.5, 1)
        self.RIGHT = Gravity(1, 0.5)
        self.LEFT = Gravity(0, 0.5)
        self.MIDDLE = Gravity(0.5, 0.5)
        self.TOP_LEFT = Gravity(0, 0)
        self.BOTTOM_RIGHT = Gravity(1, 1)
        self.TOP_RIGHT = Gravity(1, 0)
        self.BOTTOM_LEFT = Gravity(0, 1)

    def test_equal(self):
        self.assertEqual(Gravity(1, 0), self.TOP_RIGHT)
        self.assertEqual(Gravity(1.0, 0.0), self.TOP_RIGHT)
        self.assertEqual(Gravity(0.5, 0.5), self.MIDDLE)

    def test_is_direction__top(self):
        self.assertTrue(self.TOP.is_top)
        self.assertTrue(not self.TOP.is_bottom)
        self.assertTrue(not self.TOP.is_left)
        self.assertTrue(not self.TOP.is_right)
        self.assertTrue(not self.TOP.is_middle)
        self.assertTrue(not self.TOP.is_diagonal)

    def test_is_direction__bottom(self):
        self.assertTrue(not self.BOTTOM.is_top)
        self.assertTrue(self.BOTTOM.is_bottom)
        self.assertTrue(not self.BOTTOM.is_left)
        self.assertTrue(not self.BOTTOM.is_right)
        self.assertTrue(not self.BOTTOM.is_middle)
        self.assertTrue(not self.BOTTOM.is_diagonal)

    def test_is_direction__left(self):
        self.assertTrue(not self.LEFT.is_top)
        self.assertTrue(not self.LEFT.is_bottom)
        self.assertTrue(self.LEFT.is_left)
        self.assertTrue(not self.LEFT.is_right)
        self.assertTrue(not self.LEFT.is_middle)
        self.assertTrue(not self.LEFT.is_diagonal)

    def test_is_direction__right(self):
        self.assertTrue(not self.RIGHT.is_top)
        self.assertTrue(not self.RIGHT.is_bottom)
        self.assertTrue(not self.RIGHT.is_left)
        self.assertTrue(self.RIGHT.is_right)
        self.assertTrue(not self.RIGHT.is_middle)
        self.assertTrue(not self.RIGHT.is_diagonal)

    def test_is_direction__middle(self):
        self.assertTrue(self.MIDDLE.is_top)
        self.assertTrue(self.MIDDLE.is_bottom)
        self.assertTrue(self.MIDDLE.is_left)
        self.assertTrue(self.MIDDLE.is_right)
        self.assertTrue(self.MIDDLE.is_middle)
        self.assertTrue(not self.MIDDLE.is_diagonal)

    def test_is_direction__middle_left(self):
        self.assertTrue(not self.BOTTOM_LEFT.is_top)
        self.assertTrue(self.BOTTOM_LEFT.is_bottom)
        self.assertTrue(self.BOTTOM_LEFT.is_left)
        self.assertTrue(not self.BOTTOM_LEFT.is_right)
        self.assertTrue(not self.BOTTOM_LEFT.is_middle)
        self.assertTrue(self.BOTTOM_LEFT.is_diagonal)

    def test_is_direction__top_right(self):
        self.assertTrue(self.TOP_RIGHT.is_top)
        self.assertTrue(not self.TOP_RIGHT.is_bottom)
        self.assertTrue(not self.TOP_RIGHT.is_left)
        self.assertTrue(self.TOP_RIGHT.is_right)
        self.assertTrue(not self.TOP_RIGHT.is_middle)
        self.assertTrue(self.TOP_RIGHT.is_diagonal)

    def test_invert__top(self):
        self.assertNotEqual(self.TOP.invert(), self.TOP)
        self.assertEqual(self.TOP.invert(), self.BOTTOM)
        self.assertEqual(self.TOP.invert(vertical=False), self.TOP)
        self.assertEqual(self.TOP.invert(horizontal=False), self.BOTTOM)

    def test_invert__bottom(self):
        self.assertNotEqual(self.BOTTOM.invert(), self.BOTTOM)
        self.assertEqual(self.BOTTOM.invert(), self.TOP)
        self.assertEqual(self.BOTTOM.invert(vertical=False), self.BOTTOM)
        self.assertEqual(self.BOTTOM.invert(horizontal=False), self.TOP)

    def test_invert__left(self):
        self.assertNotEqual(self.LEFT.invert(), self.LEFT)
        self.assertEqual(self.LEFT.invert(), self.RIGHT)
        self.assertEqual(self.LEFT.invert(vertical=False), self.RIGHT)
        self.assertEqual(self.LEFT.invert(horizontal=False), self.LEFT)

    def test_invert__right(self):
        self.assertNotEqual(self.RIGHT.invert(), self.RIGHT)
        self.assertEqual(self.RIGHT.invert(), self.LEFT)
        self.assertEqual(self.RIGHT.invert(vertical=False), self.LEFT)
        self.assertEqual(self.RIGHT.invert(horizontal=False), self.RIGHT)

    def test_invert__middle(self):
        self.assertEqual(self.MIDDLE.invert(), self.MIDDLE)
        self.assertEqual(self.MIDDLE.invert(vertical=False), self.MIDDLE)
        self.assertEqual(self.MIDDLE.invert(horizontal=False), self.MIDDLE)

    def test_invert__bottom_left(self):
        self.assertEqual(self.BOTTOM_LEFT.invert(), self.TOP_RIGHT)
        self.assertNotEqual(self.BOTTOM_LEFT.invert(), self.BOTTOM_LEFT)
        self.assertEqual(self.BOTTOM_LEFT.invert(vertical=False), 
                         self.BOTTOM_RIGHT)
        self.assertEqual(self.BOTTOM_LEFT.invert(horizontal=False), 
                         self.TOP_LEFT)
        self.assertEqual(self.BOTTOM_LEFT.invert(vertical=False, horizontal=False), 
                         self.BOTTOM_LEFT)

    def test_invert__top_right(self):
        self.assertEqual(self.TOP_RIGHT.invert(), self.BOTTOM_LEFT)
        self.assertNotEqual(self.TOP_RIGHT.invert(), self.TOP_RIGHT)
        self.assertEqual(self.TOP_RIGHT.invert(vertical=False), 
                         self.TOP_LEFT)
        self.assertEqual(self.TOP_RIGHT.invert(horizontal=False), 
                         self.BOTTOM_RIGHT)
        self.assertEqual(self.TOP_RIGHT.invert(vertical=False, horizontal=False), 
                         self.TOP_RIGHT)

    def test_parse(self):
        self.assertEqual(Gravity.parse(''), None)
        self.assertEqual(Gravity.parse('TOP'), self.TOP)
        self.assertEqual(Gravity.parse('UP'), self.TOP)
        self.assertEqual(Gravity.parse('N'), self.TOP)
        self.assertEqual(Gravity.parse('FULL, 0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('FULL, 0.0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('1, 0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('1,0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('1.0, 0.0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('1.0,0.0'), self.TOP_RIGHT)
        self.assertEqual(Gravity.parse('HALF, HALF'), self.MIDDLE)
        self.assertEqual(Gravity.parse('HALF, 0.5'), self.MIDDLE)
        self.assertEqual(Gravity.parse('HALF, 1.0/2'), self.MIDDLE)
        self.assertEqual(Gravity.parse('0.5, 1.0-0.5'), self.MIDDLE)
        self.assertEqual(Gravity.parse('0.25*2, 2.0/2-0.5'), self.MIDDLE)
        self.assertEqual(Gravity.parse('QUARTER*2, FULL/2'), self.MIDDLE)
        self.assertRaises(ValueError, Gravity.parse, 'top')
        self.assertRaises(ValueError, Gravity.parse, 'slkfsk')
        self.assertRaises(ValueError, Gravity.parse, '1.0')
        self.assertRaises(ValueError, Gravity.parse, '1,2,3')


class GeometryTests(unittest.TestCase):
    
    def test_constructor(self):
        geo = Geometry(100, 150, 20, 30)
        self.assertEqual(geo.x2, 120)
        self.assertEqual(geo.y2, 180)
        # relative to gravity
        geo = Geometry(100, 150, 20, 30, Gravity(1, 1))
        self.assertEqual(geo.x2, 100)
        self.assertEqual(geo.y2, 150)
        self.assertEqual(geo.x, 80)
        self.assertEqual(geo.y, 120)
        # conversion to int
        geo = Geometry(1.1, 2.9, 10.5, 15.2)
        self.assertEqual(geo.x, 1)
        self.assertEqual(geo.y, 2)
        self.assertEqual(geo.width, 10)
        self.assertEqual(geo.height, 15)

    def test_set_position(self):
        geo = Geometry(0, 0, 100, 200)
        self.assertEqual(geo.x, 0)
        self.assertEqual(geo.y, 0)
        # set postion
        geo.set_position(10, 10)
        self.assertEqual(geo.x, 10)
        self.assertEqual(geo.y, 10)
        # set position relative to gravity
        geo.set_position(10, 10, Gravity(0, 0))
        self.assertEqual(geo.x, 10)
        self.assertEqual(geo.y, 10)
        geo.set_position(110, 210, Gravity(1, 1))
        self.assertEqual(geo.x, 10)
        self.assertEqual(geo.y, 10)
        geo.set_position(60, 110, Gravity(0.5, 0.5))
        self.assertEqual(geo.x, 10)
        self.assertEqual(geo.y, 10)

    def test_intersection_no_overlap(self):
        self.assertEqual(Geometry(0, 0, 1, 1) & Geometry(2, 0, 1, 1), None)

    def test_intersection_se_nw_corners_touch(self):
        self.assertEqual(Geometry(0, 0, 1, 1) & Geometry(1, 1, 1, 1),
                         Geometry(1, 1, 0, 0))

    def test_intersection_sw_ne_corners_touch(self):
        self.assertEqual(Geometry(1, 0, 1, 1) & Geometry(0, 1, 1, 2),
                         Geometry(1, 1, 0, 0))

    def test_intersection_nw_se_corners_touch(self):
        self.assertEqual(Geometry(1, 1, 1, 1) & Geometry(0, 0, 1, 1),
                         Geometry(1, 1, 0, 0))

    def test_intersection_ne_sw_corners_touch(self):
        self.assertEqual(Geometry(0, 1, 1, 1) & Geometry(1, 0, 1, 1),
                         Geometry(1, 1, 0, 0))

    def test_intersection_e_w_sides_touch(self):
        self.assertEqual(Geometry(0, 0, 1, 1) & Geometry(1, 0, 1, 1),
                         Geometry(1, 0, 0, 1))

    def test_intersection_w_e_sides_touch(self):
        self.assertEqual(Geometry(1, 0, 1, 1) & Geometry(0, 0, 1, 1),
                         Geometry(1, 0, 0, 1))

    def test_intersection_s_n_sides_touch(self):
        self.assertEqual(Geometry(0, 0, 1, 1) & Geometry(0, 1, 1, 1),
                         Geometry(0, 1, 1, 0))

    def test_intersection_n_s_sides_touch(self):
        self.assertEqual(Geometry(0, 1, 1, 1) & Geometry(0, 0, 1, 1),
                         Geometry(0, 1, 1, 0))

    def test_intersection_se_nw_corners_overlap(self):
        self.assertEqual(Geometry(0, 0, 2, 2) & Geometry(1, 1, 2, 2),
                         Geometry(1, 1, 1, 1))

    def test_intersection_sw_ne_corners_overlap(self):
        self.assertEqual(Geometry(1, 0, 2, 2) & Geometry(0, 1, 2, 2),
                         Geometry(1, 1, 1, 1))

    def test_intersection_nw_se_corners_overlap(self):
        self.assertEqual(Geometry(1, 1, 2, 2) & Geometry(0, 0, 2, 2),
                         Geometry(1, 1, 1, 1))

    def test_intersection_ne_sw_corners_overlap(self):
        self.assertEqual(Geometry(0, 1, 2, 2) & Geometry(1, 0, 2, 2),
                         Geometry(1, 1, 1, 1))

    def test_intersection_inside(self):
        self.assertEqual(Geometry(1, 1, 1, 1) & Geometry(0, 0, 3, 3),
                         Geometry(1, 1, 1, 1))

    def test_intersection_outside(self):
        self.assertEqual(Geometry(0, 0, 3, 3) & Geometry(1, 1, 1, 1),
                         Geometry(1, 1, 1, 1))


class ExtentsTests(unittest.TestCase):

    def test_vertical_horizontal(self):
        extents = Extents(10, 20, 17, 13)
        self.assertEqual(extents.horizontal, 30)
        self.assertEqual(extents.vertical, 30)


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [SizeTests, 
                  PostionTests, 
                  GravityTests, 
                  GeometryTests, 
                  ExtentsTests]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

