# schema_tests.py - unit test schemas
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

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
                (u'foo', u'type', unicode),
                (u'foo', u'id', unicode),
                (u'foo', u'name', unicode),
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
                (u'foo', u'type', unicode),
                (u'foo', u'id', unicode),
                (u'foo_strings', u'id', unicode),
                (u'foo_strings', u'list_pos', int),
                (u'foo_strings', u'strings', unicode),
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
                (u'foo', u'type', unicode),
                (u'foo', u'id', unicode),
                (u'foo_vehicle', u'id', unicode),
                (u'foo_vehicle', u'list_pos', int),
                (u'foo_vehicle', u'vehicle_type', unicode),
                (u'foo_vehicle_owners', u'id', unicode),
                (u'foo_vehicle_owners', u'dict_list_pos', int),
                (u'foo_vehicle_owners', u'list_pos', int),
                (u'foo_vehicle_owners', u'owners', unicode),
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
                (table_name, u'id', unicode),
                (table_name, u'foo', unicode),
            ]))
