""" Runs all the unit test cases
"""

import os, unittest

def import_test_cases():
    """ Imports test cases from all the local modules
    """
    print 'Importing test cases:'
    print
    
    # Discover test modules
    test_module_name_list = [
        fn[:-3]
        for fn in os.listdir('.') 
        if fn.startswith('test_') and fn.endswith('.py')]
    
    # Import test cases into the global namespace
    global_namespace = globals()
    for test_module_name in test_module_name_list:
        print ' - from %s:' % test_module_name
        test_module = __import__(test_module_name)
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if type(obj) is type and issubclass(obj, (unittest.TestCase, unittest.TestSuite)):
                print '   %s' % name
                global_namespace[name] = obj
        print
        
    print 'Done importing test cases.'

if __name__ == '__main__':
    import_test_cases()
    print
    print 'Running test cases:'
    unittest.main()
