"""Project

"""

from common import *
from mergedict import merge_recurse_inplace
from storage import ShelveStorage as Storage
import clang.cindex
import compdb
import logging
import math
import multiprocessing as mp
import os
import parser
import pprint
import re
import sys
import util

def parse_one(src, compiler, *args, **kwargs):
    logging.debug('parsing {} with {}'.format(src, args))
    return parser.parse(src, *args, **kwargs)

@util.measure
def apply_parse(args, **kwargs):
    logging.debug('apply_parse: {}, **kwargs: {}'.format(args, kwargs))
    src, others = args
    return parse_one(src, *others, **kwargs)

class Project:
    def __init__(self, builddir, basedir):
        self.builddir = builddir
        self.basedir = basedir
        if not self.basedir.endswith('/'):
            self.basedir += '/'

    @util.measure
    def scan(self):
        sources = []
        processed = set()

        re_src = re.compile(r'.*/(.*\.(c|cpp|cc))$')

        for directory, arg_string in compdb.get_all_compile_commands(self.builddir):
            args = arg_string.split()
            compiler = args[0]
            arguments = args[1:]

            src = [x for x in arguments if re_src.match(x)]
            assert(len(src) == 1)
            src = src[0]
            others = [x for x in arguments if not re_src.match(x)]

            if src.endswith('.cpp') or src.endswith('.cc'):
                others.extend(['-x' ,'c++'])

            extensions = ('.hpp', '.h')
            base, ext = os.path.splitext(src)
            headers = [(base + ext, others)
                       for ext in extensions
                       if os.path.isfile(base + ext)]
            sources.append((src, others))
            sources.extend(headers)
        return sources

    @util.measure
    def parse_all(self, sources, **kwargs):
        # from http://eli.thegreenplace.net/2012/01/16/python-parallelizing-cpu-bound-tasks-with-multiprocessing
        exclude_filters = '/usr/include'
        sources = filter(lambda s: not s[0].startswith(exclude_filters), sources)
        sources = filter(lambda s: not s[0].endswith('.c'), sources)

        # sources = filter(lambda s: s[0].endswith('hello.cpp'), sources)
        def worker(dirname, jobs, out_q):
            result_dict = {}
            for job in jobs:
                filename = job[0]
                result_dict[filename] = apply_parse(job, basedir = dirname, **kwargs)

            parsed_dict = {}
            for result in result_dict.values():
                merge_recurse_inplace(parsed_dict, result)
            out_q.put(parsed_dict)

        out_q = mp.Queue()
        nprocs = mp.cpu_count()
        jobs = sources
        chunksize = int(math.ceil(len(jobs) / float(nprocs)))
        procs = []

        for i in range(nprocs):
            p = mp.Process(
                target=worker,
                args=(self.basedir, jobs[chunksize * i:chunksize * (i + 1)],
                      out_q))
            procs.append(p)
            p.start()

        parsed_dict = {}

        for i in range(nprocs):
            result = out_q.get()
            merge_recurse_inplace(parsed_dict, result)

        for p in procs:
            p.join()

        parsed_dict['basedir'] = self.basedir

        return parsed_dict


    def parse_all_single(self, sources, **kwargs):
        pp = pprint.PrettyPrinter(indent=4)
        parsed_dict = {}
        for job in sources:
            result = apply_parse(job, basedir = self.basedir, **kwargs)
            merge_recurse_inplace(parsed_dict, result)

        parsed_dict['basedir'] = self.basedir

        return parsed_dict

if __name__ == '__main__':
    libclang_set_library_file()
    logging.basicConfig(level=logging.INFO)
    assert(len(sys.argv) > 1)
    builddir = os.path.abspath(sys.argv[1])
    basedir = os.path.abspath(sys.argv[2])
    action = None
    if len(sys.argv) == 4:
        action = sys.argv[3]
    project = Project(builddir, basedir)

    parsed_dict = {}

    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    if action == 'scan':
        pp.pprint(project.scan())
        sys.exit(0)
    elif action == 'parse':
        parsed_dict = project.parse_all(project.scan())

        pp.pprint('Parsed {} in {} with keys'.format(len(parsed_dict), builddir))
        pp.pprint(parsed_dict.keys())
    elif action == 'parse_single':
        parsed_dict = project.parse_all_single(project.scan(), debug=True)
        pp.pprint('Parsed {} in {} with keys'.format(len(parsed_dict), builddir))
        pp.pprint(parsed_dict.keys())

    dbname = 'stags.db'
    storage = Storage(dbname)
    storage_update = util.measure(storage.update)

    storage_update(parsed_dict)
