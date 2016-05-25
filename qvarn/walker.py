# walker.py - visit every part of an API item or item prototype
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


import qvarn


class ItemWalker(object):

    '''Visit every part of an API item or item prototype.

    Various parts of the backend need to "walk" through all the parts
    of an item, or a prototype. This is similar to visiting all the
    nodes in a binary tree, or othe data structure. The logic of
    walking is encapsulated here, so that it need not be repeated
    everywhere.

    This class is meant to be subclassed, and the subclasses should
    define the various ``visit_*`` methods. They are called as
    follows: assume an item that looks like this:

        {
            u'type': u'dummy',
            u'foo': u'foo',
            u'bar'; [u'bar'],
            u'foobar': [
                {
                    u'yo': False,
                    u'yoyo': 0,
                    u'baz': u[u'baz'],
                },
                {
                    u'yo': True,
                    u'yoyo': 1,
                    u'baz': u[u'pling'],
                },
            ],
        }

    The sequence of visit calls would be:

        visit_main_dict(item, [u'foo'])
        visit_main_str_list(item, u'bar')
        visit_main_dict_list(item, u'foobar', [u'yo', u'yoyo', u'baz'])
        visit_dict_in_list(item, u'foobar', 0, [u'yo', u'yoyo', u'baz'])
        visit_dict_in_list_str_list(item, u'foobar', 0, u'baz')
        visit_dict_in_list(item, u'foobar', 1, [u'yo', u'yoyo', u'baz'])
        visit_dict_in_list_str_list(item, u'foobar', 1, u'baz')

    '''

    def walk_item(self, item, proto_item):
        '''Walk every part of an item.'''
        self._walk_main_dict(item, proto_item)
        for field in self._get_str_lists(proto_item):
            self.visit_main_str_list(item, field)
        for field in self._get_dict_lists(proto_item):
            self._walk_dict_list(item, field, proto_item[field][0])

    def _walk_main_dict(self, item, proto):
        names = self._get_simple_columns(proto)
        self.visit_main_dict(item, names)

    def _get_simple_columns(self, proto):
        def is_simple(proto_value):
            return isinstance(proto_value, qvarn.column_types)
        return sorted(x for x in proto if is_simple(proto[x]))

    def _get_str_lists(self, proto):
        def is_str_list(v):
            return isinstance(v, list) and isinstance(v[0], unicode)
        return sorted(x for x in proto if is_str_list(proto[x]))

    def _get_dict_lists(self, proto):
        def is_dict_list(proto_value):
            return (isinstance(proto_value, list) and
                    isinstance(proto_value[0], dict))
        return [x for x in proto if is_dict_list(proto[x])]

    def _walk_dict_list(self, item, field, proto_dict):
        names = self._get_simple_columns(proto_dict)
        self.visit_main_dict_list(item, field, names)

        for i in range(len(item[field])):
            self.visit_dict_in_list(item, field, i, names)
            for str_list_field in self._get_str_lists(proto_dict):
                self.visit_dict_in_list_str_list(
                    item, field, i, str_list_field)

    def visit_main_dict(self, item, column_names):
        '''Visit the main dict of an item, and its simple columns.

        ``column_names`` is the list of all the simple columns only.

        '''

    def visit_main_str_list(self, item, field):
        '''Visit a string list at the top level of an item.'''

    def visit_main_dict_list(self, item, field, column_names):
        '''Visit a list of dicts at the top level.'''

    def visit_dict_in_list(self, item, field, pos, column_names):
        '''Visit a dict in a list of dicts, and the simple columns.'''

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        '''Visit a string list in a dict in a list of dicts.'''
