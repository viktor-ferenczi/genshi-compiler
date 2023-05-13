""" Unit test cases for the XML template compiler generating Python code

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

# Add the extracted distribution folder to the Python module search path
# to allow testing it before installation
import os, sys

if os.path.isdir('../genshi_compiler'):
    sys.path.insert(0, '..')

import unittest
import gettext

import genshi_compiler
from genshi_compiler import (
    constants, util, html_minimizer, python_xml_template_compiler)

import data

### Constants

TESTS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(TESTS_DIR, 'data')
TRANSLATIONS_DIR = os.path.join(DATA_DIR, 'translations')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
EXPECTED_OUTPUT_DIR = os.path.join(DATA_DIR, 'expected_output')
GENERATED_SOURCE_DIR = os.path.join(DATA_DIR, 'generated_source')

assert os.path.isdir(DATA_DIR)
assert os.path.isdir(TRANSLATIONS_DIR)
assert os.path.isdir(OUTPUT_DIR)
assert os.path.isdir(EXPECTED_OUTPUT_DIR)
assert os.path.isdir(GENERATED_SOURCE_DIR)


### Helpers

def update_translations(locale='en_US'):
    """ Updates the test translation files based on the test templates
    
    Requires pybabel on the system path.
    
    """
    if os.system('pybabel -q extract --no-location --mapping=translation.ini --output="data/messages.pot" data'):
        return False

    if os.system('pybabel -q update -i "data/messages.pot" -d "data/translations" -l %s' % locale):
        return False

    os.remove('data/messages.pot')

    return True


def compile_translations():
    """ Compiles the test translation files from .po to .mo
    
    Requires pybabel on the system path.
    
    """
    if os.system('pybabel -q compile -f -D messages -d "data/translations" -l en_US'):
        return False

    return True


### Unit test cases

class PythonXMLTemplateCompilerTestCase(unittest.TestCase):
    """ Unit test cases for the Genshi XML template compiler
    """

    def compile_template(self,
                         basename,
                         arguments='',
                         root_def=None,
                         translator=None):

        """ Compiles a single test template to a module, then import it
        the first time.
        
        basename: Name of the template file without extension, it is also the module name
        arguments: The arguments of the template like in a Python function definition
        root_def: Name of compiled template function to associate with the root element
        translator: gettext compatible translator object or None to disable i18n
        
        Returns the imported module.
        
        """
        # Load the template
        template_filename = '%s.html' % basename
        template_filepath = os.path.join(DATA_DIR, template_filename)
        with open(template_filepath, 'rt', encoding='utf8') as template_file:
            template_xml = template_file.read()
        assert template_xml

        if root_def:
            # Compile the root element into its own function
            template_xml = template_xml.replace(
                '>',
                ' py:def="%s(%s)" >' % (root_def, arguments),
                1)
            arguments = ''

        # Compile it to module source
        compiler = python_xml_template_compiler.PythonXMLTemplateCompiler()
        compiler.load(template_xml, template_filename=template_filename)
        if translator is not None:
            # FIXME: Allow for testing custom translatable element and attribute tuples!
            compiler.configure_i18n(translator)
        module_source = compiler.compile(arguments)
        assert isinstance(module_source, str)

        # Save it as a Python module file
        module_filepath = os.path.join(GENERATED_SOURCE_DIR, '%s.py' % basename)
        with open(module_filepath, 'wt') as module_file:
            module_file.write(module_source)

        # Import the module
        data_package = __import__('data.generated_source.%s' % basename, globals(), locals())
        generated_source_subpackage = getattr(data_package, 'generated_source')
        module = getattr(generated_source_subpackage, basename)

        return module

    def compare_with_expected_output(self, output, basename):
        """ Compiles a single test template to a module, import it, then
        executes the template with the test parameters given checking for
        the expected output
        
        output: The output of the compiled template
        basename: Name of the template file without extension, it is also the module name
        
        """
        # Verify the results
        expected_output_filepath = os.path.join(EXPECTED_OUTPUT_DIR, '%s.expected-output.html' % basename)
        with open(expected_output_filepath, 'rt', encoding='utf-8') as expected_output_file:
            expected_output = expected_output_file.read()
        if output != expected_output:
            util.print_diff(expected_output, output, 'Expected output', 'Output of the compiled template')
        self.assertEqual(expected_output, output)

    def compare_with_genshi(self,
                            output,
                            basename,
                            arguments,
                            template_parameters=None,
                            translator=None):

        """ Compares the output of a single compiled template with the output
        generated by Genshi itself

        output: The output of the compiled template
        basename: Name of the template file without extension, it is also the module name
        arguments: The arguments of the template like in a Python function definition
        template_parameters: Keyword parameters to pass to the template
        
        """
        # Render the same template using Genshi
        try:
            import genshi
        except ImportError:
            print()
            'Genshi is not installed, testing against Genshi skipped.'
            return

        if template_parameters is None:
            template_parameters = {}

        import genshi.template
        template_filename = '%s.html' % basename
        template_pathname = os.path.join(DATA_DIR, template_filename)
        with open(template_pathname, 'rt', encoding='utf-8') as template_file:
            source = template_file.read()
        assert source
        genshi_template = genshi.template.MarkupTemplate(
            source,
            filepath=template_pathname,
            filename=template_filename)
        if translator:
            from genshi import filters
            translator_filter = filters.Translator(translator)
            translator_filter.setup(genshi_template)
        kws = eval('dict(%s)' % arguments)
        kws.update(template_parameters)
        token_stream = genshi_template.generate(**kws)
        genshi_output = token_stream.render(method='xml', encoding=None)
        assert isinstance(genshi_output, str)

        if constants.DEBUGGING:
            with open('data/output/%s.output.html' % basename, 'wt', encoding='utf-8') as output_file:
                output_file.write(output)
            with open('data/output/%s.genshi.output.html' % basename, 'wt', encoding='utf-8') as output_file:
                output_file.write(genshi_output)

        # Normalize output to make them comparable
        minimized_output = util.remove_duplicate_whitespace(html_minimizer.minimize(output))
        minimized_genshi_output = util.remove_duplicate_whitespace(html_minimizer.minimize(genshi_output))

        # Removing all the whitespace between and around elements
        minimized_output = minimized_output.replace('>\n', '>', ).replace('> ', '>').replace('\n<', '<', ).replace(' <', '<')
        minimized_genshi_output = minimized_genshi_output.replace('>\n', '>', ).replace('> ', '>').replace('\n<', '<', ).replace(' <', '<')

        # Add back newlines after each tag to allow printing unified difference
        minimized_output = minimized_output.replace('>', '>\n', )
        minimized_genshi_output = minimized_genshi_output.replace('>', '>\n', )

        if constants.DEBUGGING:
            with open('data/output/%s.minimized.output.html' % basename, 'wt', encoding='utf-8') as output_file:
                output_file.write(minimized_output)
            with open('data/output/%s.minimized.genshi.output.html' % basename, 'wt', encoding='utf-8') as output_file:
                output_file.write(minimized_genshi_output)

        # Compare the results
        if minimized_output != minimized_genshi_output:
            util.print_diff(minimized_genshi_output, minimized_output, 'Genshi output', 'Output of the compiled template')
        self.assertEqual(minimized_genshi_output, minimized_output)

    def do_test(self,
                basename,
                arguments,
                template_parameters=None,
                root_def=False,
                translator=None):

        """ Processes all the tests for a single test template
        
        """
        if template_parameters is None:
            template_parameters = {}

        if root_def:
            # Compile the template to a module
            module = self.compile_template(
                basename=basename,
                arguments=arguments,
                root_def='html_element',
                translator=translator)

            # Invoke the compiled template with the test parameters
            output = module.html_element(**template_parameters)
        else:
            # Compile the template to a module
            module = self.compile_template(
                basename=basename,
                arguments=arguments,
                translator=translator)

            # Invoke the compiled template with the test parameters
            output = module.render(**template_parameters)
        assert isinstance(output, str)

        # Compare the results
        self.compare_with_genshi(
            output,
            basename,
            arguments,
            template_parameters,
            translator)

        # Compare the results with the pre-stored expected output
        # NOTE: We need to disable this for development, then store the expected
        #       output into the appropriate files for the public releases to
        #       allow testing without Genshi installed.
        self.compare_with_expected_output(output, basename)

    def test_basic(self):
        """ Tests basic template functionality, like the Genshi directives
        """
        self.do_test(
            basename='basic',
            arguments="count=10, text='default text', type=int, object=(1, 2, 3), empty=None",
            root_def=True)

    def test_i18n(self):
        """ Tests i18n functionality (language translation)
        """
        self.assertTrue(update_translations())
        self.assertTrue(compile_translations())

        translator = gettext.translation('messages', TRANSLATIONS_DIR, ('en_US.UTF-8',))
        assert translator.gettext('Testing markup') == 'translated: Testing markup'

        class Site(object):
            url = 'http://www.example.com'
            title = 'Google'

        class User(object):
            link = 'http://www.example.com/username/'
            username = 'test'
            realname = 'Test User'
            contact_count = 5

        self.do_test(
            basename='i18n',
            arguments="site=None, user=None, a=0, b=0, c=0",
            template_parameters=dict(site=Site(), user=User(), a=1, b=2, c=3),
            translator=translator)


if __name__ == '__main__':
    unittest.main()
