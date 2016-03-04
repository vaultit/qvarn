# read_only.py - read-only interface to databases
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


import logging
import time
import uuid

import qvarn


class ReadOnlyStorage(object):

    '''Read-only interface to a database.

    You MUST call ``set_item_prototype`` before doing anything else.

    '''

    def __init__(self):
        self._item_type = None
        self._prototype = None
        self._subitem_prototypes = qvarn.SubItemPrototypes()
        self._m = None

    def set_item_prototype(self, item_type, prototype):
        '''Set type and prototype of items in this database.'''
        self._item_type = item_type
        self._prototype = prototype

    def set_subitem_prototype(self, item_type, subitem_name, prototype):
        '''Set prototype for a subitem.'''
        self._subitem_prototypes.add(item_type, subitem_name, prototype)

    def get_item_ids(self, transaction):
        '''Get list of ids of all items.'''
        return [
            row['id']
            for row in transaction.select(self._item_type, [u'id'], None)]

    def get_item(self, transaction, item_id):
        '''Get a specific item.'''
        item = {}
        rw = ReadWalker(transaction, self._item_type, item_id)
        rw.walk_item(item, self._prototype)
        return item

    def get_subitem(self, transaction, item_id, subitem_name):
        '''Get a specific subitem.'''
        subitem = {}
        table_name = qvarn.table_name(
            resource_type=self._item_type, subpath=subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        rw = ReadWalker(transaction, table_name, item_id)
        rw.walk_item(subitem, prototype)
        return subitem

    def search(self, transaction, search_params,
               show_params):  # pragma: no cover
        '''Do a search.

        ``search_params`` is a list of (matching rule, key, value)
        tuples. The returned rows are those that match all the
        conditions in the list.
        ``show_params`` is a list containing key fields included
        in the result object. If it contains a single ``show_all``
        string, all fields are returned.

        '''

        self._m = Measurement()
        with self._m.new('build_schema'):
            schema = self._build_schema()
        ids = self._kludge(transaction, schema, search_params)
        with self._m.new('build_search_result'):
            result = self._build_search_result(transaction, ids, show_params)
        self._m.finish()
        self._m.log()
        self._m = None
        return result

    def _build_schema(self):  # pragma: no cover
        schema = qvarn.schema_from_prototype(
            self._prototype, resource_type=self._item_type)
        for subpath, subproto in self._subitem_prototypes.get_all():
            schema += qvarn.schema_from_prototype(
                subproto, resource_type=self._item_type, subpath=subpath)
        return schema

    def _kludge(self, transaction, schema, search_params):  # pragma: no cover
        sql = getattr(transaction, '_sql')

        with self._m.new('build queries based on conditions'):
            values = {}
            queries = [
                self._kludge_query(sql, schema, param, values)
                for param in search_params]
        query = u' INTERSECT '.join(queries)
        return self._kludge_execute(sql, query, values)

    def _kludge_execute(self, sql, query, values):  # pragma: no cover
        with self._m.new('get conn'):
            conn = sql.get_conn()
        try:
            with self._m.new('get cursor'):
                c = conn.cursor()
            with self._m.new('execute'):
                c.execute(query, values)
            with self._m.new('fetch rows'):
                ids = [row[0] for row in c]
                self._m.note('row count: %d' % len(ids))
        except BaseException:
            with self._m.new('put conn (except)'):
                sql.put_conn(conn)
            raise
        else:
            with self._m.new('put conn'):
                sql.put_conn(conn)
            return ids

    def _kludge_query(self, sql, schema, param, values):  # pragma: no cover
        rule_queries = {
            u'exact': u'{} = {}',
            u'gt': u'{} > {}',
            u'ge': u'{} >= {}',
            u'lt': u'{} < {}',
            u'le': u'{} <= {}',
            u'ne': u'{} != {}'
        }
        rule, key, value = param
        assert rule in rule_queries.keys()

        queries = []
        for table_name, column_name, column_type in schema:
            rand_name = unicode(uuid.uuid4())
            if column_name == key:
                query = u'SELECT DISTINCT {0}.id FROM {0} WHERE '.format(
                    sql.quote(table_name))
                qualified_name = sql.qualified_column(table_name, column_name)
                if column_type == unicode:
                    qualified_name = u'LOWER(' + qualified_name + u')'
                query += rule_queries[rule].format(
                    qualified_name,
                    sql.format_qualified_placeholder(
                        table_name, rand_name))
                name = sql.format_qualified_placeholder_name(
                    table_name, rand_name)
                values[name] = self._cast_value(value)
                queries.append(query)
        if not queries:
            # key did not match column name in any table
            raise FieldNotInResource(field=key)
        return u'(' + u' UNION '.join(queries) + u')'

    def _cast_value(self, value):  # pragma: no cover
        magic = {
            u'true': True,
            u'false': False,
        }
        lower = unicode(value).lower()
        return magic.get(lower, lower)

    def _build_search_result(self, transaction, ids,
                             show_params):  # pragma: no cover
        if show_params == [u'show_all']:
            return self._build_search_result_show_all(transaction, ids)
        else:
            return self._build_search_result_ids_only(ids)

    def _build_search_result_show_all(self, transaction,
                                      ids):  # pragma: no cover
        return {
            u'resources': [
                self.get_item(transaction, resource_id) for resource_id in ids
            ],
        }

    def _build_search_result_ids_only(self, ids):  # pragma: no cover
        return {
            u'resources': [
                {u'id': resource_id} for resource_id in ids
            ],
        }


class FieldNotInResource(qvarn.BadRequest):

    msg = u'Resource does not contain given field'


class ItemDoesNotExist(qvarn.NotFound):

    msg = u'Item does not exist'


class ReadWalker(qvarn.ItemWalker):

    '''Visit every part of an item to retrieve it from the database.'''

    def __init__(self, transaction, item_type, item_id):
        self._transaction = transaction
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        row = self._get_row(self._item_type, self._item_id, column_names)
        for name in column_names:
            item[name] = row[name]

    def _get_row(self, table_name, item_id, column_names):
        # If a dict has no non-list fields, column_names is empty.
        # This breaks the self._transaction.select call below. There's
        # no sensible way to fix the select method, so we look for the
        # id column instead.
        lookup_names = column_names or [u'id']

        match = ('=', table_name, u'id', item_id)
        rows = self._transaction.select(table_name, lookup_names, match)
        for row in rows:
            # If we don't have any columns, return an empty dict.
            return row if column_names else {}
        raise ItemDoesNotExist(item_id=item_id)

    def visit_main_str_list(self, item, field):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        item[field] = self._get_str_list(table_name, field, self._item_id)

    def _get_str_list(self, table_name, column_name, item_id):
        rows = self._get_list(table_name, item_id, [column_name])
        return [row[column_name] for row in rows]

    def _get_list(self, table_name, item_id, column_names):
        match = ('=', table_name, u'id', item_id)
        rows = self._transaction.select(
            table_name, [u'list_pos'] + column_names, match)
        in_order = self._sort_rows(rows)
        return self._make_dicts_from_rows(in_order, column_names)

    def _sort_rows(self, rows):
        def get_list_pos(row):
            return row['list_pos']
        return [row for row in sorted(rows, key=get_list_pos)]

    def _make_dicts_from_rows(self, rows, column_names):
        result = []
        for row in rows:
            a_dict = dict((name, row[name]) for name in column_names)
            result.append(a_dict)
        return result

    def visit_main_dict_list(self, item, field, column_names):
        table_name = qvarn.table_name(
            resource_type=self._item_type, list_field=field)
        item[field] = self._get_list(table_name, self._item_id, column_names)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=str_list_field)

        match = (
            'AND',
            ('=', table_name, u'id', self._item_id),
            ('=', table_name, u'dict_list_pos', unicode(pos))
        )
        rows = self._transaction.select(
            table_name, [u'list_pos', str_list_field], match)

        in_order = self._sort_rows(rows)
        result = [row[str_list_field] for row in in_order]
        item[field][pos][str_list_field] = result


class Measurement(object):  # pragma: no cover

    def __init__(self):
        self._started = time.time()
        self._ended = None
        self._steps = []

    def finish(self):
        self._ended = time.time()

    def new(self, what):
        self._steps.append(Step(what))
        return self._steps[-1]

    def note(self, what, *args):  # pragma: no cover
        self._steps[-1].note(what, *args)

    def log(self):  # pragma: no cover
        duration = self._ended - self._started
        logging.info('Transaction duration: %.3f ms', duration * 1000.0)

        logging.info('Transaction steps:')
        for step in self._steps:
            logging.info('  %.3f ms %s', step.duration * 1000.0, step.what)
            for note in step.notes:
                logging.info('    %s', note)
        logging.info('Transaction steps end')


class Step(object):  # pragma: no cover

    def __init__(self, what):
        self.what = what
        self._started = None
        self._ended = None
        self.duration = None
        self.notes = []

    def note(self, msg, *args):
        formatted = msg % args
        self.notes.append(formatted)

    def __enter__(self):
        self._started = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ended = time.time()
        self.duration = self._ended - self._started
