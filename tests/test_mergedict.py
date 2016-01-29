"""Unittest for mergedict

"""

import os
import sys

from stags.mergedict import merge_recurse_inplace
from stags.storage import ShelveStorage as Storage
from unittest import TestCase, skip

class TestMergeRecurseInplace(TestCase):
    def test_simple(self):
        d1 = {'file1': {'1:2': {'refs': [1]}, '3:4': {'refs': [2, 3]}}}
        d2 = {'file1': {'1:2': {'refs': [2, 3]}, '5:6': {'refs': [4, 5]}}}

        merge_recurse_inplace(d1, d2)
        ds_expected = {'file1': {'1:2': {'refs': [1, 2, 3]},
                                 '3:4': {'refs': [2, 3]},
                                 '5:6': {'refs': [4, 5]}}}
        self.assertEqual(d1, ds_expected)

    def test_duplicate(self):
        d1 = {'file1': {'1:2': {'kind': 'FUNCTION_DECL', 'refs': [1]}, '3:4': {'refs': [2, 3]}}}
        d2 = {'file1': {'1:2': {'kind': 'FUNCTION_DECL', 'refs': [1]}, '3:4': {'refs': [2, 3]}}}
        merge_recurse_inplace(d1, d2)
        self.assertEqual(d1, d2)

class TestMergeRecurseInplaceWithShelveStorage(TestCase):
    def test_simple(self):
        d1 = {'file1': [1]}
        d2 = {'file1': [2]}

        filename = sys._getframe().f_code.co_name + '.db'
        p = Storage(filename, writeback=True)
        p.update(d1)

        merge_recurse_inplace(p, d2, Storage)
        p.sync()

        ds_expected = {'file1': [1, 2]}
        self.assertEqual(p, ds_expected)

        p.close()
        os.remove(filename)

    def test_recursive(self):
        d1 = {'file1': {'1:2': {'refs': [1]}, '3:4': {'refs': [2, 3]}}}
        d2 = {'file1': {'1:2': {'refs': [2, 3]}, '5:6': {'refs': [4, 5]}}}

        filename = sys._getframe().f_code.co_name + '.db'
        p = Storage(filename, writeback=True)
        p.update(d1)

        merge_recurse_inplace(p, d2, Storage)
        p.sync()

        ds_expected = {'file1': {'1:2': {'refs': [1, 2, 3]},
                                 '3:4': {'refs': [2, 3]},
                                 '5:6': {'refs': [4, 5]}}}
        self.assertEqual(p, ds_expected)

        p.close()
        os.remove(filename)
