# auth_check_plugin.py - checks request authorization for accessed scope
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi
import unifiedapi.bottle as bottle


class AuthPlugin(object):

    def __init__(self, token_validation_key, token_issuer):
        self._token_validation_key = token_validation_key
        self._token_issuer = token_issuer
        self._auth_validator = unifiedapi.AuthValidator()

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._check_auth()
            self._check_scope()
            return callback(*args, **kwargs)
        return wrapper

    def _check_auth(self):
        try:
            access_token = self._auth_validator.get_access_token_from_headers(
                bottle.request.headers)
            result = self._auth_validator.validate_token(
                access_token, self._token_validation_key, self._token_issuer)
            bottle.request.environ[u'scopes'] = result[u'scopes']
            bottle.request.environ[u'client_id'] = result[u'client_id']
            bottle.request.environ[u'user_id'] = result[u'user_id']
        except unifiedapi.AuthenticationError:
            raise bottle.HTTPError(status=401)
        except unifiedapi.AuthorizationError:
            raise bottle.HTTPError(status=403)

    def _check_scope(self):
        scopes = bottle.request.environ['scopes']
        if not scopes:
            raise bottle.HTTPError(status=403)
        route_scope = self._get_current_scope()
        if route_scope not in scopes:
            raise bottle.HTTPError(status=403)

    def _get_current_scope(self):
        route_rule = bottle.request.route.rule
        request_method = bottle.request.method
        return unifiedapi.route_to_scope(route_rule, request_method)
