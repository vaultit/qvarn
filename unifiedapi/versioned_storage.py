# versioned_storage.py - versioned storage for resources
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import logging
import random

import unifiedapi


class VersionedStorage(object):

    def __init__(self):
        self._resource_type = None
        self._versions = []

    def get_resource_type(self):
        return self._resource_type

    def set_resource_type(self, resource_type):
        self._resource_type = resource_type

    @property
    def _versions_table_name(self):
        return unifiedapi.table_name(
            resource_type=self._resource_type, auxtable=u'versions')

    def get_versions(self):
        return [v.version for v in self._versions]

    def start_version(self, version_name, update_data_func):
        v = Version(version_name, update_data_func)
        self._versions.append(v)

    def add_prototype(self, prototype, **kwargs):
        v = self._versions[-1]
        v.add_prototype(prototype, kwargs)

    def prepare_storage(self, transaction):
        logging.info('Preparing storage')

        self._prepare_versions_table(transaction)
        versions = self._get_known_versions(transaction)
        logging.info('Prepared versions: %r', versions)

        if self._versions:
            first = self._versions[0]
            if first.version not in versions:
                self._prepare_first_version(transaction, first)
                self._remember_version(transaction, first)

            prev_version = first
            for v in self._versions[1:]:
                if v.version not in versions:
                    self._prepare_next_version(transaction, prev_version, v)
                    self._remember_version(transaction, v)
                prev_version = v

    def _prepare_versions_table(self, transaction):
        transaction.create_table(
            self._versions_table_name, {u'version': unicode})

    def _get_known_versions(self, transaction):
        rows = transaction.select(
            self._versions_table_name, [u'version'], None)
        return [row['version'] for row in rows]

    def _remember_version(self, transaction, version):
        transaction.insert(
            self._versions_table_name, {u'version': version.version})

    def _prepare_first_version(self, transaction, version):
        logging.info('First version: %r', version.version)
        logging.info('Creating tables: %r', version.prototype_list)
        unifiedapi.create_tables_for_resource_type(
            transaction, self._resource_type, version.prototype_list)
        if version.func:
            version.func(transaction, {})

    def _prepare_next_version(self, transaction, old_version, new_version):
        # This method is tricky. Pay attention.

        logging.info(
            'Upgrading from %r to %r',
            old_version.version, new_version.version)

        # Create lookup tables (table name to column name list) for
        # each version.
        old_tables = self._make_table_dict_from_version(old_version)
        new_tables = self._make_table_dict_from_version(new_version)

        # Rename all changed tables and create new ones in their place.
        changed_tables = self._find_changed_tables(old_tables, new_tables)
        for table in changed_tables:
            logging.info('Changed table: %r', table)
        temp_tables = self._rename_tables(transaction, changed_tables)
        self._create_tables(
            transaction, new_version.prototype_list, changed_tables)

        # Create all added tables.
        added_tables = self._find_added_tables(old_tables, new_tables)
        for table in added_tables:  # pragma: no cover
            logging.info('Added table: %r', table)
        self._create_tables(
            transaction, new_version.prototype_list, added_tables)

        # Copy columns that haven't changed, for any changed
        # tables.
        for table in changed_tables:
            old_columns = set(old_tables[table])
            new_columns = set(new_tables[table])
            shared_columns = old_columns.intersection(new_columns)
            if shared_columns:
                self._copy_shared_columns(
                    transaction, temp_tables[table], table, shared_columns)

        # This is where the app gets to munge data so nothing
        # important is lost during the schema transition, or to
        # fill in new columns with useful values, etc.
        logging.info('Calling conversion function %r', new_version.func)
        if new_version.func:
            new_version.func(transaction, temp_tables)

        # Drop all old, renamed tables.
        for table in temp_tables.values():
            logging.info('Dropping table %r', table)
            transaction.drop_table(table)

        # Drop all old tables that are no longer needed.
        for table in old_tables:  # pragma: no cover
            if table not in new_tables:
                logging.info('Dropping table %r', table)
                transaction.drop_table(table)

    def _make_table_dict_from_version(self, version):
        tables = {}
        for prototype, kwargs in version.prototype_list:
            schema = unifiedapi.schema_from_prototype(
                prototype, resource_type=self._resource_type, **kwargs)
            for table_name, column_name, _ in schema:
                if table_name not in tables:
                    tables[table_name] = []
                tables[table_name].append(column_name)
        return tables

    def _find_changed_tables(self, old_tables, new_tables):
        old_names = set(old_tables.keys())
        new_names = set(new_tables.keys())
        shared_names = old_names.intersection(new_names)
        return set(
            name
            for name in shared_names
            if old_tables[name] != new_tables[name])

    def _find_added_tables(self, old_tables, new_tables):
        old_names = set(old_tables.keys())
        new_names = set(new_tables.keys())
        return new_names.difference(old_names)

    def _create_tables(self, transaction, prototype_list, table_names):
        delta_prototype_list = []
        for prototype, kwargs in prototype_list:
            schema = unifiedapi.schema_from_prototype(
                prototype, resource_type=self._resource_type, **kwargs)
            if any(x[0] in table_names for x in schema):
                delta_prototype_list.append((prototype, kwargs))

        logging.info('Creating tables: %r', delta_prototype_list)
        unifiedapi.create_tables_for_resource_type(
            transaction, self._resource_type, delta_prototype_list)

    def _rename_tables(self, transaction, tables):
        temp_tables = {}
        for old_name in tables:
            # This assumes the likelihood of a 64-bit integer clashing
            # is low enough.
            temp_name = '%s_%s' % (old_name, random.randint(1, 2**64-1))
            logging.info('Renaming %r to %r', old_name, temp_name)
            transaction.rename_table(old_name, temp_name)
            temp_tables[old_name] = temp_name
        return temp_tables

    def _copy_shared_columns(self,
                             transaction, old_table, new_table, column_names):
        for row in transaction.select(old_table, list(column_names), None):
            values = dict(
                (x, row[x])
                for x in column_names if row[x] is not None)
            if values:
                transaction.insert(new_table, values)


class Version(object):

    def __init__(self, version, update_data_func):
        self.version = version
        self.func = update_data_func
        self.prototype_list = []

    def add_prototype(self, prototype, kwargs):
        self.prototype_list.append((prototype, kwargs))
