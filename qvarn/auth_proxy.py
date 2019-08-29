# auth_proxy.py - /auth/token proxy endpoint for dev/test environments
#
# Copyright 2018 Suomen Tilaajavastuu Oy
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


# Pylint doesn't fully understand what bottle does and doesn't know
# about all the members in all the objects. Disable related warnigs for
# this module.
#
# pylint: disable=no-member


import bottle
import requests

import qvarn


class AuthProxyResource(object):

    '''Implement a simple /auth/token endpoint that forwards to another server.

    This endpoint is only intended to use for dev/test environments in order to
    avoid using frontend services like HAProxy.

    This endpoint uses auth.proxy_to configuration parameter in order to
    forward auth requests to a different HTTP server.

    '''

    def __init__(self, proxy_to):
        self._proxy_to = proxy_to

    def prepare_resource(self, database_url):
        return [
            {
                'path': '/auth/token',
                'method': 'POST',
                'callback': self._callback,
                'skip': [
                    qvarn.AuthorizationPlugin,
                ]
            },
        ]

    def _callback(self):
        url = self._proxy_to
        data = bottle.request.body.read()
        headers = dict(bottle.request.headers)
        headers.pop('Host', None)
        response = requests.post(url, data=data, headers=headers)
        return bottle.HTTPResponse(response.content,
                                   status=response.status_code)
