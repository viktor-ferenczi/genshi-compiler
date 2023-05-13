""" Simple benchmark timing the directives.html unit test template

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

# Add the extracted distribution folder to the Python module search path
# to allow testing it before installation
import os, sys
if os.path.isdir('../genshi_compiler'):
    sys.path.insert(0, '..')

import types

try:
    import cython
except ImportError:
    cython = None

import genshi
import genshi.template

from genshi_compiler import python_xml_template_compiler

import benchmark


CWD = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.abspath(os.path.join(CWD, '..', 'tests', 'data'))


def main(template_basename='basic',
         arguments="count=10, text='default text', type=int, object=(1, 2, 3), empty=None",
         template_parameters={},
         translator=None):
    print('Benchmarking unit test template: %s' % template_basename)

    # Properties of the test template
    template_filename = '%s.html' % template_basename
    template_filepath = os.path.join(TEST_DATA_DIR, template_filename)
    
    # Load the template from the tests
    with open(template_filepath, 'rt', encoding='utf-8') as template_file:
        template_xml = template_file.read()
    assert template_xml
    
    # Parameters to pass to the compiled template
    render_parameters = eval('dict(%s)' % arguments)
    render_parameters.update(template_parameters)

    # Empty renderer to substract
    def empty_renderer(**kws):
        return ''
    def no_operation():
        local_var = empty_renderer(**render_parameters)
    
    # Compile the template to a module without writing it to a file (in memory)
    compiler = python_xml_template_compiler.PythonXMLTemplateCompiler()
    compiler.load(template_xml, template_filename=template_filename) 
    if translator is not None:
        compiler.configure_i18n(translator)
    module_source = compiler.compile(arguments)
    module_source = module_source.rstrip() + '\n'
    module = types.ModuleType(template_basename)
    exec(module_source, module.__dict__)

    def render_compiled():
        compiled_output = module.render(**render_parameters)
        
    # Load the template into Genshi
    genshi_template = genshi.template.MarkupTemplate(
        template_xml,
        filepath=template_filepath,
        filename=template_filename)

    def render_genshi():
        token_stream = genshi_template.generate(**render_parameters)
        genshi_output = token_stream.render(method='xml', encoding=None)
    
    # Time Genshi template rendering
    genshi_time = min(
        benchmark.benchmark(
            render_genshi, 
            0.1, 
            no_operation=no_operation)
        for n in range(10))
    print('Genshi: %.3f ms' % (genshi_time * 1000))

    # Time compiled template rendering
    compiled_time = min(
        benchmark.benchmark(
            render_compiled, 
            0.1, 
            no_operation=no_operation) 
        for n in range(10))
    print('Compiled: %.3f ms' % (compiled_time * 1000))

    # Time the Cython compiled version if Cython is available
    if cython:
        
        # Write out the compiled template as a pyx file
        pyx_filepath = os.path.join(CWD, '%s.pyx' % template_basename)
        with open(pyx_filepath, 'wt') as module_file:
            module_file.write(module_source)
        
        # Import it via Cython
        import pyximport
        pyximport.install()
        directives = __import__(template_basename, globals(), locals())
        def render_cython_compiled():
            cython_compiled_result = directives.render(**render_parameters)
        
        # Time it
        cython_compiled_time = min(
            benchmark.benchmark(
                render_cython_compiled, 
                0.1, 
                no_operation=no_operation) 
            for n in range(10))
        print('Cython compiled: %.3f ms' % (cython_compiled_time * 1000))

    print()


if __name__ == '__main__':
    
    main(
        template_basename='basic',
        arguments="count=10, text='default text', type=int, object=(1, 2, 3), empty=None")
    
    class Site(object):
        url = 'http://www.example.com'
        title = 'Google'
        
    class User(object):
        link = 'http://www.example.com/username/'
        username = 'test'
        realname = 'Test User'
        contact_count = 5
    
    main(
        template_basename='i18n', 
        arguments="site=None, user=None, a=0, b=0, c=0",
        template_parameters=dict(site=Site(), user=User(), a=1, b=2, c=3))
