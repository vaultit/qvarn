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

import bottle

import qvarn

from qvarn.list_resource import (
    LimitWithoutSortError, BadLimitValue, BadOffsetValue
)


class ListResourceBase(unittest.TestCase):

    resource_type = u'yo'

    prototype = {
        u'type': u'',
        u'id': u'',
        u'revision': u'',
        u'foo': u'',
        u'bar': u'',
    }

    def setUp(self):
        self._dbconn = qvarn.DatabaseConnection()
        self._dbconn.set_sql(qvarn.SqliteAdapter())

        vs = qvarn.VersionedStorage()
        vs.set_resource_type(self.resource_type)
        vs.start_version(u'first-version', None)
        vs.add_prototype(self.prototype)
        with self._dbconn.transaction() as t:
            vs.prepare_storage(t)

        self.ro = qvarn.ReadOnlyStorage()
        self.ro.set_item_prototype(self.resource_type, self.prototype)

        self.wo = qvarn.WriteOnlyStorage()
        self.wo.set_item_prototype(self.resource_type, self.prototype)

        self.resource = qvarn.ListResource()
        self.resource.set_path(self.resource_type)
        self.resource.set_item_type(self.resource_type)
        self.resource.set_item_prototype(self.prototype)
        self.resource.set_listener(FakeListenerResource())
        self.resource.prepare_resource(self._dbconn)

    def tearDown(self):
        # Reset bottle request.
        bottle.request = bottle.LocalRequest()


class ListResourceTests(ListResourceBase):

    def test_lists_no_items_initially(self):
        with self._dbconn.transaction() as t:
            items = [
                {u'type': u'yo', u'foo': u'a', u'bar': u'z'},
                {u'type': u'yo', u'foo': u'c', u'bar': u'x'},
                {u'type': u'yo', u'foo': u'b', u'bar': u'y'},
            ]
            for item in items:
                self.wo.add_item(t, item)

        # Sort by foo.
        bottle.request.environ['REQUEST_URI'] = '/search/sort/foo/show_all'
        search_result = self.resource.get_matching_items(None)
        match_list = [item[u'foo'] for item in search_result[u'resources']]
        self.assertEqual(match_list, [u'a', u'b', u'c'])

        # Sort by bar.
        bottle.request.environ['REQUEST_URI'] = '/search/sort/bar/show_all'
        search_result = self.resource.get_matching_items(None)
        match_list = [item[u'bar'] for item in search_result[u'resources']]
        self.assertEqual(match_list, [u'x', u'y', u'z'])


class LimitTests(ListResourceBase):

    def setUp(self):
        super(LimitTests, self).setUp()
        with self._dbconn.transaction() as t:
            for x in [u'a', u'b', u'c', u'd', u'e']:
                self.wo.add_item(t, {u'type': u'yo', u'foo': x, u'bar': u''})

    def _search(self, url):
        bottle.request.environ['REQUEST_URI'] = url
        search_result = self.resource.get_matching_items(None)
        return [item[u'foo'] for item in search_result[u'resources']]

    def test_limit(self):
        result = self._search(u'/search/show_all/sort/foo/limit/2')
        self.assertEqual(result, [u'a', u'b'])

    def test_offset(self):
        result = self._search(u'/search/show_all/sort/foo/offset/3')
        self.assertEqual(result, [u'd', u'e'])

    def test_limit_and_offset(self):
        result = self._search(u'/search/show_all/sort/foo/offset/1/limit/2')
        self.assertEqual(result, [u'b', u'c'])

    def test_big_offset(self):
        result = self._search(u'/search/show_all/sort/foo/offset/10')
        self.assertEqual(result, [])

    def test_limit_without_sort(self):
        message = (
            u"LIMIT and OFFSET can only be used with together SORT."
        )
        with self.assertRaises(LimitWithoutSortError, msg=message):
            self._search(u'/search/show_all/limit/2')

    def test_invalid_limit(self):
        message = (
            u"Invalid LIMIT value: invalid literal for int() with base 10: "
            u"'err'."
        )
        with self.assertRaises(BadLimitValue, msg=message):
            self._search(u'/search/show_all/sort/foo/limit/err')

    def test_invalid_offset(self):
        message = (
            u"Invalid OFFSET value: invalid literal for int() with base 10: "
            u"'err'."
        )
        with self.assertRaises(BadOffsetValue, msg=message):
            self._search(u'/search/show_all/sort/foo/offset/err')

    def test_negative_limit(self):
        message = u"Invalid LIMIT value: should be positive integer."
        with self.assertRaises(BadOffsetValue, msg=message):
            self._search(u'/search/show_all/sort/foo/offset/-1')

    def test_negative_offset(self):
        message = u"Invalid OFFSET value: should be positive integer."
        with self.assertRaises(BadOffsetValue, msg=message):
            self._search(u'/search/show_all/sort/foo/offset/-1')


class FakeListenerResource(object):

    def notify_create(self, item_id, item_revision):
        pass

    def notify_update(self, item_id, item_revision):
        pass

    def notify_delete(self, item_id):
        pass
