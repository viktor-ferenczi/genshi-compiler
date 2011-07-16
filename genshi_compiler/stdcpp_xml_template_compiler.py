""" Genshi XML template to standard C++ source code compiler

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

import base_xml_template_compiler, stdcpp_blocks


class StdcppXMLTemplateCompiler(base_xml_template_compiler.BaseXMLTemplateCompiler):
    """ Genshi XML template compiler resulting in standard C++ source code
    
    The generated module contains a render function with the signature
    given to the `compile` method. It can be used to render the template
    at runtime and returns unicode.
    
    """
    
    # Generate Python source code blocks
    blocks_module = stdcpp_blocks
