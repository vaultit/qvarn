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


class ListResourceTests(unittest.TestCase):

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

    def test_lists_no_items_initially(self):
        with self._dbconn.transaction() as t:
            items = [
                {u'type': u'yo', u'foo': u'a', u'bar': 'z'},
                {u'type': u'yo', u'foo': u'c', u'bar': 'x'},
                {u'type': u'yo', u'foo': u'b', u'bar': 'y'},
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


# XXX: creating fake classes like this one could be avoided with mock [1].
#
#      [1]: https://pypi.python.org/pypi/mock/
class FakeListenerResource(object):

    def notify_create(self, item_id, item_revision):
        pass

    def notify_update(self, item_id, item_revision):
        pass

    def notify_delete(self, item_id):
        pass
