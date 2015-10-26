""" Common

"""

import clang.cindex
import os

DEFI, DECL, KIND, SPELL, TYPE, USR, REFS, REF_LOCATION, REF_USR, TEMPLATE_USR = (
    'defi', 'decl', 'kind', 'spell', 'type', 'usr', 'refs', 'ref_location', 'ref_usr', 'template_usr',
)

BASE_CLASS, CHILD_CLASS = (
    'base_class', 'child_class'
)

def libclang_set_library_file():
    # Higher version first
    LIBCLANG_VERSIONS_SUPPORTED = (3.5, 3.4)

    for version in LIBCLANG_VERSIONS_SUPPORTED:
        libclang_so = '/usr/lib/llvm-{}/lib/libclang.so'.format(version)
        if os.path.isfile(libclang_so):
            clang.cindex.Config.set_library_file(libclang_so)
            return True
            # clang.cindex.Config.set_library_file('/usr/lib/llvm-3.5/lib/libclang.so')
    return False
