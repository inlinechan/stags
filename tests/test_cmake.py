""" Unittest for cmake directory starts with test_

"""

from unittest import TestCase, skip
import clang.cindex
import os
import subprocess
from stags.project import Project
import sys
from stags.common import *
from stags.query import query_class_hierarchy, query, Query

import logging

class TestCmake(TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            libclang_set_library_file()
        except Exception:
            pass

    @staticmethod
    def value(p, usr, key):
        return p[usr][key]

    @staticmethod
    def filename_locus(filename, locus):
        return '{}:{}'.format(filename, locus)

    @staticmethod
    def usr(p, filename, locus):
        return p[filename][locus][USR]

    @staticmethod
    def ref_usr(p, filename, locus):
        return p[filename][locus][REF_USR]

    def template_usr(self, p, filename, locus):
        import pprint
        pp = pprint.PrettyPrinter(indent=4)

        pp.pprint('template_usr() filename: {}, locus: {}'.format(filename, locus))
        pp.pprint(p)
        return p[self.basename(filename)][locus][TEMPLATE_USR]

    def run_dir(self, name):
        basedir = os.path.abspath('tests/{}'.format(name))
        if not basedir.endswith('/'):
            basedir += '/'
        builddir = os.path.join(basedir, 'build')
        if not os.path.exists(builddir):
           os.mkdir(builddir)
        pobj = subprocess.Popen(['cmake', '-DCMAKE_EXPORT_COMPILE_COMMANDS=1', basedir],
                                cwd=builddir,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        ret = pobj.wait()
        self.assertEqual(ret, 0)
        proj = Project(builddir, basedir)

        self.sources = {}
        for root, _, files in os.walk(basedir):
            for file in files:
                self.sources[file] = os.path.join(root, file)

        self.basedir = basedir
        return (proj.parse_all(proj.scan()), basedir)

    def is_declaration_of(self, p, get_usr, file1, locus1, file2, locus2):
        self.assertEqual(self.value(p, get_usr(p, self.basename(file1), locus1), DECL),
                         self.filename_locus(self.basename(file2), locus2))

    def is_definition_of(self, p, get_usr, file1, locus1, file2, locus2):
        self.assertEqual(self.value(p, get_usr(p, self.basename(file1), locus1), DEFI),
                         self.filename_locus(self.basename(file2), locus2))

    def is_baseclass_of(self, p, file1, locus1, file2, locus2):
        self.assertIn(self.usr(p, self.basename(file1), locus1),
                      self.value(p, self.usr(p, self.basename(file2), locus2), BASE_CLASS))

    def is_childclass_of(self, p, file1, locus1, file2, locus2):
        self.assertIn(self.usr(p, self.basename(file1), locus1),
                      self.value(p, self.usr(p, self.basename(file2), locus2), CHILD_CLASS))

    def basename(self, filename):
        assert(self.basedir)
        idx = filename.find(self.basedir)
        logging.error('basename: filename: {}, basedir: {}'.format(filename, self.basedir))
        if idx == -1:
            return filename
        else:
            return filename[(idx + len(self.basedir)):]

class TestDefinition(TestCmake):
    def test_definition(self):
        parsed_dict, _ = self.run_dir(sys._getframe().f_code.co_name)
        self.assertTrue(parsed_dict)

        s = self.sources
        p = parsed_dict

        self.is_declaration_of(p, self.usr, s['world.cpp'], '3:6', s['world.h'], '4:6')

class TestClass(TestCmake):
    def test_class(self):
        parsed_dict, _ = self.run_dir(sys._getframe().f_code.co_name)
        self.assertTrue(parsed_dict)

        s = self.sources
        p = parsed_dict

        self.is_declaration_of(p, self.ref_usr, s['main.cpp'], '6:8', s['derived.h'], '8:18')
        self.is_definition_of(p, self.ref_usr, s['main.cpp'], '6:8', s['derived.cpp'], '3:15')
        self.is_declaration_of(p, self.ref_usr, s['derived.cpp'], '5:11', s['base.h'], '6:18')
        self.is_definition_of(p, self.ref_usr, s['derived.cpp'], '5:11', s['base.cpp'], '3:12')
        self.is_baseclass_of(p, s['base.h'], '4:7', s['derived.h'], '6:7')
        self.is_childclass_of(p, s['derived.h'], '6:7', s['base.h'], '4:7')

        self.is_definition_of(p, self.usr, s['base.h'], '6:18', s['base.cpp'], '3:12')
        self.is_declaration_of(p, self.usr, s['base.cpp'], '3:12', s['base.h'], '6:18')

        # test CursorKind.TYPE_REF
        self.is_definition_of(p, self.ref_usr, s['derived.cpp'], '3:6', s['derived.h'], '6:7')

        # functional
        functional_tests = (
            (Query.Definition, ('base.h', '6:18'),      ('base.cpp', '3:12')),
            (Query.Definition, ('derived.h', '8:18'),   ('derived.cpp', '3:15'))
        )

        for type, src, dst in functional_tests:
            src_file, src_locus = src
            dst_file, dst_locus = dst
            query_location = self.filename_locus(s[src_file], src_locus)
            actual = query(type, query_location, p)
            expected = self.filename_locus(s[dst_file], dst_locus)
            self.assertEqual(expected, self.basedir + actual)

class TestClassMemberVariable(TestCmake):
    def test_class_member_variable(self):
        parsed_dict, _ = self.run_dir(sys._getframe().f_code.co_name)
        self.assertTrue(parsed_dict)

        s = self.sources
        p = parsed_dict

        self.is_definition_of(p, self.ref_usr, s['main.cpp'], '3:35', s['main.cpp'], '7:9')
        self.is_definition_of(p, self.ref_usr, s['main.cpp'], '4:32', s['main.cpp'], '7:9')

class TestTemplate(TestCmake):
    def test_template(self):
        parsed_dict, _ = self.run_dir(sys._getframe().f_code.co_name)
        self.assertTrue(parsed_dict)

        s = self.sources
        p = parsed_dict

        self.is_definition_of(p, self.template_usr, s['main.cpp'], '15:23', s['main.cpp'], '7:7')

        result = query_class_hierarchy(s['main.cpp'], '15:23', p, export_as="text")
        expected_result = set([('class Derived', 'Delegate<class Derived>'),
                               ('MoreDerived', 'class Derived'),
                               ('class Derived', 'class Base')])
        self.assertEqual(result, expected_result)

class TestFunctionTemplate(TestCmake):
    def test_function_template(self):
        parsed_dict, _ = self.run_dir(sys._getframe().f_code.co_name)
        self.assertTrue(parsed_dict)

        s = self.sources
        p = parsed_dict

        self.is_definition_of(p, self.template_usr, s['main.cpp'], '14:7', s['main.cpp'], '4:10')
        self.is_definition_of(p, self.template_usr, s['main.cpp'], '15:7', s['main.cpp'], '4:10')
        self.is_definition_of(p, self.template_usr, s['main.cpp'], '16:7', s['main.cpp'], '4:10')
