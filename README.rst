README for Qvarn
================

.. default-role:: literal

This source tree contains an implementation of the Qvarn RESTful
HTTPS+JSON backend for the services originally developed by Suomen
Tilaajavastuu Oy and now maintained and further developed by QvarnLabs
AB. For details of the API, see documentation in the
`docs/qvarn-api-doc` directory.

This README contains an introduction to the code, aimed at the people
who develop and/or deploy the code.

Overview
--------

Qvarn stores structured data annd provides secure, controlled access to
it. A gross simplification would be that Qvarn is a database, accessed
over a RESTful HTTP API, with a good authentication and authorization
system.

Qvarn deals with data in JSON form and is used by applications via an
HTTP API, with access control using OpenID Connect and OAuth2. Various
authentication methods, including strong ones, are provided by
Gluu_ and these can be added and adapted for local needs.

The resource types Qvarn knows about are configurable (via YAML files
in `resource_type/*.yaml` and installed as `/etc/qvarn/*.yaml`),
making Qvarn suitable to various application domains. Applications may
be written in any language, using any framework, as long as they can
use HTTP over TLS.

.. _Gluu: https://www.gluu.org/


Development environment
-----------------------

You need various tools to develop and/or run the software.

- pycodestyle_ and pylint_ static checkers for Python code. (Debian
  packages have those names.)

- flup_, an implementation of the Python Web Server Gateway
  Interface. Debian package is `python-flup`.

- PyJWT_, JWT token encoding and decoding tools. Debian package is
  `python-jwt`.

- python-cryptography_, Python cryptography tools. Debian package is
  `python-cryptography`.

- Bottle_, Python Web Framework. Debian package is `python-bottle`.

Most of these tools are installed automatically, the only thing you need to do
is to run `make`.

Unfortunatelly some tools are not available on pypi.org, you need to download
those packages manually and run `PIP_EXTRA_INDEX_URL=path/to/index make` in
order for things to work.

Here is the list of packages that are not available in pypi.org:

- http://git.liw.fi/cmdtest/

- http://git.liw.fi/cliapp/

- http://git.liw.fi/ttystatus/

.. _coverage.py: https://coverage.readthedocs.io/
.. _pycodestyle: https://pypi.org/p/pycodestyle/
.. _pylint: https://www.pylint.org/
.. _flup: https://www.saddi.com/software/flup/
.. _PyJWT: https://github.com/jpadilla/pyjwt/
.. _python-cryptography: https://cryptography.io/
.. _Bottle: https://bottlepy.org/

Once `make` successfuly done its job, you can run qvarn using `qvarn-run`
command.

By default `qvarn-run` expects a running postgres database under localhost with
`qvarn` as user, password and database name. You run get this using Docker::

  $ docker run --rm --name qvarn-postgres -p 5432:5432 \
        -e POSTGRES_PASSWORD=qvarn \
        -e POSTGRES_USER=qvarn \
        -e POSTGRES_DB=qvarn \
        -d postgres:9.4-alpine

Once database is running, you need to create database tables::

  $ qvarn-run --prepare-storage

And then you can run Qvarn::

  $ qvarn-run

By default `qvarn-run` pick a random available port and uses a temporary
directory where dinamically generated configuration and keys are stored. And
alsy, by default `qvarn-run` uses `./resource_type` for resource type
definitions.

You can specify a port, base directory and specdir like this::

  $ qvarn-run --port 9000 -d /tmp/qvarn -r my/restypes

Also you can override all Qvarn configuration variables using environment
variables (`QVARN_<section>_<option>=<value>`) and command line flags (`-o
<section>.<option>=<value>`). See Configuration_ section for more information.

`qvarn-run` uses uWSGI for running Qvarn with self-signed SSL certificate. Be
aware that `qvarn-run` uses only HTTPS and there is no HTTP option.

By default `qvarn-run` logs everyting to stdout, but you can change that with
`--logto` option.

