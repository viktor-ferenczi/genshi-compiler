""" HTML minimizer

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Minimizes HTML by reducing all duplicate whitespace and newlines.

Accepts only valid XML markup, since this function is parsing the document.
This function might modify the location of XML namespace declarations, but
the still remain valid. Comments, processing instructions and CDATA
sections are kept intact.
    
"""

__all__ = ['minimize']

import lxml
from lxml import etree

import constants


def minimize_text(text):
    if not text:
        return text
    
    if text.strip():
        if text != text.lstrip():
            text = ' ' + text.lstrip()
        if text != text.rstrip():
            text = text.rstrip() + ' '
        return text
            
    if '\n' in text:
        return '\n'
    
    return ' '

def minimize_element(element):
    element.text = minimize_text(element.text)
    element.tail = minimize_text(element.tail)
    for child in element.getchildren():
        minimize_element(child)

def minimize(html):
    """ Minimizes HTML by reducing all duplicate whitespace and newlines
    
    Accepts only valid XML markup, since this function is parsing the document.
    This function might modify the location of XML namespace declarations, but
    the still remain valid. Comments, processing instructions and CDATA
    sections are kept intact.
    
    """
    tree = etree.fromstring(constants.DOCTYPE_AND_HTML_ENTITIES + html)
    minimize_element(tree)
    tree.tail = ''
    html = etree.tostring(tree)
    return html
