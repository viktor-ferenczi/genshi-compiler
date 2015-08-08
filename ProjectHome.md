Genshi Compiler allows for compiling simple Genshi XML templates to pure Python code.

**[Quick Tutorial](http://code.google.com/p/genshi-compiler/wiki/tutorial)**

How to install:

  * Download and install the source distribution or installer appropriate for your OS
  * Or execute: `easy_install genshi_compiler`

Short summary:

Genshi Compiler allows for rendering your Genshi template to Python source code. You can save the code as a Python module or compile it into a directly usable module object in memory. Just call the render function on the module with your template parameters to render the whole template or any of your template functions to render those fragments separately.

According to my initial benchmarks the rendering speed is typically `~40x` faster than doing the same using Genshi. There is a cost of this speedup, certainly. Some of Genshi's dynamic features are not available, most notably anything that depends on a template loader (`xi:include`), the XML element tree representation (`py:match`) or the token stream (filters).

Genshi Compiler currently supports the compile time translation of element contents, attributes and the `i18n:msg` directive. Other `i18n` features (`i18n:comment`, `i18n:domain`, `i18n:choose`, `i18n:singular`, `i18n:plural`) are not supported, currently. Runtime translation of dynamic text data is possible only by passing the translator object to the template and calling it explicitly from expressions as needed. Compile time translation also means that you need to translate each template to every target language and handle the compiled modules separately.

Includes can be replaced by importing and calling other compiled template modules directly, so that is not a real limitation. Generic macro support (py:match) seems to be hopeless without slowing down the generated code considerably and loosing most of the performance gain. Token streams might be supported in the future.

This solution still allows you to speed up the most time critical parts (rendering large tables, trees, or lots of HTML user interface elements) considerably without too much effort, providing you can afford loosing the above functionality. It is also possible to combine Genshi and compiled template code for maximum flexibility and performance.

Genshi Compiler does not force any particular module naming or placement. It means that `xi:include` will not be implemented and no mapping of `href` values to module names will be added. The same applies to the multiple language translations of the same template. You are free to choose how to arrange your modules in a way compatible with your application.

You can define the template parameters by adding a `py:def` attribute to its top level element. Alternatively you can pass the argument list of the top level render function to the compile method directly (please see its docstring).

Python 3 support is in the plans.

**[Features and limitations](http://code.google.com/p/genshi-compiler/wiki/features)**

**[Benchmarks](http://code.google.com/p/genshi-compiler/wiki/benchmarks)**

&lt;wiki:gadget url="http://www.ohloh.net/p/585426/widgets/project\_users.xml?style=green" height="100" border="0"/&gt;