You can use `--daemonize` to run Qvarn in background. If `--logto` is not
specified logs will be written to `--base-dir` under `uwsgi.log` filename.

By default `qvarn-run` automatically generated RSA key pair and uses those keys
to create and validate access tokens. This way, you can use Qvarn without Gluu.
You can get access token using this command::

  $ qvarn-run --port 9000 -d /tmp/qvarn --daemonize

  $ http -f :9000/auth/token grant_type=client_credentials scope=uapi_orgs_get

Also for your convinience, access token with all available scopes is generated
automatically and you can find it in base dir under `token` file name. Since
all available scopes are included, this token can be quite large.

If like, you can run Qvarn with Gluu by using `--gluu` flag, for example::

  $ qvarn-run --gluu https://gluu.example.com

In this case RSA keys will not be generated and the only way to get access
token is through Gluu. For example::

  $ http -f -a 'clientid:secret' https://gluu.example.com//auth/token \
         grant_type=client_credentials scope=uapi_orgs_get

There is also an option to run Qvarn using SQLite database, but this option is
not fully compatible, so use it at your own risk. To run Qvarn with SQLite::

  $ qvarn-run -o database.type=sqlite

This command will automatically creates database file in base dir under
`sqlite.db` name. You can change it with `-o database.file=path/to.db`.


Building and running unit tests
-------------------------------

The code is pure Python, and as such does not need building. However,
the `./check` script runs unit tests, and the static Python checkers
`pycodestyle` and `pylint`.

Before merging into the integration branch, `./check` must pass.

There is also `make test` option, that will take care of all the dependencies
need in order to run tests.

There is also a `tox.ini` that allows you to use `tox` to run the tests against
multiple Python versions (including multiple Python 3 versions -- `make test`
currently tests only one Python 2 and one Python 3 version).


Integration tests
-----------------

The API document contains integration tests ("yarns"). These are run from the
`docs/qvarn-api-doc` directory, but there is `make test-postgres`, that
automates whole thing by using `qvarn-run` command and `run-yarn-tests` script.

Running integration tests on Python 3 can be done with `make test-postgres-py3`.
And you can run both with `make test-postgres-all`.

Also you can run `make test-sqlite` in order to run tests with SQLite database,
but at the moment some tests fail, because SQLite backend is not fully
supported and is mainly used for testing purposes.

Also you can run yarn tests using a remote Qvarn and Gluu, in order to do this,
first you need to create `~/.config/qvarn/createtoken.conf` with contents like
this:

