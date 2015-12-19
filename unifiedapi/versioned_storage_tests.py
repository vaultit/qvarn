# versioned_storage_tests.py - unit test versioned storage
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class VersionedStorageTests(unittest.TestCase):

    def test_has_no_resource_type_initally(self):
        vs = unifiedapi.VersionedStorage()
        self.assertEqual(vs.get_resource_type(), None)

    def test_sets_resource_type(self):
        vs = unifiedapi.VersionedStorage()
        vs.set_resource_type(u'foo')
        self.assertEqual(vs.get_resource_type(), u'foo')

    def test_has_no_versions_initially(self):
        vs = unifiedapi.VersionedStorage()
        self.assertEqual(vs.get_versions(), [])

    def test_starts_a_new_version(self):
        vs = unifiedapi.VersionedStorage()
        vs.start_version('v1', None)
        self.assertEqual(vs.get_versions(), ['v1'])

    def test_prepares_a_single_version(self):
        prototype_v1 = {
            u'type': u'',
            u'id': u'',
            u'foo': u'',
        }

        called = []

        def callback_v1(*args):
            called.append(callback_v1)

        sql = unifiedapi.SqliteAdapter()
        dbconn = unifiedapi.DatabaseConnection()
        dbconn.set_sql(sql)

        vs = unifiedapi.VersionedStorage()
        vs.set_resource_type(u'foo')

        vs.start_version(u'v1', callback_v1)
        vs.add_prototype(prototype_v1)

        with dbconn.transaction() as t:
            vs.prepare_storage(t)
        self.assertEqual(called, [callback_v1])

    def test_updates_data_for_each_version(self):
        prototype_v1 = {
            u'type': u'',
            u'id': u'',
            u'foo': u'',
        }

        prototype_v2 = {
            u'type': u'',
            u'id': u'',
            u'bar': u'',  # note that foo is dropped
        }

        prototype_v3 = {
            u'type': u'',
            u'id': u'',
            u'bar': u'',
            u'foobar': u'',  # added field, thus bar should be copied
        }

        called = []
        resource_type = u'resource'
        table_name = unifiedapi.table_name(resource_type=resource_type)

        def callback_v1(t, temp_tables):
            # Insert a row with an id. It should remain at end.
            t.insert(table_name, {u'id': u'foo.id'})
            called.append(callback_v1)

        def callback_v2(t, temp_tables):
            called.append(callback_v2)

        def callback_v3(t, temp_tables):
            called.append(callback_v3)

        vs = unifiedapi.VersionedStorage()
        vs.set_resource_type(resource_type)

        vs.start_version(u'v1', callback_v1)
        vs.add_prototype(prototype_v1)

        vs.start_version(u'v2', callback_v2)
        vs.add_prototype(prototype_v2)

        vs.start_version(u'v3', callback_v3)
        vs.add_prototype(prototype_v3)

        sql = unifiedapi.SqliteAdapter()
        dbconn = unifiedapi.DatabaseConnection()
        dbconn.set_sql(sql)
        with dbconn.transaction() as t:
            vs.prepare_storage(t)
            self.assertEqual(called, [callback_v1, callback_v2, callback_v3])

            rows = t.select(table_name, [u'bar', u'foobar', u'id'], {})
            self.assertEqual(
                rows,
                [{u'id': u'foo.id', u'bar': None, u'foobar': None}])
