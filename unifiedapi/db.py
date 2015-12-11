# db.py - relational database abstraction
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import logging
import string
import sqlite3

import psycopg2
import psycopg2.pool
import psycopg2.extras
import psycopg2.extensions


def open_disk_database(**kwargs):
    '''Connect to a database on disk, given its connection parameters.'''
    return PostgreSQLDatabase(**kwargs)


def open_memory_database():
    '''Connect to (and create) a database in memory only.'''
    return SQLiteDatabase()


column_types = (unicode, int, bool, buffer)


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

    def __init__(self):
        if self.__class__ == Database:
            raise NotImplementedError(
                'Cannot create an abstract Database instance')
        self.type_name = {}

    def _execute(self, sql_statement, values, expecting_results):
        raise NotImplementedError()

    def _quote(self, name):
        ok = string.ascii_letters + string.digits + '-_'
        assert name.strip(ok) == ''
        return '_'.join(name.split('-'))

    def create_table(self, table_name, *columns):
        '''Create a new table.

        The columns are specified as a list of (column name, type)
        pairs. The type MUST be one of int, unicode, or bool.

        '''

        logging.info('Creating table %r', table_name)
        col_spec = []
        for col_name, col_type in columns:
            col_spec.append(
                u'%s %s' % (self._quote(col_name), self.type_name[col_type]))

        sql = u'CREATE TABLE IF NOT EXISTS %s ' % self._quote(table_name)
        sql += u'(' + u', '.join(col_spec) + u')'

        self._execute(sql, {}, False)

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

    def add_column(self, table_name, column_name, column_type):
        sql = u'ALTER TABLE %s ' % self._quote(table_name)
        sql += u'ADD '
        sql += '%s %s' % (self._quote(column_name),
                          self.type_name[column_type])
        self._execute(sql, {}, False)

    def drop_column(self, table_name, column_name):
        sql = u'ALTER TABLE %s ' % self._quote(table_name)
        sql += u'DROP '
        sql += '%s' % self._quote(column_name)
        self._execute(sql, {}, False)

    def drop_table(self, table_name):
        sql = u'DROP TABLE %s ' % self._quote(table_name)
        self._execute(sql, {}, False)


