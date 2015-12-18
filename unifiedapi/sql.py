# sql.py - SQL dialect adaptation
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

'''Adapt to SQL dialects.

We support SQLite and PostgreSQL. They have minor differences in their
SQL, and in the Python bindings. This module provides a very light
abstraction layer to manage both. Only the minimal things required by
Qvarn are supported.

'''


import sqlite3
import string

import psycopg2
import psycopg2.pool
import psycopg2.extras
import psycopg2.extensions


column_types = (unicode, int, bool, buffer)


class SqlAdapter(object):

    '''Base class for SQL adapters.

    The format_* methods produce textual representation of various SQL
    queries.

    A "column_name_values" argument is a dict mapping a column name to
    its value value. They're used to list values to be inserted or
    updated.

    A "select_conditions" argument is identical in structure, and used
    to represent conditions for selecting rows, where a row is
    selected if its column matches the given value.

    A "column_name_types" argument is again similar, but instead of a
    value, it indicates type type of a column, when it is created.
    Types are basic Python types, and must be one of types in the
    "unifiedapi.column_types" constant.

    In addition, the get_conn/put_conn method pair returns a
    "connection" object for communicating with the database. It
    follows the usual Python database binding style. Specifically:

    * conn.cursor() returns a cursor.

    * cursor.execute(sql_text, values) executes an SQL statement
      returned by format_* methods in this class. values is a dict
      giving the values.

    The put_conn method is used to return a connection back into a
    pool so it can be reused later, possibly by another thread.

    There should be one SqlAdapter object per process. This class (or,
    specifically, its subclass) is thread safe.

    '''

    # The following is an empty dictionary by default. Subclasses MUST
    # override it.
    type_name = {}

    debug = False

    def quote(self, name):
        '''Quote a name for SQL.

        This doesn't handle all kinds of names. In fact, it asserts
        that it gets a name it can handle. The only thing it can
        handle, right now, is converting dashes to underscores.

        '''

        ok = string.ascii_letters + string.digits + '-_'
        assert name.strip(ok) == '', 'must have only allowed chars: %r' % name
        return u'_'.join(name.split('-'))

    def format_create_table(self, table_name, column_name_types):
        assert type(column_name_types) is dict

        column_specs = [
            u'{} {}'.format(self.quote(col_name), self.type_name[col_type])
            for col_name, col_type in column_name_types.items()
        ]
        sql = u'CREATE TABLE IF NOT EXISTS {} ({})'.format(
            self.quote(table_name),
            u', '.join(column_specs),
        )
        if self.debug:
            print 'create table sql:', repr(sql)
        return sql

    def format_rename_table(self, old_name, new_name):
        return u'ALTER TABLE {} RENAME TO {}'.format(
            self.quote(old_name), self.quote(new_name))

    def format_drop_table(self, table_name):
        return u'DROP TABLE %s ' % self.quote(table_name)

    def format_select(self, table_name, column_names, select_conditions):
        quoted_column_names = [self.quote(x) for x in column_names]
        sql = u'SELECT {} FROM {}'.format(
            u', '.join(quoted_column_names),
            self.quote(table_name))

        if select_conditions:
            conditions = [
                u'{} = {}'.format(
                    self.quote(col_name), self.format_placeholder(col_name))
                for col_name in select_conditions
            ]
            sql += u' WHERE {}'.format(u' AND '.join(conditions))

        return sql

    def format_insert(self, table_name, column_name_values):
        quoted_column_names = [self.quote(x) for x in column_name_values]
        placeholders = [
            self.format_placeholder(x) for x in quoted_column_names]
        return u'INSERT INTO {} ({}) VALUES ({})'.format(
            self.quote(table_name),
            u', '.join(quoted_column_names),
            u', '.join(placeholders))

    def format_update(self, table_name, select_conditions, column_name_values):
        assignments = [
            u'{} = {}'.format(self.quote(x), self.format_placeholder(x))
            for x in column_name_values
        ]
        sql = u'UPDATE {} SET {}'.format(
            self.quote(table_name),
            u', '.join(assignments))
        if select_conditions:
            conditions = [
                u'{} IS {}'.format(
                    self.quote(x), self.format_placeholder(x))
                for x in select_conditions
            ]
            sql += u' WHERE {}'.format(u', '.join(conditions))
        return sql

    def format_delete(self, table_name, select_conditions):
        conditions = [
            u'{} = {}'.format(self.quote(x), self.format_placeholder(x))
            for x in select_conditions
        ]
        return u'DELETE FROM {} WHERE {}'.format(
            self.quote(table_name),
            u' AND '.join(conditions))

    def format_placeholder(self, column_name):
        raise NotImplementedError()

    def get_conn(self):
        raise NotImplementedError()

    def put_conn(self, conn):
        raise NotImplementedError()


class SqliteAdapter(SqlAdapter):

    '''An SQL dialect adapter for SQLite.'''

    type_name = {
        bool: u'BOOLEAN',
        buffer: u'BLOB',
        int: u'INTEGER',
        unicode: u'TEXT',
    }

    def __init__(self):
        self._conn = sqlite3.connect(u':memory:')
        self.debug = False

    def format_placeholder(self, column_name):
        return ':{}'.format(self.quote(column_name))

    def get_conn(self):
        return self._conn

    def put_conn(self, conn):
        pass


class PostgresAdapter(SqlAdapter):

    '''An SQL adapter for Postgres.'''

    type_name = {
        bool: u'BOOLEAN',
        buffer: u'BYTEA',
        int: u'BIGINT',
        unicode: u'TEXT',
    }

    def __init__(self, **kwargs):
        self._check_init_args(kwargs)
        self._pool = self._create_connection_pool(kwargs)

    def _check_init_args(self, kwargs):
        # Check arguments to __init__. We do it this way, to force
        # keyword arguments to be used, since there's too many
        # arguments to use positional ones. We also verify that all
        # arguments are give, none of them are None, and that no extra
        # ones are given.

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
            assert arg in kwargs, 'must have keyword argument %r' % arg
            assert kwargs[arg] is not None, 'arg %r must not be None' % arg
        assert sorted(args) == sorted(kwargs.keys())

    def _create_connection_pool(self, kwargs):
        pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=kwargs['min_conn'],
            maxconn=kwargs['max_conn'],
            database=kwargs['db_name'],
            user=kwargs['user'],
            password=kwargs['password'],
            host=kwargs['host'],
            port=kwargs['port'])
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
        return pool

    def format_placeholder(self, column_name):
        return u'%({})s'.format(self.quote(column_name))

    def get_conn(self):
        return self._pool.getconn()

    def put_conn(self, conn):
        self._pool.putconn(conn)
