# auth_token.py - /auth/token endpoint for dev/test environments
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

import time
import datetime

import jwt
import bottle

import qvarn


class AuthTokenResource(object):

    '''Implement a simple /auth/token endpoint.

    This endpoint is only intended to use for dev/test environments in order to
    avoid using whole OpendID Connect server like Gluu.

    This endpoint uses auth.private_key configuration parameter in order to
    create a valid authorization token. If auth.private_key is not provided
    this endpoint will fail with an error.

    Private key is automatically created by `qvarn-run` script, which can be
    used for development or testing.

    '''

    def __init__(self, private_key, issuer):
        self._issuer = issuer
        self._private_key = private_key

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
        # pylint: disable=unsubscriptable-object
        scope = bottle.request.forms['scope']
        grant_type = bottle.request.forms['grant_type']

        if grant_type != 'client_credentials':
            raise UnsuportedGrantType(grant_type=grant_type)

        expires = time.time() + datetime.timedelta(days=10).total_seconds()
        claims = {
            'iss': self._issuer,
            'sub': 'user',
            'aud': 'client',
            'exp': expires,
            'scope': scope,
        }
        token = jwt.encode(claims, self._private_key, algorithm='RS512')
        return {
            'access_token': token.decode(),
            'expires_in': expires,
            'scope': scope,
            'token_type': 'bearer',
        }


class UnsuportedGrantType(qvarn.BadRequest):
    msg = (
        u'Grant type {grant_type} is not supported. Only client_credentials '
        u'grant type is supported.'
    )