class SQLiteDatabase(Database):
    '''An SQLite database abstraction.

    This class provides a memory based SQLite specific implementation
    for the Database abstraction. It is meant to be used only in unit
    test cases.

    '''

    def __init__(self):
        super(SQLiteDatabase, self).__init__()
        self.type_name = {
            buffer: u'BLOB',
            int: u'INTEGER',
            unicode: u'TEXT',
            bool: u'BOOLEAN',
        }
        assert set(self.type_name.keys()) == set(column_types)

        # This connection must exist as long as the SQLDatabase object
        # exists, since it's memory backed. If we close the connection,
        # the database disappears.
        self._real_conn = self._get_conn()

        # This connection is managed by the context manager.
        self._conn = None

        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

    def _get_conn(self):
        conn = sqlite3.connect(
            u':memory:',
            isolation_level="IMMEDIATE",
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def _in_transaction(self):
        return self._conn is not None

    def __enter__(self):
        assert not self._in_transaction
        self._conn = self._real_conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._in_transaction
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._conn = None

    def _execute(self, sql, values, expecting_results):
        c = self._real_conn.cursor()
        c.execute(sql, values)
        if expecting_results:
            return [row for row in c]

    def insert(self, table_name, *columns):
        '''Insert a row into a table.

        Columns are provided as a list of (column name, value) pairs.

        '''

        assert self._in_transaction

        for name, value in columns:
            assert value is None or type(value) in column_types

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

        self._execute(sql, values, False)

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

        rows = self._execute(sql, match_columns, True)

        result = []
        for row in rows:
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

        self._execute(sql, match_columns, False)


class PostgreSQLDatabase(Database):
    '''A PostgreSQL database abstraction.

    This class provides a PostgreSQL specific implementation
    for the Database abstraction. It is meant to be used in production
    environment and will not be tested with unit tests.

    '''

    def __init__(self, **kwargs):
        # Check arguments. We do it this way, to force keyword
        # arguments to be used, since there's too many arguments to
        # use positional ones. We also verify that all arguments are
        # give, none of them are None, and that no extra ones are
        # given.
        args = [
            'host',
            'port',
            'db_name',
            'user',
            'password',
            'min_conn',
            'max_conn'
        ]
        for arg in args:
            assert arg in kwargs
            assert kwargs[arg] is not None
        assert sorted(args) == sorted(kwargs.keys())

        super(PostgreSQLDatabase, self).__init__()
        self.type_name = {
            buffer: u'BYTEA',
            int: u'BIGINT',
            unicode: u'TEXT',
            bool: u'BOOLEAN',
        }
        assert set(self.type_name.keys()) == set(column_types)

        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=kwargs['min_conn'],
            maxconn=kwargs['max_conn'],
            database=kwargs['db_name'],
            user=kwargs['user'],
            password=kwargs['password'],
            host=kwargs['host'],
            port=kwargs['port'],
            cursor_factory=psycopg2.extras.RealDictCursor)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
        self._conn = None

    @property
    def _in_transaction(self):
        return self._conn is not None

    def __enter__(self):
        assert not self._in_transaction
        self._conn = self._pool.getconn()

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert self._in_transaction
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        self._pool.putconn(self._conn)
        self._conn = None

    def _execute(self, sql, values, expecting_results):
        if self._conn is None:
            conn = self._pool.getconn()
            rows = self._execute_with_conn(
                conn, sql, values, expecting_results)
            self._pool.putconn(conn)
            return rows
        else:
            return self._execute_with_conn(
                self._conn, sql, values, expecting_results)

    def _execute_with_conn(self, conn, sql, values, expecting_results):
        c = conn.cursor()
        c.execute(sql, values)
        if expecting_results:
            return [row for row in c]

    def insert(self, table_name, *columns):
        '''Insert a row into a table.

        Columns are provided as a list of (column name, value) pairs.

        '''

        assert self._in_transaction

        for name, value in columns:
            assert value is None or type(value) in column_types

        values = {}
        for name, value in columns:
            if value is not None:
                values[self._quote(name)] = value
        column_names = values.keys()

        sql = u'INSERT INTO %s' % table_name
        sql += u' (' + u', '.join(column_names) + u')'
        sql += (u' VALUES ( ' +
                u', '.join('%({0})s'.format(name) for name in column_names) +
                u')')

        self._execute(sql, values, False)

    def _select_helper(self, table_name, column_names, match_columns):
        quoted_names = [self._quote(x) for x in column_names]
        sql = u'SELECT %s FROM %s' % (
            u','.join(quoted_names), self._quote(table_name))

        if match_columns:
            # Add condition for a column. This results in an SQL
            # snippets such as "foo = %(foo) AND bar IS %(bar)", where
            # "foo" and "bar" are columns names, and "%(foo)" and "%(bar)"
            # are placeholders for the value, using PostgreSQL Python
            # binding syntax.

            condition = ' AND '.join(
                '{0} = %({0})s'.format(self._quote(x)) for x in match_columns)
            sql += u' WHERE ' + condition

        rows = self._execute(sql, match_columns, True)
        result = []
        for row in rows:
            a_dict = {}
            for i in range(len(column_names)):
                a_dict[unicode(column_names[i])] = row[
                    str(quoted_names[i])]
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
        # snippets such as "foo = %(foo) AND bar IS %(bar)", where
        # "foo" and "bar" are columns names, and "%(foo)" and "%(bar)"
        # are placeholders for the value, using PostgreSQL Python
        # binding syntax.

        condition = ' AND '.join(
            '{0} = %({0})s'.format(self._quote(x)) for x in match_columns)
        sql += u' WHERE ' + condition

        self._execute(sql, match_columns, False)
