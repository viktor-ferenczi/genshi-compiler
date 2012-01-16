""" Utility functions

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Provides context independent utility functions.

"""

import difflib, xml.sax.saxutils

import constants, util


# XML escaping (does not support HTML entities, only the base set of XML entities)
escape_text = xml.sax.saxutils.escape
unescape_xml = xml.sax.saxutils.unescape

def escape_attribute(value, quoteattr=xml.sax.saxutils.quoteattr):
    """ Escapes a value to be usitable for double quoted XML attributes
    """
    return quoteattr("'" + value)[2: -1]

def is_identifier(name):
    """ Returns True if the given name is acceptable as a Python identifier
    """
    return constants.RX_IDENTIFIER.match(name)

def namespace_url_to_prefix(nsmap, full_name):
    """ Maps tag or attribute name from the long namespace reference (URL)
    to the short prefix format
    
    nsmap: map of namespace URLs to prefixes
    
    """
    if not full_name.startswith('{'):
        return full_name
    
    i = full_name.find('}')
    assert i > 0, 'Invalid tag or attribute name: %r' % (full_name, )
    
    namespace_url = full_name[1: i]
    name = full_name[i + 1:]
    
    prefix = nsmap.get(namespace_url)
    
    if prefix:
        return '%s:%s' % (prefix, name)

    return name

def split_source_to_lines(source_text, depth=0, tab_size=8):
    """ Splits the source code text to code lines, convert tabulators
    to spaces, remove common indentation, define the code lines with
    the given depth
    
    """
    # Split the source code to lines.
    # Also remove trailing whitespace and convert all tabs to spaces.
    code_line_list = [
        util.tab_to_space(code_line.rstrip(), tab_size)
        for code_line in source_text.split('\n')]
    
    # Count whitespace at the beginning of each line
    code_line_with_whitespace_count_list = [
        (code_line,
         len(constants.RX_LEFT_WHITESPACE.match(code_line).group(1)))
        for code_line in code_line_list]
    
    # Determine the common indentation
    common_indentation = min(
        whitespace_count
        for code_line, whitespace_count in code_line_with_whitespace_count_list)
    
    # Remove common indentation by dedenting all the lines
    lines = [
        (depth, code_line[common_indentation:])
        for code_line in code_line_list]
    
    return lines

def tab_to_space(code_line, tab_size=8):
    """ Replaces tabulators with spaces
    """
    # Look up each tab character one by one
    while 1:
        
        # Find the next tab character
        tab_position = code_line.find('\t')
        if tab_position < 0:
            break
        
        # Replace that single tab with as many spaces as needed to position text
        code_line = code_line.replace(
            '\t', ' ' * (tab_size - tab_position % tab_size), 1)
        
    return code_line

def parse_boolean_expression(expression, default=None):
    """ Parses trivial constant boolean expressions
    
    Returns True if the expression is always true.
    Returns False if the expression is always false.
    Returns default if the expression is empty.
    Returns the expression as is otherwise.
    
    """
    expression = expression.strip()
    if not expression:
        return default
    
    if expression.lower() == 'true':
        return True
    
    if expression.lower() == 'false':
        return False
    
    if expression.isdigit():
        return bool(int(expression))
    
    return expression

def reduce_whitespace(whitespace):
    """ Reduces the whitespace to a single newline if there's a newline there
    or a single space otherwise
    """
    assert not whitespace.strip()
    
    if not whitespace:
        return whitespace
    
    if '\n' in whitespace:
        return '\n'
    
    return ' '

def remove_duplicate_whitespace(text):
    """ Removes all the duplicate whitespace and newline characters
    """
    return constants.RX_DUPLICATE_WHITESPACE.subn(
        lambda m: reduce_whitespace(m.group(0)), text)[0]

def separate_whitespace(text):
    """ Separates the leading and trailing whitespace
    
    Returns (leading_whitespace, non_whitespace_text, trailing_whitespace)
    
    """
    empty_string = text[:0]
    if not text.strip():
        return (text, empty_string, empty_string)
    left, center, right = constants.RX_LEFT_RIGHT_WHITESPACE.match(text).groups()
    return (left, center or empty_string, right or empty_string)

def print_diff(a_text, b_text, a_label, b_label):
    """ Returns printable unified diff of two multiline text values
    """
    # We need to ensure that the last line has a newline at its end to
    # prevent a missing newline in the last diff line, if the last line
    # is removed in b_text
    if a_text[-1:] not in '\r\n':
        a_text += '\n'
    if b_text[-1:] not in '\r\n':
        b_text += '\n'

    # Determine and print unified diff
    print ''.join(
        difflib.unified_diff(
            a_text.splitlines(1),
            b_text.splitlines(1),
            a_label,
            b_label))
