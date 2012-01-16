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
        self.assertEquals(util.escape_attribute("&"), '&amp;')
        self.assertEquals(util.escape_attribute("<"), '&lt;')
        self.assertEquals(util.escape_attribute(">"), '&gt;')
        self.assertEquals(util.escape_attribute('"'), '&quot;')
        self.assertEquals(util.escape_attribute("'"), "'")
    
    def test_tab_to_space(self):
        self.assertEquals(util.tab_to_space(''),  '')
        self.assertEquals(util.tab_to_space(' '),  ' ')
        self.assertEquals(util.tab_to_space('\t'),  ' ' * 8)
        self.assertEquals(util.tab_to_space(' ' * 7 + '\t'),  ' ' * 8)
        self.assertEquals(util.tab_to_space('\t\t'),  ' ' * 16)
        self.assertEquals(util.tab_to_space('\t \t'),  ' ' * 16)
        self.assertEquals(util.tab_to_space('\t' + ' ' * 7 + '\t'),  ' ' * 16)
        self.assertEquals(util.tab_to_space('\tx'),  ' ' * 8 + 'x')
        self.assertEquals(util.tab_to_space('x\ty'),  'x' + ' ' * 7 + 'y')
        self.assertEquals(util.tab_to_space('x\ty'),  'x' + ' ' * 7 + 'y')
        self.assertEquals(util.tab_to_space('x\tya\tb'),  'x' + ' ' * 7 + 'ya' + ' ' * 6 + 'b')
        
    def test_remove_duplicate_whitespace(self):
        self.assertEquals(util.remove_duplicate_whitespace(''), '')
        self.assertEquals(util.remove_duplicate_whitespace(' '), ' ')
        self.assertEquals(util.remove_duplicate_whitespace('  '), ' ')
        self.assertEquals(util.remove_duplicate_whitespace('   '), ' ')
        self.assertEquals(util.remove_duplicate_whitespace('x   x'), 'x x')
        self.assertEquals(util.remove_duplicate_whitespace(' x   x '), ' x x ')
        self.assertEquals(util.remove_duplicate_whitespace('  x   x  '), ' x x ')
        self.assertEquals(util.remove_duplicate_whitespace('\n \n \tx \t  x\n \t \n'), '\nx x\n')
        
    def test_separate_whitespace(self):
        self.assertEquals(util.separate_whitespace(''), ('', '', ''))
        self.assertEquals(util.separate_whitespace(' '), (' ', '', ''))
        self.assertEquals(util.separate_whitespace('  '), ('  ', '', ''))
        self.assertEquals(util.separate_whitespace(' x'), (' ', 'x', ''))
        self.assertEquals(util.separate_whitespace('x '), ('', 'x', ' '))
        self.assertEquals(util.separate_whitespace(' x '), (' ', 'x', ' '))
        self.assertEquals(util.separate_whitespace('\n x'), ('\n ', 'x', ''))
        self.assertEquals(util.separate_whitespace('x\t '), ('', 'x', '\t '))
        self.assertEquals(util.separate_whitespace('\t x \n'), ('\t ', 'x', ' \n'))
        
    # TODO: Test all the other functions

if __name__ == '__main__':
    unittest.main()
