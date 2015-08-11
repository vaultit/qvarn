import bottle

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
        return bottle.template('index')

    
app = AuthorizationCodeFlowApp()
app.run()
