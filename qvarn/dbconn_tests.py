# dbconn_tests.py - unit tests
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


import unittest

import qvarn


class DatabaseConnectionTests(unittest.TestCase):

    def test_gets_and_puts_conn(self):
        dummy = DummyAdapter()
        dbconn = qvarn.DatabaseConnection()
        dbconn.set_sql(dummy)
        with dbconn.transaction():
            pass
        self.assertTrue(dummy.get_conn_was_first)
        self.assertTrue(dummy.put_conn_was_second)


class DummyAdapter(object):

    def __init__(self):
        self.get_conn_was_first = False
        self.put_conn_was_second = False

    def get_conn(self):
        if not self.put_conn_was_second:
            self.get_conn_was_first = True
        return DummyConn()

    def put_conn(self, conn):
        if self.get_conn_was_first:
            self.put_conn_was_second = True


class DummyConn(object):

    def commit(self):
        pass

    def rollback(self):
        pass
