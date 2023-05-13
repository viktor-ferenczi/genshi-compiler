""" Unit test cases for the utility module

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

# Add the extracted distribution folder to the Python module search path
# to allow testing it before installation
import os, sys

if os.path.isdir('../genshi_compiler'):
    sys.path.insert(0, '..')

import unittest

import genshi_compiler
from genshi_compiler import util


class UtilityTestCase(unittest.TestCase):
    """ Unit test cases for the utility functions
    """

    def test_escape_attribute(self):
        self.assertEqual(util.escape_attribute("&"), '&amp;')
        self.assertEqual(util.escape_attribute("<"), '&lt;')
        self.assertEqual(util.escape_attribute(">"), '&gt;')
        self.assertEqual(util.escape_attribute('"'), '&quot;')
        self.assertEqual(util.escape_attribute("'"), "'")

    def test_tab_to_space(self):
        self.assertEqual(util.tab_to_space(''), '')
        self.assertEqual(util.tab_to_space(' '), ' ')
        self.assertEqual(util.tab_to_space('\t'), ' ' * 8)
        self.assertEqual(util.tab_to_space(' ' * 7 + '\t'), ' ' * 8)
        self.assertEqual(util.tab_to_space('\t\t'), ' ' * 16)
        self.assertEqual(util.tab_to_space('\t \t'), ' ' * 16)
        self.assertEqual(util.tab_to_space('\t' + ' ' * 7 + '\t'), ' ' * 16)
        self.assertEqual(util.tab_to_space('\tx'), ' ' * 8 + 'x')
        self.assertEqual(util.tab_to_space('x\ty'), 'x' + ' ' * 7 + 'y')
        self.assertEqual(util.tab_to_space('x\ty'), 'x' + ' ' * 7 + 'y')
        self.assertEqual(util.tab_to_space('x\tya\tb'), 'x' + ' ' * 7 + 'ya' + ' ' * 6 + 'b')

    def test_remove_duplicate_whitespace(self):
        self.assertEqual(util.remove_duplicate_whitespace(''), '')
        self.assertEqual(util.remove_duplicate_whitespace(' '), ' ')
        self.assertEqual(util.remove_duplicate_whitespace('  '), ' ')
        self.assertEqual(util.remove_duplicate_whitespace('   '), ' ')
        self.assertEqual(util.remove_duplicate_whitespace('x   x'), 'x x')
        self.assertEqual(util.remove_duplicate_whitespace(' x   x '), ' x x ')
        self.assertEqual(util.remove_duplicate_whitespace('  x   x  '), ' x x ')
        self.assertEqual(util.remove_duplicate_whitespace('\n \n \tx \t  x\n \t \n'), '\nx x\n')

    def test_separate_whitespace(self):
        self.assertEqual(util.separate_whitespace(''), ('', '', ''))
        self.assertEqual(util.separate_whitespace(' '), (' ', '', ''))
        self.assertEqual(util.separate_whitespace('  '), ('  ', '', ''))
        self.assertEqual(util.separate_whitespace(' x'), (' ', 'x', ''))
        self.assertEqual(util.separate_whitespace('x '), ('', 'x', ' '))
        self.assertEqual(util.separate_whitespace(' x '), (' ', 'x', ' '))
        self.assertEqual(util.separate_whitespace('\n x'), ('\n ', 'x', ''))
        self.assertEqual(util.separate_whitespace('x\t '), ('', 'x', '\t '))
        self.assertEqual(util.separate_whitespace('\t x \n'), ('\t ', 'x', ' \n'))

    # TODO: Test all the other functions


if __name__ == '__main__':
    unittest.main()
