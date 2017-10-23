import setuptools

# Get version info
__version__ = None
__release__ = None
exec open('genshi_compiler/version.py')

setuptools.setup(
    name='genshi-compiler',
    version=__release__,
    description='Genshi template compiler',
    long_description='''\
Genshi Compiler allows for compiling simple Genshi XML templates
to pure Python code. You can render the whole template or any of
the template functions by importing generated code. The generated
code is typically ~40x faster than rendering the same via Genshi.
There is a cost of this speedup. Some of Genshi's dynamic
features are not available, most notably anything that depends
on a template loader (xi:include, xi:fallback), the XML element
tree representation (py:match) or the token stream (filters).
Language translation (i18n) support is currently limited
to simple text inside the translatable elements and attributes
and the i18n:msg directive.''',  
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
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
    url='https://github.com/viktor-ferenczi/genshi-compiler/',
    license='MIT',
    packages=['genshi_compiler'],
    test_suite='unittest',
    zip_safe=False,
    install_requires=['lxml'],
    )
