""" Unit test cases for the HTML minimizer

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
from genshi_compiler import html_minimizer


class HtmlMinimizerTestCase(unittest.TestCase):
    """ Unit test cases for the utility functions
    """

    def test_html_minimizer(self):
        self.assertEquals(html_minimizer.minimize('<html />'), '<html/>')
        self.assertEquals(html_minimizer.minimize('  <html />   '), '<html/>')
        self.assertEquals(html_minimizer.minimize(' \n <html />  \n '), '<html/>')
        self.assertEquals(html_minimizer.minimize('<html></html>'), '<html/>')
        self.assertEquals(html_minimizer.minimize('<html>x</html>'), '<html>x</html>')
        self.assertEquals(html_minimizer.minimize('<html> x </html>'), '<html> x </html>')
        self.assertEquals(html_minimizer.minimize('<html>  x  </html>'), '<html> x </html>')
        self.assertEquals(html_minimizer.minimize('<html> \n x \n </html>'), '<html> x </html>')
        self.assertEquals(html_minimizer.minimize('<html> \n </html>'), '<html>\n</html>')
        self.assertEquals(html_minimizer.minimize('<html> \n\n \n  \n \n  </html>'), '<html>\n</html>')

if __name__ == '__main__':
    unittest.main()
