# Web application utilizing OAuth 2.0 Authorization Code flow

Application uses [bottle]() web framework and [Beaker]() for session
management (cookies). Additionally we will be making the HTTP requests
with [requests]() library.

Application is tested on Debian 8.1, codename Jessie. Debian packages needed
are `python-requests`, `python-bottle` and `python-beaker`.

#### We start by implementing a web application that serves the client (browser) an index page with `Hello!`.

authorization_code_flow_webapp.py:

    import bottle


    class AuthorizationCodeFlowApp(object):

      def __init__(self):
        # Constructor creates the base bottle application
        self._app = bottle.app()

      def run(self):
        self.add_routes()
        bottle.run(self._app, host='127.0.0.1', port=8080, reloader=True, debug=True)

      def add_routes(self):
        # All the routes that the web application serves
        self._app.route(path='/', method='GET', callback=self.index)

      def index(self):
        return bottle.template('index')


    app = AuthorizationCodeFlowApp()
    app.run()

views/index.tpl:

    Hello!

Visit the page http://127.0.0.1:8080/ and it should display a page with `Hello!`.

#### We create the redirect url and display it on the index page as a link.

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

As we are generating the random state string with uuid we need to add an import. We end up with:

    import bottle
    import uuid


    class AuthorizationCodeFlowApp(object):

        def __init__(self):
            # Constructor creates the base bottle application
            self._app = bottle.app()

        def run(self):
            self.add_routes()
            bottle.run(self._app, host='127.0.0.1', port=8080,
                       reloader=True, debug=True)

        def add_routes(self):
            # All the routes that the web application serves
            self._app.route(path='/', method='GET', callback=self.get_index)

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


Visit the page http://127.0.0.1:8080/ and you should now be able to click the link and see a login page after clicking it.

#### We add callback path listener to our application.

#### We create add session management to our application, store the state parameter and verify it in callback.
