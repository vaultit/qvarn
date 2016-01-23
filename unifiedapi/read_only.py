# read_only.py - read-only interface to databases
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


class ReadOnlyStorage(object):

    '''Read-only interface to a database.

    You MUST call ``set_item_prototype`` before doing anything else.

    '''

    def __init__(self):
        self._item_type = None
        self._prototype = None
        self._subitem_prototypes = unifiedapi.SubItemPrototypes()

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
        table_name = unifiedapi.table_name(
            resource_type=self._item_type, subpath=subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        rw = ReadWalker(transaction, table_name, item_id)
        rw.walk_item(subitem, prototype)
        return subitem

    def search(self, transaction, search_params, show_params):
        '''Do a search.

        ``search_params`` is a list of (matching rule, key, value)
        tuples. The returned rows are those that match all the
        conditions in the list.
        ``show_params`` is a list containing key fields included
        in the result object. If it contains a single ``show_all``
        string, all fields are returned.

        '''

        tsw = TableSearchWalker(
            transaction, self._item_type, self._prototype, {})
        tsw.walk_item(self._prototype, self._prototype)

        subprotos = self._subitem_prototypes.get_all()
        for subitem in subprotos:
            subproto = subitem[1]
            tsw = TableSearchWalker(
                transaction,
                unifiedapi.table_name(
                    resource_type=self._item_type, subpath=subitem[0]),
                subproto,
                tsw.table_map)
            tsw.walk_item(subproto, subproto)

        result = self._do_search(transaction, search_params, tsw.table_map)
        if show_params:
            if u'show_all' in show_params:
                return {
                    u'resources': [
                        self.get_item(transaction, resource_id)
                        for resource_id in result
                    ],
                }
        else:
            return {
                u'resources': [
                    {u'id': resource_id} for resource_id in result
                ],
            }

    def _do_search(self, transaction, search_params, table_map):

        final_result = set()
        params_by_table = {}
        results_added = False

        for search_param in search_params:
            if search_param[0] == 'exact':
                field = unicode(search_param[1])
                table_names = table_map[field]
                for table_name in table_names:
                    if table_name in params_by_table:
                        match = params_by_table[table_name]
                    else:
                        match = {}
                        params_by_table[table_name] = match
                    match[field] = self._format_search_param(search_param[2])

        for table_name, match in params_by_table.iteritems():
            select_condition = self._build_condition(table_name, match)
            result = set()
            rows = transaction.select(table_name, [u'id'], select_condition)
            for row in rows:
                result.add(row[u'id'])
            if len(result) > 0:
                if results_added:
                    final_result.intersection_update(result)
                else:
                    final_result.update(result)
                results_added = True
        return final_result

    def _format_search_param(self, search_param):
        search_param = unicode(search_param)
        if search_param.lower() == u'true':
            return True
        if search_param.lower() == u'false':
            return False
        return search_param

    def _build_condition(self, table_name, match):
        conds = []
        for column_name, value in match.items():
            conds.append(('=', table_name, column_name, value))
        return ('AND',) + tuple(conds)


class ItemDoesNotExist(unifiedapi.NotFound):

    msg = u'Item does not exist'


class ReadWalker(unifiedapi.ItemWalker):

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
        table_name = unifiedapi.table_name(
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
        table_name = unifiedapi.table_name(
            resource_type=self._item_type, list_field=field)
        item[field] = self._get_list(table_name, self._item_id, column_names)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = unifiedapi.table_name(
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


class TableSearchWalker(unifiedapi.ItemWalker):

    '''Visit every part of an item to find the correct parent item
    for a selected item.'''

    def __init__(self, transaction, item_type, proto_type, table_map):
        self._transaction = transaction
        self._item_type = item_type
        self._proto_type = proto_type
        self.table_map = table_map

    def visit_main_dict(self, item, column_names):
        for name in column_names:
            if name in self.table_map:
                table_set = self.table_map[name]  # pragma: no cover
            else:
                table_set = set()
                self.table_map[name] = table_set
            table_name = unifiedapi.table_name(resource_type=self._item_type)
            table_set.add(table_name)

    def visit_main_str_list(self, item, field):
        if field in self.table_map:
            table_set = self.table_map[field]  # pragma: no cover
        else:
            table_set = set()
            self.table_map[field] = table_set
        table_name = unifiedapi.table_name(
            resource_type=self._item_type, list_field=field)
        table_set.add(table_name)

    def visit_main_dict_list(self, item, field, column_names):
        for name in column_names:
            if name in self.table_map:
                table_set = self.table_map[name]
            else:
                table_set = set()
                self.table_map[name] = table_set
            table_name = unifiedapi.table_name(
                resource_type=self._item_type, list_field=field)
            table_set.add(table_name)

    def visit_dict_in_list(self, item, field, pos, column_names):
        for name in column_names:
            if name in self.table_map:
                table_set = self.table_map[name]
            else:
                table_set = set()  # pragma: no cover
                self.table_map[name] = table_set  # pragma: no cover
            table_name = unifiedapi.table_name(
                resource_type=self._item_type, list_field=field)
            table_set.add(table_name)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        if str_list_field in self.table_map:
            table_set = self.table_map[str_list_field]
        else:
            table_set = set()
            self.table_map[str_list_field] = table_set
        table_name = unifiedapi.table_name(
            resource_type=self._item_type,
            list_field=field,
            subdict_list_field=str_list_field)
        table_set.add(table_name)
