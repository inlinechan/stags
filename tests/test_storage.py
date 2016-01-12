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

    def test_save_and_delitem_dict(self):
        src = {'1': 2, '3': 4}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        d.close()

        d = Storage(filename)
        del d['1']
        self.assertFalse(d.has_key('1'))
        self.assertTrue(d.has_key('3'))
        d.close()

        os.remove(filename)

    def test_save_and_delitem_child_dict(self):
        src = {'1': 2, 'child': {'3': 4, '5': 6}}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        d.close()

        d = Storage(filename)
        child = d['child']
        del child['3']
        self.assertFalse('3' in child)
        d['child'] = child
        self.assertFalse(d['child'].has_key('3'))
        d.close()

        d = Storage(filename, 'r')
        self.assertFalse(d['child'].has_key('3'))
        d.close()

        os.remove(filename)

    def test_save_and_update_dict(self):
        src = {'1': 2, '3': 4}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['3'], 4)
        d.close()

        d = Storage(filename)
        new = {'1': 10, '3': 20}
        d.update(new)
        self.assertEqual(d['1'], 10)
        self.assertEqual(d['3'], 20)
        d.close()

        os.remove(filename)

    def test_save_and_update_not_delete_item_dict(self):
        src = {'1': 2, '3': 4}
        filename = sys._getframe().f_code.co_name
        d = Storage(filename, 'n')
        d.update(src)
        self.assertEqual(d['1'], 2)
        self.assertEqual(d['3'], 4)
        d.close()

        d = Storage(filename)
        new = {'2': 10, '3': 20}
        d.update(new)
        self.assertTrue('1' in d) # does not delete '1'
        self.assertEqual(d['2'], 10)
        self.assertEqual(d['3'], 20)
        d.close()

        os.remove(filename)
