# auth_validator.py - implements authorization header and token validation
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import jwt


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class AuthValidator(object):

    ''' Utilities for handling authorization header and JWT token validation.
    '''

    def get_access_token_from_headers(self, headers):
        ''' Gets access token from headers dict.
        Raises AuthenticationError for missing Authorization header.
        Raises AuthorizationError for invalid Authorization header.
        '''
        # Header has to be present in the form "Authorization: Bearer token"
        if u'Authorization' not in headers:
            raise AuthenticationError()
        auth_header_value = headers[u'Authorization']
        auth_header_values = auth_header_value.split(u' ')
        if not len(auth_header_values) == 2 or \
           not auth_header_values[0].lower() == 'bearer':
            raise AuthorizationError()
        return auth_header_values[1]

    def validate_token(self, access_token, token_validation_key, issuer):
        ''' Validates access token with validation key.
        Raises AuthorizationError on invalid token.

        Token validation result is a dict containing:

        scopes: a list of scope strings that the requester has access to
        client_id: id of the client that the end-user is using
        user_id: id of the end-user
        '''
        try:
            payload = jwt.decode(
                access_token,
                token_validation_key,
                options={
                    # Do not validate audience (we don't know the client_id)
                    u'verify_aud': False
                },
                issuer=issuer)
            # Additionally always require sub field (subject)
            if u'sub' not in payload:
                raise AuthorizationError()
            return {
                u'scopes': payload[u'scope'].split(' '),
                u'user_id': payload[u'sub'],
                u'client_id': payload[u'aud']
            }
        except jwt.InvalidTokenError:
            raise AuthorizationError()
