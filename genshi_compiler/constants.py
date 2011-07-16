""" Constants

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Provides all the constants at one single place.

"""

import os, re, htmlentitydefs, cStringIO

import lxml
from lxml import etree


# Debugging inside Wing IDE
DEBUGGING = 'WINGDB_PYTHON' in os.environ

# Enables the detection of recursive blocks right when the loop is created
DETECT_RECURSION = DEBUGGING

# Enables showing debug information in the compiled template code
GENERATE_DEBUG_COMMENTS = DEBUGGING

# Dump the block tree at various stages
DUMP_BLOCK_TREE_BEFORE_POSTPROCESSING = DEBUGGING and False
DUMP_BLOCK_TREE_AFTER_POSTPROCESSING = DEBUGGING and False
DUMP_BLOCK_TREE_AFTER_OPTIMIZATION = DEBUGGING and False

# Dump differences in block tree dumps
# NOTE: Generating these can be very slow and take many seconds on a Core i7!
PRINT_POSTPROCESSING_DIFFERENCE = DEBUGGING and False
PRINT_OPTIMIZATION_DIFFERENCE = DEBUGGING and False

# Matches strings suitable as Python identifiers
RX_IDENTIFIER = re.compile(r'^[a-z_][a-z_0-9]*$', re.I)

# Regexp to split text containing template variable references
RX_TEMPLATE_EXPRESSION = re.compile(r'\$([a-z0-9_\.]+)|\$\{(.*?)\}', re.I)

# Regexp to find duplicate whitespace and newline characters
RX_DUPLICATE_WHITESPACE = re.compile(r'(\s\s+)')

# Regexp to count whitespace at the beginning of a source code line
RX_LEFT_WHITESPACE = re.compile(r'^(\s*).*$')

# Split a text to heading whitespace, text and trailing whitespace
RX_WHITESPACE_HEAD_TAIL = re.compile(r'^(\s*)(.*?)(\s*)$', re.DOTALL)

# XML namespace identifiers
XML_NAMESPACE_GENSHI = 'http://genshi.edgewall.org/'
XML_NAMESPACE_XINCLUDE = 'http://www.w3.org/2001/XInclude'

# Genshi element directives
GENSHI_ELEMENTS = (
    'py:def',
    'py:match',
    'py:when',
    'py:otherwise',
    'py:for',
    'py:if',
    'py:choose',
    'py:with',
    'xi:include',
    'xi:fallback')

# Genshi attribute directives in reverse processing order, since we build up
# the generated code bottom-up, e.g. from the deeper structure to the top level
GENSHI_ATTRIBUTES = (
    'py:strip',
    'py:attrs',
    'py:content',
    'py:replace',
    'py:with',
    'py:choose',
    'py:if',
    'py:for',
    'py:otherwise',
    'py:when',
    'py:match',
    'py:def')

# Genshi elements and attributes with full URL prefixes
def xml_namespace_prefix_to_url(name):
    """ Converts a name using the usual py: and xi: prefixes to one
    with the Genshi namespace URL in curly brackets (lxml's notation)
    
    """
    name = name.replace('py:', '{%s}' % XML_NAMESPACE_GENSHI)
    name = name.replace('xi:', '{%s}' % XML_NAMESPACE_XINCLUDE)
    return name
GENSHI_ELEMENTS_WITH_URL = map(xml_namespace_prefix_to_url, GENSHI_ELEMENTS)
GENSHI_ATTRIBUTES_WITH_URL = map(xml_namespace_prefix_to_url, GENSHI_ATTRIBUTES)
del xml_namespace_prefix_to_url

# HTML entities as a DTD
DOCTYPE_AND_HTML_ENTITIES = (
    '<!DOCTYPE html [' +
    ''.join(
        '<!ENTITY %s "&#%d;">' % (name, value)
        for name, value in htmlentitydefs.name2codepoint.items()) +
    ']>')

# HTML elements can be written in short form without a closing tag
# See also: http://www.w3.org/TR/xhtml1/#guidelines
SHORT_HTML_ELEMENTS = (
    'base',
    'meta',
    'link',
    'hr',
    'br',
    'param',
    'img',
    'area',
    'input',
    'col',
    'basefont',
    'isindex',
    'frame')
SHORT_HTML_ELEMENTS_SET = frozenset(SHORT_HTML_ELEMENTS)

# FIXME: This is not used, currently.
### HTML attributes with boolean value
### See also: http://www.w3.org/TR/xhtml1/#guidelines
##BOOLEAN_HTML_ATTRIBUTES = (
##    'compact',
##    'nowrap',
##    'ismap',
##    'declare',
##    'noshade',
##    'checked',
##    'disabled',
##    'readonly',
##    'multiple',
##    'selected',
##    'noresize',
##    'defer')
##BOOLEAN_HTML_ATTRIBUTES_SET = frozenset(BOOLEAN_HTML_ATTRIBUTES)
