""" Simple benchmark timing the directives.html unit test template

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

# Add the extracted distribution folder to the Python module search path
# to allow testing it before installation
import os, sys
if os.path.isdir('../genshi_compiler'):
    sys.path.append('..')

import types

try:
    import cython
except ImportError:
    cython = None

import genshi
import genshi.template

import genshi_compiler
from genshi_compiler import util, html_minimizer, python_xml_template_compiler

import benchmark


CWD = os.path.dirname(__file__)
TEST_DATA_DIR = os.path.abspath(os.path.join(CWD, '..', 'tests', 'data'))


def main():
    # Properties of the test template
    template_basename = 'directives'
    template_filename = '%s.html' % template_basename
    template_filepath = os.path.join(TEST_DATA_DIR, template_filename)
    arguments = "count=10, text='default text', type=int, object=(1, 2, 3), empty=None"
    
    # Load the template from the tests
    with open(template_filepath, 'rt') as template_file:
        template_xml = template_file.read()
    assert template_xml.decode('utf8')
    
    # Compile the template to a module without writing it to a file (in memory)
    compiler = python_xml_template_compiler.PythonXMLTemplateCompiler()
    compiler.load(template_xml, template_filename=template_filename) 
    module_source = compiler.compile(arguments)
    module_source = module_source.rstrip() + '\n'
    module = types.ModuleType('directives')
    exec module_source in module.__dict__
    render_compiled = module.render

    # Load the template into Genshi
    genshi_template = genshi.template.MarkupTemplate(
        template_xml,
        filepath=template_filepath,
        filename=template_filename)
    def render_genshi(kws = eval('dict(%s)' % arguments)):
        token_stream = genshi_template.generate(**kws)
        genshi_output = token_stream.render(method='xml', encoding=None)
    
    # Time Genshi template rendering
    genshi_time = min(benchmark.benchmark(render_genshi, 0.1) for n in xrange(10))
    print 'Genshi: %.3f ms' % (genshi_time * 1000)

    # Time compiled template rendering
    compiled_time = min(benchmark.benchmark(render_compiled, 0.1) for n in xrange(10))
    print 'Compiled: %.3f ms' % (compiled_time * 1000)

    # Time the Cython compiled version if Cython is available
    if cython:
        
        # Write out the compiled template as a pyx file
        pyx_filepath = os.path.join(CWD, '%s.pyx' % template_basename)
        with open(pyx_filepath, 'wt') as module_file:
            module_file.write(module_source)
        
        # Import it via Cython
        import pyximport
        pyximport.install()
        import directives
        render_cython_compiled = directives.render
        
        # Time it
        cython_compiled_time = min(benchmark.benchmark(render_cython_compiled, 0.1) for n in xrange(10))
        print 'Cython compiled: %.3f ms' % (cython_compiled_time * 1000)
    
if __name__ == '__main__':
    main()
