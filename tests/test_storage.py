"""Unittest for ShelveStorage

"""

from stags.storage import ShelveStorage as Storage
from unittest import TestCase
import os
import sys
from tempfile import mkstemp

class TestShelveStorage(TestCase):
    def setup(self):
        pass

    def tearDown(self):
        pass

    def test_db_file_saved(self):
        # http://stackoverflow.com/a/13514318/2229134
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d['hello'] = 'world'
        self.assertEqual(d['hello'], 'world')
        d.close()
        os.remove(filename)

    def test_write_and_read(self):
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d['hello'] = 'world'
        self.assertEqual(d['hello'], 'world')
        d.close()

        d = Storage(filename, 'r')
        self.assertEqual(d['hello'], 'world')
        d.close()

        os.remove(filename)

    def test_write_dict(self):
        src = {1: 2, 3: 4}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d['src'] = src
        self.assertEqual(d['src'][1], 2)
        self.assertEqual(d['src'][3], 4)
        d.close()

        d = Storage(filename, 'r')
        self.assertEqual(d['src'][1], 2)
        self.assertEqual(d['src'][3], 4)
        d.close()

        os.remove(filename)

    def test_update_dict(self):
        src = {'1': 2, '3': 4}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['3'], 4)
        d.close()

        d = Storage(filename, 'r')
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['3'], 4)
        d.close()

        os.remove(filename)

    def test_update_complex_dict(self):
        src = {'1': 2, 'recur': {'3': 4, '5': 6}}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['recur'], {'3': 4, '5': 6})
        d.close()

        d = Storage(filename, 'r')
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['recur'], {'3': 4, '5': 6})
        d.close()

        os.remove(filename)

