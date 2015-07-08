import re

import unifiedapi.bottle as bottle


class AuthScopePlugin(object):

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._check_scope()
            return callback(*args, **kwargs)
        return wrapper

    def _check_scope():
        scopes = bottle.request.environ.get('scopes')
        if not scopes:
            raise bottle.HTTPError(status=403)
        route_scope = self._get_current_scope()
        if route_scope not in scopes:
            raise bottle.HTTPError(status=403)

    def _get_current_scope(self):
        route_rule = bottle.request.route.rule
        # Replace <xx> with id, non greedy (?) so we don't replace <xx>XX<xx>.
        # TODO search
        route_scope = re.sub(r'<.+?>', 'id', route_rule)
        route_scope = route_scope.replace(u'/', u'_')
        route_scope = u'uapi%s_%s' % (route_scope, bottle.request.method)
        return route_scope.lower()
