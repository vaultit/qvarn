import requests

import unifiedapi.bottle as bottle


class AuthCheckPlugin(object):

    def __init__(self, introspection_url):
        self._introspection_url = introspection_url

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._check_authorization()
            return callback(*args, **kwargs)
        return wrapper

    def _check_authorization(self):
        access_token = self._get_access_token()
        scopes = self._get_authorised_scopes(access_token)
        # TODO add user id
        bottle.request.environ.set('scopes', scopes)

    def _get_access_token(self):
        if not u'Authorization' in bottle.request.headers:
            raise bottle.HTTPError(status=401)
        auth_header_value = bottle.request.headers[u'Authorization']
        auth_header_values = auth_header_value.split(u' ')
        if not len(auth_header_values) == 2 or \
           not auth_header_values[0].lower() == 'bearer':
            raise bottle.HTTPError(status=403)
        return auth_header_values[1]

    def _get_authorised_scopes(self, access_token):
        # TODO verify
        response = requests.get(
            self._introspection_url,
            params={u'token': access_token},
            headers={u'Authorization': u'Bearer ' + access_token},
            verify=False)
        if not response.status_code == 200:
            raise bottle.HTTPError(status=403)
        response_content = response.json()
        return response_content[u'scope'].split(' ')
