# dbconn_tests.py - unit tests
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


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
