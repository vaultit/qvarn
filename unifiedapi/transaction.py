# transaction.py - database transactions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import logging


class Transaction(object):

    def __init__(self):
        self._sql = None
        self._conn = None

    def set_sql(self, sql):
        self._sql = sql

    def __enter__(self):
        assert self._sql is not None
        assert self._conn is None
        self._conn = self._sql.get_conn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._conn is not None
        if exc_type is None:
            self._conn.commit()
        else:  # pragma: no cover
            self._conn.rollback()
        self._sql.put_conn(self._conn)
        self._conn = None

    def _execute(self, query, values):
        logging.debug('Executing SQL: %r using %r', query, values)
        c = self._conn.cursor()
        c.execute(query, values)
        return c

    def create_table(self, table_name, column_name_type_pairs):
        query = self._sql.format_create_table(
            table_name, column_name_type_pairs)
        self._execute(query, {})

    def rename_table(self, old_name, new_name):
        query = self._sql.format_rename_table(old_name, new_name)
        self._execute(query, {})

    def drop_table(self, table_name):
        query = self._sql.format_drop_table(table_name)
        self._execute(query, {})

    def select(self, table_name, column_names, select_conditions):
        query = self._sql.format_select(
            table_name, column_names, select_conditions)
        cursor = self._execute(query, select_conditions)
        return self._construct_row_dicts(column_names, cursor)

    def _construct_row_dicts(self, column_names, cursor):
        result = []
        for row in cursor:
            row_dict = {}
            for i in range(len(column_names)):
                row_dict[unicode(column_names[i])] = row[i]
            result.append(row_dict)
        return result

    def insert(self, table_name, column_name_values):
        query = self._sql.format_insert(table_name, column_name_values)
        self._execute(query, column_name_values)

    def update(self, table_name, select_conditions, column_name_values):
        query = self._sql.format_update(
            table_name, select_conditions, column_name_values)
        self._execute(query, column_name_values)

    def delete(self, table_name, select_conditions):
        logging.debug('Transaction.delete: table_name=%r', table_name)
        logging.debug(
            'Transaction.delete: select_conditions=%r', select_conditions)
        query = self._sql.format_delete(table_name, select_conditions)
        self._execute(query, select_conditions)
