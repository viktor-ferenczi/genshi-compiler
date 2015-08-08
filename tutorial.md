# Quick Tutorial #

## Import the compiler ##

```
import genshi_compiler
from genshi_compiler import python_xml_template_compiler
```

## Load an XML template ##

We just use a string literal here, but you could load the template from a file or just pass a file object as `xml_template`:

```
xml_template = '''\
<html xmlns:py="http://genshi.edgewall.org/">
  <body>
    <table>
      <tr py:for="y in xrange(a, b)">
        <td py:for="x in xrange(16)" py:content="unichr(16 * y + x)" />
      </tr>
    </table>
  </body>
</html>'''
```

## Create a compiler instance ##

You need to create a compiler object:

```
compiler = python_xml_template_compiler.PythonXMLTemplateCompiler()
```

Compiler objects are reusable, you can compile multiple templates in a series using a single object. The compiler is not thread safe, please don't try to compile multiple templates in parallel. Using separate compiler objects for each thread will work as expected.

Fully qualified module and class names are used to allow for later extension to text templates and other output languages while keeping the names consistent.

## Load the template ##

```
compiler.load(
    xml_template,
    'character_table.html',
    'character_table')
```

The filename and identifier are optional, but useful for debugging and make the source code comment at the top of the generated code a bit more verbose.

## Compile the template ##

module\_source = compiler.compile('a, b')

It will generate the following pure Python source code:

```
#!/usr/bin/python
# -*- coding: ascii -*-

""" Generated template rendering code based on the following Genshi
XML template: character_table

WARNING: This is automatically generated source code!
WARNING: Do NOT modify this file by hand or YOUR CHANGES WILL BE LOST!

Modify the character_table.html
XML template file, then regenerate this module instead.

"""

import xml.sax.saxutils

# Converts any object to unicode
_x_to_text = unicode

# XML escapes text
_x_escape_text = xml.sax.saxutils.escape

def _x_escape_attribute(value, quoteattr=xml.sax.saxutils.quoteattr):
    """ Escapes a value to be usitable for double quoted XML attributes
    """
    return quoteattr("'" + value)[2: -1]

def _x_format_attributes(_x_append_markup, attributes):
    """ Emits attributes at runtime
    """
    global _x_escape_attribute

    for attribute_name, attribute_value in attributes.iteritems():
        if attribute_value is not None:
            _x_append_markup(' %s="%s"' % (
                attribute_name, _x_escape_attribute(attribute_value)))

def render(a, b):
    global _x_escape_text, _x_to_text
    
    _x_markup_fragments = []
    _x_append_markup = _x_markup_fragments.append
    
    _x_append_markup(u'<html>\n<body>\n<table>\n<tr>\n<td></td>\n</tr>\n</table>\n</body>\n</html>')
    
    _x_html = ''.join(_x_markup_fragments)
    return _x_html
```

It is pretty much the code you would need to write by hand to render the same content in a secure and optimal way. But maintaining the Genshi XML template is easier, it is the whole point of the compiler.

## Compile the Python source code into a module ##

You can compile the source code directly to a Python module without having to write it to disk file:

```
import types
module = types.ModuleType('character_table')
exec module_source in module.__dict__
```

It is useful for development and for long running server side applications. For building products for deployment you can do better by saving the generated code into a Python module file and just import it from your release build. Such a solutions avoids the delivery of your original template, the template compiler and its dependencies.

## Render the template ##

You can render the template by invoking the `render` function of your compiled template module:

```
html = module.render(2, 8)
```

The output is always an unicode object:

type(html)
<type 'unicode'>

You can also call any of the template functions defined in your XML template.

Output of the above example template (printing to an UTF-8 console):

```
html = html.encode('utf-8')
print html
```

Output:

```
<html>
<body>
<table>
<tr>
<td> </td><td>!</td><td>"</td><td>#</td><td>$</td><td>%</td><td>&amp;</td><td>'</td><td>(</td><td>)</td><td>*</td><td>+</td><td>,</td><td>-</td><td>.</td><td>/</td>
</tr><tr>
<td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>:</td><td>;</td><td>&lt;</td><td>=</td><td>&gt;</td><td>?</td>
</tr><tr>
<td>@</td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td>
</tr><tr>
<td>P</td><td>Q</td><td>R</td><td>S</td><td>T</td><td>U</td><td>V</td><td>W</td><td>X</td><td>Y</td><td>Z</td><td>[</td><td>\</td><td>]</td><td>^</td><td>_</td>
</tr><tr>
<td>`</td><td>a</td><td>b</td><td>c</td><td>d</td><td>e</td><td>f</td><td>g</td><td>h</td><td>i</td><td>j</td><td>k</td><td>l</td><td>m</td><td>n</td><td>o</td>
</tr><tr>
<td>p</td><td>q</td><td>r</td><td>s</td><td>t</td><td>u</td><td>v</td><td>w</td><td>x</td><td>y</td><td>z</td><td>{</td><td>|</td><td>}</td><td>~</td><td></td>
</tr>
</table>
</body>
</html>
```

Which looks like:

<table cellpadding='2' border='1' cellspacing='0'>
<tr>
<td> </td><td>!</td><td>"</td><td>#</td><td>$</td><td>%</td><td><code>&amp;</code></td><td>'</td><td>(</td><td>)</td><td><code>*</code></td><td>+</td><td>,</td><td>-</td><td>.</td><td>/</td>
</tr><tr>
<td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>:</td><td>;</td><td><code>&lt;</code></td><td>=</td><td><code>&gt;</code></td><td>?</td>
</tr><tr>
<td>@</td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td>
</tr><tr>
<td>P</td><td>Q</td><td>R</td><td>S</td><td>T</td><td>U</td><td>V</td><td>W</td><td>X</td><td>Y</td><td>Z</td><td>[</td><td><code>\</code></td><td>]</td><td>^</td><td><code>_</code></td>
</tr><tr>
<td>`</td><td>a</td><td>b</td><td>c</td><td>d</td><td>e</td><td>f</td><td>g</td><td>h</td><td>i</td><td>j</td><td>k</td><td>l</td><td>m</td><td>n</td><td>o</td>
</tr><tr>
<td>p</td><td>q</td><td>r</td><td>s</td><td>t</td><td>u</td><td>v</td><td>w</td><td>x</td><td>y</td><td>z</td><td>{</td><td>|</td><td>}</td><td>~</td><td></td>
</tr>
</table>