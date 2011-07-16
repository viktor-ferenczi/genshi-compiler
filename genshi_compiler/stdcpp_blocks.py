""" Classes to represent standard C++ source code blocks

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
// %(template_identifier)s.h
// -*- coding: ascii -*-

/* Generated template rendering code based on the following Genshi
XML template: %(template_identifier)s

WARNING: This is automatically generated source code!
WARNING: Do NOT modify this file by hand or YOUR CHANGES WILL BE LOST!

Modify the %(template_filename)s
XML template file, then regenerate this header file instead.

*/

#include <map>
#include <list>
#include <string>

typedef std::string _xt_string;
typedef std::list<_xt_string> _xt_output;
typedef std::map<_xt_string, _xt_string> _xt_dynamic_attribute_map;

// Escapes the following characters: & < >
inline _xt_string _x_escape_text(_xt_string) {
}

// Escapes the following characters: & < > " '
inline _xt_string _x_escape_attribute(_xt_string) {
}

// Converts string to string (identity)
inline _xt_string _x_str_to_text(_xt_string) {
    return _xt_string;
}

// Converts 8 bit UTF-8 text to _xt_string
inline _xt_string_x_str_to_text(const char *s) {
}

// Converts a boolean value to unicode text, e.g. "True" or "False"
inline _xt_string_x_bool_to_text(bool n) {
}

// Converts an integer to unicode text
inline _xt_string_x_int_to_text(int n) {
}

// Converts a long to unicode text
inline _xt_string_x_long_to_text(long n) {
}

// Converts a float to unicode text with maximum precision
inline _xt_string_x_float_to_text(float n) {
}

// Converts a double to unicode text with maximum precision
inline _xt_string_x_double_to_text(double n) {
}

def _xf_format_attributes(_xt_output output, _xt attributes):
    """ Emits attributes at runtime
    
    The attributes can be 
    
    """
    
# TODO: Continue here!

    
    global _x_escape_attribute
    
    for attribute_name, attribute_value in attributes.iteritems():
        if attribute_value is not None:
            _xf_append_markup(' %%s="%%s"' %% (
                attribute_name, _x_escape_attribute(attribute_value)))
'''
    
    # No module footer needed
    
class FunctionDefinitionBlock(base_blocks.FunctionDefinitionBlock):
    __slots__ = base_blocks.FunctionDefinitionBlock.__slots__
    
    # Function body header
    header_template = '''\
global _x_escape_text, _x_escape_attribute, _x_to_text

_x_markup_fragments = []
_xf_append_markup = _x_markup_fragments.append
'''
    
    # Function body footer
    footer_template = '''\

_x_html = ''.join(_x_markup_fragments)
return _x_html
'''
    
    def format(self, depth=0):    
        
        lines = (
            [(depth, 'def %s:' % self.data)] +
            base_blocks.FunctionDefinitionBlock.format(self, depth))
        
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
            if self.data.strip():
                lines = self.format_switch(depth)
            else:
                lines = self.format_if_elif_else(depth)
        else:
            if self.otherwise_blocks:
                lines = self.otherwise_blocks[0].format(depth)
            else:
                lines = []
                
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)

        return lines
    
    def format_switch(self, depth, counter=itertools.count()):
        """ There is a test expression we have to check for possible values
        """
        
        index = counter.next()
        function_name = '_x_switch_%d' % index
        variable_name = '_x_switch_value_%d' % index
        
        lines = [(depth, 'def %s(%s):' % (function_name, variable_name))]
        
        for when_block in self.when_blocks:
            when_lines = (
                [(depth + 1, 'if %s == (%s):' % (variable_name, when_block.data))] +
                when_block.format(depth + 2) +
                [(depth + 2, 'return')])
            if constants.GENERATE_DEBUG_COMMENTS:
                when_block.insert_debug_comment(when_lines, depth + 1)
            lines.extend(when_lines)
        
        if self.otherwise_blocks:
            otherwise_lines = self.otherwise_blocks[0].format(depth + 1)
            if constants.GENERATE_DEBUG_COMMENTS:
                self.otherwise_blocks[0].insert_debug_comment(otherwise_lines, depth + 1)
            lines.extend(otherwise_lines)
            
        lines.append((depth, '%s(%s)' % (function_name, self.data)))
        
        return lines
    
    def format_if_elif_else(self, depth):
        """ The test expression is empty, so we test for truth values only
        """
        lines = []
        
        for index, when_block in enumerate(self.when_blocks):
            statement = 'elif' if index else 'if'
            when_lines = (
                [(depth, '%s %s:' % (statement, when_block.data))] +
                when_block.format(depth + 1))
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
        
        if self.opening_tag:
            # NOTE: Empty string strip expressions are already processed in the
            #       compilation phase. So we do not get an empty expression or
            #       static truth values here, only expressions have to be
            #       evaluated at runtime.
            if self.strip_expression:
                index = counter.next()
                variable_name = '_x_keep_%d' % index
                lines.append('%s = not (%s)' % (variable_name, self.strip_expression))
                lines.append('if %s:')
                lines.extend(self.opening_tag.format(depth + 1))
            else:
                lines.extend(self.opening_tag.format(depth))
                
        lines.extend(base_blocks.ElementBlock.format(self, depth))
        
        if self.closing_tag:
            if self.strip_expression:
                lines.append('if %s:')
                lines.extend(self.closing_tag.format(depth + 1))
            else:
                lines.extend(self.closing_tag.format(depth))
                
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class OpeningTagBlock(base_blocks.OpeningTagBlock):
    __slots__ = base_blocks.OpeningTagBlock.__slots__

class ClosingTagBlock(base_blocks.ClosingTagBlock):
    __slots__ = base_blocks.ClosingTagBlock.__slots__

### Generated source code blocks
    
class MarkupBlock(base_blocks.MarkupBlock):
    __slots__ = base_blocks.MarkupBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_xf_append_markup(%r)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class MarkupExpressionBlock(base_blocks.MarkupExpressionBlock):
    __slots__ = base_blocks.MarkupExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_xf_append_markup(%s)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class TextExpressionBlock(base_blocks.TextExpressionBlock):
    __slots__ = base_blocks.TextExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_xf_append_markup(_x_escape_text(_x_to_text(%s)))' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class AttributeExpressionBlock(base_blocks.AttributeExpressionBlock):
    __slots__ = base_blocks.AttributeExpressionBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_xf_append_markup(_x_escape_attribute(_x_to_text(%s)))' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class DynamicAttributesBlock(base_blocks.DynamicAttributesBlock):
    __slots__ = base_blocks.DynamicAttributesBlock.__slots__
    
    def format(self, depth=0):
        lines = [(depth, '_xf_format_attributes(_xf_append_markup, %s)' % self.data)]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines

class StaticCodeBlock(base_blocks.StaticCodeBlock):
    __slots__ = base_blocks.StaticCodeBlock.__slots__
