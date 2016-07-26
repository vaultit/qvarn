# authorization_validator.py - implements authorization header and token
#                              validation
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


import datetime

import jwt
import bottle

import qvarn


class AuthorizationValidator(object):

    '''Validate request headers and JWT access token.

    Separated from AuthorizationPlugin for easier testing. No need to
    mock global bottle.request.

    '''

    def get_access_token_from_headers(self, headers):
        '''Get access token from headers dict.'''

        # Header has to be present in the form "Authorization: Bearer token"
        if u'Authorization' not in headers:
            raise AuthorizationHeaderMissing()

        authorization_header_value = headers[u'Authorization']
        authorization_header_values = authorization_header_value.split(u' ')
        if len(authorization_header_values) != 2 or \
           not authorization_header_values[0].lower() == 'bearer':
            raise InvalidAuthorizationHeaderFormat()

        return authorization_header_values[1]

    def validate_token(self, access_token, token_validation_key, issuer):
        '''Validate access token with validation key.

        Token validation result is a dict containing:

        scopes: a list of scope strings that the requester has access to
        client_id: id of the client that the end-user is using
        user_id: id of the end-user

        '''

        try:
            payload = self._decode_token(
                access_token, token_validation_key, issuer)
            self._check_token_subject(payload)
        except InvalidAccessTokenError:
            bottle.response.headers['WWW-Authenticate'] = \
                'Bearer error="invalid_token"'
            raise

        return {
            u'scopes': payload[u'scope'].split(' '),
            u'user_id': payload[u'sub'],
            u'client_id': payload[u'aud']
        }

    def _decode_token(self, access_token, token_validation_key, issuer):
        '''Return decoded access token.'''
        try:
            return jwt.decode(
                access_token,
                token_validation_key,
                options={
                    # Do not validate audience (we don't know the client_id)
                    u'verify_aud': False
                },
                issuer=issuer,
                algorithms=[u'RS512'],
                # Leeway for time checks (issued at, expiration)
                leeway=datetime.timedelta(seconds=60),
            )
        except jwt.InvalidTokenError, e:
            qvarn.log.log(
                'error',
                msg_text='Access token is invalid: jwt.decode')
            raise InvalidAccessTokenError(token_error=unicode(e))

    def _check_token_subject(self, payload):
        # Always require sub field (subject).
        if u'sub' not in payload:
            qvarn.log.log('error', msg_text='Access token has no sub field')
            raise InvalidAccessTokenError(
                token_error=u'Invalid subject (sub)')


class AuthorizationHeaderMissing(qvarn.Unauthorized):

    msg = u'Authorization header is missing'


class InvalidAuthorizationHeaderFormat(qvarn.Forbidden):

    msg = u'Authorization header is in invalid format'


class InvalidAccessTokenError(qvarn.Unauthorized):

    msg = u'Access token is invalid: {token_error}'
