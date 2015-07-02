import requests

import unifiedapi.bottle as bottle


class AuthPlugin(object):

    def __init__(self, introspection_url):
        self._introspection_url = introspection_url

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._check_authorisation()
            return callback(*args, **kwargs)
        return wrapper

    def _check_authorisation(self):
        if not u'Authorization' in bottle.request.headers:
            raise bottle.HTTPError(status=401)
        auth_header_value = bottle.request.headers[u'Authorization']
        auth_header_values = auth_header_value.split(u' ')
        if not len(auth_header_values) == 2 or not auth_header_values[0].lower() == 'bearer':
            raise bottle.HTTPError(status=403)
        access_token = auth_header_values[1]
        # TODO remove verify = False
        r = requests.get(self._introspection_url, params={u'token': access_token}, headers={u'Authorization': u'Bearer ' + access_token}, verify=False)
        if not r.status_code == 200:
            raise bottle.HTTPError(status=403)
