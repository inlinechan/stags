""" Common utility

"""

import logging
import time

def measure(func, *args, **kwargs):
    def start(*args, **kwargs):
        begin = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        arg = args
        while not (isinstance(arg, str) or isinstance(arg, int) or isinstance(arg, float)):
            if isinstance(arg, list) or isinstance(arg, tuple):
                arg = arg[0]
            elif isinstance(args, dict):
                arg = ''
            else:
                arg = ''

        arg_trun = arg
        if len(arg) > 70:
            arg_trun = arg[:67]
        logging.info('{} took {:6.3f} sec {}'.format(func.__name__ ,
                                                     end - begin, arg_trun))
        logging.debug('with {} and {}'.format(args, kwargs))
        return result
    return start
