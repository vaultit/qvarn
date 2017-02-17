# transaction.py - database transactions
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


import qvarn


class Transaction(object):

    '''Execute SQL statements in a transaction.

    All SQL statements in Qvarn get executed through this class. It
    provides methods for each type of statement Qvarn needs, executes
    them, and logs data about the execution.

    This class is meant to be used as a context manager with the
    Python with statement. When entered, the transaction starts. When
    exited, the transaction ends, automatically either committong or
    rolling back the transaction, depending on the cause of the exit.

    Since different database engines implement the SQL standard in
    different ways, this transaction class delegates the formation of
    the actual text of the statements to an SQLAdapter subclass. No
    actual SQL text is allowed anywhere outside SQLAdapter and its
    subclasses.

    '''

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
        self._measurement = qvarn.Measurement()
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
        self._measurement.log(exc_tb)
        self._conn = None
        self._measurement = None

    def _execute(self, what, query, values):
        with self._measurement.new(what) as m:
            c = self._conn.cursor()
            c.execute(query, values)
            m.note(query=query, values=values)
        return c

    def create_table(self, table_name, column_name_type_pairs):
        query = self._sql.format_create_table(
            table_name, column_name_type_pairs)
        self._execute('CREATE TABLE', query, {})

    def add_column(self, table_name, column_name, column_type):
        query = self._sql.format_add_column(
            table_name, column_name, column_type)
        self._execute('ALTER TABLE', query, {})

    def rename_table(self, old_name, new_name):
        query = self._sql.format_rename_table(old_name, new_name)
        self._execute('RENAME TABLE', query, {})

    def drop_table(self, table_name):
        query = self._sql.format_drop_table(table_name)
        self._execute('DROP TABLE', query, {})

    def select(self, table_name, column_names, select_condition):
        query, values = self._sql.format_select(
            table_name, column_names, select_condition)
        cursor = self._execute('SELECT', query, values)
        with self._measurement.new('fetch-rows') as m:
            rows = self._construct_row_dicts(column_names, cursor)
            m.note(row_count=len(rows))
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
        self._execute('INSERT', query, column_name_values)

    def update(self, table_name, select_conditions, column_name_values):
        query, values = self._sql.format_update(
            table_name, select_conditions, column_name_values)
        self._execute('UPDATE', query, values)

    def delete(self, table_name, select_conditions):
        query, values = self._sql.format_delete(table_name, select_conditions)
        self._execute('DELETE', query, values)
