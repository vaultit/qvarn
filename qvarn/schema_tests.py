# schema_tests.py - unit test schemas
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

import six

import qvarn


class SchemaFromPrototypeTests(unittest.TestCase):

    def test_raises_error_for_empty_prototype(self):
        with self.assertRaises(Exception):
            qvarn.schema_from_prototype({})

    def test_gives_correct_schema_from_prototype_with_simple_fields(self):
        prototype = {
            u'type': u'',
            u'name': u'',
            u'age': 0,
        }
        schema = qvarn.schema_from_prototype(
            prototype, resource_type=u'foo')
        self.assertEqual(
            sorted(schema),
            sorted([
                (u'foo', u'type', six.text_type),
                (u'foo', u'id', six.text_type),
                (u'foo', u'name', six.text_type),
                (u'foo', u'age', int),
            ]))

    def test_gives_correct_schema_from_prototype_with_string_list(self):
        prototype = {
            u'type': u'',
            u'id': u'',
            u'strings': [u''],
        }
        schema = qvarn.schema_from_prototype(
            prototype, resource_type=u'foo')
        self.assertEqual(
            sorted(schema),
            sorted([
                (u'foo', u'type', six.text_type),
                (u'foo', u'id', six.text_type),
                (u'foo_strings', u'id', six.text_type),
                (u'foo_strings', u'list_pos', int),
                (u'foo_strings', u'strings', six.text_type),
            ]))

    def test_gives_correct_schema_from_prototype_with_dict_list(self):
        prototype = {
            u'type': u'',
            u'id': u'',
            u'vehicle': [
                {
                    u'vehicle_type': u'',
                    u'owners': [u''],
                },
            ],
        }
        schema = qvarn.schema_from_prototype(
            prototype, resource_type=u'foo')
        self.assertEqual(
            sorted(schema),
            sorted([
                (u'foo', u'type', six.text_type),
                (u'foo', u'id', six.text_type),
                (u'foo_vehicle', u'id', six.text_type),
                (u'foo_vehicle', u'list_pos', int),
                (u'foo_vehicle', u'vehicle_type', six.text_type),
                (u'foo_vehicle_owners', u'id', six.text_type),
                (u'foo_vehicle_owners', u'dict_list_pos', int),
                (u'foo_vehicle_owners', u'list_pos', int),
                (u'foo_vehicle_owners', u'owners', six.text_type),
            ]))

    def test_gives_correct_schema_from_prototype_with_inner_dict_list(self):
        prototype = {
            u'type': u'',
            u'id': u'',
            u'vehicle': [
                {
                    u'vehicle_type': u'',
                    u'owners': [
                        {
                            u'owner_names': [u''],
                            u'owned_from_year': 0,
                        },
                    ],
                },
            ],
        }
        schema = qvarn.schema_from_prototype(
            prototype, resource_type=u'foo')
        self.maxDiff = None
        self.assertEqual(
            sorted(schema),
            sorted([
                (u'foo', u'type', six.text_type),
                (u'foo', u'id', six.text_type),

                (u'foo_vehicle', u'id', six.text_type),
                (u'foo_vehicle', u'list_pos', int),
                (u'foo_vehicle', u'vehicle_type', six.text_type),

                (u'foo_vehicle_owners', u'id', six.text_type),
                (u'foo_vehicle_owners', u'dict_list_pos', int),
                (u'foo_vehicle_owners', u'list_pos', int),
                (u'foo_vehicle_owners', u'owned_from_year', int),

                (u'foo_vehicle_owners_owner_names', u'id', six.text_type),
                (u'foo_vehicle_owners_owner_names', u'dict_list_pos', int),
                (u'foo_vehicle_owners_owner_names', u'list_pos', int),
                (u'foo_vehicle_owners_owner_names', u'str_list_pos', int),
                (u'foo_vehicle_owners_owner_names', u'owner_names',
                 six.text_type),
            ]))

    def test_gives_correct_schema_from_prototype_for_subresource(self):
        prototype = {
            u'foo': u'',
        }
        schema = qvarn.schema_from_prototype(
            prototype, resource_type='big', subpath=u'secret')
        table_name = qvarn.table_name(
            resource_type=u'big', subpath=u'secret')
        self.assertEqual(
            sorted(schema),
            sorted([
                (table_name, u'id', six.text_type),
                (table_name, u'foo', six.text_type),
            ]))
