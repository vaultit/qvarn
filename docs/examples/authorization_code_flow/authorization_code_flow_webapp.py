import bottle
import uuid
from beaker.middleware import SessionMiddleware

class AuthorizationCodeFlowApp(object):

    def __init__(self):
        # Constructor creates the base bottle application
        self._app = bottle.app()
        self._client_id = '@!1E2D.4C48.2272.F616!0001!CC3B.680A!0008!49F2.648F'
        self._client_secret = 'dc560868-8b1d-4acb-91c6-96908a9ed0f4'
        self._redirect_uri = 'http://127.0.0.1:8080/callback'
        self._auth_scope = 'uapi_orgs_get uapi_orgs_id_delete ' \
                           + 'uapi_orgs_id_get uapi_orgs_id_put uapi_orgs_post'

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

    def get_index(self):
        # Access the session for state variable
        session = bottle.request.environ['beaker.session']
        state = session.get(u'state')
        if not state:
            state = unicode(uuid.uuid4())
            session[u'state'] = state
            session.save()
        # Create the URL for authentication
        auth_url = 'https://hlv3-alpha.tilaajavastuu.io/' \
                   + 'oxauth/seam/resource/restv1/oxauth/authorize' \
                   + '?scope=' + self._auth_scope \
                   + '&response_type=code' \
                   + '&client_id=' + self._client_id \
                   + '&redirect_uri=' + self._redirect_uri \
                   + '&state=' + state
        return bottle.template('index', auth_url=auth_url)

    def process_callback(self):
        params = bottle.request.params
        session = bottle.request.environ['beaker.session']
        if session.get(u'state'):
            if session.get(u'state') == params.get(u'state'):
                '''r = requests.post'''
                pass


app = AuthorizationCodeFlowApp()
app.run()
