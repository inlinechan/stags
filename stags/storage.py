"""Persistent and simple in-memory storage

"""

import UserDict
import shelve

class ShelveStorage(UserDict.DictMixin):
    def __init__(self, filename, *args):
        self.dict = shelve.open(filename, *args)

    def __setitem__(self, key, value):
        # cursor = self.dict[key]
        # cursor = value
        # self.dict[key] = value
        self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]

    def __delitem__(self, key):
        self.dict.__delitem__(key)

    def keys(self):
        return self.dict.keys()

    def __del__(self):
        self.dict.close()

    def close(self):
        self.__del__()

    def sync(self):
        self.dict.sync()
