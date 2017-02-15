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


import time
import uuid
import collections

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

    def get_item(self, transaction, item_id, main_fields=None):
        '''Get a specific item.'''
        item = {}
        rw = ReadWalker(
            transaction, self._item_type, item_id, main_fields=main_fields)
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
               show_params, sort_params=None):  # pragma: no cover
        '''Do a search.

        ``search_params`` is a list of (matching rule, key, value)
        tuples. The returned rows are those that match all the
        conditions in the list.
        ``show_params`` is a list containing key fields included
        in the result object. If it contains a single ``show_all``
        string, all fields are returned.
        ``sort_params`` is a list of strings, where each string is
        a field to sort by.

        '''

        self._m = Measurement()
        with self._m.new('build_schema'):
            schema = self._build_schema()
        ids = self._kludge(transaction, schema, search_params, sort_params)
        with self._m.new('build_search_result'):
            result = self._build_search_result(transaction, ids, show_params)
        self._m.finish()
        self._m.log(None)
        self._m = None
        return result

    def _build_schema(self):  # pragma: no cover
        schema = qvarn.schema_from_prototype(
            self._prototype, resource_type=self._item_type)
        for subpath, subproto in self._subitem_prototypes.get_all():
            schema += qvarn.schema_from_prototype(
                subproto, resource_type=self._item_type, subpath=subpath)
        return schema

    def _kludge(self, transaction, schema, search_params,
                sort_params=None):  # pragma: no cover
        sql = getattr(transaction, '_sql')
        main_table = qvarn.table_name(resource_type=self._item_type)

        with self._m.new('build param conditions'):
            values = {}
            tables_used = [main_table]
            conds = [
                self._kludge_conds(
                    sql, schema, param, values, main_table, tables_used)
                for param in search_params]

        with self._m.new('build order by fields'):
            tables_used = [main_table]
            join_conditions = {}
            sort_params = sort_params or []
            order_by_fields = [
                self._kludge_order_by_fields(
                    sql, schema, key, main_table, tables_used, join_conditions)
                for key in sort_params]

        with self._m.new('build full sql query'):
            query = u'SELECT DISTINCT {1}.id FROM {0} AS {1}'.format(
                sql.quote(main_table), u't0')
            for idx, table_name in enumerate(tables_used):
                if table_name != main_table:
                    table_alias = u't' + str(idx)
                    query += (u' LEFT JOIN {1} AS {2} ON {0}.id = {2}.id'
                              .format(u't0', sql.quote(table_name),
                                      sql.quote(table_alias)))
                    if idx in join_conditions:
                        query += ' AND ' + join_conditions[idx]
            if conds:
                query += u' WHERE ' + u' AND '.join(
                    u'({})'.format(c) for c in conds)
            if order_by_fields:
                query += u' ORDER BY ' + u', '.join(order_by_fields)
            self._m.note(query=query, values=values)

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
                self._m.note(row_count=len(ids))
        except BaseException:
            with self._m.new('put conn (except)'):
                sql.put_conn(conn)
            raise
        else:
            with self._m.new('put conn'):
                sql.put_conn(conn)
            return ids

    def _kludge_conds(self, sql, schema, param, values,
                      main_table, tables_used):  # pragma: no cover
        rule_queries = {
            u'exact': u'{} = {}',
            u'gt': u'{} > {}',
            u'ge': u'{} >= {}',
            u'lt': u'{} < {}',
            u'le': u'{} <= {}',
            u'ne': u'{} != {}',
            u'startswith': u'{} LIKE {} || \'%%\'',
            u'contains': u'{} LIKE \'%%\' || {} || \'%%\''
        }
        rule, key, value = param
        assert rule in rule_queries.keys()

        conds = []
        for table_name, column_name, column_type in schema:
            rand_name = unicode(uuid.uuid4())
            if column_name == key:
                if table_name == main_table:
                    table_alias = u't0'
                else:
                    table_alias = u't' + str(len(tables_used))
                    tables_used.append(table_name)
                qualified_name = sql.qualified_column(table_alias, column_name)
                if column_type == unicode:
                    qualified_name = u'LOWER(' + qualified_name + u')'
                conds.append(rule_queries[rule].format(
                    qualified_name,
                    sql.format_qualified_placeholder(
                        table_name, rand_name)))
                name = sql.format_qualified_placeholder_name(
                    table_name, rand_name)
                values[name] = self._cast_value(value)
        if not conds:
            # key did not match column name in any table
            raise FieldNotInResource(field=key)
        return u' OR '.join(conds)

    def _kludge_order_by_fields(self, sql, schema, key, main_table,
                                tables_used, join_conditions):
        columns_by_table_name = collections.defaultdict(list)
        for table_name, column_name, column_type in schema:
            columns_by_table_name[table_name].append(column_name)

        for table_name, column_name, column_type in schema:
            if column_name == key:
                if table_name == main_table:
                    table_alias = u't0'
                else:
                    idx = len(tables_used)
                    table_alias = u't' + str(idx)
                    tables_used.append(table_name)
                    join_conds = self._kludge_first_item_join_cond(
                        sql, table_alias, columns_by_table_name[table_name])
                    join_conditions[idx] = join_conds
                return sql.qualified_column(table_alias, column_name)
        # key did not match column name in any table
        raise FieldNotInResource(field=key)

    def _kludge_first_item_join_cond(self, sql, table_alias, columns):
        # Build extra condition JOIN conditions in order to join just first
        # itemns in lists, whre query should consider only first item in list.
        list_pos_names = set([
            u'list_pos',
            u'str_list_pos',
            u'dict_list_pos',
        ])
        conds = []
        for column_name in columns:
            if column_name in list_pos_names:
                qualified_name = sql.qualified_column(table_alias, column_name)
                conds.append('{} = 0'.format(qualified_name))
        return ' AND '.join(conds)

    def _cast_value(self, value):  # pragma: no cover
        magic = {
            u'true': True,
            u'false': False,
        }
        lower = unicode(value).lower()
        return magic.get(lower, lower)

    def _build_search_result(self, transaction, ids,
                             show_params):  # pragma: no cover
        fields = []
        for param in show_params:
            if param == u'show_all':
                return self._build_search_result_show_all(transaction, ids)
            elif isinstance(param, tuple) and param[0] == u'show':
                fields.append(param[1])

        if fields:
            return self._build_search_result_with_fields(
                transaction, ids, fields)
        else:
            return self._build_search_result_ids_only(ids)

    def _build_search_result_show_all(self, transaction,
                                      ids):  # pragma: no cover
        return {
            u'resources': [
                self.get_item(transaction, resource_id) for resource_id in ids
            ],
        }

    def _build_search_result_with_fields(self, transaction, ids,
                                         fields):  # pragma: no cover
        if u'id' not in fields:
            fields = fields + [u'id']
        return {
            u'resources': [
                self.get_item(transaction, resource_id, main_fields=fields)
                for resource_id in ids
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

    def __init__(self, transaction, item_type, item_id, main_fields=None):
        self._transaction = transaction
        self._item_type = item_type
        self._item_id = item_id
        self._main_fields = main_fields

    def _get_main_str_lists(self, proto):
        return [
            x for x in self._get_str_lists(proto)
            if self._main_field_ok(x)
        ]

    def _get_main_dict_lists(self, proto):
        return [
            x for x in self._get_dict_lists(proto)
            if self._main_field_ok(x)
        ]

    def _main_field_ok(self, field):
        return not self._main_fields or field in self._main_fields

    def visit_main_dict(self, item, column_names):
        if self._main_fields:  # pragma: no cover
            column_names = [c for c in column_names if c in self._main_fields]
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
        if self._main_field_ok(field):
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
        if self._main_field_ok(field):
            table_name = qvarn.table_name(
                resource_type=self._item_type, list_field=field)
            item[field] = self._get_list(
                table_name, self._item_id, column_names)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        if not self._main_field_ok(field):  # pragma: no cover
            return

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

    def visit_inner_dict_list(self, item, outer_field, inner_field,
                              column_names):
        if not self._main_field_ok(outer_field):  # pragma: no cover
            return

        table_name = qvarn.table_name(
            resource_type=self._item_type,
            list_field=outer_field,
            subdict_list_field=inner_field)

        column_names = [u'list_pos', u'dict_list_pos'] + column_names

        match = ('=', table_name, u'id', self._item_id)
        rows = self._transaction.select(table_name, column_names, match)

        def get_pos(row):
            return row[u'dict_list_pos'], row[u'list_pos']

        in_order = list(sorted(rows, key=get_pos))

        for outer_dict in item[outer_field]:
            if inner_field not in outer_dict:
                outer_dict[inner_field] = []

        for row in self._make_dicts_from_rows(in_order, column_names):
            i = row.pop(u'dict_list_pos')
            j = row.pop(u'list_pos')
            inner_list = item[outer_field][i][inner_field]
            assert j == len(inner_list), '{} != {}'.format(j, len(inner_list))
            inner_list.append(row)


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

    def note(self, **kwargs):  # pragma: no cover
        self._steps[-1].note(**kwargs)

    def log(self, exc_info):  # pragma: no cover
        duration = self._ended - self._started
        qvarn.log.log(
            'kludge-sql-transaction',
            duration_ms=duration * 1000.0,
            success=(exc_info is None),
            exc_info=exc_info,
            steps=[
                {
                    'what': step.what,
                    'duration_ms': step.duration * 1000.0,
                    'notes': step.notes,
                }
                for step in self._steps
            ]
        )


class Step(object):  # pragma: no cover

    def __init__(self, what):
        self._started = None
        self._ended = None
        self.what = what
        self.duration = None
        self.notes = []

    def note(self, **kwargs):
        self.notes.append(kwargs)

    def __enter__(self):
        self._started = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ended = time.time()
        self.duration = self._ended - self._started
