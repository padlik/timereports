#!/bin/env python

import collections


class LazyDict(collections.MutableMapping):
    """
        Dict for processing elements only once they are accessed
    """

    def __init__(self, *args, **kwargs):
        self._lazy_dict = dict()
        self.update(*args, **kwargs)

    def __len__(self):
        return len(self._lazy_dict)

    def __iter__(self):
        for key in self._lazy_dict.keys():
            yield key

    def __delitem__(self, key):
        """
        @param key - value of this key will be invalidated, item will not be actually removed:
        @return: None
        """
        if key in self._lazy_dict.keys():
            self._lazy_dict[key] = None
        else:
            raise KeyError("Key '%s' does now exists" % key)

    def __setitem__(self, key, value):
        self._lazy_dict[key] = value
        self.updated(key, value)

    def updated(self, key, value):
        pass

    def __batch_update__(self, items):
        return items

    def __getitem__(self, key):
        items = {_key: _val for _key, _val in self._lazy_dict.iteritems() if not _val}
        if items:
            items = self.__batch_update__(items)
            self.update(items)
        return self._lazy_dict[key]

    def __repr__(self):
        return repr(self._lazy_dict)

    def __str__(self):
        return str(self._lazy_dict)

    def clear(self):
        """
        Does not actually clear, but reset all items for processing
        when cache is invalidated
        @return: None
        """
        self._lazy_dict = {key: None for key in self._lazy_dict.keys()}

    def real_clear(self):
        self._lazy_dict.clear()

    def real_delitem(self, item):
        del self._lazy_dict[item]
