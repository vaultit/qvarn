# dbconn.py - Transactions on database connections
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


class DatabaseConnection(object):

    '''Allow transactions on a database connection.'''

    def __init__(self):
        self._sql = None

    def set_sql(self, sql):
        self._sql = sql

    def transaction(self):
        trans = unifiedapi.Transaction()
        trans.set_sql(self._sql)
        return trans
