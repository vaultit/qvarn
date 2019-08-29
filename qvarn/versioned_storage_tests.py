# versioned_storage_tests.py - unit test versioned storage
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


import itertools
import unittest

import six
import pytest
import sqlalchemy as sa

import qvarn


class VersionedStorageTests(unittest.TestCase):

    def setUp(self):
        sql = qvarn.SqliteAdapter()
        self.dbconn = qvarn.DatabaseConnection()
        self.dbconn.set_sql(sql)

    def test_has_no_resource_type_initally(self):
        vs = qvarn.VersionedStorage()
        self.assertEqual(vs.get_resource_type(), None)

    def test_sets_resource_type(self):
        vs = qvarn.VersionedStorage()
        vs.set_resource_type(u'foo')
        self.assertEqual(vs.get_resource_type(), u'foo')

    def test_has_no_versions_initially(self):
        vs = qvarn.VersionedStorage()
        self.assertEqual(vs.get_versions(), [])

    def test_starts_a_new_version(self):
        vs = qvarn.VersionedStorage()
        vs.start_version('v1')
        self.assertEqual(vs.get_versions(), ['v1'])

    def test_prepares_a_single_version(self):
        prototype_v1 = {
            u'type': u'',
            u'id': u'',
            u'foo': u'',
        }

        vs = qvarn.VersionedStorage()
        vs.set_resource_type(u'foo')

        vs.start_version(u'v1')
        vs.add_prototype(prototype_v1)

        with self.dbconn.transaction() as t:
            vs.prepare_storage(t)
            self.assertSchema(t, {
                'foo': ['foo', 'id', 'type'],
                'foo__aux_versions': ['version'],
            })

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

        vs = qvarn.VersionedStorage()
        vs.set_resource_type('resource')

        vs.start_version(u'v1')
        vs.add_prototype(prototype_v1)

        with self.dbconn.transaction() as t:
            vs.prepare_storage(t)
            self.assertVersions(t, 'resource', ['v1'])

        with self.dbconn.transaction() as t:
            t.insert('resource', {'id': 'foo.id'})

        vs.start_version(u'v2')
        vs.add_prototype(prototype_v2)

        vs.start_version(u'v3')
        vs.add_prototype(prototype_v3)

        with self.dbconn.transaction() as t:
            vs.prepare_storage(t)

        with self.dbconn.transaction() as t:
            self.assertVersions(t, 'resource', ['v1', 'v2', 'v3'])
            self.assertSchema(t, {
                'resource': ['bar', 'foo', 'foobar', 'id', 'type'],
                'resource__aux_versions': ['version'],
            })
            self.assertData(t, 'resource', ('id', 'bar', 'foobar'), [
                ('foo.id', None, None),
            ])

    def test_schema_migration(self):
        vs = qvarn.VersionedStorage()
        vs.set_resource_type(u'rt')

        # Do initial migration
        vs.start_version(u'v1')
        vs.add_prototype({
            u'type': u'',
            u'id': u'',
            u'items': [{
                u'str': u'',
                u'lst': [u''],
            }]
        })
        with self.dbconn.transaction() as t:
            vs.prepare_storage(t)
            self.assertSchema(t, {
                'rt': ['id', 'type'],
                'rt__aux_versions': ['version'],
                'rt_items': ['id', 'list_pos', 'str'],
                'rt_items_lst': ['dict_list_pos', 'id', 'list_pos', 'lst'],
            })

        # Add new version and do another migration.
        vs.start_version(u'v2')
        vs.add_prototype({
            u'type': u'',
            u'id': u'',
            u'items': [{
                u'str': u'',
                u'lst': [u''],
                u'new_1': u'',
            }],
            u'new_2': u'',
            u'items_3': [u''],
        })
        with self.dbconn.transaction() as t:
            vs.prepare_storage(t)
            self.assertSchema(t, {
                'rt': ['id', 'new_2', 'type'],
                'rt__aux_versions': ['version'],
                'rt_items': ['id', 'list_pos', 'new_1', 'str'],
                'rt_items_3': ['id', 'items_3', 'list_pos'],
                'rt_items_lst': ['dict_list_pos', 'id', 'list_pos', 'lst'],
            })

    def assertSchema(self, transaction, expected):
        engine = transaction.get_engine()
        metadata = sa.MetaData()
        metadata.reflect(engine)
        tables = {
            table.name: sorted(c.name for c in table.columns)
            for table in metadata.sorted_tables
        }
        self.assertEqual(tables, expected)

    def assertData(self, transaction, table_name, columns, expected):
        rows = transaction.select(table_name, columns, None)
        data = [tuple(row[c] for c in columns) for row in rows]
        self.assertEqual(data, expected)

    def assertVersions(self, transaction, resource_type, expected):
        table_name = qvarn.table_name(resource_type=resource_type,
                                      auxtable=u'versions')
        rows = transaction.select(table_name, ['version'], None)
        versions = [row['version'] for row in rows]
        self.assertEqual(versions, expected)


def get_data(dbconn, table_name, columns):

    def value(v):
        if six.PY2:
            # pylint: disable=undefined-variable
            return bytes(v) if isinstance(v, buffer) else v  # noqa
        return bytes(v) if isinstance(v, memoryview) else v

    with dbconn.transaction() as t:
        if isinstance(columns, (list, tuple)):
            rows = t.select(table_name, columns, None)
            return [tuple(value(row[c]) for c in columns) for row in rows]
        else:
            rows = t.select(table_name, [columns], None)
            return [value(row[columns]) for row in rows]


@pytest.mark.parametrize(
    'old, new',
    itertools.permutations(qvarn.column_types, 2)
)
def test_field_type_change(dbconn, old, new):

    def typ(x):
        return x(b'') if x is memoryview else x()

    def val(x):
        return b'1' if x is memoryview else x(1)

    dbconn.drop_tables(['rt', 'rt__aux_versions'])

    vs = qvarn.VersionedStorage()
    vs.set_resource_type(u'rt')

    # Do initial migration
    vs.start_version(u'v1')
    vs.add_prototype({
        u'type': u'',
        u'id': u'',
        u'field': typ(old),
    })
    with dbconn.transaction() as t:
        vs.prepare_storage(t)

    with dbconn.transaction() as t:
        t.insert('rt', {'id': '1', 'field': val(old)})

    assert get_data(dbconn, 'rt', 'field') == [val(old)]

    # Do migration with a field type changed
    vs.start_version(u'v2')
    vs.add_prototype({
        u'type': u'',
        u'id': u'',
        u'field': typ(new),
    })
    with dbconn.transaction() as t:
        vs.prepare_storage(t)

    assert get_data(dbconn, 'rt', 'field') == [val(new)]
