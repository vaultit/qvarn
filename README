README for Qvarn
================

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
[Gluu][] and these can be added and adapted for local needs.

The resource types Qvarn knows about are configurable (via YAML files
in `resource_type/*.yaml` and installed as `/etc/qvarn/*.yaml`),
making Qvarn suitable to various application domains. Applications may
be written in any language, using any framework, as long as they can
use HTTP over TLS.

[Gluu]: https://www.gluu.org/


Development environment
-----------------------

You need various tools to develop and/or run the software. It's
easiest to do this on Debian (version 8.x, code name jessie). It may
be possible to run the code in other environments (if so, please add
details here).

* [CoverageTestRunner][], a Python unit test runner for running the
  unit tests. Note that `nose-tests` is insufficient (it'll run, but
  won't check coverage diligently enough). Debian package is
  `python-coverage-test-runner`.
* [pep8][] and [pylint][] static checkers for Python code. (Debian
  packages have those names.)
* [flup][], an implementation of the Python Web Server Gateway
  Interface. Debian package is `python-flup`.
* [PyJWT][], JWT token encoding and decoding tools. Debian package is
  `python-jwt`.
* [python-cryptography][], Python cryptography tools. Debian package is
  `python-cryptography`.
* [Bottle][], Python Web Framework. Debian package is `python-bottle`.

[CoverageTestRunner]: http://liw.fi/coverage-test-runner/
[coverage.py]: http://nedbatchelder.com/code/coverage/
[pep8]: http://pypi.python.org/pypi/pep8
[pylint]: http://www.pylint.org/
[flup]: http://www.saddi.com/software/flup/
[PyJWT]: https://github.com/jpadilla/pyjwt/
[python-cryptography]: https://cryptography.io/
[Bottle]: http://bottlepy.org/

Building and running unit tests
-------------------------------

The code is pure Python, and as such does not need building. However,
the `./check` script runs unit tests, and the static Python checkers
`pep8` and `pylint`.

Before merging into the integration branch, `./check` must pass.


Integration tests
-----------------

The API document contains integration tests ("yarns"). These are run
from the `docs/qvarn-api-doc` directory. These are run by first
deploying the software on a host, using instructions that do not yet
exist (please nag).

The yarns require the `createtoken` tool to be configured. Create
`~/.config/qvarn/createtoken.conf` with contents like this:

    [https://qvarn.example.com]
    client_id = G00G00G000
    client_secret = thisisveryverysecrethushhush

In other words, it's an INI file with a section named after the URL of
the Qvarn instance that runs (not the associated Gluu instance). The
client id and secret are set up in the Gluu instance associated with
the API instance.

The integration tests are run using the `yarn` tool, like this:

    cd docs/qvarn-api-doc
    ./test-api https://qvarn.example.com

where `qvarn.example.com` is the Qvarn API instance being tested.

See the documentation for `yarn` for more options. `yarn` is part of
the `cmdtest` package (see [home page](http://liw.fi/cmdtest/)). You
need at least version 0.27.


Writing unit tests
------------------

Unit tests are run using `CoverageTestRunner` module, written by Lars
Wirzenius. It can be found at <http://liw.fi/coverage-test-runner/>.
This test runner uses [coverage.py][] to measure test coverage, and
measures a code module's coverage only when its own test module is
run. Coverage for `qvarn/foo.py` is only measured when
`qvarn/foo_tests.py` is run. Also, the test runner fails the test
suite unless all statements are either covered by tests, or explicitly
marked as excluded from coverage, using a comment such as the
following:

    # Justification for exclusion from coverage: The following thing
    # is obviously correct, but it's difficult to make a good test
    # case for it.
    if very_difficult_condition:  # pragma: no cover
        this_is_not_measured()

Note that you should always include a justification for a pragma.
Otherwise code reviewers and developers in the future who need to look
at the code will assume you're lazy.

If an entire module is going to be without unit tests, it should be
added to the `without-tests` file at the root of the source tree.
`CoverageTestRunner` will then not complain that there are no tests
for it.

When writing or changing code, it's easy to achieve 100% statement
coverage if using TDD, writing one test at a time, and ensuring
coverage never drops.

`CoverageTestRunner` and `coverage.py` are both packaged for Debian.


Coding style
------------

Qvarn is written in Python 2, until all its dependencies are available
for Python 3 and available for a Debian stable release.

Code must be formatted according to [PEP8][]. The `./check` script
runs a tool to check for many formatting and other style details.

[PEP8]: https://www.python.org/dev/peps/pep-0008/

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

* `BackendApplication` --- the main program of the application:
  command line parsing, starting of the HTTP server. This class is
  parameterised, not subclassed. The main parameters are the resources
  to serve, and the the routes that the resource provides.

* `ListResource`, `SimpleResource` --- classes to provide the two
  kinds of resources. `ListResource` provides code for resources that
  manage a set of items (such as persons or organisations). Such
  resources are mostly identical to each other, except for details
  such as item type and allowed fields. `SimpleResource` provides for
  simpler resources such as `/version`. Both these classes are
  parameterised, instead of subclassed.

* `Database` --- all the code talking directly to the database; this
  provides a fairly light abstraction providing only the functionality
  we use (or are meant to use).

* `ReadOnlyStorage`, `WriteOnlyStorage` --- store and retrieve simple
  Python dictionary objects representing the kinds of items that the
  API deal with. Basically, these are very trivial ORMs that map
  JSON-like Python objects into rows in relation databases. Reading
  and writing are kept explicitly separate to implement an
  architecture where writes all go into one database instance, which
  gets replicated to any number of read-only databases. By keeping the
  classes separate, it is slightly difficult to accidentally write to
  the wrong place.

* `StoragePreparer` --- manage database schemas and migrations. The
  class maintains a sequence of preparation steps. Every time we make
  a schema change, we add another step, which makes the relevant
  changes: adds or removes tables or columns, and fills new columns
  and tables with the correct data. Every database instance goes
  through the same sequence, even if it is brand new. This should
  guarantee we can always migrate to a newer version, with minimal
  manual intervention.

* `ItemValidator` --- validate that an API item (JSON-like Python
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

* `build-essential` --- all the basic development tools, such as C and
  C++ compilers and development libraries
* `debhelper` --- a packaging helper utility, which makes packaging
  much easier
* `python-all` --- all Python versions (packaging is a little simpler
  if they're all installed)
* `devscripts` --- supplies the `dch` and `debuild` tools.

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

1. `debuild -us -uc` (the options prevent digital signatures from
   being created).


A deployed system
-----------------

The deployed system, as installed from the Debian package, looks like
this:

* The Python library `qvarn` is installed in the usual location
  for such, in Debian: `/usr/lib/python2.7/dist-packages/qvarn`.

* The backend application is installed in `/usr/bin`.

* The backend application is started by `uwsgi`, which is configured
  via `/etc/uwsgi`.

* The `haproxy` load balancer is used to direct HTTP requests from the
  external network interface to the right localhost port. The
  `haproxy` config is configured using external means (e.g., Ansible).

* There are several log files involved:

    - `/var/log/haproxy.log`
    - `/var/log/uwsgi/*/*`
    - `/var/log/qvarn/qvarn.log*`

* All services run as the `www-data` user and `www-data` group.


Legalese
--------

This version of Qvarn is free software.

While Qvarn itself is under the AGPL3+ license (see below), this
license does NOT apply to clients of the HTTP API Qvarn provides.

Copyright 2015, 2016 Suomen Tilaajavastuu Oy
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
along with this program.  If not, see <http://www.gnu.org/licenses/>.
