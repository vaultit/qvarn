# subitem_protos.py - keep track of subitem prototypes
#
# Copyright 2015, 2016 Suomen Tilaajavastuu Oy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
