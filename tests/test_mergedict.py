"""Unittest for mergedict

"""

from unittest import TestCase
from stags.mergedict import merge_recurse_inplace

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
