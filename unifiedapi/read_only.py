# read_only.py - read-only interface to databases
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


class ReadOnlyStorage(object):

    '''Read-only interface to a database.

    You MUST call ``set_db`` and ``set_item_prototype`` before doing
    anything else.

    '''

    def __init__(self):
        self._db = None
        self._item_type = None
        self._prototype = None

    def set_db(self, db):
        '''Set the database to use.'''
        self._db = db

    def set_item_prototype(self, item_type, prototype):
        '''Set type and prototype of items in this database.'''
        self._item_type = item_type
        self._prototype = prototype

    def get_item_ids(self):
        '''Get list of ids of all items.'''
        return [
            row['id']
            for row in self._db.select(self._item_type, [u'id'])]

    def get_item(self, item_id):
        '''Get a specific item.'''
        item = {}
        rw = ReadWalker(self._db, self._item_type, item_id)
        rw.walk_item(item, self._prototype)
        return item

    def get_search_matches(self, matching_rules, search_fields,
                           search_values):
        '''Do a search.'''

        tsw = TableSearchWalker(self._db, self._item_type, self._prototype,
                                {})
        tsw.walk_item(self._prototype, self._prototype)

        result = self._do_search(search_fields, search_values, matching_rules,
                                 tsw.table_map)

        result_list = []
        for row_id in result:
            result_list.append({u'id': row_id})

        return {u'matches': result_list}

    def _do_search(self, search_fields, search_values, matching_rules,
                   table_map):

        final_result = set()
        results_added = False

        for i in range(len(search_fields)):
            result = set()
            field = unicode(search_fields[i])
            match = {}
            match[field] = unicode(search_values[i])
            table_names = table_map[field]
            param_result = set()
            for table_name in table_names:
                if matching_rules[i] == 'exact':
                    for row in self._db.select_matching_rows(table_name,
                                                             [u'id'],
                                                             match):
                        result.add(row[u'id'])
                else:
                    raise bottle.HTTPError(status=400)
                param_result.update(result)
            if results_added:
                final_result.intersection_update(param_result)
            else:
                final_result.update(param_result)
            results_added = True

        return final_result


class ItemDoesNotExist(unifiedapi.BackendException):

    msg = u'Item {id} does not exist'


class ReadWalker(unifiedapi.ItemWalker):

    '''Visit every part of an item to retrieve it from the database.'''

    def __init__(self, db, item_type, item_id):
        self._db = db
        self._item_type = item_type
        self._item_id = item_id

    def visit_main_dict(self, item, column_names):
        row = self._get_row(self._item_type, self._item_id, column_names)
        for name in column_names:
            item[name] = row[name]

    def _get_row(self, table_name, item_id, column_names):
        match = {
            u'id': item_id
        }
        rows = self._db.select_matching_rows(table_name, column_names, match)
        for row in rows:
            return row
        raise ItemDoesNotExist(id=item_id)

    def visit_main_str_list(self, item, field):
        table_name = self._db.make_table_name(item[u'type'], field)
        item[field] = self._get_str_list(table_name, field, self._item_id)

    def _get_str_list(self, table_name, column_name, item_id):
        rows = self._get_list(table_name, item_id, [column_name])
        return [row[column_name] for row in rows]

    def _get_list(self, table_name, item_id, column_names):
        match = {
            u'id': item_id
        }
        rows = self._db.select_matching_rows(
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
        table_name = self._db.make_table_name(item[u'type'], field)
        item[field] = self._get_list(table_name, item['id'], column_names)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = self._db.make_table_name(
            item[u'type'], field, str_list_field)

        match = {
            u'id': item[u'id'],
            u'dict_list_pos': unicode(pos),
        }
        rows = self._db.select_matching_rows(
            table_name, [u'list_pos', str_list_field], match)

        in_order = self._sort_rows(rows)
        result = [row[str_list_field] for row in in_order]
        item[field][pos][str_list_field] = result


class TableSearchWalker(unifiedapi.ItemWalker):

    '''Visit every part of an item to find the correct parent item
    for a selected item.'''

    def __init__(self, db, item_type, proto_type, table_map):
        self._db = db
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

            table_set.add(self._item_type)

    def visit_main_str_list(self, item, field):
        if field in self.table_map:
            table_set = self.table_map[field]  # pragma: no cover
        else:
            table_set = set()
            self.table_map[field] = table_set

        table_set.add(self._db.make_table_name(self._item_type, field))

    def visit_main_dict_list(self, item, field, column_names):
        for name in column_names:
            if name in self.table_map:
                table_set = self.table_map[name]
            else:
                table_set = set()
                self.table_map[name] = table_set
            table_set.add(self._db.make_table_name(self._item_type, field))

    def visit_dict_in_list(self, item, field, pos, column_names):
        for name in column_names:
            if name in self.table_map:
                table_set = self.table_map[name]
            else:
                table_set = set()  # pragma: no cover
                self.table_map[name] = table_set  # pragma: no cover
            table_set.add(self._db.make_table_name(self._item_type, field))

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        if str_list_field in self.table_map:
            table_set = self.table_map[str_list_field]
        else:
            table_set = set()
            self.table_map[str_list_field] = table_set

        table_set.add(self._db.make_table_name(self._item_type, field,
                                               str_list_field))
