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


import base64
import bottle
import requests
import time
import uuid
from beaker.middleware import SessionMiddleware

class AuthorizationCodeFlowApp(object):

    def __init__(self):
        # Constructor creates the base bottle application
        self._app = bottle.app()
        self._redirect_uri = 'http://127.0.0.1:8080/callback'
        # All these will be provided to API users by Tilaajavastuu
        self._api_url = 'https://hlv3-alpha.tilaajavastuu.io'
        self._client_id = '@!1E2D.4C48.2272.F616!0001!CC3B.680A!0008!49F2.648F'
        self._client_secret = 'dc560868-8b1d-4acb-91c6-96908a9ed0f4'
        self._auth_scope = 'uapi_orgs_get'

    def run(self):
        self.add_routes()
        sessioned_app = SessionMiddleware(self._app, {})
        bottle.run(sessioned_app, host='127.0.0.1', port=8080,
                   reloader=True, debug=True)

    def add_routes(self):
        # All the routes that the web application serves
        self._app.route(path='/', method='GET', callback=self.get_index)
        self._app.route(path='/callback', method='GET',
                        callback=self.process_callback)
        self._app.route(path='/orgs', method='GET', callback=self.get_orgs)

    def get_index(self):
        # Session is needed to store 'state' variable.
        session = bottle.request.environ['beaker.session']
        state = session.get('state')
        # Only generate state if we haven't yet
        if not state:
            state = str(uuid.uuid4())
            session['state'] = state
            session.save()
        # Create the URL for authentication
        auth_url = self._api_url + '/auth/authorize' \
                   + '?scope=' + self._auth_scope \
                   + '&response_type=code' \
                   + '&client_id=' + self._client_id \
                   + '&redirect_uri=' + self._redirect_uri \
                   + '&state=' + state
        return bottle.template('index', auth_url=auth_url)

    def process_callback(self):
        params = bottle.request.params
        session = bottle.request.environ['beaker.session']
        if params.get('state'):
            # Check that the state still matches the one we stored (security)
            if session.get('state') == params.get('state'):
                if params.get('error'):
                    return bottle.template('error',
                                           error=params.get(
                                               'error_description'))
                # Generate basic auth header
                basic_auth_token = 'Basic ' + base64.standard_b64encode(
                    self._client_id + ':' + self._client_secret)
                # Request access token
                r = requests.post(self._api_url + '/auth/token',
                                  data={'grant_type': 'authorization_code',
                                        'redirect_uri': self._redirect_uri,
                                        'code': params.get('code')},
                                  headers={'Authorization': basic_auth_token},
                                  verify=False)
                if r.ok:
                    session['access_token'] = r.json()['access_token']
                    session['token_expiry'] = time.time() \
                                              + r.json()['expires_in']
                    session.save()
                    bottle.redirect('/orgs')
                else:
                    return bottle.template('error',
                                           error=r.json()['error_description'])

        bottle.redirect('/')

    def get_orgs(self):
        session = bottle.request.environ['beaker.session']
        if 'access_token' not in session:
            return bottle.template('error', error='Unauthorized')
        r = requests.get(self._api_url + '/orgs',
                         headers={'Authorization':
                                  'Bearer ' + session.get('access_token')},
                         verify=False)
        if r.ok:
            return bottle.template('list', items=r.json()[u'resources'])
        return bottle.template('error', error=r.text)


app = AuthorizationCodeFlowApp()
app.run()
