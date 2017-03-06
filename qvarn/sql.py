# sql.py - SQL dialect adaptation
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

    A "column_name_types" argument is similar, but instead of a value,
    it indicates type type of a column, when it is created. Types are
    basic Python types, and must be one of types in the
    "qvarn.column_types" constant.

    A "select_condition" argument is a tree structure describing an
    arbitrarily complex boolean expression. The tree nodes may be of
    the following shapes:

        ('=', table_name, column_name, value)
        ('AND', cond...)
        ('OR', cond...)

    where "cond..." zero or more conditions of the same structure as
    the tree. A '=' node specifies a condition of where table row
    matches if its column has an exact value. The 'AND' and 'OR' nodes
    combine other conditions to a more complicated one.

    A select_condition may be None to indicate that all rows match.

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

    def quote(self, name):
        '''Quote a name for SQL.

        This doesn't handle all kinds of names. In fact, it asserts
        that it gets a name it can handle. The only thing it can
        handle, right now, is converting dashes to underscores.

        '''

        ok = string.ascii_letters + string.digits + '-_'
        assert name.strip(ok) == '', 'must have only allowed chars: %r' % name
        return u'_'.join(name.split('-'))

    def qualified_column(self, table_name, column_name):
        return u'{}.{}'.format(self.quote(table_name), self.quote(column_name))

    def format_create_table(self, table_name, column_name_types):
        assert isinstance(column_name_types, dict)

        column_specs = [
            u'{} {}'.format(self.quote(col_name), self.type_name[col_type])
            for col_name, col_type in column_name_types.items()
        ]
        sql = u'CREATE TABLE IF NOT EXISTS {} ({})'.format(
            self.quote(table_name),
            u', '.join(column_specs),
        )
        return sql

    def format_add_column(self, table_name, column_name, column_type):
        sql = u'ALTER TABLE {} ADD COLUMN {} {}'.format(
            self.quote(table_name),
            self.quote(column_name),
            self.type_name[column_type])
        return sql

    def format_rename_table(self, old_name, new_name):
        return u'ALTER TABLE {} RENAME TO {}'.format(
            self.quote(old_name), self.quote(new_name))

    def format_drop_table(self, table_name):
        return u'DROP TABLE IF EXISTS %s ' % self.quote(table_name)

    def format_select(self, table_name, column_names, select_condition):
        '''Format an SQL SELECT statement.

        Return the statement, and a list of values to use for the
        placeholders, suitable to give to a database connection
        execution.

        '''

        table_names = set(
            [table_name] + self._get_table_names(select_condition))

        sql = u'SELECT {} FROM {}'.format(
            u', '.join(
                self.qualified_column(table_name, x)
                for x in column_names),
            u', '.join(self.quote(x) for x in table_names))
        if select_condition:
            sql += u' WHERE ' + self._format_condition(select_condition)

        values = self._construct_values({}, select_condition)

        return sql, values

    def _get_table_names(self, condition):
        if condition is None:
            return []
        assert condition[0] in ('=', 'AND', 'OR')

        if condition[0] == '=':
            return [condition[1]]
        else:
            result = []
            for cond in condition[1:]:
                result += self._get_table_names(cond)
            return result

    def _construct_values(self, values, condition):
        if condition is None:
            return values

        op = condition[0]
        assert op in ('=', 'AND', 'OR')

        if op == '=':
            _, table_name, column_name, value = condition
            x = self.format_qualified_placeholder_name(table_name, column_name)
            values[x] = value
        else:
            for cond in condition[1:]:
                self._construct_values(values, cond)

        return values

    def _format_condition(self, condition):
        funcs = {
            '=': self._format_equal,
            'AND': self._format_and,
            'OR': self._format_or,
        }
        func = funcs[condition[0]]
        return func(*condition[1:])

    def _format_equal(self, table_name, column_name, value):
        return u'{}.{} = {}'.format(
            self.quote(table_name),
            self.quote(column_name),
            self.format_qualified_placeholder(table_name, column_name))

    def _format_and(self, *conds):
        return self._format_andor(u'AND', *conds)

    def _format_or(self, *conds):
        return self._format_andor(u'OR', *conds)

    def _format_andor(self, op, *conds):
        op = u' {} '.format(op)
        return op.join(
            u'({})'.format(self._format_condition(c)) for c in conds)

    def format_limit(self, limit=None, offset=None):
        raise NotImplementedError()

    def format_insert(self, table_name, column_name_values):
        quoted_column_names = [self.quote(x) for x in column_name_values]
        placeholders = [
            self.format_placeholder(x) for x in quoted_column_names]
        return u'INSERT INTO {} ({}) VALUES ({})'.format(
            self.quote(table_name),
            u', '.join(quoted_column_names),
            u', '.join(placeholders))

    def format_update(self, table_name, select_condition, column_name_values):
        assignments = [
            u'{} = {}'.format(self.quote(x), self.format_placeholder(x))
            for x in column_name_values
        ]
        sql = u'UPDATE {} SET {}'.format(
            self.quote(table_name),
            u', '.join(assignments))
        if select_condition:
            sql += u' WHERE ' + self._format_condition(select_condition)

        values = self._construct_values(
            column_name_values.copy(), select_condition)
        return sql, values

    def format_delete(self, table_name, select_condition):
        '''Format an SQL DELETE statement.

        Return the statement, and a list of values to use for the
        placeholders, suitable to give to a database connection
        execution.

        '''

        sql = u'DELETE FROM {} WHERE {}'.format(
            self.quote(table_name),
            self._format_condition(select_condition))

        values = self._construct_values({}, select_condition)

        return sql, values

    def format_placeholder(self, column_name):
        raise NotImplementedError()

    def format_qualified_placeholder(self, table_name, column_name):
        raise NotImplementedError()

    def format_qualified_placeholder_name(self, table_name, column_name):
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

    def format_limit(self, limit=None, offset=None):
        query = []
        if limit is None and offset is not None:
            limit = -1
        if limit is not None:
            query.append(u'LIMIT %d' % limit)
        if offset is not None:
            query.append(u'OFFSET %d' % offset)
        return u' '.join(query)

    def format_placeholder(self, column_name):
        return ':{}'.format(self.quote(column_name))

    def format_qualified_placeholder(self, table_name, column_name):
        q = self.format_qualified_placeholder_name(table_name, column_name)
        return ':{}'.format(q)

    def format_qualified_placeholder_name(self, table_name, column_name):
        q = self.qualified_column(table_name, column_name)
        return q.encode('hex')

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

        # These are needed (in Python 2) so that we always get
        # database input in Unicode. See
        # http://initd.org/psycopg/docs/usage.html for details.
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
        return pool

    def format_limit(self, limit=None, offset=None):
        query = []
        if limit is None and offset is not None:
            limit = 'ALL'
        if limit is not None:
            query.append(u'LIMIT %s' % limit)
        if offset is not None:
            query.append(u'OFFSET %d' % offset)
        return u' '.join(query)

    def format_placeholder(self, column_name):
        return u'%({})s'.format(self.quote(column_name))

    def format_qualified_placeholder(self, table_name, column_name):
        q = self.format_qualified_placeholder_name(table_name, column_name)
        return u'%({})s'.format(q)

    def format_qualified_placeholder_name(self, table_name, column_name):
        return self.qualified_column(table_name, column_name)

    def get_conn(self):
        return self._pool.getconn()

    def put_conn(self, conn):
        self._pool.putconn(conn)
