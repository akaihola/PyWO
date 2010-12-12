import unittest

import os
import sys
sys.path.insert(0, '../')
sys.path.insert(0, './')


from core import Gravity, Size, Geometry, Borders

class TestSize(unittest.TestCase):

    def setUp(self):
        self.HALF_FULL = Size(0.5, 1.0)

    def test_parse_value(self):
        self.assertEquals(Size.parse_value('FULL'), 1.0)
        self.assertEquals(Size.parse_value('F'), 1.0)
        self.assertEquals(Size.parse_value('1'), 1.0)
        self.assertEquals(Size.parse_value('1.0'), 1.0)
        self.assertEquals(Size.parse_value('H+H'), 1.0)
        self.assertEquals(Size.parse_value('H+0.5'), 1.0)
        self.assertEquals(Size.parse_value('0.25*4'), 1.0)
        self.assertEquals(Size.parse_value('Q*4'), 1.0)
        self.assertEquals(Size.parse_value('0.25*2+H'), 1.0)
        self.assertEquals(Size.parse_value('8*HALF/4'), 1.0)
        self.assertEquals(Size.parse_value('8*HALF/2-FULL'), 1.0)
        self.assertEquals(Size.parse_value('HALF'), 0.5)
        self.assertEquals(Size.parse_value('H'), 0.5)
        self.assertEquals(Size.parse_value('0.5'), 0.5)
        self.assertEquals(Size.parse_value('THIRD'), 1.0/3)
        self.assertEquals(Size.parse_value('T'), 1.0/3)
        self.assertEquals(Size.parse_value('QUARTER'), 0.25)
        self.assertEquals(Size.parse_value('Q'), 0.25)
        self.assertEquals(Size.parse_value('0.25'), 0.25)
        self.assertEquals(Size.parse_value('HALF,FULL'), [0.5, 1])
        self.assertEquals(Size.parse_value(''), None)
        self.assertEquals(Size.parse_value(' '), None)
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


class TestGravity(unittest.TestCase):

    # TODO: check changes in Gravity!

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

    def test_is_direction(self):
        self.assert_(self.TOP.is_top)
        self.assert_(not self.TOP.is_bottom)
        self.assert_(not self.TOP.is_left)
        self.assert_(not self.TOP.is_right)
        self.assert_(not self.TOP.is_middle)
        self.assert_(not self.TOP.is_diagonal)

        self.assert_(not self.BOTTOM.is_top)
        self.assert_(self.BOTTOM.is_bottom)
        self.assert_(not self.BOTTOM.is_left)
        self.assert_(not self.BOTTOM.is_right)
        self.assert_(not self.BOTTOM.is_middle)
        self.assert_(not self.BOTTOM.is_diagonal)

        self.assert_(not self.LEFT.is_top)
        self.assert_(not self.LEFT.is_bottom)
        self.assert_(self.LEFT.is_left)
        self.assert_(not self.LEFT.is_right)
        self.assert_(not self.LEFT.is_middle)
        self.assert_(not self.LEFT.is_diagonal)

        self.assert_(not self.RIGHT.is_top)
        self.assert_(not self.RIGHT.is_bottom)
        self.assert_(not self.RIGHT.is_left)
        self.assert_(self.RIGHT.is_right)
        self.assert_(not self.RIGHT.is_middle)
        self.assert_(not self.RIGHT.is_diagonal)

        self.assert_(self.MIDDLE.is_top)
        self.assert_(self.MIDDLE.is_bottom)
        self.assert_(self.MIDDLE.is_left)
        self.assert_(self.MIDDLE.is_right)
        self.assert_(self.MIDDLE.is_middle)
        self.assert_(not self.MIDDLE.is_diagonal)

        self.assert_(not self.BOTTOM_LEFT.is_top)
        self.assert_(self.BOTTOM_LEFT.is_bottom)
        self.assert_(self.BOTTOM_LEFT.is_left)
        self.assert_(not self.BOTTOM_LEFT.is_right)
        self.assert_(not self.BOTTOM_LEFT.is_middle)
        self.assert_(self.BOTTOM_LEFT.is_diagonal)

        self.assert_(self.TOP_RIGHT.is_top)
        self.assert_(not self.TOP_RIGHT.is_bottom)
        self.assert_(not self.TOP_RIGHT.is_left)
        self.assert_(self.TOP_RIGHT.is_right)
        self.assert_(not self.TOP_RIGHT.is_middle)
        self.assert_(self.TOP_RIGHT.is_diagonal)

    def test_invert(self):
        self.assertNotEqual(self.TOP.invert(), self.TOP)
        self.assertEqual(self.TOP.invert(), self.BOTTOM)
        self.assertNotEqual(self.BOTTOM.invert(), self.BOTTOM)
        self.assertEqual(self.BOTTOM.invert(), self.TOP)

        self.assertNotEqual(self.LEFT.invert(), self.LEFT)
        self.assertEqual(self.LEFT.invert(), self.RIGHT)
        self.assertNotEqual(self.RIGHT.invert(), self.RIGHT)
        self.assertEqual(self.RIGHT.invert(), self.LEFT)

        self.assertEqual(self.BOTTOM_LEFT.invert(), self.TOP_RIGHT)
        self.assertNotEqual(self.BOTTOM_LEFT.invert(), self.BOTTOM_LEFT)
        self.assertEqual(self.TOP_RIGHT.invert(), self.BOTTOM_LEFT)
        self.assertNotEqual(self.TOP_RIGHT.invert(), self.TOP_RIGHT)

        self.assertEqual(self.MIDDLE.invert(), self.MIDDLE)
        self.assertEqual(self.MIDDLE.invert(vertical=False), self.MIDDLE)
        self.assertEqual(self.MIDDLE.invert(horizontal=False), self.MIDDLE)

        self.assertEqual(self.BOTTOM_LEFT.invert(vertical=False), 
                         self.BOTTOM_RIGHT)
        self.assertEqual(self.BOTTOM_LEFT.invert(horizontal=False), 
                         self.TOP_LEFT)
        self.assertEqual(self.BOTTOM_LEFT.invert(vertical=False, horizontal=False), 
                         self.BOTTOM_LEFT)

    def test_parse(self):
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


