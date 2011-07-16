""" Base class for Genshi XML template compilers

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Provides the base class for the XML template compilers implementing all the
common logic and functionality.

"""

import os

import lxml
from lxml import etree

import constants, util, base_blocks


class BaseXMLTemplateCompiler(object):
    """ Base class for Genshi XML template compilers
    
    Provides the common logic required to compile a Genshi XML template
    to source code written in any programming language. The Genshi template
    is fully read into memory, then parsed into an element tree.
    
    """
    
    ### Options
    ### (end users are expected to override them to customize the compiler)
    
    # One level of source code indentation
    indentation = '    '

    # Enables optimizing of the generated source code by matching various
    # patterns on the tree of source code blocks before formatting it.
    # Such optimizations do not change the generated output in any way,
    # only make the generated code smaller and faster to execute.
    # Optimization preserves the readability of the generated source code.
    optimize_generated_code = True
    
    # Enables the removal of duplicate whitespace (including newlines) from
    # markup statically embedded into the generated source code. It won't
    # strip whitespace coming from dynamic template variables. It is mostly
    # useful for minimizing HTML output. Disabled by default for Genshi
    # compatiblity, but please note, that the whitespace behavior is still
    # different from Genshi is many cases.
    reduce_whitespace = False
    
    # Enables template variable substitution inside HTML comments
    # NOTE: It would be logical, but disabled for Genshi compatibility.
    process_html_comments = False
    
    # Enables the elimination of HTML comment elements
    # NOTE: It would be handy, but disabled for Genshi compatibility.
    remove_html_comments = False
    
    ### Overridables
    ### (overridden by subclasses to implement the various language targets)
    
    # Module providing the *Block subclasses to represent blocks of generated code
    blocks_module = base_blocks
    
    ### Initialization and cleanup
    
    def __init__(self):

        # Output standard, either 'xml' or 'xhtml' during the compilation phase
        self.output_standard = ''
        
        # Template filename, used only in comments put into the generated code
        self.template_filename = ''
        
        # Template name, used in the generated source code as module/class name
        self.template_identifier = ''
        
        # ElementTree instance containing the parsed template
        self.template = None
        
        if constants.GENERATE_DEBUG_COMMENTS:
            # Lines of the XML template, used to quote the XML in debug comments
            self.template_lines = []
            
        # Maps XML URLs to prefixes for all the XML namespaces can happen
        # in the output of the compiled template. It does not contain the
        # XML namespaces corresponding to Genshi directives.
        self.namespace_map = {}
        
        # Module block
        self.module_block = None
        
        # Set of function names to identify template functions returning markup
        self.function_names = set()
        
        # Map of compiler methods for each Genshi element
        self.element_translator_map = dict(
            (lxml_name, getattr(self, 'translate_' + directive.replace(':', '_')))
            for lxml_name, directive in zip(constants.GENSHI_ELEMENTS_WITH_URL, constants.GENSHI_ELEMENTS))
        
        # Map of compiler methods for each Genshi attribute
        self.attribute_compiler_map = dict(
            (lxml_name, getattr(self, 'compile_' + directive.replace(':', '_')))
            for lxml_name, directive in zip(constants.GENSHI_ATTRIBUTES_WITH_URL, constants.GENSHI_ATTRIBUTES))
        
    def load(self,
             template_source,
             template_filename='',
             template_identifier='',
             encoding='utf-8',
             template_standard='xhtml',
             parser_parameters={}):
        """ Loads an XML template
        
        template_source: str containing the XML template as string or unicode object
            or a file like object to read the template from
                  
        template_filename: optional template file name for use in
            source code comments
        
        template_identifier: optional template identifier to use in
            source code comments and as the basis of class/function names
            depending on the output programming language (wherever needed)
            
        encoding: encoding of the template, defaults to UTF-8
        
        template_standard: either 'xml' or 'xhtml'; leaving this 'xhtml'
            selects the XHTML 1.0 DTD plus the Latin-1 HTML entities
        
        parser_parameters: you can pass additional keyword parameters here
            as a dictionary, they will be passed to the constructor of the
            lxml.etree.XMLParser class
        
        """
        assert template_standard in ('xml', 'xhtml')
        
        self.template_standard = template_standard
        
        # Determine the default template file name if possible
        if (not template_filename and
            not isinstance(template_source, basestring) and
            hasattr(template_source, 'name')):
            
            # Take the file name from the file object
            template_filename = template_source.name
            
        # Determine the template's identifier if possible
        if template_filename and not template_identifier:
            template_identifier = os.path.basename(template_filename).split('.', 1)[0].replace('-', '_')
            if not util.is_identifier(template_identifier):
                template_identifier = None
        
        # Store template names
        self.template_filename = template_filename or 'unnamed_template'
        self.template_identifier = template_identifier or 'unnamed_template'
        
        # Load the template from a file object if needed
        if not isinstance(template_source, basestring):
            template_source = template_source.read()

        if constants.GENERATE_DEBUG_COMMENTS:
            self.template_lines = template_source.splitlines()
            # Allow indexing template lines from 1, since the element.sourceline
            # values are starting from 1, not zero
            self.template_lines.insert(0, '')

        # Create the appropriate parser and configure it
        kws = dict(
            encoding=encoding,
            resolve_entities=False,
            ns_clean=True)
        kws.update(parser_parameters)
        parser = etree.XMLParser(**kws)

        if self.template_standard == 'xhtml':
            #kws['load_dtd'] = True
            
            # Fail on existing DOCTYPE
            assert not template_source.lstrip().startswith('<!'), (
                "Please remove the current <!DOCTYPE > definition or "
                "set the template_standard to 'xml'!")
            
            # Prepend the DTD for the entities
            # FIXME: It would be faster to feed it to the parser before the document.
            template_source = constants.DOCTYPE_AND_HTML_ENTITIES + template_source
        
        # Parse and store the template
        self.template = etree.fromstring(template_source, parser)
        
        # Prepare namespace map and reverse map based on the actual
        # namespace declarations of the template loaded
        self.namespace_map = dict(
            (url, prefix)
            for prefix, url in self.template.nsmap.iteritems()
            if url not in (constants.XML_NAMESPACE_GENSHI, constants.XML_NAMESPACE_XINCLUDE))
        
    def cleanup(self):
        """ Cleanup function, clears the loaded template
        """
        self.output_standard = ''
        self.template_filename = ''
        self.template_identifier = ''
        self.template = None
        self.namespace_map.clear()
        if constants.GENERATE_DEBUG_COMMENTS:
            self.template_lines = []
            
    ### Generic compiler logic
    
    def compile(self, arguments='', output_standard='xhtml'):
        """ Compiles the previously loaded template into module source code
        
        arguments: Python argument list definition for all the variables the
            template accepts, it is used for the `render` function of the
            compiled module
            
        output_standard: set it to 'xml' to get the smallest XML output or
            'xhtml' to get an output compatible with most current browsers
        
        If you set the mode parameter to 'xhtml', then the compiler expects
        the standard HTML entities and write out code adding the closing
        tags and boolean attributes according to the W3C XHTML 1.0 standard.
        It is essential for compatiblity with certain IE versions.
        
        See also: http://www.w3.org/TR/xhtml1/#guidelines
        
        Returns the source code of the module as ASCII string.
        
        Also sets the template attribute of the TemplateCompiler instance
        to None, since the template is modified in the process.
        
        """
        assert self.template is not None, 'No template loaded!'
        assert output_standard in ('xml', 'xhtml')
        
        blocks_module = self.blocks_module
        lineno = self.template.sourceline

        self.output_standard = output_standard
        
        # Recursively build up the compiled module
        # NOTE: Template functions are appended directly to self.module_block,
        #       so the render function will be the last one defined.
        self.function_names.clear()
        
        self.module_block = blocks_module.ModuleBlock(lineno, self)
        
        main_block = self.compile_element(self.template, self.namespace_map)
        
        self.compile_py_def(
            main_block,
            self.template,
            'render(%s)' % arguments)
        
        self.dump_block_tree(
            self.module_block,
            constants.DUMP_BLOCK_TREE_BEFORE_POSTPROCESSING,
            'Block tree before postprocessing:')
        
        if constants.PRINT_POSTPROCESSING_DIFFERENCE:
            before_postprocessing_dump = self.module_block.pretty_format()
        
        # Postprocess blocks
        result = self.postprocess(self.module_block)
        assert len(result) == 1
        self.module_block = result[0]

        if constants.PRINT_POSTPROCESSING_DIFFERENCE:
            after_postprocessing_dump = self.module_block.pretty_format()
            print 'Postprocessing difference:'
            print
            if before_postprocessing_dump == after_postprocessing_dump:
                print 'No difference.'
            else:
                util.print_diff(
                    before_postprocessing_dump,
                    after_postprocessing_dump,
                    'Before postprocessing',
                    'After postprocessing')
            print
        
        self.dump_block_tree(
            self.module_block,
            constants.DUMP_BLOCK_TREE_AFTER_POSTPROCESSING,
            'Block tree after postprocessing:')
        
        if self.optimize_generated_code:

            if constants.PRINT_OPTIMIZATION_DIFFERENCE:
                before_optimization_dump = self.module_block.pretty_format()
            
            # Optimize generated code lines
            result = self.optimize(self.module_block)
            assert len(result) == 1
            self.module_block = result[0]
            
            self.dump_block_tree(
                self.module_block,
                constants.DUMP_BLOCK_TREE_AFTER_OPTIMIZATION,
                'Block tree after code optimization:')
        
            if constants.PRINT_OPTIMIZATION_DIFFERENCE:
                after_optimization_dump = self.module_block.pretty_format()
                print 'Optimization difference:'
                print
                if before_optimization_dump == after_optimization_dump:
                    print 'No difference.'
                else:
                    util.print_diff(
                        before_optimization_dump,
                        after_optimization_dump,
                        'Before optimization',
                        'After optimization')
                print
        
        # Recursively format the hierarchy of blocks into actual source code lines
        lines = self.module_block.format()
        if constants.DEBUGGING:
            for item in lines:
                depth, code = item
                assert isinstance(depth, (int, long))
                assert depth >= 0
                assert isinstance(code, str)
                
        # Reduce duplicate empty lines
        if len(lines) > 1:
            for index in xrange(len(lines) - 1, 0, -1):
                if lines[index - 1][1].strip() or lines[index][1].strip():
                    continue
                del lines[index]
        
        # Construct the indented source code string
        indentation = self.indentation
        module_source = '\n'.join(
            indentation * depth + code
            for depth, code in lines)
        assert isinstance(module_source, str)
        
        # Ensure that we have a newline after the last code line
        module_source = module_source.rstrip() + '\n'
        
        # Cleanup
        self.module_block = None
        self.function_names.clear()
        
        # Return source code of the module as an ASCII string
        return module_source
    
    def compile_element(self, element, namespace_map=None):
        """ Compiles a template element (recursive)
        
        element: lxml Element to compile
        
        Returns a block representing the compiled element.
        
        """
        escape_text = util.escape_text
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        # Identify the element's type
        if element.tag is etree.ProcessingInstruction:
            # Processing instruction
            code = element.text
            block = blocks_module.DummyBlock(lineno)
            block.append(blocks_module.StaticCodeBlock(lineno, code))
            if constants.GENERATE_DEBUG_COMMENTS:
                block.template_line = ''
            
        elif element.tag is etree.Comment:
            # XML comment
            block = blocks_module.DummyBlock(lineno)
            
            if (not self.remove_html_comments and
                not element.text.lstrip().startswith('!')):
                
                # It is not a Genshi comment and we need to keep it in the output
                if self.process_html_comments:
                    
                    # Substitute template variables inside comments
                    block.append(blocks_module.MarkupBlock(lineno, '<!--'))
                    block.append(self.compile_text(lineno, element.text))
                    block.append(blocks_module.MarkupBlock(lineno, '-->'))
                else:
                    
                    # Do not substitute template variables inside comments
                    block.append(
                        blocks_module.MarkupBlock(
                            lineno, '<!--%s-->' % escape_text(element.text)))
                
            if constants.GENERATE_DEBUG_COMMENTS:
                block.template_line = self.template_lines[lineno]
                
        elif element.tag is etree.Entity:
            # Processing instruction
            block = blocks_module.MarkupBlock(lineno, element.text)
            if constants.GENERATE_DEBUG_COMMENTS:
                block.template_line = self.template_lines[lineno]
            
        else:
            # Element, including Genshi directives
            assert isinstance(element.tag, basestring), 'Unknown element: %r' % element
        
            # Translate genshi element to their attribute format in place
            element_translator = self.element_translator_map.get(element.tag)
            if element_translator:
                # It is a Genshi element, so translate it to an attribute
                element_translator(element)
                
            # Collect Genshi directives defined as attributes while respecting
            # Genshi's processing order. Genshi specific attributes are removed
            # from the element in the process. The resulting list is in reverse
            # processing order, since we build up the generated code from the
            # deeper structure to the top level one.
            genshi_attributes = []
            directive_compiler = None
            for attribute_name in constants.GENSHI_ATTRIBUTES_WITH_URL:
                attribute_value = element.attrib.pop(attribute_name, None)
                if attribute_value is not None:
                    directive_compiler = self.attribute_compiler_map.get(attribute_name)
                    genshi_attributes.append((directive_compiler, attribute_value.strip()))
    
            # Create the block corresponding to the current element
            # NOTE: Namespaces has to be declared in each of the child elements
            #       if we can't declare them in the parent, since the parent is
            #       a Genshi directive element and won't go to the output.
            if element_translator:
                # It is a Genshi directive element
                block = blocks_module.DummyBlock(lineno)
                child_namespace_map = namespace_map
            else:
                # It is a non-Genshi element
                block = self.compile_foreign_element(element, namespace_map)
                child_namespace_map = None
                
            # Substitute variables into the enclosed text if any
            if element.text:
                block.append(self.compile_text(lineno, element.text))
            
            # Recursively compile child elements
            for child_element in element.iterchildren():
                block.append(self.compile_element(child_element, child_namespace_map))
            
            # Mark as a compiled element
            block.element = block
            element_block = block
                
            # Apply the Genshi directives
            for directive_compiler, attribute_value in genshi_attributes:
                block = directive_compiler(block, element, attribute_value)
                block.element = element_block
                
        # Substitute variables into the trailing text if any
        if element.tail:
            element_block = block
            block = self.blocks_module.DummyBlock(lineno)
            block.append(element_block)
            block.append(self.compile_text(lineno, element.tail))
        
        return block
    
    def compile_foreign_element(self, element, namespace_map):
        """ Compiles a non-Genshi (foreign) element
        
        Returns a block representing the compiled element.
        
        """
        escape_attribute = util.escape_attribute
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        # Opening tag, namespace declarations, attributes from to the template
        tag_name = util.namespace_url_to_prefix(self.namespace_map, element.tag)
        lc_tag_name = tag_name.lower()
        opening_tag = blocks_module.OpeningTagBlock(lineno, lc_tag_name)
        opening_tag.append(blocks_module.MarkupBlock(lineno, u'<%s' % tag_name))

        # Namespace declarations
        if namespace_map:
            for namespace_url, namespace_prefix in sorted(namespace_map.items()):
                xmlns_attribute_markup = u' xmlns%s="%s"' % (
                    u':%s' % namespace_prefix if namespace_prefix else u'',
                    escape_attribute(namespace_url))
                opening_tag.append(blocks_module.MarkupBlock(lineno, xmlns_attribute_markup))
                
        # Attributes defined in the template
        for attribute_name, attribute_value in sorted(element.attrib.items()):
            opening_tag.append(
                blocks_module.MarkupBlock(
                    lineno,
                    u' %s="' % util.namespace_url_to_prefix(self.namespace_map, attribute_name)))
            opening_tag.append(self.compile_text(lineno, attribute_value, attribute=True))
            opening_tag.append(blocks_module.MarkupBlock(lineno, u'"'))
            
        # NOTE: Opening tags are closed only later in the postprocessing step.
        
        # Closing tag
        closing_tag = blocks_module.ClosingTagBlock(lineno, lc_tag_name)
        closing_tag.append(blocks_module.MarkupBlock(lineno, u'</%s>' % tag_name))
        
        # NOTE: Short tags are introduced later in the postprocessing step.
        
        # Block representing the element
        block = blocks_module.ElementBlock(
            lineno,
            lc_tag_name,
            opening_tag=opening_tag,
            closing_tag=closing_tag)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            block.template_line = self.template_lines[lineno]
        
        return block
    
    ### Methods transforming Genshi elements to their attribute variant for uniform processing.
    ### These methods modify the element in place by adding a new attribute.
    
    def translate_py_def(self, element):
        assert 'function' in element.attrib, 'Missing function attribute of element: %s' % element
        element.attrib['{%s}def' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('function')
    
    def translate_py_match(self, element):
        raise NotImplementedError('py:match is not supported')

    def translate_py_when(self, element):
        assert 'test' in element.attrib, 'Missing test attribute of element: %s' % element
        element.attrib['{%s}when' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('test')

    def translate_py_otherwise(self, element):
        element.attrib['{%s}otherwise' % constants.XML_NAMESPACE_GENSHI] = ''
    
    def translate_py_for(self, element):
        assert 'each' in element.attrib, 'Missing each attribute of element: %s' % element
        element.attrib['{%s}for' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('each')
    
    def translate_py_if(self, element):
        assert 'test' in element.attrib, 'Missing test attribute of element: %s' % element
        element.attrib['{%s}if' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('test')
    
    def translate_py_choose(self, element):
        assert 'test' in element.attrib, 'Missing test attribute of element: %s' % element
        element.attrib['{%s}choose' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('test')
    
    def translate_py_with(self, element):
        assert 'vars' in element.attrib, 'Missing vars attribute of element: %s' % element
        element.attrib['{%s}with' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('vars')
    
    def translate_xi_include(self, element):
        raise NotImplementedError('xi:include is not supported, currently')
    
    def translate_xi_fallback(self, element):
        raise NotImplementedError('xi:include and xi:fallback are not supported, currently')
    
    ### Methods compiling Genshi attributes to Python code.
    ### These methods return a block representing the compiled element.
    
    def compile_py_def(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        assert attribute_value, 'Empty py:def attribute of element: %s' % element

        # Register the function as a known one
        # NOTE: We need this to compile code not putting every call to
        # template functions into Markup(), which would result in escaping
        # the generated markup. Keeping the set of template function names
        # allows for considering them as functions returning markup without
        # having to do this runtime.
        function_name = attribute_value.split('(', 1)[0]
        assert function_name not in self.function_names, 'Duplicate template function: %s' % function_name
        self.function_names.add(function_name)
        
        # Construct the function definition
        function_definition = blocks_module.FunctionDefinitionBlock(lineno, attribute_value)
        function_definition.append(block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            function_definition.template_line = self.template_lines[lineno]
        
        # Append the function definition to the module
        self.module_block.append(function_definition)
        
        # No direct output of template function definitions, so return an empty block
        return blocks_module.DummyBlock(lineno)
    
    def compile_py_match(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        raise NotImplementedError('py:match cannot be compiled, so not supported')

    def compile_py_when(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        assert attribute_value, 'Empty py:when attribute of element: %s' % element
        
        case_block = blocks_module.CaseBlock(lineno, attribute_value)
        case_block.append(block)

        if constants.GENERATE_DEBUG_COMMENTS:
            case_block.template_line = self.template_lines[lineno]
        
        return case_block
        
    def compile_py_otherwise(self, block, element, attribute_value):
        lineno = element.sourceline
        
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        otherwise_block = self.blocks_module.OtherwiseBlock(lineno)
        otherwise_block.append(block)
            
        if constants.GENERATE_DEBUG_COMMENTS:
            otherwise_block.template_line = self.template_lines[lineno]
            
        return otherwise_block
    
    def compile_py_for(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        assert attribute_value, 'Empty py:for attribute of element: %s' % element
        
        loop_block = blocks_module.LoopBlock(lineno, attribute_value)
        loop_block.append(block)

        if constants.GENERATE_DEBUG_COMMENTS:
            loop_block.template_line = self.template_lines[lineno]
        
        return loop_block
    
    def compile_py_if(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        assert attribute_value, 'Empty py:if attribute of element: %s' % element
        
        # Look for a static values
        attribute_value = util.parse_boolean_expression(attribute_value)
        
        if attribute_value is True:
            # Always True, preserve element
            return block
        
        if attribute_value is False:
            # Always False, remove element
            return blocks_module.DummyBlock(lineno)
        
        # Keep the element runtime based on the given conditional expression
        condition_block = blocks_module.ConditionalBlock(lineno, attribute_value)
        condition_block.append(block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            condition_block.template_line = self.template_lines[lineno]
        
        return condition_block
        
    def compile_py_choose(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline

        switch_block = blocks_module.SwitchBlock(lineno, attribute_value)
        
        # We need to push the switch construct below the current element
        element = block.element
        switch_block.extend(element.children)
        element.children = [switch_block]
        
        if constants.GENERATE_DEBUG_COMMENTS:
            switch_block.template_line = self.template_lines[lineno]
        
        return block
    
    def compile_py_with(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        assert attribute_value, 'Empty py:vars attribute of element: %s' % element
        
        with_block = blocks_module.WithBlock(lineno, attribute_value)
        with_block.append(block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            with_block.template_line = self.template_lines[lineno]
        
        return with_block
            
    def compile_py_replace(self, block, element, attribute_value):
        lineno = element.sourceline
        
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        # Replace the element with the result of the given runtime expression
        replace_block = self.blocks_module.TextExpressionBlock(lineno, attribute_value)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            replace_block.template_line = self.template_lines[lineno]
        
        return replace_block
        
    def compile_py_content(self, block, element, attribute_value):
        lineno = element.sourceline
        
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        # Replace children with the result of the given runtime expression
        content_block = self.blocks_module.TextExpressionBlock(lineno, attribute_value)
        block.clear()
        block.append(content_block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            content_block.template_line = self.template_lines[lineno]
        
        return block

    def compile_py_attrs(self, block, element, attribute_value):
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
    
        # Find the element this directive is applying to
        element_block = block.element
        assert isinstance(element_block, base_blocks.ElementBlock), (
            'No element this py:attrs is applying to!')

        # If the opening tag was removed due to py:replace, then just ignore
        # py:attrs along with the removed element (no simple way to add
        # attributes to a possible element added by py:replace dynamically)
        if not element_block.opening_tag:
            return block
        
        # Store the dynamic attributes expression for the element
        dynamic_attributes_block = blocks_module.DynamicAttributesBlock(lineno, attribute_value)
        element_block.opening_tag.append(dynamic_attributes_block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            dynamic_attributes_block.template_line = self.template_lines[lineno]
        
        return block
    
    def compile_py_strip(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
    
        # Find the element this directive is applying to
        element_block = block.element
        assert isinstance(element_block, base_blocks.ElementBlock), 'No element this py:strip is applying to!'
        
        # Look for a static values
        attribute_value = util.parse_boolean_expression(attribute_value, default=True)
        
        if attribute_value is True:
            # Always True, remove the opening and closing tags
            element_block.opening_tag = None
            element_block.closing_tag = None
            return block
        
        if attribute_value is False:
            # Always False, keep the opening and closing tags
            return block
        
        # Runtime condition
        element_block.strip_expression = attribute_value
        
        return block
        
    ### Methods compiling text and attribute values
    
    def compile_text(self, lineno, text, attribute=False):
        """ Compiles template variable references inside a text fragment
        
        Returns the compiled source code lines in the form of a list of
        (indentation_level, kind, line) tuples, where line is ASCII string.
        
        """
        escape = util.escape_attribute if attribute else util.escape_text
        blocks_module = self.blocks_module

        # We always return a block
        block = blocks_module.DummyBlock(lineno)
        
        # Empty text?
        if not text:
            return block
        
        # Find all template expressions
        fragment_list = constants.RX_TEMPLATE_EXPRESSION.split(text)
        # NOTE: assert (len(fragment_list) - 1) % 3 == 0
        
        # Append the leading text block
        first_fragment = fragment_list[0]
        if first_fragment:
            block.append(
                blocks_module.MarkupBlock(
                    lineno, 
                    escape(first_fragment.replace('$$', '$'))))
        
        # Append each template expression and their trailing text blocks
        for i in xrange(1, len(fragment_list), 3):
            
            expression1, expression2, fragment = fragment_list[i: i + 3]
            expression = expression1 or expression2
            
            if expression is not None:
                block.append(self.compile_template_expression(lineno, expression, attribute))
                
            if fragment:
                block.append(
                    blocks_module.MarkupBlock(
                        lineno,
                        escape(fragment.replace('$$', '$'))))

        return block
    
    def compile_template_expression(self, lineno, expression, attribute=False):
        """ Compiles a single template expression outputting text or HTML
        
        Returns the compiled code block.
        
        """
        expression = expression.strip()
        assert expression, 'Empty template expression'
        
        # NOTE: Markup() expressions will be translated to
        #       MarkupExpressionBlock by the postprocessor.
        if attribute:
            block = self.blocks_module.AttributeExpressionBlock(lineno, expression)
        else:
            block = self.blocks_module.TextExpressionBlock(lineno, expression)

        if constants.GENERATE_DEBUG_COMMENTS:
            block.template_line = self.template_lines[lineno]
            
        return block
    
    ### Postprocessor
    
    def postprocess(self, block, switch=None):
        """ Postprocesses the block hierarchy
        
        Returns the list of replacement blocks.
        
        """
        # Collect py:when and py:otherwise directives for the enclosing py:switch one
        if isinstance(block, base_blocks.SwitchBlock):
            switch = block
        elif isinstance(block, base_blocks.CaseBlock):
            assert switch, 'Found py:when directive without an enclosing py:choose!'
            switch.when_blocks.append(block)
        elif isinstance(block, base_blocks.OtherwiseBlock):
            assert switch, 'Found py:otherwise directive without an enclosing py:choose!'
            switch.otherwise_blocks.append(block)
            
        # Do not escape the output of template functions defined in this template
        if isinstance(block, base_blocks.TextExpressionBlock):
            
            expression = block.data.strip()
            
            if expression.endswith(')'):
                
                function_name = expression.split('(', 1)[0].strip()
                
                if function_name == 'Markup':
                    block = self.blocks_module.MarkupExpressionBlock(
                        block.lineno, expression[7: -1].strip())
                
                if function_name in self.function_names:
                    block = self.blocks_module.MarkupExpressionBlock(
                        block.lineno, expression)
                    
            elif expression == 'None':
                # Genshi converts None values expressions to empty output
                return []
            
        # Finalize foreign elements
        if isinstance(block, base_blocks.ElementBlock):
            
            if block.opening_tag:
                
                # We can't shorten the element if there are any child elements
                # in it or we are outputting XHTML and this element does not
                # have a short form.
                # See also: http://www.w3.org/TR/xhtml1/#guidelines
                if (block.children or
                    (self.output_standard == 'xhtml' and 
                     ':' not in block.data and
                     block.data not in constants.SHORT_HTML_ELEMENTS_SET)):
                    
                    # Close opening tag
                    block.opening_tag.append(
                        self.blocks_module.MarkupBlock(block.lineno, u'>'))
                    
                else:
                    # Shorten the element
                    block.opening_tag.append(
                        self.blocks_module.MarkupBlock(block.lineno, u' />'))
                    block.closing_tag = None
                    
        if constants.DETECT_RECURSION:
            assert not block.contains(self)
            
        # Postprocess all the child blocks, it also allows for replacing them
        block.apply_transformation(self.postprocess, switch)
        
        return [block]
            
    ### Optimizer making the generated code simpler and more efficient
    
    def optimize(self, block):
        """ Optimizes the source code block hierarchy
        
        Returns the list of replacement blocks.
        
        """
        blocks_module = self.blocks_module
        
        # Optimize all the child blocks first
        block.apply_transformation(self.optimize)
        
        # py:with specific optimizations
        if isinstance(block, base_blocks.WithBlock):

            # Extract leading and trailing static elements from py:with blocks
            if (block.children and
                (block.children[0].is_invariant() or
                 block.children[-1].is_invariant())):
                
                leading_invariant_blocks = []
                while block.children and block.children[0].is_invariant():
                    leading_invariant_blocks.append(block.children.pop(0))
                    
                trailing_invariant_blocks = []
                while block.children and block.children[-1].is_invariant():
                    trailing_invariant_blocks.append(block.children.pop(-1))

                block = blocks_module.DummyBlock(
                    block.lineno,
                    children=(
                        leading_invariant_blocks +
                        ([] if block.is_empty() else [block]) +
                        trailing_invariant_blocks))
            
            # Collide nested py:with directives (single child only)
            if (len(block.children) == 1 and
                isinstance(block.children[0], base_blocks.WithBlock)):
            
                block.data = '%s; %s' % (block.data.rstrip(';'), block.children[0].data)
                block.children = block.children[0].children
                
        # Static markup optimizations
        if isinstance(block, base_blocks.MarkupBlock):
            
            # Redundant whitespace elimination (HTML minimizer)
            if self.reduce_whitespace and block.data:
                
                if block.data.strip():
                    # Reduce the heading and trailing whitespace
                    heading_whitespace, text, trailing_whitespace = (
                        constants.RX_WHITESPACE_HEAD_TAIL.match(block.data).groups())
                    block.data = (
                        util.reduce_whitespace(heading_whitespace) +
                        text +
                        util.reduce_whitespace(trailing_whitespace))
                    
                else:
                    # Reduce whitespace markup
                    block.data = util.reduce_whitespace(block.data)
        
        # Foreign element optimizations
        if isinstance(block, base_blocks.ElementBlock):
            
            # Put the opening and closing tags into the list of children
            # blocks if the tags cannot be stripped out. It allows for
            # colliding the tags with the tail and head of static contents.
            if block.strip_expression is None:

                if block.opening_tag:
                    if constants.GENERATE_DEBUG_COMMENTS:
                        block.template_line = (
                            (block.opening_tag.template_line or '') +
                            block.template_line)
                    block.children[0:0] = block.opening_tag.children
                    block.opening_tag = None
                    
                if block.closing_tag:
                    if constants.GENERATE_DEBUG_COMMENTS:
                        block.template_line += (block.closing_tag.template_line or '')
                    block.children.extend(block.closing_tag.children)
                    block.closing_tag = None
                    
                # Remove the unnecessary ElementBlock container,
                # it allows for colliding it with the surrounding markup
                element_block = block
                block = base_blocks.DummyBlock(
                    element_block.lineno,
                    children=element_block.children)
                
                if constants.GENERATE_DEBUG_COMMENTS:
                    block.template_line = element_block.template_line
                
        # Collide blocks emitting static markup
        children = block.children
        if len(children) > 1:
            
            for index in xrange(len(children) - 1, 0, -1):
                
                first_block = children[index - 1]
                second_block = children[index]
                
                if (isinstance(first_block, base_blocks.MarkupBlock) and
                    isinstance(second_block, base_blocks.MarkupBlock)):
                    
                    first_block.data += second_block.data
                    
                    if constants.GENERATE_DEBUG_COMMENTS:
                        first_block.template_line = (
                            (first_block.template_line or '') + 
                            (second_block.template_line or ''))
                    
                    del children[index]
                    
        # Remove unnecessary level of block nesting
        if isinstance(block, base_blocks.DummyBlock):
            return block.children
        
        # Drop empty blocks not affecting the output of the generated code
        if block.is_empty():
            return []
        
        return [block]
        
    ### Debugging
    
    def dump_block_tree(self, block, output, description):
        """ Writes out the pretty formatted dump of the block tree
        
        Does not do anything if the truth value of the output is False,
        that means a disabled dump output.
        
        block: block to dump
        
        output: file object, file name or any other object with a true
            truth value to dump the block to stdout
            
        description: description to print to stdout before dumping there
        
        """
        if not output:
            return
        
        dump = block.pretty_format()
        
        if isinstance(output, file):
            output.write(dump)
            
        elif isinstance(output, basestring):
            with open(output, 'wt') as output_file:
                output_file.write(dump)
                
        else:
            print description
            print
            print dump
            print
