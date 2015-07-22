# auth_validator_tests.py - unit tests for AuthValidator
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest
import jwt
import time

import unifiedapi


def get_valid_token():
    now = time.time()
    return {
        u'oxValidationURI': u'https://gluu.tilaajavastuu.io/oxauth/opiframe',
        u'oxOpenIDConnectVersion': u'openidconnect-1.0',
        u'c_hash': u'dSxmNqq0uc7rT-c0qgr276hH-yUaW9HMaKY-2xyBM90',
        u'aud': u'@!1E2D.4C48.2272.F616!0001!CC3B.680A!0008!C2A9.C9A2',
        u'sub': u'useridhash',
        u'iss': u'https://gluu.tilaajavastuu.io',
        u'exp': now + 3600,
        u'auth_time': now - 60,
        u'iat': now - 120,
        u'scope': u'openid person_resource_id uapi_orgs_get uapi_orgs_post'
    }


class AuthValidatorTests(unittest.TestCase):

    def setUp(self):
        self.auth_validator = unifiedapi.AuthValidator()

    def test_no_authorization_header_errors_raises(self):
        with self.assertRaises(unifiedapi.AuthenticationError):
            self.auth_validator.get_access_token_from_headers({})

    def test_invalid_authorization_header_format_raises(self):
        with self.assertRaises(unifiedapi.AuthorizationError):
            self.auth_validator.get_access_token_from_headers({
                'Authorization': 'Fail tokentoken'
            })

    def test_valid_authorization_header_format_returns_token(self):
        token = self.auth_validator.get_access_token_from_headers({
            'Authorization': 'Bearer tokentoken'
        })
        self.assertEqual(token, 'tokentoken')

    def test_token_validation_with_valid_token(self):
        secret = u'secret'
        token = get_valid_token()
        encoded_token = jwt.encode(token, secret, algorithm='HS512')
        self.auth_validator.validate_token(
            encoded_token,
            secret,
            token[u'iss'])

    def test_token_validation_with_invalid_issuer(self):
        secret = u'secret'
        token = get_valid_token()
        encoded_token = jwt.encode(token, secret, algorithm='HS512')
        with self.assertRaises(unifiedapi.AuthorizationError):
            self.auth_validator.validate_token(
                encoded_token,
                secret,
                u'otherissuer')

    def test_token_validation_with_missing_subject(self):
        secret = u'secret'
        token = get_valid_token()
        del token[u'sub']
        encoded_token = jwt.encode(token, secret, algorithm='HS512')
        with self.assertRaises(unifiedapi.AuthorizationError):
            self.auth_validator.validate_token(
                encoded_token,
                secret,
                token[u'iss'])
