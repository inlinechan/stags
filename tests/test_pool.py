"""Unittest for multiprocessing.pool

"""

from unittest import TestCase
import multiprocessing as mp

def cube(x):
    return x**3

class TestPool(TestCase):
    def test_pool_map(self):
        pool = mp.Pool(processes=4)
        results = pool.map(cube, range(10))
        self.assertEqual([x**3 for x in range(10)], results)
