# read_only_tests.py - unit tests for ReadOnlyStorage
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


import unittest

import qvarn


def _build_item(baz=(u'bling', u'blang'), bool=True, bar=u'barbaz',
                dicts_bar=(u'bong', u'Bang'), bars=(u'bar1', u'bar2'),
                foo=u'foobar'):
    return {
        u'type': u'yo',
        u'foo': foo,
        u'bar': bar,
        u'bars': list(bars),
        u'dicts': [
            {
                u'baz': baz[0],
                u'foobars': [],
                u'foo': [],
                u'bar': dicts_bar[0],
                u'inner': [
                    {
                        u'inner_foo': u'inner_foo',
                    },
                ],
            },
            {
                u'baz': baz[1],
                u'foobars': [],
                u'foo': [],
                u'bar': dicts_bar[1],
                u'inner': [],
            },
        ],
        u'bool': bool,
    }


class ReadOnlyStorageTests(unittest.TestCase):

    resource_type = u'yo'

    prototype = {
        u'type': u'',
        u'id': u'',
        u'revision': u'',
        u'foo': u'',
        u'bar': u'',
        u'bars': [u''],
        u'dicts': [
            {
                u'baz': u'',
                u'foobars': [u''],
                u'foo': [u''],
                u'bar': u'',
                u'inner': [
                    {
                        u'inner_foo': u'',
                    },
                ],
            },
        ],
        u'bool': False,
    }

    item = _build_item()

    subitem_name = u'secret'

    subitem_prototype = {
        u'secret_identity': u'',
    }

    def setUp(self):
        self._dbconn = qvarn.DatabaseConnection()
        self._dbconn.set_sql(qvarn.SqliteAdapter())

        vs = qvarn.VersionedStorage()
        vs.set_resource_type(self.resource_type)
        vs.start_version(u'first-version', None)
        vs.add_prototype(self.prototype)
        vs.add_prototype(self.subitem_prototype, subpath=self.subitem_name)
        with self._dbconn.transaction() as t:
            vs.prepare_storage(t)

        self.ro = qvarn.ReadOnlyStorage()
        self.ro.set_item_prototype(self.item[u'type'], self.prototype)
        self.ro.set_subitem_prototype(
            self.item[u'type'], self.subitem_name, self.subitem_prototype)

        self.wo = qvarn.WriteOnlyStorage()
        self.wo.set_item_prototype(self.item[u'type'], self.prototype)
        self.wo.set_subitem_prototype(
            self.item[u'type'], self.subitem_name, self.subitem_prototype)

    def test_lists_no_items_initially(self):
        with self._dbconn.transaction() as t:
            self.assertEqual(self.ro.get_item_ids(t), [])

    def test_raises_error_when_item_does_not_exist(self):
        with self.assertRaises(qvarn.ItemDoesNotExist):
            with self._dbconn.transaction() as t:
                self.ro.get_item(t, u'does-not-exist')

    def test_lists_added_item(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            self.assertIn(added[u'id'], self.ro.get_item_ids(t))

    def test_gets_added_item(self):
        self.maxDiff = None
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            item = self.ro.get_item(t, added[u'id'])
            self.assertEqual(added, item)

    def test_gets_empty_subitem_of_added_item(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            subitem = self.ro.get_subitem(t, added[u'id'], self.subitem_name)
            self.assertEqual(subitem[u'secret_identity'], u'')

    def dont_test_search_main_item(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t, [(u'exact', u'foo', u'foobar')], [])
        self.assertEqual(search_result, {u'resources': [{u'id': new_id}]})

    def dont_test_search_main_list(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t, [('exact', u'bars', u'bar1')], {})
        self.assertIn(new_id, search_result[u'resources'][0][u'id'])

    def dont_test_search_multiple_conditions(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t,
                [
                    (u'exact', u'foo', u'foobar'),
                    (u'exact', u'bars', u'bar1')
                ],
                [])
        self.assertIn(new_id, search_result[u'resources'][0][u'id'])

    def dont_test_search_multiple_conditions_from_same_table(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t,
                [
                    (u'exact', u'foo', u'foobar'),
                    (u'exact', u'type', u'yo')
                ],
                [])
        self.assertIn(new_id, search_result[u'resources'][0][u'id'])

    def dont_test_search_multiple_conditions_from_different_rows(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t,
                [
                    (u'exact', u'baz', u'bling'),
                    (u'exact', u'baz', u'blang')
                ],
                [])
        self.assertIn(new_id, search_result[u'resources'][0][u'id'])

    def dont_test_search_condition_with_multiple_targets(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t, [(u'exact', u'bar', u'barbaz')], [])
        match_list = search_result[u'resources']
        self.assertIsNot(0, len(match_list))
        self.assertIn(new_id, match_list[0][u'id'])

    def dont_test_search_with_show_all(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t, [(u'exact', u'foo', u'foobar')], [u'show_all'])
        match_list = search_result[u'resources']
        self.assertIn(new_id, match_list[0][u'id'])
        self.assertIn(u'barbaz', match_list[0][u'bar'])

    def dont_test_search_with_boolean(self):
        with self._dbconn.transaction() as t:
            self.wo.add_item(t, self.item)
            search_result = self.ro.search(
                t, [(u'exact', u'bool', 'false')], [u'show_all'])
        match_list = search_result[u'resources']
        self.assertEqual(match_list, [])

    def dont_test_case_insensitive_search(self):
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, self.item)
            new_id = added[u'id']
            search_result = self.ro.search(
                t, [(u'exact', u'bar', u'BANG')], [u'show_all'])
        match_list = search_result[u'resources']
        self.assertIn(new_id, match_list[0][u'id'])

    def test_case_search_bad_key(self):
        with self.assertRaises(qvarn.FieldNotInResource):
            with self._dbconn.transaction() as t:
                self.wo.add_item(t, self.item)
                self.ro.search(t, [(u'exact', u'KEY', u'BANG')], [u'show_all'])

    def test_search_sort_by_nested_field_in_a_list(self):
        with self._dbconn.transaction() as t:
            for baz in [(u'b', u'a'), (u'c', u'b'), (u'a', u'c')]:
                self.wo.add_item(t, _build_item(baz=baz))
            search_result = self.ro.search(t, [], [u'show_all'], [u'baz'])
        match_list = [item[u'dicts'][0][u'baz']
                      for item in search_result[u'resources']]
        self.assertEqual(match_list, [u'a', u'b', u'c'])

    def test_search_sort_by_bool(self):
        with self._dbconn.transaction() as t:
            for value in [True, False]:
                self.wo.add_item(t, _build_item(bool=value))
            search_result = self.ro.search(t, [], [u'show_all'], [u'bool'])
        match_list = [item[u'bool'] for item in search_result[u'resources']]
        self.assertEqual(match_list, [0, 1])

    def test_search_sort_by_invalid_field_name(self):
        with self._dbconn.transaction() as t:
            self.wo.add_item(t, self.item)
            with self.assertRaises(qvarn.FieldNotInResource):
                search_result = self.ro.search(t, [], [], [u'invalid'])

    def test_search_sort_by_dict(self):
        with self._dbconn.transaction() as t:
            self.wo.add_item(t, self.item)
            with self.assertRaises(qvarn.FieldNotInResource):
                search_result = self.ro.search(t, [], [], [u'dicts'])

    def test_search_sort_by_first_instance(self):
        # If a field with same name appears more than one time in deffered
        # resource places, use only first instance. First means by the order of
        # qvarn.ItemWalker.
        with self._dbconn.transaction() as t:
            items = [
                {u'bar': u'a', u'dicts_bar': (u'z', u'z')},
                {u'bar': u'c', u'dicts_bar': (u'x', u'x')},
                {u'bar': u'b', u'dicts_bar': (u'y', u'y')},
            ]
            for kwargs in items:
                self.wo.add_item(t, _build_item(**kwargs))
            search_result = self.ro.search(t, [], ['show_all'], [u'bar'])
        match_list = [item[u'bar'] for item in search_result[u'resources']]
        self.assertEqual(match_list, [u'a', u'b', u'c'])

    def test_search_sort_by_multiple_fields(self):
        # If a field with same name appears more than one time in deffered
        # resource places, use only first instance. First means by the order of
        # qvarn.ItemWalker.
        with self._dbconn.transaction() as t:
            items = [
                {u'foo': u'a', u'bar': u'x'},
                {u'foo': u'a', u'bar': u'z'},
                {u'foo': u'a', u'bar': u'y'},
                {u'foo': u'b', u'bar': u'a'},
            ]
            for kwargs in items:
                self.wo.add_item(t, _build_item(**kwargs))
            search_result = self.ro.search(
                t, [], ['show_all'], [u'foo', u'bar'])
        match_list = [(item[u'foo'], item[u'bar'])
                      for item in search_result[u'resources']]
        self.assertEqual(match_list, [
            (u'a', u'x'),
            (u'a', u'y'),
            (u'a', u'z'),
            (u'b', u'a'),
        ])
