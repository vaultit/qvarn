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


import json
import unittest
import urllib

import bottle

import qvarn

from qvarn.list_resource import (
    LimitWithoutSortError, BadLimitValue, BadOffsetValue, BadAnySearchValue
)


class ListResourceBase(unittest.TestCase):

    resource_type = u'yo'

    prototype = {
        u'type': u'',
        u'id': u'',
        u'revision': u'',
        u'foo': u'',
        u'bar': u'',
        u'lst': [u''],
    }

    _default_show = None

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

    def _add_item(self, foo=u'', bar=u'', lst=None):
        with self._dbconn.transaction() as t:
            self.wo.add_item(t, {
                u'type': u'yo',
                u'foo': foo,
                u'bar': bar,
                u'lst': lst or [],
            })

    def _search(self, url, show=None):
        bottle.request.environ['REQUEST_URI'] = url
        search_result = self.resource.get_matching_items(url)
        bottle.request = bottle.LocalRequest()

        show = self._default_show if show is None else show
        if show is None:
            return search_result[u'resources']
        else:
            return [x[show] for x in search_result[u'resources']]


class ListResourceTests(ListResourceBase):

    def test_lists_no_items_initially(self):
        self._add_item(foo=u'a', bar=u'z')
        self._add_item(foo=u'c', bar=u'x')
        self._add_item(foo=u'b', bar=u'y')

        # Sort by foo.
        result = self._search(u'/search/sort/foo/show_all', show='foo')
        self.assertEqual(result, [u'a', u'b', u'c'])

        # Sort by bar.
        result = self._search(u'/search/sort/bar/show_all', show='bar')
        self.assertEqual(result, [u'x', u'y', u'z'])


class LimitTests(ListResourceBase):
    _default_show = 'foo'

    def setUp(self):
        super(LimitTests, self).setUp()
        self._add_item(foo=u'a')
        self._add_item(foo=u'b')
        self._add_item(foo=u'c')
        self._add_item(foo=u'd')
        self._add_item(foo=u'e')

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
        with self.assertRaises(LimitWithoutSortError) as e:
            self._search(u'/search/show_all/limit/2')
        self.assertEqual(str(e.exception), (
            u"LIMIT and OFFSET can only be used with together SORT."
        ))

    def test_invalid_limit(self):
        with self.assertRaises(BadLimitValue) as e:
            self._search(u'/search/show_all/sort/foo/limit/err')
        self.assertEqual(str(e.exception), (
            u"Invalid LIMIT value: invalid literal for int() with base 10: "
            u"'err'."
        ))

    def test_invalid_offset(self):
        with self.assertRaises(BadOffsetValue) as e:
            self._search(u'/search/show_all/sort/foo/offset/err')
        self.assertEqual(str(e.exception), (
            u"Invalid OFFSET value: invalid literal for int() with base 10: "
            u"'err'."
        ))

    def test_negative_limit(self):
        with self.assertRaises(BadLimitValue) as e:
            self._search(u'/search/show_all/sort/foo/limit/-1')
        self.assertEqual(str(e.exception), (
            u"Invalid LIMIT value: should be positive integer."
        ))

    def test_negative_offset(self):
        with self.assertRaises(BadOffsetValue) as e:
            self._search(u'/search/show_all/sort/foo/offset/-1')
        self.assertEqual(str(e.exception), (
            u"Invalid OFFSET value: should be positive integer."
        ))


class SearchAnyTests(ListResourceBase):

    def test_exact_scalar(self):
        self._add_item(foo=u'a')
        self._add_item(foo=u'b')
        self._add_item(foo=u'c')

        value = urllib.quote(json.dumps([u'a', u'b']), safe='')
        result = self._search(u'/search/any/exact/foo/%s/show_all' % value,
                              show=u'foo')
        self.assertEqual(result, [u'a', u'b'])

    def test_contains_scalar(self):
        self._add_item(foo=u'foo')
        self._add_item(foo=u'bar')
        self._add_item(foo=u'baz')
        self._add_item(foo=u'xyz')

        value = urllib.quote(json.dumps([u'o', u'a']), safe='')
        result = self._search(u'/search/any/contains/foo/%s/show_all' % value,
                              show=u'foo')
        self.assertEqual(result, [u'foo', u'bar', u'baz'])

    def test_startswith_scalar(self):
        self._add_item(foo=u'foo')
        self._add_item(foo=u'bar')
        self._add_item(foo=u'baz')
        self._add_item(foo=u'xyz')

        value = urllib.quote(json.dumps([u'fo', u'ba']), safe='')
        result = self._search(u'/search/any/startswith/foo/%s/show_all' % value,
                              show=u'foo')
        self.assertEqual(result, [u'foo', u'bar', u'baz'])

    def test_exact_list(self):
        self._add_item(lst=list(u'abc'))
        self._add_item(lst=list(u'def'))
        self._add_item(lst=list(u'ghj'))

        value = urllib.quote(json.dumps([u'b', u'd']), safe='')
        result = self._search(u'/search/any/exact/lst/%s/show_all' % value,
                              show=u'lst')
        self.assertEqual(result, [
            list(u'abc'),
            list(u'def'),
        ])

    def test_exact_list_multiple(self):
        self._add_item(lst=list(u'abc'))
        self._add_item(lst=list(u'def'))
        self._add_item(lst=list(u'ghj'))

        value = urllib.quote(json.dumps([u'g', u'j']), safe='')
        result = self._search(u'/search/any/exact/lst/%s/show_all' % value,
                              show=u'lst')
        self.assertEqual(result, [
            list(u'ghj'),
        ])

    def test_non_json_value(self):
        with self.assertRaises(BadAnySearchValue) as e:
            self._search(u'/search/any/exact/foo/bar/show_all')
        self.assertEqual(str(e.exception), (
            u"Can't parse ANY search value: No JSON object could be decoded."
        ))

    def test_non_list_value(self):
        with self.assertRaises(BadAnySearchValue) as e:
            self._search(u'/search/any/exact/foo/0/show_all')
        self.assertEqual(str(e.exception), (
            u"Can't parse ANY search value: 0 is not a list."
        ))


class FakeListenerResource(object):

    def notify_create(self, item_id, item_revision):
        pass

    def notify_update(self, item_id, item_revision):
        pass

    def notify_delete(self, item_id):
        pass