class TestGeometry(unittest.TestCase):
    
    def test_constructor(self):
        geo = Geometry(100, 150, 20, 30)
        self.assertEquals(geo.x2, 120)
        self.assertEquals(geo.y2, 180)
        geo = Geometry(100, 150, 20, 30, Gravity(1, 1))
        self.assertEquals(geo.x2, 100)
        self.assertEquals(geo.y2, 150)
        self.assertEquals(geo.x, 80)
        self.assertEquals(geo.y, 120)
        geo = Geometry(1.1, 2.9, 10.5, 15.2)
        self.assertEquals(geo.x, 1)
        self.assertEquals(geo.y, 2)
        self.assertEquals(geo.width, 10)
        self.assertEquals(geo.height, 15)

    def test_set_position(self):
        geo = Geometry(0, 0, 100, 200)
        self.assertEquals(geo.x, 0)
        self.assertEquals(geo.y, 0)
        geo.set_position(10, 10)
        self.assertEquals(geo.x, 10)
        self.assertEquals(geo.y, 10)
        geo.set_position(10, 10, Gravity(0, 0))
        self.assertEquals(geo.x, 10)
        self.assertEquals(geo.y, 10)
        geo.set_position(110, 210, Gravity(1, 1))
        self.assertEquals(geo.x, 10)
        self.assertEquals(geo.y, 10)
        geo.set_position(60, 110, Gravity(0.5, 0.5))
        self.assertEquals(geo.x, 10)
        self.assertEquals(geo.y, 10)


class TestBorders(unittest.TestCase):

    def test_vertical_horizontal(self):
        borders = Borders(10, 20, 17, 13)
        self.assertEquals(borders.horizontal, 30)
        self.assertEquals(borders.vertical, 30)


if __name__ == '__main__':
    main_suite = unittest.TestSuite()
    for suite in [TestSize, TestGravity, TestGeometry, TestBorders]:
        main_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(suite))
    unittest.TextTestRunner(verbosity=2).run(main_suite)

