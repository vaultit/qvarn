# authorization_validator_tests.py - unit tests for AuthorizationValidator
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


private_test_key = '''-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEApbW6bK3hmCGyBAM0RHd7nZMn+/NHOzsd4jJoOcSeJIk9SPnT
m/l/2ycUEEuqyt5hoyABjofZJV8S3RHk/fCaHeb0mvKokhoTXQQKTHOWvUyKKtqV
6YGmwwKD6WEyPSJbEtBVElr5j/YTYco/D0sIrbhUMVSpCIQT/I1ytGOlnLfqHM20
HSQusgtRjkUWkaDCBFHebY5C7CpnHNyd5ApeQC2MiZDSpi67GraMJ4ttbimWRUYA
dsYU11lLlPdpXgwiTeDz8pAsYSajXQVX7WBWnWC11JYMBXcu480eavDNdBTHt++Z
lcWYutGoAK5XTWhRg46jRVOmmHumj3yNh9W+xwIDAQABAoIBAQCX62KNTmB7a7Db
cuCRQIVI8md+2gtc5xa/kHzzMSnWzycrZza0UWoBTfNb+TMMqBIVTjt/I1ZVp7MQ
j95DXTi930YzY/Jdd6B270RN0M7Kn4gwP5OerylmsUCkTmKTn5KlTfAgUt1nOS+N
wLBNYfoD4fD2BOqvDv+P01HsxUpIwO3xEKp6TvkumnbXgDjgyVrGFoYCgSu/7xuX
KnqSRz2KvvukAP0ZkLrT69oCUodv4Ya336yjEGgD7YFlvkHjEl97kwr5ziNuoCer
04iLsKRV2Lj+4oy4HKFdxaGAiENLR4VNrhZDINMBKCe/vgpDXfN6jUCuxdb7ndN9
2l+9eZxpAoGBANVtHQ2fNs/jyaWdvh42BJycZbmcC5xZ78ipSzDZ6IqLzTd85zeW
0a4Roxv4viZncp/WuV1hYigE3uv+qpTLSEzdANfY3SXUUv0q+undcO8huaFNdpgF
DpkQD/uwFxkYdNiD/FWCP9BRUSQM4k468S38OEe93PX1QiTmMcQBfOvdAoGBAMbD
6ufUucu9CB+t6OcDICAboLXvmWKTzUOUraENRwLxn2cdfWmbbKBqxK6xHpusWjYp
qwS4Y+hfXM1flbIGirYjIqkjCdeSY4naVyOo4QqCyPIK9RXwHjysSLi/Kc7LL3KP
yzcEHYIm7UAxlm9VTIgefUhvwA2SVfNxPOykiYzzAoGBAJMS0BSVBQaZqFmyrFLR
UrhBpnATsoSaDX0v/Jq7b14aHN8B+av7CJ91k/swnIiGfRzcsXxCIYwGX0AtjItg
0n/1RCF6Vls9R7sipSoH6U1A5lTbtr/nrDmaMgl1PVWT3uFdgsPCMAt0HgBDyKe0
QoM37eiyU9RCoMQgxWaWx+kZAoGBAMavuxYo/9yYRhGcv06FQky2MU0Mh/ARPMNM
UM/HvO9FZokl4mJ5ufkVISxa4vTMMZUoy8o5I615/gNRhArkHS56KsCVxNXXgGah
ei+sNeBS4dmJeHqIf0E5GqyKcplDZFeJQ6LoGzMqBEkCCJWb15fNmoCZLIqkeASU
ckk/JDxfAoGAHUjRwU36XhH4wKrGd71avRc1nx6OGVuwzyiiZEEaaLPrXg8gJBaR
ec1V6k23+H/CRrzMFGZCIbMNQaxhPxfCaBINHygcZQ4jsIepFxmcDV++Fi/jMHMf
cImjZ9dxwWFeouQhOHalSyCiWWYgHSWw3r4jj/L/h2VjchzMOvJQt6A=
-----END RSA PRIVATE KEY-----'''


public_test_key = '''ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCltbpsreGYIbIEAzREd3
udkyf780c7Ox3iMmg5xJ4kiT1I+dOb+X/bJxQQS6rK3mGjIAGOh9klXxLdEeT98Jod5vSa8qiSGhNdB
ApMc5a9TIoq2pXpgabDAoPpYTI9IlsS0FUSWvmP9hNhyj8PSwituFQxVKkIhBP8jXK0Y6Wct+oczbQd
JC6yC1GORRaRoMIEUd5tjkLsKmcc3J3kCl5ALYyJkNKmLrsatowni21uKZZFRgB2xhTXWUuU92leDCJ
N4PPykCxhJqNdBVftYFadYLXUlgwFdy7jzR5q8M10FMe375mVxZi60agArldNaFGDjqNFU6aYe6aPfI
2H1b7H'''


class AuthorizationValidatorTests(unittest.TestCase):

    def setUp(self):
        self.authorization_validator = unifiedapi.AuthorizationValidator()

    def test_no_authorization_header_errors_raises(self):
        with self.assertRaises(unifiedapi.Unauthorized):
            self.authorization_validator.get_access_token_from_headers({})

    def test_invalid_authorization_header_format_raises(self):
        with self.assertRaises(unifiedapi.Forbidden):
            self.authorization_validator.get_access_token_from_headers({
                'Authorization': 'Fail tokentoken'
            })

    def test_valid_authorization_header_format_returns_token(self):
        token = self.authorization_validator.get_access_token_from_headers({
            'Authorization': 'Bearer tokentoken'
        })
        self.assertEqual(token, 'tokentoken')

    def test_token_validation_with_valid_token(self):
        token = get_valid_token()
        encoded_token = jwt.encode(token, private_test_key, algorithm='RS512')
        result = self.authorization_validator.validate_token(
            encoded_token,
            public_test_key,
            token[u'iss'])
        self.assertEqual(
            result,
            {
                u'scopes': [
                    u'openid',
                    u'person_resource_id',
                    u'uapi_orgs_get', u'uapi_orgs_post'
                ],
                u'user_id': u'useridhash',
                u'client_id':
                    u'@!1E2D.4C48.2272.F616!0001!CC3B.680A!0008!C2A9.C9A2'
            })

    def test_token_validation_with_invalid_issuer(self):
        token = get_valid_token()
        encoded_token = jwt.encode(token, private_test_key, algorithm='RS512')
        with self.assertRaises(unifiedapi.Forbidden):
            self.authorization_validator.validate_token(
                encoded_token,
                public_test_key,
                u'otherissuer')

    def test_token_validation_with_missing_subject(self):
        token = get_valid_token()
        del token[u'sub']
        encoded_token = jwt.encode(token, private_test_key, algorithm='RS512')
        with self.assertRaises(unifiedapi.Forbidden):
            self.authorization_validator.validate_token(
                encoded_token,
                public_test_key,
                token[u'iss'])
