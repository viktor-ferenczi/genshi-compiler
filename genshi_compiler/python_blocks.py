""" Classes to represent Python source code blocks

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

import itertools

import constants, util, base_blocks


### Control constructs

DummyBlock = base_blocks.DummyBlock

class ModuleBlock(base_blocks.ModuleBlock):
    __slots__ = base_blocks.ModuleBlock.__slots__
    
    # Header of the generated Python modules
    header_template = '''\
#!/usr/bin/python
# -*- coding: ascii -*-

""" Generated template rendering code

WARNING: This is automatically generated source code!
WARNING: Do NOT modify this file by hand or YOUR CHANGES WILL BE LOST!

Modify the following XML template file instead:

%(template_filename)s

Then don't forget to regenerate this module.

"""

import xml.sax.saxutils


# Converts any object to unicode
_x_to_text = unicode

# XML escaping text
_x_escape_text = xml.sax.saxutils.escape

def _x_escape_attribute(value, quoteattr=xml.sax.saxutils.quoteattr):
    """ Escapes an XML attribute value
    """
    return quoteattr("'" + value)[2: -1]

def _x_format_attributes(_x_append_markup, attributes):
    """ Emits dynamic attributes at runtime
    """
    global _x_escape_attribute

    for attribute_name, attribute_value in attributes.iteritems():
        if attribute_value is not None:
            _x_append_markup(' %%s="%%s"' %% (
                attribute_name, _x_escape_attribute(attribute_value)))
'''    
    
    # No module footer needed
    
class FunctionDefinitionBlock(base_blocks.FunctionDefinitionBlock):
    __slots__ = base_blocks.FunctionDefinitionBlock.__slots__
    
    # Function body header
    # NOTE: Do NOT add gettext_translator to the list of globals!
    #       That can be owerridden by a parameter, it is intentional!
    header_template = '''\
global _x_to_text, _x_escape_text

_x_markup_fragments = []
_x_append_markup = _x_markup_fragments.append

'''
    
    # Function body footer
    footer_template = '''\

_x_html = u''.join(_x_markup_fragments)
return _x_html
'''
    
    # Empty function
    empty_body_template = '''\
return u''
'''
    
    def format(self, depth=0):
        lines = (
            [(depth, 'def %s:' % self.data)] +
            base_blocks.FunctionDefinitionBlock.format(self, depth + 1))
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)

        return lines
    
class LoopBlock(base_blocks.LoopBlock):
    __slots__ = base_blocks.LoopBlock.__slots__
    
    def format(self, depth=0):
        lines = (
            [(depth, 'for %s:' % self.data)] +
            base_blocks.LoopBlock.format(self, depth + 1))
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)

        return lines

class ConditionalBlock(base_blocks.ConditionalBlock):
    __slots__ = base_blocks.ConditionalBlock.__slots__
    
    def format(self, depth=0):
        lines = (
            [(depth, 'if %s:' % self.data)] +
            base_blocks.ConditionalBlock.format(self, depth + 1))

        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class SwitchBlock(base_blocks.SwitchBlock):
    __slots__ = base_blocks.SwitchBlock.__slots__
    
    def format(self, depth=0):
        
        assert len(self.otherwise_blocks) < 2, (
            'Only one py:otherwise directive is allowed inside a py:choose! '
            'Found %d of them!' % len(self.otherwise_blocks))
        
        if self.when_blocks:
            lines = self.format_if_elif_else(depth, self.data.strip())
        else:
            if self.otherwise_blocks:
                lines = self.otherwise_blocks[0].format(depth)
            else:
                lines = []
                
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)

        return lines
    
    def format_if_elif_else(self,
                            depth,
                            expression='',
                            counter=itertools.count()):
        """ The test expression is empty, so we test for truth values only
        """
        lines = []

        if expression:
            index = counter.next()
            variable_name = '_x_switch_%d' % index
            lines.append((depth, '%s = %s' % (variable_name, expression)))
        
        for index, when_block in enumerate(self.when_blocks):
            statement = 'elif' if index else 'if'
            if expression:
                condition = '%s == (%s)' % (variable_name, when_block.data)
            else:
                condition = when_block.data
            when_lines = [(depth, '%s %s:' % (statement, condition))]
            when_lines.extend(when_block.format(depth + 1))
            if constants.GENERATE_DEBUG_COMMENTS:
                when_block.insert_debug_comment(when_lines, depth)
            lines.extend(when_lines)
        
        if self.otherwise_blocks:
            otherwise_lines = (
                [(depth, 'else:')] +
                self.otherwise_blocks[0].format(depth + 1))
            if constants.GENERATE_DEBUG_COMMENTS:
                self.otherwise_blocks[0].insert_debug_comment(otherwise_lines, depth)
            lines.extend(otherwise_lines)
            
        return lines

class CaseBlock(base_blocks.CaseBlock):
    __slots__ = base_blocks.CaseBlock.__slots__
    
class OtherwiseBlock(base_blocks.OtherwiseBlock):
    __slots__ = base_blocks.OtherwiseBlock.__slots__

class WithBlock(base_blocks.WithBlock):
    __slots__ = base_blocks.WithBlock.__slots__
    
    def format(self, depth=0, counter=itertools.count()):
        index = counter.next()
        function_name = '_x_with_%d' % index
        
        lines = (
            [(depth, 'def %s():' % function_name),
             (depth + 1, self.data)] +
            base_blocks.WithBlock.format(self, depth + 1) +
            [(depth, '%s()' % function_name)])
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
        
### Element hierarchy    
    
class ElementBlock(base_blocks.ElementBlock):
    __slots__ = base_blocks.ElementBlock.__slots__
    
    def format(self, depth=0, counter=itertools.count()):
        lines = []
        
        if self.start_tag:
            # NOTE: Empty string strip expressions are already processed in the
            #       compilation phase. So we do not get an empty expression or
            #       static truth values here, only expressions have to be
            #       evaluated at runtime.
            if self.strip_expression:
                index = counter.next()
                variable_name = '_x_keep_%d' % index
                lines.append((depth, '%s = not (%s)' % (variable_name, self.strip_expression)))
                lines.append((depth, 'if %s:' % variable_name))
                lines.extend(self.start_tag.format(depth + 1))
            else:
                lines.extend(self.start_tag.format(depth))
                
        lines.extend(base_blocks.ElementBlock.format(self, depth))
        
        if self.end_tag:
            if self.strip_expression:
                lines.append((depth, 'if %s:' % variable_name))
                lines.extend(self.end_tag.format(depth + 1))
            else:
                lines.extend(self.end_tag.format(depth))
                
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class OpeningTagBlock(base_blocks.OpeningTagBlock):
    __slots__ = base_blocks.OpeningTagBlock.__slots__

class ClosingTagBlock(base_blocks.ClosingTagBlock):
    __slots__ = base_blocks.ClosingTagBlock.__slots__
    
class AttributeValueBlock(base_blocks.AttributeValueBlock):
    __slots__ = base_blocks.AttributeValueBlock.__slots__
    
### Generated source code blocks
    
class MarkupBlock(base_blocks.MarkupBlock):
    __slots__ = base_blocks.MarkupBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(%r)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class AttributeValueFragmentBlock(base_blocks.AttributeValueFragmentBlock):
    __slots__ = base_blocks.AttributeValueFragmentBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(%r)' % util.escape_attribute(self.data))]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class TextBlock(base_blocks.TextBlock):
    __slots__ = base_blocks.TextBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(%r)' % util.escape_text(self.data))]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class MarkupExpressionBlock(base_blocks.MarkupExpressionBlock):
    __slots__ = base_blocks.MarkupExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(%s)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class TextExpressionBlock(base_blocks.TextExpressionBlock):
    __slots__ = base_blocks.TextExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(_x_escape_text(_x_to_text(%s)))' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class AttributeExpressionBlock(base_blocks.AttributeExpressionBlock):
    __slots__ = base_blocks.AttributeExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_append_markup(_x_escape_attribute(_x_to_text(%s)))' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class DynamicAttributesBlock(base_blocks.DynamicAttributesBlock):
    __slots__ = base_blocks.DynamicAttributesBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_x_format_attributes(_x_append_markup, %s)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class StaticCodeBlock(base_blocks.StaticCodeBlock):
    __slots__ = base_blocks.StaticCodeBlock.__slots__
