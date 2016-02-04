# authorization_plugin.py - checks request authorization
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi
import bottle


class AuthorizationPlugin(object):

    def __init__(self, token_validation_key, token_issuer):
        self._token_validation_key = token_validation_key
        self._token_issuer = token_issuer
        self._authz_validator = unifiedapi.AuthorizationValidator()

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._check_auth()
            self._check_scope()
            return callback(*args, **kwargs)
        return wrapper

    def _check_auth(self):
        access_token = self._authz_validator.get_access_token_from_headers(
            bottle.request.headers)
        result = self._authz_validator.validate_token(
            access_token, self._token_validation_key, self._token_issuer)
        bottle.request.environ[u'scopes'] = result[u'scopes']
        bottle.request.environ[u'client_id'] = result[u'client_id']
        bottle.request.environ[u'user_id'] = result[u'user_id']

    def _check_scope(self):
        scopes = bottle.request.environ['scopes']
        route_scope = self._get_current_scope()
        if not scopes or route_scope not in scopes:
            bottle.response.headers['WWW-Authenticate'] = \
                'Bearer error="insufficient_scope"'
            raise NoAccessToRouteScope(route_scope=route_scope)

    def _get_current_scope(self):
        route_rule = bottle.request.route.rule
        request_method = bottle.request.method
        return unifiedapi.route_to_scope(route_rule, request_method)


class NoAccessToRouteScope(unifiedapi.Forbidden):

    msg = u'No access to route scope'
