# Benchmarks #

## Environment ##

  * CPU: Intel Core i7 920 @ 2.67GHz
  * Motherboard: Gigabyte GA-EX58-UD5
  * Memory: Kingston 3x2GB DDR3 1600MHz CL9 KHX1600C9D3T1K3/6GX at its default memory profile
  * OS: Ubuntu 10.04 amd64, GNOME
  * HDD: Intel X25-M SSD

Some of these components are not relevant to the tests for sure. I've documented them for completeness. Testing were done on the host machine (not inside a VM) while there were no significant background tasks or disk activity.

Please note, that these benchmarks are not covering all possible cases, so they can only be used to give you a rough idea on how much speed boost you can expect from compiling your template.

Test methods:

  * Genshi: The template is rendered by Genshi. Loading of the template is not measured, only the `template.generate()` and `stream.render()` calls.

  * Compiled: The template is rendered by the generated Python code. Measured the execution time of the `render` method of the compiled template.

  * Cython compiled: The template is rendered by an C extension module created by Cython compiling the generated Python source code. (No type declarations are added.)

Please note, that your test results may vary due to background processing and disk I/O, but that's normal.

You can find the benchmark scripts in the `benchmarks` subdirectory of the source distribution.

## Unit test templates ##

1. `benchmark_directives.py`

  * Genshi: 7.267 ms (1.00x)
  * Compiled: 0.179 ms (40.60x)
  * Cython compiled: 0.167 ms (43.51x)