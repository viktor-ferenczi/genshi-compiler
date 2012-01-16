""" Base class for Genshi XML template compilers

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Provides the base class for the XML template compilers implementing all the
common logic and functionality.

"""

import os, itertools

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
        
        # Template filename, used only in source code comments and compile time exceptions
        self.template_filename = ''
        
        # Template name, used in the generated source code as module/class name
        self.template_identifier = ''
        
        # Encoding of the loaded template
        self.template_encoding = ''
        
        # ElementTree instance containing the parsed template
        self.template = None
        
        # Language translation
        self.translator = None
        self.translator_ugettext = None
        self.translator_ungettext = None
        self.translatable_elements = None
        self.translatable_attributes = None
        self.translatable_element_set = set()
        self.translatable_attribute_set = set()
        
        if constants.GENERATE_DEBUG_COMMENTS:
            # Lines of the XML template, used to quote the XML in debug comments
            self.template_lines = []
            
        # Maps XML URLs to prefixes for all the XML namespaces can happen
        # in the output of the compiled template. It does not contain the
        # XML namespaces corresponding to Genshi directives.
        self.namespace_map = {}
        
        # Module block
        self.module_block = None
        
        # Map of compiled template function names to their signature
        self.function_map = {}
        
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
             template_encoding='utf-8',
             template_standard='xhtml',
             parser_parameters={}):
        """ Loads an XML template
        
        template_source: str containing the XML template as string or
            unicode object or a file like object to read the template from.
                  
        template_filename: Optional template file name for use in
            source code comments.
        
        template_identifier: Optional template identifier to use in
            source code comments and as the basis of class/function names
            depending on the output programming language (wherever needed).
            
        template_encoding: Encoding of the template, defaults to UTF-8.
        
        template_standard: Either 'xml' or 'xhtml'; leaving this 'xhtml'
            selects the XHTML 1.0 DTD plus the Latin-1 HTML entities.
        
        parser_parameters: You can pass additional keyword parameters here
            as a dictionary, they will be passed to the constructor of the
            lxml.etree.XMLParser class.
        
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
        
        # Store template names and encoding
        self.template_filename = template_filename or 'unnamed_template'
        self.template_identifier = template_identifier or 'unnamed_template'
        self.template_encoding = template_encoding
        
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
            encoding=template_encoding,
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
            if url not in constants.XML_NAMESPACES_PROCESSED)
        
    def cleanup(self):
        """ Cleanup function, clears the loaded template
        """
        self.output_standard = ''
        self.template_filename = ''
        self.template_identifier = ''
        self.template = None
        self.translator = None
        self.translator_ugettext = None
        self.translator_ungettext = None
        self.translatable_element_set.clear()
        self.translatable_attribute_set.clear()
        self.namespace_map.clear()
        self.function_map.clear()
        if constants.GENERATE_DEBUG_COMMENTS:
            self.template_lines = []

    ### Configuration
    
    def configure_i18n(
        self,
        translator,
        translatable_elements=None,
        translatable_attributes=None):
        
        """ Configures compile time language translation
        
        Call this method to configure compile time language translation.
        In order to be effective this method must be called before 
        compiling the template.
        
        Translation is done at compile time. If you need runtime translation
        of dynamic data, then you need to pass a translator function to the
        rendered template and do the affected translations manually.
        
        translator: gettext compatible translator object, the compiler
            is using only the ugettext and ungettext methods. Pass None
            as the translator to disable i18n support.
        
        translatable_elements: Iterable yielding the name of element
            to translate. They must include the namespace prefix if
            applicable, None value defaults to:
            
            for 'xhtml' output:
                ('a', 'caption', 'dd', 'dt', 'label', 'legend', 'li', 
                 'option', 'p', 'rb', 'rp', 'rt', 'td', 'th', 'title')
            
            for 'xml' output you need to list the elements explicitly,
            no element are translated by default: ()
        
        translatable_attributes: Iterable yielding the names of the 
            translatable element attributes, they must include the
            namespace prefix if applicable, None value defaults to:
            
            for 'xhtml' output:
                ('abbr', 'alt', 'label', 'prompt', 'standby',
                 'summary', 'title')
            
            for 'xml' output you need to list the attributes explicitly,
            no element are translated by default: ()
            
            Dynamically added attributes (py:attrs) are not translated
            by Genshi Compiler, you need to call your translation function
            in order to get such values translated.
            
        """
        self.translator = translator
        self.translatable_elements = translatable_elements
        self.translatable_attributes = translatable_attributes
        
    ### Generic compiler logic
    
    def compile(self,
                arguments='',
                output_standard='xhtml'):
    
        """ Compiles the previously loaded template into module source code
        
        arguments: Python argument list definition for all the variables the
            template accepts, it is used for the `render` function of the
            compiled module. Alternatively you can define the top level
            element of your template as a function (py:def) and call that
            instead of the default `render` function. Please note, that it
            causes the default `render` function to return empty markup just
            like in the case of Genshi.
            
        output_standard: Set it to 'xml' to get the smallest XML output or
            'xhtml' to get an output compatible with most current browsers.
            
        If you set the mode parameter to 'xhtml', then the compiler expects
        the standard HTML entities and write out code adding the end tags
        and boolean attributes according to the W3C XHTML 1.0 standard.
        It is essential for compatiblity with certain IE versions.
        
        See also: http://www.w3.org/TR/xhtml1/#guidelines
        
        Language translation is applied runtime using the provided translation
        function, which must be named _ and 
        
        Returns the source code of the module as ASCII string.
        
        After successful compilation the function_map member variable of
        the compiler object gives the compiled template functions available
        at the module level of the compiled template module.
        
        Sets the template attribute of the TemplateCompiler instance
        to None, since the template is modified in the process. The XML
        template need to be loaded again for a repeated compilation.
        
        """
        assert self.template is not None, 'No template loaded!'
        
        blocks_module = self.blocks_module
        lineno = self.template.sourceline
        
        # Validate output standard
        assert output_standard in ('xml', 'xhtml')
        self.output_standard = output_standard
        
        # Finalize i18n settings
        if self.translator:

            # Extract translator functions
            self.translator_ugettext = self.translator.ugettext
            self.translator_ungettext = self.translator.ungettext
            
            # Defaults
            if output_standard == 'xhtml':
                default_translatable_elements = constants.XHTML_ELEMENTS_TO_TRANSLATE
                default_translatable_attributes = constants.XHTML_ATTRIBUTES_TO_TRANSLATE
            else:
                default_translatable_elements = ()
                default_translatable_attributes = ()
                
            # Turn the lists into sets
            self.translatable_element_set = set(
                self.translatable_elements or default_translatable_elements)
            self.translatable_attribute_set = set(
                self.translatable_attributes or default_translatable_attributes)
        
        # Recursively build up the compiled module
        # NOTE: Template functions are appended directly to self.module_block,
        #       so the render function will be the last one defined.
        self.function_map.clear()
        
        self.module_block = blocks_module.ModuleBlock(lineno, self)
        
        main_block = self.compile_element(self.template, self.namespace_map)
        
        if 'render' in self.function_map:
            assert not arguments, (
                'Both a template function named "render" and arguments for '
                'the whole template are defined! Only one of these can be '
                'defined.')
        else:
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
        # NOTE: Leaving the contents of the function_map intentionally.
        
        # Return source code of the module as an ASCII string
        return module_source
    
    def compile_element(self, element, namespace_map=None):
        """ Compiles a template element (recursive)
        
        element: lxml Element to compile.
        
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
                    self.compile_text(lineno, block, element.text)
                    block.append(blocks_module.MarkupBlock(lineno, '-->'))
                else:
                    
                    # Do not substitute template variables inside comments
                    block.append(
                        blocks_module.MarkupBlock(
                            lineno, '<!--%s-->' % element.text))
                
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
            
            # Is this element i18n translatable?
            lc_tagname_with_namespace_prefix = (
                util.namespace_url_to_prefix(self.namespace_map, element.tag))
            translatable_element = (
                lc_tagname_with_namespace_prefix in self.translatable_element_set)
            
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
                block = self.compile_foreign_element(
                    element, namespace_map, translatable_element)
                child_namespace_map = None
                
            # Substitute variables into the enclosed text if any
            if element.text:
                self.compile_text(lineno, block, element.text, translatable=translatable_element)
            
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
            
            # Is the parent element i18n translatable?
            translatable_parent_element = False
            parent_element = element.getparent()
            if parent_element is not None:
                lc_tagname_with_namespace_prefix = util.namespace_url_to_prefix(
                    self.namespace_map, parent_element.tag)
                translatable_parent_element = (
                    lc_tagname_with_namespace_prefix in self.translatable_element_set)
                
            self.compile_text(lineno, block, element.tail, translatable=translatable_parent_element)
            
        return block
    
    def compile_foreign_element(self, element, namespace_map, translatable_element=False):
        """ Compiles a non-Genshi (foreign) element
        
        Returns a block representing the compiled element.
        
        """
        escape_attribute = util.escape_attribute
        blocks_module = self.blocks_module
        lineno = element.sourceline

        # Block representing the element
        tag_name = util.namespace_url_to_prefix(self.namespace_map, element.tag)
        lc_tag_name = tag_name.lower()
        element_block = blocks_module.ElementBlock(lineno, lc_tag_name)
        element_block.element = element_block

        if constants.GENERATE_DEBUG_COMMENTS:
            element_block.template_line = self.template_lines[lineno]
        
        # Start tag, namespace declarations, attributes from to the template
        start_tag = blocks_module.OpeningTagBlock(lineno, lc_tag_name)
        element_block.start_tag=start_tag
        start_tag.append(blocks_module.MarkupBlock(lineno, u'<%s' % tag_name))
        
        # Namespace declarations
        if namespace_map:
            for namespace_url, namespace_prefix in sorted(namespace_map.items()):
                xmlns_attribute_markup = u' xmlns%s="%s"' % (
                    u':%s' % namespace_prefix if namespace_prefix else u'',
                    escape_attribute(namespace_url))
                start_tag.append(blocks_module.MarkupBlock(lineno, xmlns_attribute_markup))
                
        # Compile the attributes defined for this element in the XML template
        for attribute_name, attribute_value in sorted(element.attrib.items()):
            
            # Open the attribute
            attribute_name_with_namespace_prefix = util.namespace_url_to_prefix(
                self.namespace_map, attribute_name)
            start_tag.append(
                blocks_module.MarkupBlock(
                    lineno,
                    u' %s="' % attribute_name_with_namespace_prefix))
            
            # Create block to generate the attribute's value
            attribute_value_block = self.blocks_module.AttributeValueBlock(
                lineno, attribute_name_with_namespace_prefix)
            attribute_value_block.element = element_block
            
            # Is this attribute translatable?
            translatable_attribute = (
                attribute_name_with_namespace_prefix in self.translatable_attribute_set)
            
            # Compile the contents of this attribute
            self.compile_text(
                lineno, 
                attribute_value_block, 
                attribute_value, 
                attribute=attribute_value_block,
                translatable=translatable_attribute)
            
            # Close the attribute
            start_tag.append(attribute_value_block)
            start_tag.append(blocks_module.MarkupBlock(lineno, u'"'))
            
        # NOTE: Start tags are closed only later in the postprocessing step.
        
        # End tag
        end_tag = blocks_module.ClosingTagBlock(lineno, lc_tag_name)
        element_block.end_tag = end_tag
        end_tag.append(blocks_module.MarkupBlock(lineno, u'</%s>' % tag_name))
        
        # NOTE: Short tags are introduced later by the postprocessing step.
        
        return element_block
    
    ### Methods transforming Genshi elements to their attribute variant for uniform processing.
    ### These methods modify the element in place by adding a new attribute.
    
    def translate_py_def(self, element):
        assert 'function' in element.attrib, 'Missing function attribute of element: %s' % element
        element.attrib['{%s}def' % constants.XML_NAMESPACE_GENSHI] = element.attrib.pop('function')
    
    def translate_py_match(self, element):
        raise NotImplementedError('Found unsupported py:match element at %s#%d!' % (self.template_filename or 'Line ', element.sourceline))

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
        
    def translate_i18n_msg(self, element):
        assert 'params' in element.attrib, 'Missing params attribute of element: %s' % element
        element.attrib['{%s}msg' % constants.XML_NAMESPACE_I18N] = element.attrib.pop('params')
    
    def translate_i18n_comment(self, element):
        raise NotImplementedError('Found py:comment element at %s#%d, but py:comment is only supported only as an attribute!' % (self.template_filename or 'Line ', element.sourceline))
    
    def translate_i18n_domain(self, element):
        # FIXME: I could not find documentation on i18n:domain as an element,
        #        so I had to choose an ad-hoc attribute name here!
        assert 'name' in element.attrib, 'Missing name attribute of element: %s' % element
        element.attrib['{%s}domain' % constants.XML_NAMESPACE_I18N] = element.attrib.pop('name')
    
    def translate_i18n_choose(self, element):
        assert 'numeral' in element.attrib, 'Missing numeral attribute of element: %s' % element
        element.attrib['{%s}choose' % constants.XML_NAMESPACE_I18N] = (
            u'%s; %s' % (element.attrib.pop('numeral'), element.attrib.pop('params', '')))
        
    def translate_i18n_singular(self, element):
        element.attrib['{%s}singular' % constants.XML_NAMESPACE_I18N] = ''
    
    def translate_i18n_plural(self, element):
        element.attrib['{%s}plural' % constants.XML_NAMESPACE_I18N] = ''
    
    def translate_xi_include(self, element):
        raise NotImplementedError('Found unsupported xi:include element at %s#%d' % (self.template_filename or 'Line ', element.sourceline))
    
    def translate_xi_fallback(self, element):
        raise NotImplementedError('Found unsupported py:fallback element at %s#%d' % (self.template_filename or 'Line ', element.sourceline))
    
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
        function_signature = attribute_value.strip()
        assert function_name not in self.function_map, 'Duplicate template function: %s' % function_name
        self.function_map[function_name] = function_signature
        
        # Construct the function definition
        function_definition = blocks_module.FunctionDefinitionBlock(lineno, function_signature)
        function_definition.append(block)
        
        if constants.GENERATE_DEBUG_COMMENTS:
            function_definition.template_line = self.template_lines[lineno]
        
        # Append the function definition to the module
        self.module_block.append(function_definition)
        
        # No direct output of template function definitions, so return an empty block
        return blocks_module.DummyBlock(lineno)
    
    def compile_i18n_domain(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
##        blocks_module = self.blocks_module
##        lineno = element.sourceline
##        
##        assert attribute_value, 'Empty i18n:domain attribute of element: %s' % element
##        
##        with_block = blocks_module.WithBlock(lineno, attribute_value)
##        with_block.append(block)
##        
##        if constants.GENERATE_DEBUG_COMMENTS:
##            with_block.template_line = self.template_lines[lineno]
##        
##        return with_block

        raise NotImplementedError('TODO')
    
    def compile_py_match(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        raise NotImplementedError('Found unsupported py:match attribute at %s#%d' % (self.template_filename or 'Line ', element.sourceline))

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
    
    def compile_i18n_plural(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        raise NotImplementedError('TODO')
    
    def compile_i18n_singular(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        raise NotImplementedError('TODO')
    
    def compile_i18n_choose(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        raise NotImplementedError('TODO')
    
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
            
        # The expression must be ASCII
        # FIXME: This limitation should be lifted eventually, since 
        #        variable names can include non-ASCII characters in Python.
        #        We enforce this now since the generated source code is ASCII.
        if isinstance(attribute_value, unicode):
            attribute_value = attribute_value.encode('ascii')
        
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
            
        # The expression must be ASCII
        # FIXME: This limitation should be lifted eventually, since 
        #        variable names can include non-ASCII characters in Python.
        #        We enforce this now since the generated source code is ASCII.
        if isinstance(attribute_value, unicode):
            attribute_value = attribute_value.encode('ascii')
        
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

        # If the start tag was removed due to py:replace, then just ignore
        # py:attrs along with the removed element (no simple way to add
        # attributes to a possible element added by py:replace dynamically)
        if not element_block.start_tag:
            return block
        
        # Store the dynamic attributes expression for the element
        dynamic_attributes_block = blocks_module.DynamicAttributesBlock(lineno, attribute_value)
        element_block.start_tag.append(dynamic_attributes_block)
        
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
            # Always True, remove the opening and end tags
            element_block.start_tag = None
            element_block.end_tag = None
            return block
        
        if attribute_value is False:
            # Always False, keep the start and end tags
            return block
        
        # Runtime condition
        element_block.strip_expression = attribute_value
        
        return block
        
    def compile_i18n_comment(self, block, element, attribute_value):
        # i18n comment attributes are not written to the output
        return block
    
    def compile_i18n_msg(self, block, element, attribute_value):
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
            
        blocks_module = self.blocks_module
        lineno = element.sourceline
        
        # Split the parameter list and check for no parameters
        if attribute_value.strip():
            parameter_name_list = [
                name.strip() for name in attribute_value.split(',')]
        else:
            # No parameters defined
            if element.tag.lower() == '{%s}msg' % constants.XML_NAMESPACE_I18N:
                # It should result in no output for compatibility with Genshi's
                # behavior. Otherwise it would be logical to just output its
                # translated text contents.
                return blocks_module.DummyBlock(lineno)
            
            # Just keep the translated text contents,
            # no parameter substitution needed
            return block
        
        # Check for invalid parameter names
        for parameter_name in parameter_name_list:
            if not util.is_identifier(parameter_name):
                raise ValueError(
                    'Invalid i18n:msg parameter on line #%d (not a valid identifier): %s' % 
                    (element.sourceline, parameter_name))
            
        # There must be no duplicate parameter names
        if len(set(parameter_name_list)) != len(parameter_name_list):
            raise ValueError(
                'Duplicate i18n:msg parameter name on line #%d: %s' % 
                (element.sourceline, attribute_value))
        
        # Construct translatable template
        
        # Fill in the parameter_name and element_number attributes in the
        # subtree of the i18n:msg directive and look for unsupported elements
        element_map = {}
        parameter_map = {}
        iter_element_numbers = itertools.count(1)
        iter_parameters = iter(parameter_name_list)
        block.apply_transformation(self.transform_i18n_msg_block, iter_element_numbers, iter_parameters, element_map, parameter_map)
        
        # Construct the translatable string template from the children
        # (it prevents considering a top level ElementBlock as a string template item)
        text = base_blocks.BaseBlock.get_i18n_text(block)
        left_whitespace, string_template, right_whitespace = util.separate_whitespace(text)
        if not string_template:
            raise ValueError('Empty i18n:msg block on line #%d!' % block.lineno)
        
        # Translate the string template at compile time, it consists of the
        # hierarchy of translatable text, plus the element and expression
        # markers. The translation can change the position of expressions,
        # but can't change the hierarchy of elements.
        if self.translator:
            translated_string_template = self.translator_ugettext(string_template)
        else:
            translated_string_template = string_template
        
        # Replace the element markers in the string template with more usable ones
        while 1:
            translated_string_template, count = constants.RX_I18N_MSG_ELEMENT.subn(ur'%(start:\1)s\2%(end:\1)s', translated_string_template)
            if not count:
                break
            
        # Construct output based on the translated string template
        string_template_item_list = constants.RX_I18N_MSG_TEMPLATE_ITEM.split(translated_string_template)
        string_template_item_iter = iter(string_template_item_list)
        block_list = [blocks_module.TextBlock(lineno, string_template_item_iter.next())]
        for item_identifier, text_fragment in itertools.izip(string_template_item_iter, string_template_item_iter):
            if ':' in item_identifier:
                element_number = int(item_identifier.split(':')[1])
                element_block = element_map.get(element_number)
                if element_block is None:
                    raise ValueError(
                        'Invalid element reference [%d:...] in '
                        'translated string template: %r' % 
                        (element_number, string_template))
                if 0:
                    assert isinstance(element_block, base_blocks.ElementBlock)
                if item_identifier.startswith('start:'):
                    block_list.append(element_block.start_tag)
                    # FIXME: It is a workaround needed, since we remove the
                    # ElementBlock which prevents the postprocessing step from
                    # correctly adding the ending > character here. Short tags
                    # should not be used for translated elements, so it is okay
                    # this way for now.
                    block_list.append(blocks_module.MarkupBlock(element_block.lineno, u'>'))
                elif item_identifier.startswith('end:'):
                    block_list.append(element_block.end_tag)
            else:
                text_expression_block = parameter_map.get(item_identifier)
                if text_expression_block is None:
                    raise ValueError(
                        'Invalid parameter reference %%(%s)s in '
                        'translated string template: %r' % 
                        (item_identifier, string_template))
                block_list.append(text_expression_block)
            block_list.append(blocks_module.TextBlock(lineno, text_fragment))
            
        # Add whitespace if any
        if left_whitespace:
            block_list.insert(0, blocks_module.TextBlock(lineno, left_whitespace))
        if right_whitespace:
            block_list.append(blocks_module.TextBlock(lineno, right_whitespace))
            
        if constants.GENERATE_DEBUG_COMMENTS:
            block.template_line = (
                self.template_lines[lineno] + 
                ': language translation of string template: %r => %r' % 
                (string_template, translated_string_template))
            
        # Replace the children with the blocks generating the translated contents
        block.children[:] = block_list
        
        return block
    
    def transform_i18n_msg_block(self, block, iter_element_numbers, iter_parameters, element_map, parameter_map):
        """ Transforms a block to be usable in the subtree of an i18n:msg block
        """
        # Type hint
        if 0:
            assert isinstance(block, base_blocks.BaseBlock)
        
        if 'parameter_name' in block.__slots__:
            # Assign parameter names to template expressions
            try:
                block.parameter_name = iter_parameters.next()
            except StopIteration:
                raise ValueError(
                    'No parameter name defined for one or more expression '
                    'inside i18n:msg element at line #%d!' % block.lineno)
            parameter_map[block.parameter_name] = block
        
        elif 'element_number' in block.__slots__:
            # Assign integer serial numbers to the elements
            block.element_number = iter_element_numbers.next()
            element_map[block.element_number] = block
            
        block.apply_transformation(self.transform_i18n_msg_block, iter_element_numbers, iter_parameters, element_map, parameter_map)
        
        return [block]
    
    ### Methods compiling text and attribute values
    
    def compile_text(self, lineno, block, text, attribute=None, translatable=False):
        """ Compiles template variable references inside a text fragment
        
        lineno: Template source code line number.
        
        block: Container block to append to.
        
        text: Template text with template expressions in it to compile.
        
        attribute: AttributeValueBlock instance if the expression generates
            the value of an element attribute, otherwise None.
            
        translatable: True if the text fragment is part of a translatable element.
            It is always False if translation support is disabled, since the sets
            of translatable elements and attributes are empty in that case.
        
        """
        blocks_module = self.blocks_module

        # Empty text?
        if not text:
            return block

        # Function to append a fragment to the output, determines runtime escaping
        if attribute:
            block_class = self.blocks_module.AttributeValueFragmentBlock
        else:
            block_class = self.blocks_module.TextBlock
        
        # Find all template expressions
        fragment_list = constants.RX_TEMPLATE_EXPRESSION.split(text)
        # NOTE: assert (len(fragment_list) - 1) % 4 == 0
        
        # Append the leading text block
        first_fragment = fragment_list[0]
        if first_fragment:
            if translatable and first_fragment.strip():
                # Translate text at compile time, but only without the surrounding whitespace
                left_whitespace, stripped_text, right_whitespace = util.separate_whitespace(first_fragment)
                stripped_text = self.translator_ugettext(stripped_text)
                first_fragment = left_whitespace + stripped_text + right_whitespace
            fragment_block = block_class(lineno, first_fragment)
            fragment_block.attribute = attribute
            block.append(fragment_block)
        
        # Append each template expression and their trailing text blocks
        for i in xrange(1, len(fragment_list), 4):
            
            expression1, expression2, expression3, fragment = fragment_list[i: i + 4]
            expression = expression1 or expression2 or expression3
            
            if expression is not None:
                expression_block = self.compile_template_expression(lineno, expression, attribute)
                block.append(expression_block)
                
            if fragment:
                if translatable and fragment.strip():
                    # Translate text at compile time, but only without the surrounding whitespace
                    left_whitespace, stripped_text, right_whitespace = util.separate_whitespace(fragment)
                    stripped_text = self.translator_ugettext(stripped_text)
                    fragment = left_whitespace + stripped_text + right_whitespace
                fragment_block = block_class(lineno, fragment)
                fragment_block.attribute = attribute
                block.append(fragment_block)
    
    def compile_template_expression(self, lineno, expression, attribute=None):
        """ Compiles a single template expression outputting text or HTML

        lineno: Template source code line number.
        
        expression: Template expression to compile (without the $ or {}),
            it can also be '$' for the '$$' escape.
        
        attribute: AttributeValueBlock instance if the expression generates
            (part of) the value of an element attribute, otherwise None.
        
        Returns the resulting code block.
        
        """
        expression = expression.strip()
        assert expression, 'Empty template expression'
        
        # The expression must be ASCII
        # FIXME: This limitation should be lifted eventually, since 
        #        variable names can include non-ASCII characters in Python.
        #        We enforce this now since the generated source code is ASCII.
        if isinstance(expression, unicode):
            expression = expression.encode('ascii')
        
        # NOTE: Markup() expressions will be translated to
        #       MarkupExpressionBlock by the postprocessor.
        if expression == '$':
            block = self.blocks_module.TextBlock(lineno, '$')
        elif attribute:
            block = self.blocks_module.AttributeExpressionBlock(lineno, expression)
            block.attribute = attribute
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
        if constants.DETECT_RECURSION:
            assert not block.contains(self)
            
        # Pass the enclosing py:switch directive down in the hierarchy
        if isinstance(block, base_blocks.SwitchBlock):
            switch = block

        # Postprocess all the child blocks, it also allows for replacing them
        block.apply_transformation(self.postprocess, switch)

        # Collect py:when and py:otherwise directives for the enclosing py:switch one
        if isinstance(block, base_blocks.CaseBlock):
            assert switch, 'Found py:when directive without an enclosing py:choose on line #%d!' % block.lineno
            switch.when_blocks.append(block)
            return []
        if isinstance(block, base_blocks.OtherwiseBlock):
            assert switch, 'Found py:otherwise directive without an enclosing py:choose on line #%d!' % block.lineno
            switch.otherwise_blocks.append(block)
            return []

        # Mark the py:switch directive as "prepared" when all its children have been processed
        if isinstance(block, base_blocks.SwitchBlock):
            block.prepared = True
        
        # Do not escape the output of template functions defined in this template
        if isinstance(block, base_blocks.TextExpressionBlock):
            
            expression = block.data.strip()
            
            if expression.endswith(')'):
                
                function_name = expression.split('(', 1)[0].strip()
                
                if function_name == 'Markup':
                    block = self.blocks_module.MarkupExpressionBlock(
                        block.lineno, expression[7: -1].strip())
                
                if function_name in self.function_map:
                    block = self.blocks_module.MarkupExpressionBlock(
                        block.lineno, expression)
                    
            elif expression == 'None':
                # Genshi converts None valued expressions to empty output
                return []
            
        # Finalize elements
        if isinstance(block, base_blocks.ElementBlock):
            
            if block.start_tag:
                
                # We can't shorten the element if there are any child elements
                # in it or we are outputting XHTML and this element does not
                # have a short form.
                # See also: http://www.w3.org/TR/xhtml1/#guidelines
                if (block.children or
                    (self.output_standard == 'xhtml' and 
                     ':' not in block.data and
                     block.data not in constants.SHORT_HTML_ELEMENTS_SET)):
                    
                    # Close start tag
                    block.start_tag.append(
                        self.blocks_module.MarkupBlock(block.lineno, u'>'))
                    
                else:
                    # Shorten the element
                    block.start_tag.append(
                        self.blocks_module.MarkupBlock(block.lineno, u' />'))
                    block.end_tag = None
                    
        return [block]
            
    ### Optimizer making the generated code simpler and more efficient
    
    def optimize(self, block):
        """ Optimizes the source code block hierarchy
        
        Returns the list of replacement blocks.
        
        """
        blocks_module = self.blocks_module
        
        # Clear parent references to break reference loops
        # NOTE: Such references can only be used by the compilation and
        #       postprocessing phases, they must not be used by the
        #       optimizations or the formatting methods. All information 
        #       must be stored in the blocks by now.
        block.element = None
        block.attribute = None
        
        # Optimize all the child blocks first
        block.apply_transformation(self.optimize)
        
        # Extract leading and trailing invariant markup whenever possible
        if (isinstance(block, (base_blocks.WithBlock, blocks_module.AttributeValueBlock)) and
            (block.children and
            (block.children[0].is_invariant() or
             block.children[-1].is_invariant()))):
        
            leading_invariant_blocks = []
            while block.children and block.children[0].is_invariant():
                leading_invariant_blocks.append(block.children.pop(0))
                
            trailing_invariant_blocks = []
            while block.children and block.children[-1].is_invariant():
                trailing_invariant_blocks.insert(0, block.children.pop(-1))

            block = blocks_module.DummyBlock(
                block.lineno,
                children=(
                    leading_invariant_blocks +
                    ([] if block.is_empty() else [block]) +
                    trailing_invariant_blocks))

            # Optimize the newly added block
            block.apply_transformation(self.optimize)
        
        # Collide nested py:with directives (single child only)
        if (isinstance(block, base_blocks.WithBlock) and
            len(block.children) == 1 and
            isinstance(block.children[0], base_blocks.WithBlock)):
        
            block.data = '%s; %s' % (block.data.rstrip(';'), block.children[0].data)
            block.children = block.children[0].children
        
        # Foreign element optimizations
        if isinstance(block, base_blocks.ElementBlock):
            
            # Put the start and end tags into the list of children
            # blocks if the tags cannot be stripped out. It allows for
            # colliding the tags with the tail and head of static contents.
            if block.strip_expression is None:

                # Inline the start tag
                if block.start_tag:
                    if constants.GENERATE_DEBUG_COMMENTS:
                        block.template_line = (
                            (block.start_tag.template_line or '') +
                            block.template_line)
                    block.children[0:0] = block.start_tag.children
                    block.start_tag = None
                    
                # Inline the end tag
                if block.end_tag:
                    if constants.GENERATE_DEBUG_COMMENTS:
                        block.template_line += (block.end_tag.template_line or '')
                    block.children.extend(block.end_tag.children)
                    block.end_tag = None
                    
                # Remove the ElementBlock container,
                # it allows for colliding it with the surrounding markup
                element_block = block
                block = base_blocks.DummyBlock(
                    element_block.lineno,
                    children=element_block.children)
                
                if constants.GENERATE_DEBUG_COMMENTS:
                    block.template_line = element_block.template_line
                
                # Optimize the newly added block
                block.apply_transformation(self.optimize)
                
        # Concatenate subsequent child blocks emitting static markup
        children = block.children
        if len(children) > 1:
            
            for index in xrange(len(children) - 1, 0, -1):
                
                first_block = children[index - 1]
                second_block = children[index]
                
                if (isinstance(first_block, base_blocks.InvariantBlock) and
                    isinstance(second_block, base_blocks.InvariantBlock)):
                    
                    concatenated_markup = (
                        first_block.get_markup() + second_block.get_markup())
                    
                    concatenated_block = self.blocks_module.MarkupBlock(
                        lineno=first_block.lineno,
                        data=concatenated_markup)
                    
                    if constants.GENERATE_DEBUG_COMMENTS:
                        concatenated_block.template_line = (
                            (first_block.template_line or '') + 
                            (second_block.template_line or ''))
                        
                    children[index - 1] = concatenated_block
                    del children[index]
                    
        # Static markup and text content optimizations,
        # these do not affect attribute values
        if isinstance(block, (base_blocks.MarkupBlock, base_blocks.TextBlock)):
            
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
        
        block: Block to dump.
        
        output: File object, file name or any other object with a true
            truth value to dump the block to stdout.
            
        description: Description to print to stdout before dumping there.
        
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
