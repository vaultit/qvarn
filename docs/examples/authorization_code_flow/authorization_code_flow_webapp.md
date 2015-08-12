# Web application utilizing OAuth 2.0 Authorization Code flow

Application uses [bottle]() web framework and [Beaker]() for session
management (cookies).

Debian packages needed are `python-bottle` and `python-beaker`.

#### We start by implementing a web application that serves the client (browser) an index page with `Hello!`.

authorization_code_flow_webapp.py:

    import bottle

    class AuthorizationCodeFlowApp(object):

      def __init__(self):
        self._app = bottle.app()

      def run(self):
        self.add_routes()
        bottle.run(self._app, host='127.0.0.1', port=8080, reloader=True, debug=True)

      def add_routes(self):
        self._app.route(path='/', method='GET', callback=self.index)

      def index(self):
        return bottle.template('index')

    app = AuthorizationCodeFlowApp()
    app.run()

views/index.tpl:

    Hello!

Visit the page http://127.0.0.1/ and it should display a page with `Hello!`.

#### Next we create the redirect url and display it on the index page as a link.

authorization_code_flow_webapp.py:

In method get_index we create the authentication url and give it to the view.

    def get_index(self):
        auth_url = 'https://gluu.tilaajavastuu.io/' \
                   + 'oxauth/seam/resource/restv1/oxauth/authorize' \
                   + '?scope=uapi_orgs_get uapi_orgs_id_get' \
                   + '&response_type=code' \
                   + '&client_id=XXXXXXXXXXXXXXXXXXX' \
                   + '&redirect_uri=127.0.0.1:8080/callback' \
                   + '&state=' + str(uuid.uuid4())
        return bottle.template('index', auth_url=auth_url)

As we are generating the random state string with uuid we need to add an import. We end up with:

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

views/index.tpl:

We show the given url in the index view as a link.

    <a href="{{auth_url}}">Sign in!</a>

Visit the page http://127.0.0.1/ and you should now be able to click the link and see a login page after clicking it.
