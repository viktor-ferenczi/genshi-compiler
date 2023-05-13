""" Unit test cases for the HTML minimizer

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

# Add the extracted distribution folder to the Python module search path
# to allow testing it before installation
import os
import sys

if os.path.isdir('../genshi_compiler'):
    sys.path.insert(0, '..')

import unittest

from genshi_compiler import html_minimizer


class HtmlMinimizerTestCase(unittest.TestCase):
    """ Unit test cases for the utility functions
    """

    def test_html_minimizer(self):
        self.assertEqual(html_minimizer.minimize('<html />'), b'<html/>')
        self.assertEqual(html_minimizer.minimize('  <html />   '), b'<html/>')
        self.assertEqual(html_minimizer.minimize(' \n <html />  \n '), b'<html/>')
        self.assertEqual(html_minimizer.minimize('<html></html>'), b'<html/>')
        self.assertEqual(html_minimizer.minimize('<html>x</html>'), b'<html>x</html>')
        self.assertEqual(html_minimizer.minimize('<html> x </html>'), b'<html> x </html>')
        self.assertEqual(html_minimizer.minimize('<html>  x  </html>'), b'<html> x </html>')
        self.assertEqual(html_minimizer.minimize('<html> \n x \n </html>'), b'<html> x </html>')
        self.assertEqual(html_minimizer.minimize('<html> \n </html>'), b'<html>\n</html>')
        self.assertEqual(html_minimizer.minimize('<html> \n\n \n  \n \n  </html>'), b'<html>\n</html>')


if __name__ == '__main__':
    unittest.main()
