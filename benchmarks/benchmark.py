""" Utility for benchmarking Python code

(C) 2011 - Viktor Ferenczi <viktor@ferenczi.eu>
    
License: MIT

"""

import time


def benchmark(function,
              period=1.0,
              minimum_time=1e-9,
              get_time=time.time,
              unbenchmarked_first_call=True,
              no_operation=lambda: None):
    """ Runs the given function as many times as it can in the given
    period of time
    
    function: callable (function) to benchmark
    
    period: approximate time period to repeatedly run the function
    
    get_time: function to acquire the current CPU or wall clock time
        with the highest precision possible
    
    unbenchmarked_first_call: set to False to prevent the first,
        unbenchmarked call to the callable
        
    no_operation: empty function used for the empty benchmark loop test,
        you should not need to midify this normally, but if you need
        to substract some internal operations or calls from the final
        results, then it might be useful to override this
    
    Returns the time needed to execute a single function call in average,
    substracting the empty benchmark loop and the function call itself.
    
    If you're timing a function which completes very quickly, then run
    the benchmark multiple times with a smaller period value and take
    the minimum execution time to get the most accurate result.
    
    """
    get_time = time.time
    
    # Time the empty benchmark loop first
    if function is no_operation:
        nop_time = 0.0
    else:
        nop_time = benchmark(no_operation, 0.1)

    # Call the function once without timing to fill any caches
    if unbenchmarked_first_call:
        function()
    
    # Wait for a clock tick
    st = get_time()
    while st == time.time():
        pass
    st = get_time()
    et = st + period 
    
    # Run the function as many times as we can in the given period of time
    count = 0
    while 1:
        function()
        count += 1
        if get_time() > et:
            break
        
    # Calculate the average execution time
    et = get_time()
    t = (et - st) / count - nop_time
    return max(minimum_time, t)


if __name__ == '__main__':
    print 'No operation: %.3f us (should be 0.001)' % (benchmark(lambda: None) * 1000000)
    print 'Convert to int: %.3f us' % (benchmark(lambda: int('123')) * 1000000)
    print 'Convert to bool: %.3f us' % (benchmark(lambda: bool('123')) * 1000000)
