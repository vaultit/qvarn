# listener_resource_tests.py - unit tests for listener resource
#
# Copyright 2017 Suomen Tilaajavastuu Oy
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


class ListenerResourceBase(unittest.TestCase):

    resource_type = u'yo'

    prototype = {
        u'type': u'',
        u'id': u'',
        u'revision': u'',
        u'value': u'',
    }

    _default_show = None

    def setUp(self):
        self._dbconn = qvarn.DatabaseConnection()
        self._dbconn.set_sql(qvarn.SqliteAdapter())

        vs = qvarn.VersionedStorage()
        vs.set_resource_type(self.resource_type)
        vs.start_version(u'first-version', None)
        vs.add_prototype(self.prototype)
        vs.add_prototype(qvarn.listener_prototype, auxtable=u'listener')
        vs.add_prototype(qvarn.notification_prototype,
                         auxtable=u'notification')
        with self._dbconn.transaction() as t:
            vs.prepare_storage(t)

        self.ro = qvarn.ReadOnlyStorage()
        self.ro.set_item_prototype(self.resource_type, self.prototype)

        self.wo = qvarn.WriteOnlyStorage()
        self.wo.set_item_prototype(self.resource_type, self.prototype)

        self.listener = qvarn.ListenerResource()
        self.listener.set_top_resource_path(self.resource_type,
                                            self.resource_type)
        self.listener.prepare_resource(self._dbconn)

        self.resource = qvarn.ListResource()
        self.resource.set_path(self.resource_type)
        self.resource.set_item_type(self.resource_type)
        self.resource.set_item_prototype(self.prototype)
        self.resource.set_listener(self.listener)
        self.resource.prepare_resource(self._dbconn)

    def tearDown(self):
        # Reset bottle request.
        bottle.request = bottle.LocalRequest()


class ListenerResourceTests(ListenerResourceBase):

    def test_notifications(self):
        # Create new listener.
        bottle.request.url = ''
        bottle.request.qvarn_json = {
            u'notify_of_new': True,
            u'listen_on_all': True,
        }
        listener = self.listener.post_listener()
        listener = self.listener.get_listener(listener[u'id'])

        # Create a resource.
        with self._dbconn.transaction() as t:
            added = self.wo.add_item(t, {
                u'type': u'yo',
                u'value': u'42',
            })
        self.listener.notify_create(added[u'id'], added[u'revision'])

        # Get notifications
        notifications = self.listener.get_notifications(listener[u'id'])
        self.assertEqual(len(notifications[u'resources']), 1)

        # Check if notification received refers to the added resource.
        notification = self.listener.get_notification(
            notifications[u'resources'][0][u'id'])
        self.assertEqual(notification[u'resource_id'], added[u'id'])
