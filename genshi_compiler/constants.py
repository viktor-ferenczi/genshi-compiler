""" Constants

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Provides all the constants at one single place.

"""

import os, re, htmlentitydefs, itertools

import lxml
from lxml import etree


# Debugging inside Wing IDE
DEBUGGING = 'WINGDB_PYTHON' in os.environ

# Enables the detection of recursive blocks right when the loop is created
DETECT_RECURSION = DEBUGGING

# Enables showing debug information in the compiled template code
GENERATE_DEBUG_COMMENTS = DEBUGGING and False

# Dump the block tree at various stages
DUMP_BLOCK_TREE_BEFORE_POSTPROCESSING = DEBUGGING and False
DUMP_BLOCK_TREE_AFTER_POSTPROCESSING = DEBUGGING and False
DUMP_BLOCK_TREE_AFTER_OPTIMIZATION = DEBUGGING and False

# Dump differences in block tree dumps
# NOTE: Generating these can be very slow and take many seconds on a Core i7!
PRINT_POSTPROCESSING_DIFFERENCE = DEBUGGING and False
PRINT_OPTIMIZATION_DIFFERENCE = DEBUGGING and False

# Matches strings suitable as Python identifiers
RX_IDENTIFIER = re.compile(r'^[a-z_]\w*$', re.I)

# Regexp to split text containing template variable references
RX_TEMPLATE_EXPRESSION = re.compile(
    r'\$(?:(\$)|\{(.*?)\}|([a-z_]\w*(?:\.[a-z_]\w*)*))', re.I)

# Regexp to find duplicate whitespace and newline characters
RX_DUPLICATE_WHITESPACE = re.compile(r'(\s\s+)', re.DOTALL)

# Regexp to count whitespace at the beginning
RX_LEFT_WHITESPACE = re.compile(r'^(\s*).*$', re.DOTALL)

# Regexp to separate the lading and trailing whitespace if any
RX_LEFT_RIGHT_WHITESPACE = re.compile(r'^(\s*)(.*?)(\s*)$', re.DOTALL)

# Split a text to heading whitespace, text and trailing whitespace
RX_WHITESPACE_HEAD_TAIL = re.compile(r'^(\s*)(.*?)(\s*)$', re.DOTALL)

# Regular expression to match the element template in i18n:msg translations
RX_I18N_MSG_ELEMENT = re.compile(ur'\[(\d+):(.*?)\]')

# Regular expression to split the translated i18n:msg template at compile time
RX_I18N_MSG_TEMPLATE_ITEM = re.compile(ur'%\(([a-z_0-9:]+)\)s', re.I)

# XML namespace identifiers
XML_NAMESPACE_GENSHI = 'http://genshi.edgewall.org/'
XML_NAMESPACE_I18N = 'http://genshi.edgewall.org/i18n'
XML_NAMESPACE_XINCLUDE = 'http://www.w3.org/2001/XInclude'

# Tuple of all of our namespace identifiers, they must not go into the output
XML_NAMESPACES_PROCESSED = (
    XML_NAMESPACE_GENSHI,
    XML_NAMESPACE_I18N,
    XML_NAMESPACE_XINCLUDE)

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
    'i18n:msg',
    'i18n:comment',
    'i18n:domain',
    'i18n:choose',
    'i18n:singular',
    'i18n:plural',
    'xi:include',
    'xi:fallback',
    )

# Genshi attribute directives in reverse processing order, since we build up
# the generated code bottom-up, e.g. from the deeper structure to the top level
GENSHI_ATTRIBUTES = (
    'i18n:comment',
    'i18n:msg',
    'py:strip',
    'py:attrs',
    'py:content',
    'py:replace',
    'py:with',
    'i18n:choose',
    'i18n:singular',
    'i18n:plural',
    'py:choose',
    'py:if',
    'py:for',
    'py:otherwise',
    'py:when',
    'py:match',
    'i18n:domain',
    'py:def',
    )

# Genshi elements and attributes with full URL prefixes
# FIXME: It could be written faster, but it is at least readable this way.
def xml_namespace_prefix_to_url(name):
    """ Converts a name using the usual py:, xi: or i18n: prefixes to one
    with the Genshi namespace URL in curly brackets (lxml's notation)
    
    """
    if name.startswith('py:'):
        return '{%s}%s' % (XML_NAMESPACE_GENSHI, name[3:])
    
    if name.startswith('xi:'):
        return '{%s}%s' % (XML_NAMESPACE_XINCLUDE, name[3:])
    
    if name.startswith('i18n:'):
        return '{%s}%s' % (XML_NAMESPACE_I18N, name[5:])
    
    return name

GENSHI_ELEMENTS_WITH_URL = tuple(
    itertools.imap(xml_namespace_prefix_to_url, GENSHI_ELEMENTS))

GENSHI_ATTRIBUTES_WITH_URL = tuple(
    itertools.imap(xml_namespace_prefix_to_url, GENSHI_ATTRIBUTES))

del xml_namespace_prefix_to_url

# HTML entities as a DTD
DOCTYPE_AND_HTML_ENTITIES = (
    '<!DOCTYPE html [' +
    ''.join(
        '<!ENTITY %s "&#%d;">' % (name, value)
        for name, value in htmlentitydefs.name2codepoint.items()) +
    ']>')

# HTML elements can be written in short form without a end tag
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
    'frame',
    )
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
##    'defer',
##    )
##BOOLEAN_HTML_ATTRIBUTES_SET = frozenset(BOOLEAN_HTML_ATTRIBUTES)

# Default list of XHTML 1.1 elements with translatable contents
XHTML_ELEMENTS_TO_TRANSLATE = (
    'a',
    'caption', 
    'dd', 
    'dt', 
    'label', 
    'legend', 
    'li', 
    'option', 
    'p', 
    'rb', 
    'rp', 
    'rt', 
    'td', 
    'th', 
    'title',
    'span',
    'div',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    )

# Default list of XHTML 1.1 attributes with translatable value
# FIXME: It does not consider the value attribute of input buttons for translation!
XHTML_ATTRIBUTES_TO_TRANSLATE = (
    'abbr', 
    'alt', 
    'label', 
    'prompt', 
    'standby', 
    'summary', 
    'title',
    )

# Additional entities for escaping XML, it is for use with xml.sax.saxutils.escape
# NOTE: These are above the core set of &amp; &lt; &gt; entities.
EXTRA_ESCAPE_XML_ENTITIES = {
    "'": '&apos;',
    '"': '&quot;',
    }

# Additional entities for unescaping XML, it is for use with xml.sax.saxutils.unescape
# NOTE: These are above the core set of &amp; &lt; &gt; entities.
EXTRA_UNESCAPE_XML_ENTITIES = {
    '&apos;': "'",
    '&quot;': '"',
    }
