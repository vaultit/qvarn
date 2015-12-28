# transaction.py - database transactions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import logging
import time


class Transaction(object):

    def __init__(self):
        self._sql = None
        self._conn = None
        self._measurement = None

    def set_sql(self, sql):
        self._sql = sql

    def __enter__(self):
        assert self._sql is not None
        assert self._conn is None
        assert self._measurement is None
        logging.debug('Transaction starts')
        self._measurement = Measurement()
        self._conn = self._sql.get_conn()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._conn is not None
        assert self._measurement is not None
        if exc_type is None:
            self._conn.commit()
        else:  # pragma: no cover
            self._conn.rollback()
        self._sql.put_conn(self._conn)
        self._measurement.finish()
        self._measurement.log()
        if exc_type is None:  # pragma: no cover
            logging.info('Transaction OK')
        else:  # pragma: no cover
            logging.warning('Transaction failed')
        self._conn = None
        self._measurement = None

    def _execute(self, query, values):
        with self._measurement.new('SQL query') as m:
            c = self._conn.cursor()
            c.execute(query, values)
            m.note('query: %r', query)
            m.note('values: %r', values)
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
        with self._measurement.new('fetch-rows') as m:
            rows = self._construct_row_dicts(column_names, cursor)
            m.note('Result is %d rows', len(rows))
        return rows

    def _construct_row_dicts(self, column_names, cursor):
        result = []
        indexes = range(len(column_names))
        for row in cursor:
            row_dict = {}
            for i in indexes:
                row_dict[column_names[i]] = row[i]
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
        query = self._sql.format_delete(table_name, select_conditions)
        self._execute(query, select_conditions)


class Measurement(object):

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


class Step(object):

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
