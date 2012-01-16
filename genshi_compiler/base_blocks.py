""" Base class to represent a block of generated source code

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

import constants, util


class BaseBlock(object):
    """ Base class for classes representig a block of generated source code
    
    It is like a namedtuple, but allows for source code completion in Wing IDE.

    data: compile time information the source code line can be rendered from
    lineno: corresponding line number in the Genshi template
    depth: integer level of source code indentation
    
    Please note, that subclasses must also include __slots__ to conserve memory!
    
    """
    __slots__ = (
        'lineno', 
        'data', 
        'children',
        'element',
        'attribute')
    
    if constants.GENERATE_DEBUG_COMMENTS:
        __slots__ = __slots__ + ('template_line', )
    
    def __init__(self,
                 lineno,
                 data=None,
                 children=None):
        
        assert isinstance(lineno, int)
        assert children is None or isinstance(children, list)

        # Template (source) line number
        self.lineno = lineno
        
        # Data required to render the source code block (not its children)
        self.data = data
        
        # List of child blocks
        self.children = children or []
        
        # Refers to the foreign (non-Genshi) element containing this block.
        # It is set only for certain elements where knowing the element is
        # needed. It is used only dueing the compilation and postprocessing
        # phases and cleared by the optimization step to break the reference
        # loops.
        self.element = None
        
        # Refers to the AttributeValueBlock containing this block or None
        self.attribute = None
        
        # Template line, used only while printing debug comments
        if constants.GENERATE_DEBUG_COMMENTS:
            self.template_line = None
        
    def __str__(self):
        member_variables = [
            (name, getattr(self, name))
            for name in self.__slots__]
        member_variables = ', '.join(
            ('%s=%s(...)' % (name, value.__class__.__name__)
             if isinstance(value, BaseBlock)
             else '%s=%r' % (name, value))
            for name, value in member_variables)
        return '%s(%s)' % (self.__class__.__name__, member_variables)

# NOTE: The full repr isn't really useful, since producing too verbose output
#       and failing badly if we accidentally have a loop in out block tree.
##    def __repr__(self):
##        member_variables = ', '.join(
##            '%s=%r' % (name, getattr(self, name))
##            for name in self.__slots__)
##        return '%s(%s)' % (self.__class__.__name__, member_variables)

    __repr__ = __str__
    
    ### Operations

    def clear(self):
        del self.children[:]
    
    if constants.DETECT_RECURSION:
        
        def contains(self, block, visited=set()):
            if id(self) in visited:
                return False
            visited.add(id(self))
            for child in self.children:
                if child is block:
                    return True
                if child.contains(block, visited):
                    return True
            return False
        
        def append(self, *blocks):
            assert self not in blocks
            for block in blocks:
                assert isinstance(block, BaseBlock)
                assert not self.contains(block)
            self.children.extend(blocks)
            
        def extend(self, blocks):
            assert self not in blocks
            for block in blocks:
                assert isinstance(block, BaseBlock)
                assert not self.contains(block)
            self.children.extend(blocks)
            
    else:
            
        def append(self, *blocks):
            self.children.extend(blocks)
            
        def extend(self, blocks):
            self.children.extend(blocks)

    def apply_transformation(self, transformation, *args, **kws):
        """ Applies the given transformation to all the child blocks
        
        transformation: Function to call to transform the block to something
            else, receives the block as its first parameter and returns the
            list of replacement blocks, which can be an empty list to remove
            the block completely.
            
        args, kws: Extra parameters to pass to the transformation function.
        
        """
        transformed_children = []
        for child in self.children:
            transformed_children.extend(transformation(child, *args, **kws))
        self.children = transformed_children
        
    ### Queries

    def is_empty(self):
        """ Returns True if the block can't generate any output for sure
        and is not needed for the structure of the generated code for
        another reason, e.g. removing this block will not affect the
        output of the generated code in any way
        
        """
        return not self.children
    
    def is_whitespace(self):
        """ Returns True if this block represents only empty or whitespace
        markup for sure
        
        Child blocks are also considered to any depth.
        Newline and tabulators are considered whitespace.
        
        """
        for child in self.children:
            if child.is_whitespace():
                return True
        return False
    
    def is_invariant(self):
        """ Returs True if the block does not use any of the
        template variables for sure
        
        """
        return False

    def get_i18n_text(self):
        return u''.join(child.get_i18n_text() for child in self.children)
    
    ### Overridables
    
    def format(self, depth=0):
        """ Formats source code
        
        depth: indentation depth
        
        Returns list of code line tuples: (depth, code)
        
        """
        lines = self.format_children(depth)
        
        if constants.GENERATE_DEBUG_COMMENTS and self.__class__ is BaseBlock:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
    def format_children(self, depth):
        lines = []
        
        for child in self.children:
            child_lines = child.format(depth)
            lines.extend(child_lines)

        return lines
    
    ### Debugging

    if constants.DEBUGGING:
        
        def pretty_format(self, depth=0, indent='  '):
            indentation = indent * (depth + 1)
            
            member_variables = [
                (name, getattr(self, name))
                for name in self.__slots__
                if name != 'template_line']
            
            contains_any_block = False
            for name, value in member_variables:
                if isinstance(value, BaseBlock):
                    contains_any_block = True
                    break
                
            formatted_member_variables = []
            
            if self.children or contains_any_block:
                for name, value in member_variables:
                    if name == 'data' and value is None:
                        continue
                    elif name in ('element', 'attribute'):
                        if value is None:
                            continue
                        elif value is self:
                            formatted_value = 'self'
                        elif value:
                            formatted_value = '%s(lineno=%d)' % (value.__class__.__name__, value.lineno)
                        else:
                            formatted_value = repr(value)
                    elif name == 'children':
                        if value:
                            formatted_value = ',\n'.join(
                                indentation + indent + item.pretty_format(depth + 2)
                                for item in value)
                            formatted_value = '[\n%s]' % (formatted_value)
                        else:
                            continue
                    elif isinstance(value, BaseBlock):
                        formatted_value = value.pretty_format(depth + 1)
                    else:
                        formatted_value = repr(value)
                    formatted_member_variables.append(
                        '%s%s=%s' % (indentation, name, formatted_value))
                return '%s(\n%s)' % (self.__class__.__name__, ',\n'.join(formatted_member_variables))
            
            for name, value in member_variables:
                if name == 'data' and value is None:
                    continue
                elif name == 'element':
                    if value is None:
                        continue
                    elif value is self:
                        formatted_value = 'self'
                    elif value:
                        formatted_value = '%s(lineno=%d)' % (value.__class__.__name__, value.lineno)
                    else:
                        formatted_value = repr(value)
                elif name == 'children':
                    continue
                elif isinstance(value, BaseBlock):
                    formatted_value = value.pretty_format(depth + 1)
                else:
                    formatted_value = repr(value)
                formatted_member_variables.append(
                    '%s=%s' % (name, formatted_value))
            return '%s(%s)' % (self.__class__.__name__, ', '.join(formatted_member_variables))
    
    if constants.GENERATE_DEBUG_COMMENTS:
        
        def insert_debug_comment(self, lines, depth):
            """ Inserts a comment line referring to the template line number
            """
            if self.template_line is not None:
                
                if self.template_line:
                    comment = '# Line #%d: %s' % (self.lineno, self.template_line.strip())
                else:
                    comment = '# Line #%d' % self.lineno
                    
                lines[0:0] = [
                    (depth, ''),
                    (depth, comment)]
                lines.append((depth, ''))
                
class BaseFramedBlock(BaseBlock):
    """ Intermediate base class for blocks with a header and footer
    given as source code templates
    
    """
    __slots__ = BaseBlock.__slots__
    
    # Multiline source code templates for the header and footer parts
    header_template = ''
    footer_template = ''
    
    def format_frame(self, body, depth, info):
        """ Formats the block with the code header and footer (frame)
        """
        # Construct header and footer of the function's body
        header_source = self.header_template % info
        header = util.split_source_to_lines(header_source, depth)
        footer_source = self.footer_template % info
        footer = util.split_source_to_lines(footer_source, depth)
        
        # Construct function definition
        lines = header + body + footer
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
            
        return lines
    
class BaseCodeBlock(BaseBlock):
    """ Base class for code blocks
    
    These blocks must not have any child elements.
    
    """
    __slots__ = BaseBlock.__slots__

    def __init__(self,
                 lineno,
                 data=None,
                 children=[]):
        
        BaseBlock.__init__(self, lineno, data, children)
        
        assert not children, 'No child blocks allowed!'
    
    def clear(self):
        assert False, 'No child blocks allowed!'
        
    def append(self, *blocks):
        assert False, 'No child blocks allowed!'
        
    def extend(self, blocks):
        assert False, 'No child blocks allowed!'
        
    def insert(self, index, block):
        assert False, 'No child blocks allowed!'
        
    def is_empty(self):
        return False
    
    def is_whitespace(self):
        return False
    
    def get_i18n_text(self):
        return u''

    def format(self, depth=0):
        raise NotImplementedError('Override this method!')

    def format_children(self, depth=0):
        assert False, 'No child blocks allowed!'
    
### Control constructs

class DummyBlock(BaseBlock):
    """ Block without additional functionality to group other blocks
    """
    __slots__ = BaseBlock.__slots__
    
class ModuleBlock(BaseFramedBlock):
    """ Block representing the whole generated program module
    
    The data is the template compiler instance.
    
    """
    __slots__ = BaseFramedBlock.__slots__

    def is_empty(self):
        return False
    
    def is_whitespace(self):
        return False
    
    def format(self, depth=0):

        body = self.format_body(depth)
        
        # Module information is taken directly from the template compiler object
        module_info = self.data.__dict__
        
        # Frame the module
        lines = self.format_frame(body, depth, module_info)
        
        return lines
    
    ### Overridables
    
    def format_body(self, depth):
        
        lines = BaseFramedBlock.format(self, depth)
        
        return lines
    
class FunctionDefinitionBlock(BaseFramedBlock):
    """ Block representing a template function definition
    
    The data is the signature of the function, like: fn(a, b=2, c=3)
    
    """
    __slots__ = BaseFramedBlock.__slots__
    
    # Template for the body of empty function definitions
    empty_body_template = ''
    
    def is_empty(self):
        return False
    
    def is_whitespace(self):
        return True

    def get_info(self):
        signature = self.data
        function_name, arguments = signature.split('(', 1)
        arguments = arguments[:-1]
        
        function_info = dict(
            signature=signature,
            function_name=function_name,
            arguments=arguments)
        
        return function_info
    
    def format(self, depth=0):
        
        # Function information
        function_info = self.get_info()

        # Format the body of the function
        body = self.format_body(depth)
        
        # Empty function?
        if not body:
            empty_body_source = self.empty_body_template % function_info
            lines = util.split_source_to_lines(empty_body_source, depth)
            return lines
        
        # Frame the function definition
        lines = self.format_frame(body, depth, function_info)
        
        return lines
    
    ### Overridables
    
    def format_body(self, depth):
        
        lines = BaseFramedBlock.format(self, depth)
        
        return lines
    
class LoopBlock(BaseBlock):
    """ Loop block (for loop)
    
    The data is `variable in expression` in Python's loop format.
    
    The specific compiler might be able to translate it to a non-Python
    programming language, at least a limited subset of such expressions.
    
    """
    __slots__ = BaseBlock.__slots__

class ConditionalBlock(BaseBlock):
    """ Conditional block
    
    The data is an expression to evaluate runtime to get a truth value.
    
    """
    __slots__ = BaseBlock.__slots__
    
class SwitchBlock(BaseBlock):
    """ Block resulting from the compilation of a py:choose directive
    
    The data is an expression to evaluate runtime which will serve as
    the basis for comparison with the case expressions. Empty string
    value indicates that the case clauses will contain truth value
    expressions.
    
    """
    __slots__ = BaseBlock.__slots__ + (
        'when_blocks',
        'otherwise_blocks',
        'prepared')

    def __init__(self,
                 lineno,
                 data=None,
                 children=None,
                 prepared=False):
        
        BaseBlock.__init__(self, lineno, data, children)
    
        # Postprocessing collects the py:when and py:otherwise blocks
        self.when_blocks = []
        self.otherwise_blocks = []
        self.prepared = prepared

    def apply_transformation(self, transformation, *args, **kws):
        BaseBlock.apply_transformation(self, transformation, *args, **kws)

        # NOTE: 
        # We must NOT process the self.when_blocks and self.otherwise_blocks 
        # during the postprocessing step, since they are filled only during
        # that same step which would cause an infinite loop!
        if self.prepared:
            
            for block in self.when_blocks:
                block.apply_transformation(transformation, *args, **kws)
                
            for block in self.otherwise_blocks:
                block.apply_transformation(transformation, *args, **kws)
    
class CaseBlock(BaseBlock):
    """ Block resulting from the compilation of a py:when directive
    
    The data is an expression to evaluate runtime to get a truth value.
    
    """
    __slots__ = BaseBlock.__slots__

    def format(self, depth=0):
        return self.format_children(depth)
    
class OtherwiseBlock(BaseBlock):
    """ Block resulting from the compilation of a py:otherwise directive
    """
    __slots__ = BaseBlock.__slots__

    def format(self, depth=0):
        return self.format_children(depth)
    
class WithBlock(BaseBlock):
    """ Block resulting from the compilation of a py:with directive
    
    The data is the semicolon separated list of local variable assignments.
    
    """
    __slots__ = BaseBlock.__slots__
    
### Element hierarchy

class ElementBlock(BaseBlock):
    """ Block representing a non-Genshi element
    
    The data is the lower case tag name without the XML namespace prefix.
    
    """
    __slots__ = BaseBlock.__slots__ + (
        'start_tag',
        'end_tag',
        'strip_expression',
        'element_number')
    
    def __init__(self,
                 lineno,
                 data=None,
                 children=[],
                 start_tag=None,
                 end_tag=None,
                 strip_expression=None,
                 element_number=None):
        BaseBlock.__init__(self, lineno, data, children)
        
        # Block representing the compiled start tag of the element
        # FIXME: It could be just a list of blocks.
        self.start_tag = start_tag
        
        # Block representing the compiled end tag of the element
        # FIXME: It could be just a list of blocks.
        self.end_tag = end_tag
        
        # Expression to strip out the start and end tags at runtime
        # if any or None to unconditionally keep the tags
        self.strip_expression = strip_expression
        
        # Serial number of this element inside an i18n:msg directive
        self.element_number = element_number
        
        # Type hints
        if 0:
            assert isinstance(self.start_tag, OpeningTagBlock)
            assert isinstance(self.end_tag, ClosingTagBlock)

    def apply_transformation(self, transformation, *args, **kws):
        BaseBlock.apply_transformation(self, transformation, *args, **kws)
        
        # FIXME: Redundant code!
        
        if self.start_tag:
            start_tag = transformation(self.start_tag, *args, **kws)
            if start_tag:
                assert len(start_tag) == 1
                assert isinstance(start_tag[0], OpeningTagBlock)
                self.start_tag = start_tag[0]
            else:
                self.start_tag = None
            
        if self.end_tag:
            end_tag = transformation(self.end_tag, *args, **kws)
            if end_tag:
                assert len(end_tag) == 1
                assert isinstance(end_tag[0], ClosingTagBlock)
                self.end_tag = end_tag[0]
            else:
                self.end_tag = None
        
    def is_empty(self):
        if self.start_tag and not self.start_tag.is_empty():
            return False
        if self.end_tag and not self.end_tag.is_empty():
            return False
        return not self.children
    
    def is_whitespace(self):
        if self.start_tag or self.end_tag:
            return False
        return BaseBlock.is_whitespace(self)
    
    def get_i18n_text(self):
        children_i18n_text = BaseBlock.get_i18n_text(self)
        return u'[%d:%s]' % (self.element_number, children_i18n_text)
    
    if constants.DETECT_RECURSION:
        
        def contains(self, block, visited=set()):
            if self.start_tag and self.start_tag.contains(block, visited):
                return True
            if self.end_tag and self.end_tag.contains(block, visited):
                return True
            return BaseBlock.contains(self, block, visited)
    
# FIXME: This block class would not be needed if element_block.start_tag would be a list of blocks.
class OpeningTagBlock(BaseBlock):
    """ Block representing the start tag of an element
    
    The data is the lower case tag name without the XML namespace prefix.
    
    """
    __slots__ = BaseBlock.__slots__
    
# FIXME: This block class would not be needed if element_block.end_tag would be a list of blocks.
class ClosingTagBlock(BaseBlock):
    """ Block representing the end tag of an element
    
    The data is the lower case tag name without the XML namespace prefix.
    
    """
    __slots__ = BaseBlock.__slots__
    
    def is_invariant(self):
        return True

class AttributeValueBlock(BaseBlock):
    """ Block representing the value of an element attribute
    
    The data is the name of the element attribute, including the namespace
    prefix if any.
    
    """
    __slots__ = BaseBlock.__slots__
    
### Generated source code blocks

class InvariantBlock(BaseCodeBlock):
    """ Common base class for code blocks emitting invariant markup or text
    """
    __slots__ = BaseCodeBlock.__slots__

    def is_empty(self):
        return not self.data
        
    def is_whitespace(self):
        return not self.data.strip()

    def is_invariant(self):
        return True
    
    def get_markup(self):
        raise NotImplementedError('Override this method!')

class MarkupBlock(InvariantBlock):
    """ Code block emitting raw markup to the output
    
    The data is the unicode markup should be written directly to the output
    without escaping.
    
    """
    __slots__ = InvariantBlock.__slots__

    def get_markup(self):
        return self.data
    
class AttributeValueFragmentBlock(InvariantBlock):
    """ Code block emitting XML attribute escaped text output
    
    The data is the original (non-escaped) text.
    
    """
    __slots__ = InvariantBlock.__slots__

    def get_markup(self):
        return util.escape_attribute(self.data)
    
class TextBlock(InvariantBlock):
    """ Code block emitting XML escaped text output
    
    The data is the original (non-escaped) text.
    
    """
    __slots__ = InvariantBlock.__slots__

    def get_markup(self):
        return util.escape_text(self.data)
    
    def get_i18n_text(self):
        return self.data
    
class ExpressionBlock(BaseCodeBlock):
    """ Base class for the expression blocks
    """
    __slots__ = BaseCodeBlock.__slots__
    
class TranslatableExpressionBlock(ExpressionBlock):
    """ Base class for expressing blocks can play a role in i18n:msg directives
    """
    __slots__ = ExpressionBlock.__slots__ + (
        'parameter_name', )
    
    def __init__(self,
                 lineno,
                 data=None,
                 children=[],
                 parameter_name=None):
        ExpressionBlock.__init__(self, lineno, data, children)
        
        # Name of the corresponding parameter of the enclosing i18n:msg directive
        self.parameter_name = parameter_name
    
    def get_i18n_text(self):
        return u'%%(%s)s' % self.parameter_name
    
class MarkupExpressionBlock(TranslatableExpressionBlock):
    """ Code block emitting the result of a runtime evaluated expression
    as raw markup to the output
    
    The data is an expression must be executed runtime, its result value
    is written to the output without escaping.
    
    """
    __slots__ = TranslatableExpressionBlock.__slots__
    
class TextExpressionBlock(TranslatableExpressionBlock):
    """ Code block emitting the result of a runtime evaluated expression
    as XML escaped text to the output
    
    The data is an expression must be executed runtime, its result value
    is escaped, then written to the output.
    
    """
    __slots__ = TranslatableExpressionBlock.__slots__
    
class AttributeExpressionBlock(ExpressionBlock):
    """ Code block emitting the result of a runtime evaluated expression
    as XML attribute escaped text to the output
    
    The data is an expression must be executed runtime, its result value
    is attribute escaped, then written to the output.
    
    """
    __slots__ = ExpressionBlock.__slots__
    
class DynamicAttributesBlock(BaseCodeBlock):
    """ Block representing code adding attributes at runtime (py:attrs)
    
    The data is the expression to be evaluated runtime to a dictionary
    containing the names and values of the dynamic attributes to be added
    to the output at template rendering time. Attribute values are escaped
    automatically at runtime. The order of dynamic attributes is
    indeterminate. It is impossible to replace attributes put into
    the element right in the XML template, a duplicate attribute will go
    into the output instead, which might render the document invalid.
    
    """
    __slots__ = BaseCodeBlock.__slots__

class StaticCodeBlock(BaseCodeBlock):
    """ Block representing static code, like the one in processing instructions
    """
    
    def is_invariant(self):
        return True

    def format(self, depth=0):
        
        lines = util.split_source_to_lines(self.data, depth)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            self.insert_debug_comment(lines, depth)
        
        return lines
