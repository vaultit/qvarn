# db.py - relational database abstraction
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import string
import sqlite3


def open_disk_database(filename):
    '''Connect to (and create) a database on disk, given its filename.'''
    return SQLiteDatabase(filename)


def open_memory_database():
    '''Connect to (and create) a database in memory only.'''
    return SQLiteDatabase(u':memory:')


class Database(object):
    '''A database abstraction.

    This class provides a minimal database abstraction, for the kinds
    of operations the backend needs to do. Note that we purposefully
    restrict the operations to be very simple.

    For transactions, this class is meant to be used as a Python
    context manager:

        db = open_memory_database()
        with db:
            db.create_table(...)

    In other words, the transaction is what happens in the with
    statement. If the with statement body ends normally, the
    transaction is committed; if there's an exception, the transaction
    is aborted and it is as if it had never happened. Any changes to
    the database MUST be done within a transaction.

    The caller does not need to be too careful about table and column
    names. They are quoted appropriately (for example, a dash becomes
    an underscore). However, it's best to stick to printable ASCII, as
    anything else is likely to not work.

    '''

    def make_table_name(self, *components):
        '''Create a name for a table from the given components.'''
        return '_'.join(self._quote(x) for x in components)

    def _quote(self, name):
        ok = string.ascii_letters + string.digits + '-_'
        assert name.strip(ok) == ''
        return '_'.join(name.split('-'))

    def select(self, table_name, column_names):
        '''Retrieve the given columns from all rows.'''

        return self._select_helper(table_name, column_names, {})

    def select_matching_rows(self, table_name, column_names, match_columns):
        '''Like select, but only rows matching a condition.

        ``match_columns`` is a dict, where the key is a column name
        and the value is its value. If the dict is empty, an empty
        list is returned.

        '''

        if match_columns:
            return self._select_helper(table_name, column_names, match_columns)
        else:
            return []

    def _select_helper(self, table_name, column_names, match_columns):
        raise NotImplementedError


class SQLiteDatabase(Database):

    def __init__(self, url):
        self._conn = sqlite3.connect(
            url,
            isolation_level="IMMEDIATE",
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self._conn.row_factory = sqlite3.Row
        self._in_transaction = False

    def __enter__(self):
        assert not self._in_transaction
        self._in_transaction = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._in_transaction
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._in_transaction = False

    def create_table(self, table_name, *columns):
        '''Create a new table.

        The columns are specified as a list of (column name, type)
        pairs. The type MUST be one of int, unicode, or bool.

        '''

        assert self._in_transaction

        type_name = {
            buffer: u'BLOB',
            int: u'INTEGER',
            unicode: u'TEXT',
            bool: u'BOOLEAN',
        }

        col_spec = []
        for col_name, col_type in columns:
            col_spec.append(
                u'%s %s' % (self._quote(col_name), type_name[col_type]))

        sql = u'CREATE TABLE IF NOT EXISTS [%s] ' % self._quote(table_name)
        sql += u'(' + u', '.join(col_spec) + u')'

        c = self._conn.cursor()
        c.execute(sql)

    def insert(self, table_name, *columns):
        '''Insert a row into a table.

        Columns are provided as a list of (column name, value) pairs.

        '''

        assert self._in_transaction

        for name, value in columns:
            assert value is None or type(value) in (unicode, int, bool, buffer)

        values = {}
        for name, value in columns:
            if value is not None:
                values[self._quote(name)] = value
        column_names = values.keys()

        sql = u'INSERT INTO %s' % table_name
        sql += u' (' + u', '.join(column_names) + u')'
        sql += (u' VALUES ( ' +
                u', '.join(':%s' % name for name in column_names) +
                u')')

        c = self._conn.cursor()
        c.execute(sql, values)

    def _select_helper(self, table_name, column_names, match_columns):
        quoted_names = [self._quote(x) for x in column_names]
        sql = u'SELECT %s FROM %s' % (
            u','.join(quoted_names), self._quote(table_name))

        if match_columns:
            # Add condition for a column. This results in an SQL
            # snippets such as "foo IS :foo AND bar IS :bar", where
            # "foo" and "bar" are columns names, and ":foo" and ":bar"
            # are placeholders for the value, using SQLite Python
            # binding syntax.

            condition = ' AND '.join(
                '{0} IS :{0}'.format(self._quote(x)) for x in match_columns)
            sql += u' WHERE ' + condition

        c = self._conn.cursor()
        c.execute(sql, match_columns)

        result = []
        for row in c:
            a_dict = {}
            for i in range(len(column_names)):
                a_dict[unicode(column_names[i])] = row[str(quoted_names[i])]
            result.append(a_dict)
        return result

    def delete_matching_rows(self, table_name, match_columns):
        '''Delete rows matching a condition.

        The condition is given the same way as for
        select_matching_rows.

        '''

        assert self._in_transaction

        sql = u'DELETE FROM %s' % self._quote(table_name)

        # Add condition for a column. This results in an SQL
        # snippets such as "foo IS :foo AND bar IS :bar", where
        # "foo" and "bar" are columns names, and ":foo" and ":bar"
        # are placeholders for the value, using SQLite Python
        # binding syntax. The values are fed to SQLite using the
        # values dict created below.

        condition = ' AND '.join(
            '{0} IS :{0}'.format(self._quote(x)) for x in match_columns)
        sql += u' WHERE ' + condition

        c = self._conn.cursor()
        c.execute(sql, match_columns)
        return c
