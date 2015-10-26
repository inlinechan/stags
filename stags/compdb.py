"""Compilation database module

"""

import clang.cindex
import logging
import os
import sys

# generator
def compile_commands(dirname):
    assert(dirname and os.path.isdir(dirname))
    compdb = clang.cindex.CompilationDatabase.fromDirectory(dirname)
    yield compdb.getAllCompileCommands()

def get_all_compile_commands(dirname):
    """
    Get an iterable object of each compile command having (dirname, arguments)
    """
    assert(dirname and os.path.isdir(dirname))
    for cmds in compile_commands(dirname):
        for cmd in cmds:
            yield (cmd.directory, ' '.join([arg for arg in cmd.arguments]))

if __name__ == '__main__':
    libclang_set_library_file()
    logging.basicConfig(level=logging.INFO)
    dirname = sys.argv[1]
    assert(dirname)

    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    for direc, arg in get_all_compile_commands(dirname):
        print('{} => {}'.format(direc, arg))

