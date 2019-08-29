# healthcheck.py - /healthcheck endpoint
#
# Copyright 2019 Suomen Tilaajavastuu Oy
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


class HealthcheckEndpoint(object):

    def __init__(self):
        self._dbconn = None

    def prepare_resource(self, dbconn):
        self._dbconn = dbconn

        return [
            {
                'path': '/healthcheck',
                'method': 'GET',
                'callback': self,
                'skip': [qvarn.AuthorizationPlugin],
            },
        ]

    def __call__(self):
        with self._dbconn.transaction() as t:
            c = t.execute('SELECT', 'SELECT 1')
            result = c.fetchall()
        assert result == [(1,)], result
        return {'message': 'healthy', 'status': 'OK'}
