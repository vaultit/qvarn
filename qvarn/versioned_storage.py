# versioned_storage.py - versioned storage for resources
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


import collections

import six
import sqlalchemy as sa

import qvarn


class VersionedStorage(object):

    '''Prepare storage for different resource type versions.

    Note that this is versions for resource types, not actual
    resources.

    '''

    def __init__(self):
        self._resource_type = None
        self._versions = []

    def get_resource_type(self):
        return self._resource_type

    def set_resource_type(self, resource_type):
        self._resource_type = resource_type

    @property
    def _versions_table_name(self):
        return qvarn.table_name(
            resource_type=self._resource_type, auxtable=u'versions')

    def get_versions(self):
        return [v.version for v in self._versions]

    def start_version(self, version_name):
        v = Version(version_name, None)
        self._versions.append(v)

    def add_prototype(self, prototype, **kwargs):
        v = self._versions[-1]
        v.add_prototype(prototype, kwargs)

    def prepare_storage(self, transaction, tables=None):
        self._prepare_versions_table(transaction)
        versions = self._get_known_versions(transaction)
        qvarn.log.log('previously-prepared-versions',
                      resource_type=self._resource_type, versions=versions)

        tables = tables or get_current_tables(transaction)
        for v in self._versions:
            if v.version not in versions:
                self._prepare_version(transaction, v, tables)
                self._remember_version(transaction, v)

    def _prepare_versions_table(self, transaction):
        transaction.create_table(
            self._versions_table_name, {u'version': six.text_type})

    def _get_known_versions(self, transaction):
        rows = transaction.select(
            self._versions_table_name, [u'version'], None)
        return [row['version'] for row in rows]

    def _remember_version(self, transaction, version):
        transaction.insert(
            self._versions_table_name, {u'version': version.version})

    def _prepare_version(self, transaction, version, tables):
        # Collect what is missing.
        create_tables = collections.defaultdict(dict)
        create_columns = collections.defaultdict(dict)
        change_columns = collections.defaultdict(dict)
        for prototype, kwargs in version.prototype_list:
            schema = qvarn.schema_from_prototype(
                prototype, resource_type=self._resource_type, **kwargs)
            for table_name, column_name, column_type in schema:

                # Create table
                if table_name not in tables:
                    create_tables[table_name][column_name] = column_type

                # Add column
                elif column_name not in tables[table_name]:
                    create_columns[table_name][column_name] = column_type

                # Alter column
                elif column_type != tables[table_name][column_name]:
                    change_columns[table_name][column_name] = (
                        tables[table_name][column_name],
                        column_type,
                    )

        # Create missing tables.
        for table_name in create_tables:
            transaction.create_table(table_name, create_tables[table_name])
            tables[table_name] = dict(create_tables[table_name])

        # Create missing columns.
        for table_name, columns in create_columns.items():
            for column_name, column_type in columns.items():
                transaction.add_column(table_name, column_name, column_type)
                tables[table_name][column_name] = column_type

        # Change column types.
        for table_name, columns in change_columns.items():
            for column_name, (old, new) in columns.items():
                transaction.alter_column(table_name, column_name, old, new)
                tables[table_name][column_name] = new


class Version(object):

    def __init__(self, version, update_data_func):
        self.version = version
        self.func = update_data_func
        self.prototype_list = []

    def add_prototype(self, prototype, kwargs):
        self.prototype_list.append((prototype, kwargs))


def get_current_tables(transaction):

    def get_type(c):
        t = c.type.python_type
        if six.PY2:
            if isinstance(c.type, sa.String):
                return six.text_type
        return memoryview if t is bytes else t

    engine = transaction.get_engine()
    metadata = sa.MetaData()
    metadata.reflect(engine)
    return {
        table.name: {c.name: get_type(c) for c in table.columns}
        for table in metadata.sorted_tables
    }
