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


class BasicRouteTests(unittest.TestCase):

    def test_basic_route_to_scope(self):
        route_scope = qvarn.route_to_scope('/orgs', 'GET')
        self.assertEqual(route_scope, u'uapi_orgs_get')

    def test_basic_id_route_to_scope(self):
        route_scope = qvarn.route_to_scope('/orgs/<item_id>', 'PUT')
        self.assertEqual(route_scope, u'uapi_orgs_id_put')

    def test_basic_subitem_route_to_scope(self):
        route_scope = qvarn.route_to_scope(
            '/orgs/<item_id>/document', 'PUT')
        self.assertEqual(route_scope, u'uapi_orgs_id_document_put')

    def test_search_route_to_scope(self):
        route_scope = qvarn.route_to_scope(
            '/orgs/search/<search_criteria:path>', 'GET')
        self.assertEqual(route_scope, u'uapi_orgs_search_id_get')

    def test_listener_notification_route_to_scope(self):
        route_scope = qvarn.route_to_scope(
            '/orgs/listeners/<id>/notifications/<id>', 'DELETE')
        self.assertEqual(
            route_scope, u'uapi_orgs_listeners_id_notifications_id_delete')


class TableNameTests(unittest.TestCase):

    def test_returns_correct_name_for_just_resource_type(self):
        name = qvarn.table_name(resource_type=u'foo')
        self.assertEqual(name, u'foo')

    def test_returns_name_for_list_field(self):
        name = qvarn.table_name(resource_type=u'foo', list_field=u'bar')
        self.assertEqual(name, u'foo_bar')

    def test_returns_name_for_string_list_in_dicts_in_dict_list(self):
        name = qvarn.table_name(
            resource_type=u'foo', list_field=u'bar', subdict_list_field=u'yo')
        self.assertEqual(name, u'foo_bar_yo')

    def test_returns_name_for_subresource(self):
        name = qvarn.table_name(
            resource_type=u'foo', subpath=u'bar')
        self.assertEqual(name, u'foo__path_bar')

    def test_returns_name_for_subresource_list_field(self):
        name = qvarn.table_name(
            resource_type=u'foo', subpath=u'bar', list_field=u'yo')
        self.assertEqual(name, u'foo__path_bar_yo')

    def test_returns_name_for_subresource_list_in_subdict(self):
        name = qvarn.table_name(
            resource_type=u'foo', subpath=u'bar', list_field=u'yo',
            subdict_list_field=u'ugh')
        self.assertEqual(name, u'foo__path_bar_yo_ugh')

    def test_returns_name_for_auxiliary_table(self):
        name = qvarn.table_name(
            resource_type=u'foo', auxtable=u'listeners')
        self.assertEqual(name, u'foo__aux_listeners')

    def test_returns_name_for_auxiliary_table_list_field(self):
        name = qvarn.table_name(
            resource_type=u'foo', auxtable=u'listeners', list_field=u'bar')
        self.assertEqual(name, u'foo__aux_listeners_bar')

    def test_fails_without_resource_type(self):
        with self.assertRaises(qvarn.ComplicatedTableNameError):
            qvarn.table_name()

    def test_fails_if_subdict_list_field_without_list_field(self):
        with self.assertRaises(qvarn.ComplicatedTableNameError):
            qvarn.table_name(
                resource_type=u'foo', subdict_list_field=u'bar')

    def test_fails_if_both_auxtable_and_subpath(self):
        with self.assertRaises(qvarn.ComplicatedTableNameError):
            qvarn.table_name(
                resource_type=u'foo', auxtable=u'aux', subpath=u'path')

    def test_fails_if_both_auxtable_and_subdict_list_field(self):
        with self.assertRaises(qvarn.ComplicatedTableNameError):
            qvarn.table_name(
                resource_type=u'foo', auxtable=u'aux',
                list_field='yo', subdict_list_field=u'bar')
