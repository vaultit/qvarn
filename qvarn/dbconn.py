# dbconn.py - Transactions on database connections
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


class DatabaseConnection(object):

    '''Allow transactions on a database connection.'''

    def __init__(self):
        self._sql = None

    def set_sql(self, sql):
        self._sql = sql

    def transaction(self):
        trans = qvarn.Transaction()
        trans.set_sql(self._sql)
        return trans
