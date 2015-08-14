# TODO

Käyttäjätunnukset gluuhun kaikille + person resource id.

# Web application utilizing OAuth 2.0 Authorization Code flow

Application uses [bottle]() web framework and [Beaker]() for session
management (cookies). Additionally we will be making the HTTP requests
with [requests]() library.

Application is tested on Debian 8.1, codename Jessie. Debian packages needed
are `python-requests`, `python-bottle` and `python-beaker`.

The most important objects or methods (and their attributes or arguments) used
here are:

Bottle's request class which is available in global `bottle.request` variable.
`bottle.request.params` contains a dictionary of query parameters.
`bottle.request.environ['beaker.session']` contains a dictionary of variables
stored in the session cookie. Session dictionary can be saved after changes
with `.save()` method.

Bottle's template method `bottle.template()`.
First argument is a string which is the template name. Templates are used
by default from `views/TEMPLATE_NAME.tpl`. Method takes other named arguments
(in form `key=value`) that can be used in the template.

Bottle application's route method. Takes (named) arguments `path` (what the
  web app listens to), `method` (what HTTP method it listens to) and `callback` (what function is used to handle the request).

Requests library's post method. Makes a HTTP POST request to an url given as
the first argument. Data sent in the request body is defined with `data`
argument as a dictionary (sent as `application/x-www-form-urlencoded` by
  default). Headers are defined with `headers` arguments also as a dictionary.
  As we are making the requests to a test server with a self signed certificate we need also to set `verify` argument to false (do not use in
    production).

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

Let's fill the callback method. We need to grab the store `state` from session. We also need the query parameters.

    def process_callback(self):
          params = bottle.request.params
          session = bottle.request.environ['beaker.session']

Only handle the request if query params contain `state`. Check for an error
status and show an error page if the authentication was unsuccessful.

    if params.get('state'):
        if params.get('error'):
                    return bottle.template('error',
                                           error=params.get(
                                               'error_description'))

views/index.tpl:

    {{error}}

 Otherwise check that the states match.

authorization_code_flow_webapp.py:

        # Check that the state still matches the one we stored (security)
        if session.get('state') == params.get('state'):

Now we are ready to make the access token request. Create the basic
authorization header contents.

    # Generate basic auth header
    basic_auth_token = 'Basic ' + base64.standard_b64encode(
        self._client_id + ':' + self._client_secret)

Make the request!

Parameters

* `grant_type` --- **Required.** Value must be `authorization_code` when
  using authorization code flow.
* `redirect_uri` --- **Required.** This URI must match the redirect URI
  where end-user's browser was redirected after successful
  authentication and authorization.
* `code` --- **Required.** Authorization code received from the
  authorization server.


    # Request access token
    r = requests.post(self._api_url + '/auth/token',
                      data={'grant_type': 'authorization_code',
                            'redirect_uri': self._redirect_uri,
                            'code': params.get('code')},
                      headers={'Authorization': basic_auth_token},
                      verify=False)

If everything went well, save the access token to session.

    if r.ok:
        session['access_token'] = r.json()['access_token']
        session['token_expiry'] = time.time() \
                                  + r.json()['expires_in']
        session.save()
        bottle.redirect('/orgs')

Otherwise show an error page.

    else:
        return bottle.template('error',
                               error=r.json()['error_description'])

At the end of the method just redirect users away from the callback.

    bottle.redirect('/')

### We add organisation id listing

Add the route.

    def add_routes(self):
        # All the routes that the web application serves
        self._app.route(path='/', method='GET', callback=self.get_index)
        self._app.route(path='/callback', method='GET',
                        callback=self.process_callback)
        self._app.route(path='/orgs', method='GET', callback=self.get_orgs)

    def get_orgs(self):
        pass

We need the session once again.

        session = bottle.request.environ['beaker.session']

Show an error if the access token is missing.

    if 'access_token' not in session:
        return bottle.template('error', error='Unauthorized')

Otherwise we can just request the organisations and show them on the page.

    r = requests.get(self._api_url + '/orgs',
                     headers={'Authorization':
                              'Bearer ' + session.get('access_token')},
                     verify=False)
    if r.ok:
        return bottle.template('list', items=r.json()[u'resources'])
    return bottle.template('error', error=r.text)

views/list.tpl:

    <ul>
      % for item in items:
      <li>{{item[u'id']}}</li>
      % end
    </ul>
