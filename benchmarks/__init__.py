""" Genshi Compiler - Benchmarks

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

Please note, that these benchmarks are NOT covering all possible cases,
so they can only be used to give you a rough idea on how much speed boost
you can expect from compiling your template.

For current benchmarks and results please see the following Wiki page:
http://code.google.com/p/genshi-compiler/wiki/benchmarks

== benchmark_directives.py ==
 
   This script compares the rendering speed of the directives.html template
   while rendering via Genshi, rendering by executing the compiled template
   and rendering by executing the Cython compiled extension of the
   generated Python code.
   
   Our results:
   
   * Genshi: 7.267 ms (1.00x)
   * Compiled: 0.179 ms (40.60x)
   * Cython compiled: 0.167 ms (43.51x)

TODO: More benchmarks: big table, big tree, lots of UI elements, SVG, etc.

"""
