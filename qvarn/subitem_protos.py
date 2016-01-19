# subitem_protos.py - keep track of subitem prototypes
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


class SubItemPrototypes(object):

    def __init__(self):
        self._prototypes = {}

    def add(self, item_type, subitem_name, prototype):
        key = self._key(item_type, subitem_name)
        assert key not in self._prototypes
        self._prototypes[key] = prototype

    def _key(self, item_type, subitem_name):
        return (item_type, subitem_name)

    def get(self, item_type, subitem_name):
        key = self._key(item_type, subitem_name)
        return self._prototypes[key]

    def get_all(self):
        return [
            (self._subitem_name(key), prototype)
            for key, prototype in self._prototypes.items()]

    def _subitem_name(self, key):
        return key[1]
