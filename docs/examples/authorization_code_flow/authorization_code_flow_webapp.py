import bottle
import uuid

class AuthorizationCodeFlowApp(object):

    def __init__(self):
        self._app = bottle.app()

    def run(self):
        self.add_routes()
        bottle.run(self._app, host='127.0.0.1', port=8080,
                   reloader=True, debug=True)

    def add_routes(self):
        self._app.route(path="/", method="GET", callback=self.get_index)

    def get_index(self):
        auth_url = 'https://gluu.tilaajavastuu.io/' \
                   + 'oxauth/seam/resource/restv1/oxauth/authorize' \
                   + '?scope=uapi_orgs_get uapi_orgs_id_get' \
                   + '&response_type=code' \
                   + '&client_id=XXXXXXXXXXXXXXXXXXX' \
                   + '&redirect_uri=127.0.0.1:8080/callback' \
                   + '&state=' + str(uuid.uuid4())
        return bottle.template('index', auth_url=auth_url)

    
app = AuthorizationCodeFlowApp()
app.run()
