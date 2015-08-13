# TODO

Käyttäjätunnukset gluuhun kaikille + person resource id.

# Web application utilizing OAuth 2.0 Authorization Code flow

Application uses [bottle]() web framework and [Beaker]() for session
management (cookies). Additionally we will be making the HTTP requests
with [requests]() library.

Application is tested on Debian 8.1, codename Jessie. Debian packages needed
are `python-requests`, `python-bottle` and `python-beaker`.

#### We start by implementing a web application that serves the client (browser) an index page with `Hello!`.

authorization_code_flow_webapp.py:

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

        def get_index(self):
            return bottle.template('index')


    app = AuthorizationCodeFlowApp()
    app.run()


views/index.tpl:

    Hello!

Visit the page http://127.0.0.1:8080/ and it should display a page with
`Hello!`.

#### We create the redirect url and display it on the index page as a link.

authorization_code_flow_webapp.py:

For the redirect url we need to generate the state parameter:

    def get_index(self):
        # Session is needed to store 'state' variable.
        session = bottle.request.environ['beaker.session']
        state = session.get('state')
        # Only generate state if we haven't yet
        if not state:
            state = str(uuid.uuid4())
            session['state'] = state
            session.save()
        return bottle.template('index')

After that we can create the authentication url and give it to the view.

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

Parameters are described in the authentication documentation:

* `scope` --- **Optional.** Contain scope values that the client application is
  requesting access to, e.g. `uapi_orgs_post`. Values are separated with
  spaces.
* `response_type` --- **Required.** Value must be `code` when using
  authorization code flow.
* `client_id` --- **Required.** Client application's unique client
  identifier.
* `redirect_uri` --- **Required.** Response will be sent to this URI. This
  URI must match one of the redirect URI values registered for the client.
* `state` --- **Required.** Unique random string that is used to maintain
  session between the request and the callback. CSRF mitigation is
  done by binding the value to browser cookie and validating the state
  in callback.

views/index.tpl:

We show the given url in the index view as a link.

    <a href="{{auth_url}}">Sign in!</a>

Visit the page http://127.0.0.1:8080/ and you should now be able to click the
link and see a login page after clicking it.

#### We add callback path listener to our application.

Next we need a callback path listener to grab the code query parameter and
request access token.

authorization_code_flow_webapp.py:

    def add_routes(self):
        # All the routes that the web application serves
        self._app.route(path='/', method='GET', callback=self.get_index)
        self._app.route(path='/callback', method='GET',
                        callback=self.process_callback)

    def process_callback(self):
      pass


#### We create add session management to our application, store the state parameter and verify it in callback.
