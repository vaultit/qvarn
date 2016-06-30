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
        u'bool': False
    }

    item = {
        u'type': u'yo',
        u'foo': u'foobar',
        u'bar': u'barbaz',
        u'bars': [u'bar1', u'bar2'],
        u'dicts': [
            {
                u'baz': u'bling',
                u'foobars': [],
                u'foo': [],
                u'bar': u'bong',
                u'inner': [
                    {
                        u'inner_foo': u'inner_foo',
                    },
                ],
            },
            {
                u'baz': u'blang',
                u'foobars': [],
                u'foo': [],
                u'bar': u'Bang',
                u'inner': [],
            },
        ],
        u'bool': True
    }

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
