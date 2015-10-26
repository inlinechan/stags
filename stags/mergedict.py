""" Merge two dict

"""

from common import *
import pprint
import util

def merge_recurse_inplace(d1, d2):
    """ Merge small dict to large dict recursive manner

    """

    if isinstance(d1, dict) and isinstance(d2, dict):
        for key in d2.keys():
            if key in d1:
                if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    merge_recurse_inplace(d1[key], d2[key])
                elif isinstance(d1[key], list) and isinstance(d2[key], list):
                    for value in d2[key]:
                        if not value in d1[key]:
                            d1[key].append(value)
                else:
                    d1[key] = d2[key]
            else:
                d1[key] = d2[key]
    elif isinstance(d1, list) and isinstance(d2, list):
        for value in d2:
            if not value in d1:
                d1.append(value)
    else:
        assert False