.. code-block:: ini

    [https://qvarn.example.com]
    client_id = G00G00G000
    client_secret = thisisveryverysecrethushhush

In other words, it's an INI file with a section named after the URL of
the Qvarn instance that runs (not the associated Gluu instance). The
client id and secret are set up in the Gluu instance associated with
the API instance.

Then you can run integration tests like this::

    cd docs/qvarn-api-doc
    ./test-api https://qvarn.example.com

where `qvarn.example.com` is the Qvarn API instance being tested.

See the documentation for `yarn` for more options. `yarn` is part of
the `cmdtest` package (see `home page <http://liw.fi/cmdtest/>`_). You
need at least version 0.27.


Writing unit tests
------------------

Unit tests are run using `py.test`. It can be found at
https://pytest.org/.


Coding style
------------

Qvarn is written in a common language subset of Python 2 and Python 3
(the `six` module helps with that).

Code must be formatted according to PEP8_. The `./check` script
runs a tool to check for many formatting and other style details.

.. _PEP8: https://www.python.org/dev/peps/pep-0008/

Code must be kept clean. The `./check` script runs `pylint` to check
for many mistakes; it can also find some actual errors, such as
missing parameters. However, `pylint` is sometimes over-eager in its
checks, and so `./check` turns off some warnings. The script documents
the reasons for those.

Any strings that are meant for containing text, both literals and
values, MUST be Unicode strings. That means literals should be in the
form of `u'this is Unicode'`, with the leading `u`.


Implementation architecture
---------------------------

The backend consists of the `qvarn-backend` program. It handles all
resource types. Most of the code is in a Python library `qvarn`,
containing the following major classes:

- `BackendApplication` --- the main program of the application:
  command line parsing, starting of the HTTP server. This class is
  parameterised, not subclassed. The main parameters are the resources
  to serve, and the the routes that the resource provides.

- `ListResource`, `SimpleResource` --- classes to provide the two
  kinds of resources. `ListResource` provides code for resources that
  manage a set of items (such as persons or organisations). Such
  resources are mostly identical to each other, except for details
  such as item type and allowed fields. `SimpleResource` provides for
  simpler resources such as `/version`. Both these classes are
  parameterised, instead of subclassed.

- `Database` --- all the code talking directly to the database; this
  provides a fairly light abstraction providing only the functionality
  we use (or are meant to use).

- `ReadOnlyStorage`, `WriteOnlyStorage` --- store and retrieve simple
  Python dictionary objects representing the kinds of items that the
  API deal with. Basically, these are very trivial ORMs that map
  JSON-like Python objects into rows in relation databases. Reading
  and writing are kept explicitly separate to implement an
  architecture where writes all go into one database instance, which
  gets replicated to any number of read-only databases. By keeping the
  classes separate, it is slightly difficult to accidentally write to
  the wrong place.

- `StoragePreparer` --- manage database schemas and migrations. The
  class maintains a sequence of preparation steps. Every time we make
  a schema change, we add another step, which makes the relevant
  changes: adds or removes tables or columns, and fills new columns
  and tables with the correct data. Every database instance goes
  through the same sequence, even if it is brand new. This should
  guarantee we can always migrate to a newer version, with minimal
  manual intervention.

- `ItemValidator` --- validate that an API item (JSON-like Python
  object) is at least minimally valid. This happens by matching the
  item against a prototype item, and making sure all fields are there,
  and have values of the right type. This parameterised class provides
  generic validation; additional validation is then applied per item
  type, as needed.

In addition, there are a few auxiliary classes and functions. For the
full details, please read the source code and embedded docstrings. (If
the code too hard to read, that's a bug that needs fixing.)


On databases
------------

We have a simple approach to databases. They are used as stupid
storage with lookup. We do not use constraints, triggers, stored
functions, or other database smarts, because such things are harder to
understand and to verify than real code. The `Database` class reflects
this, as does the overall system architecture, which has been designed
to not need much intelligence from the database layer.


Source code layout
------------------

Most of the code is in the `qvarn` library. This library is unit
tested.

The `debian` directory has the files needed to build Debian (`.dsc`
and `.deb`) packages.


Building Debian packages
------------------------

You need to build Debian packages in a Debian system (or a system
sufficiently like Debian; Ubuntu probably works). You need at least
the following packages installed:

- `build-essential` - all the basic development tools, such as C and
  C++ compilers and development libraries

- `debhelper` - a packaging helper utility, which makes packaging
  much easier

- `python-all` - all Python versions (packaging is a little simpler
  if they're all installed)

- `devscripts` - supplies the `dch` and `debuild` tools.

(This list may be inadequate. If you notice a problem, please change
the list.)

Make sure the `DEBEMAIL` environment variable holds your e-mail
address (`foo.bar@example.com`). Set it in your `.bashrc` or other
suitable place.

To prepare and build Debian packages:

1. If you've made any changes, update `debian/changelog`:

   1. `dch -v X.Y-Z This is a summary of my change.` (where X.Y-Z is
       the new version number).
   2. `dch -r ''` (replaces UNRELEASED in the first line).

2. `debuild -us -uc` (the options prevent digital signatures from
   being created).


A deployed system
-----------------

The deployed system, as installed from the Debian package, looks like
this:

- The Python library `qvarn` is installed in the usual location
  for such, in Debian: `/usr/lib/python2.7/dist-packages/qvarn`.

- The backend application is installed in `/usr/bin`.

- The backend application is started by `uwsgi`, which is configured
  via `/etc/uwsgi`.

- The `haproxy` load balancer is used to direct HTTP requests from the
  external network interface to the right localhost port. The
  `haproxy` config is configured using external means (e.g., Ansible).

- There are several log files involved:

  - `/var/log/haproxy.log`
  - `/var/log/uwsgi/*/*`
  - `/var/log/qvarn/qvarn.log*`

- All services run as the `www-data` user and `www-data` group.


Configuration
-------------

Qvarn can be configured via:

- configuration file

- environment variables

- command line arguments

These configuration options are listed in the same order as they are read.
Configuration options at the bottom overrides preceding parameters.

Available configuration options:

.. code-block:: ini

  [main]
  specdir = /etc/qvarn
  log-max-files = 10
  log-max-bytes = 10240
  log = syslog
  enable_access_log = false
  access_log_entry_chunk_size = 300

  [database]
  type = postgres
  host = localhost
  port = 5432
  name = qvarn
  user = qvarn
  password = qvarn
  readonly = false
  minconn = 1
  maxconn = 5
  file =

  [auth]
  token_issuer =
  token_validation_key =
  token_private_key_file = 

All these configuration options can be overriden using environment variables,
for example `QVARN_SPECDIR`, `QVARN_DATABASE_NAME`. Environment variable names
are constructed using `QVARN_<scetion>_<option>` pattern.  Section `[main]` can
be ommited, for example `QVARN_SPECDIR`.

All configuration and environment variables can be overrided by `qvarn-backend`
script command line options. For example::

  qvarn-backend \
      --config /etc/qvarn/qvarn.conf \
      -o main.specdir=/etc/qvarn/resources \
      -o database.name=qvarn2

`--config` option also can be specified using `QVARN_CONFIG` environment
variable.


Available configuration parameters
----------------------------------

**main.access_log_entry_chunk_size**
    Number of objects put into single log entry. For example, if user receives
    900 resources, then if `main.access_log_entry_chunk_size` is 300, then 3
    log entries will be created, each containing 300 accessed ids.

    Log consumer backend can limit size of single log entry, so you need to set
    this value close to allowed maximum in order to increase performance.


Extensions
----------

Extensions can be configured like this:

.. code-block:: ini

  [extension:myapp1]
  endpoint = http://extensions:9100/myapp1

  [extension:myapp2]
  endpoint = http://extensions:9100/myapp2

Required scopes example::

  uapi_ext_myapp1_query_get
  uapi_ext_myapp2_query_get

API call example::

  /ext/myapp1/query
  /ext/myapp2/query

Qvarn in this case works as a proxy. Qvarn accepts `/ext/<extension>/<query>`,
checks access rights using `uapi_ext_<extension>_<query>_get` scope and if
everything is ok, then calls extension endpoint with the same parameters. Then
reads response from extension endpoint, logs what data was returned and returns
it to the client.

Extensions are configured per extensions, not per query. Once you defined
extension endpoint in Qvarn configuration, extension can expose multiple
queries, without changing Qvarn configuration. Each query still requires new
scope.

You can override extension parameters via environment variables. But this only
works, if Qvarn configuration file has extension section (even if section is
empty). Example of environment variable::

  QVARN_EXTENSION_MYAPP1_ENDPOINT=http://localhost:9100

Also you can  override extension parameters via command line options::

  qvarn-run -o extension:myapp1.endpoint=http://localhost:9100 ...


Healthcheck
-----------

Healthcheck is a public endpoint and does not require any authorization::

   /healthcheck

It simply runs `SELECT 1` query.


Legalese
--------

This version of Qvarn is free software.

While Qvarn itself is under the AGPL3+ license (see below), this
license does NOT apply to clients of the HTTP API Qvarn provides.

Copyright 2015, 2016, 2017, 2018 Suomen Tilaajavastuu Oy
Copyright 2015, 2016 QvarnLabs AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
