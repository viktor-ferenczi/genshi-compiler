import setuptools

# Get version info
__version__ = None
__release__ = None
exec open('genshi_compiler/version.py')

setuptools.setup(
    name='Genshi Compiler',
    version=__release__,
    description='Genshi XML template compiler',
    long_description='''\
Genshi Compiler allows for compiling simple Genshi XML templates
to pure Python code. You can render the whole template or any of
the template functions by importing generated code. The generated
code is typically ~40x faster than rendering the same via Genshi.
There is a cost of this speedup. Some of Genshi's dynamic
features are not available, most notably anything that depends
on a template loader (xi:include, xi:fallback), the XML element
tree representation (py:match) or the token stream (filters).''',  
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
        ], 
    keywords='python genshi compiler codegeneration template performance',
    author='Viktor Ferenczi',
    author_email='viktor@ferenczi.eu',
    url='http://code.google.com/p/genshi-compiler',
    license='MIT',
    packages=['genshi_compiler'],
    test_suite='unittest',
    zip_safe=False,
    install_requires=['lxml'],
    )