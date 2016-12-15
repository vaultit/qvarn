# backend_app.py - implement main parts of a backend application
#
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


import argparse
import ConfigParser
import os
import sys
import yaml

import bottle

import qvarn


# We want to load strings as unicode, not str.
# From http://stackoverflow.com/questions/2890146/
# It seems this will be unnecessary in Python 3.

def construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    if node.value == 'blob':
        return buffer('')
    return self.construct_scalar(node)


yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


log = qvarn.StructuredLog()
log.set_log_writer(qvarn.NullSlogWriter())
qvarn.hijack_logging(log)


class BackendApplication(object):

    '''Main program of a backend application.

    This class provides the logic for command line parsing, log file
    setup, and starting of HTTP service, plus other things that are
    common to all backend applications. Backend applications are
    expected to all have the same external interface, provided by this
    class.

    This class is parameterised by calling the
    ``set_storage_preparer``, ``add_resource`` and ``add_routes``
    methods. The application actually starts when UWSGI starts the
    Bottle application that our prepare_for_wsgi method returns.

    The resources added with ``add_resource`` MUST have a
    ``prepare_resource`` method, which gets as its parameter the
    database, and returns a representation of routes suitable to be
    given to ``add_routes``. The resource object does not need to call
    ``add_routes`` directly.

    '''

    def __init__(self):
        self._app = bottle.app()

        # We'll parse the HTTP request body ourselves, because Bottle
        # sometimes wants to use simplejson, which returns plain
        # strings instead of Unicode strings, and that's not
        # acceptable to us.
        self._app.config['autojson'] = False

        self._dbconn = None
        self._vs_list = []
        self._resources = []
        self._conf = None

    def add_versioned_storage(self, versioned_storage):
        self._vs_list.append(versioned_storage)

    def add_resource(self, resource):
        '''Adds a resource that this application serves.

        A resource is represented by a class that has a
        ``prepare_resource`` method.

        '''

        self._resources.append(resource)

    def add_routes(self, routes):
        '''Add routes to the application.

        A route is the path serve (e.g., "/version"), the HTTP method
        ("GET"), and the callback function. The path may use bottle.py
        route syntax to extract parameters from the path.

        The routes are provided as a list of dicts, where each dict
        has the keys ``path``, ``method``, and ``callback``.

        '''

        for route in routes:
            self._app.route(**route)

    def prepare_for_uwsgi(self, specdir):
        '''Prepare the application to be run by uwsgi.

        Load resource type specifications from specdir, if in prepare
        mode.

        Return a Bottle application that uwsgi can use. The caller
        should assign it to a global variable called "application", or
        some other name uwsgi is configured to use.

        '''

        # The actual running is in run_helper. Here we just catch
        # exceptions and handle them in some useful manner.

        try:
            self.run_helper(specdir)
        except qvarn.QvarnException as e:
            log.log('error', exc_info=True, msg_text=str(e))
            sys.stderr.write('ERROR: {}\n'.format(str(e)))
            sys.exit(1)
        except SystemExit as e:
            sys.exit(e.code if isinstance(e.code, int) else 1)
        except BaseException as e:
            log.log('error', exc_info=True, msg_text=str(e))
            sys.stderr.write('ERROR: {}\n'.format(str(e)))
            sys.exit(1)
        else:
            return self._app

    def run_helper(self, specdir):
        self._conf, args = self._parse_config()

        if args.prepare_storage:
            # Logging should be the first plugin (outermost wrapper)
            self._configure_logging(self._conf)
            qvarn.log.set_context('prepare-storage')
            self._connect_to_storage(self._conf)
            specs = self._load_specs_from_files(specdir)
            self._add_resource_types_from_specs(specs)
            self._prepare_storage(self._conf)
        else:
            # Logging should be the first plugin (outermost wrapper)
            self._configure_logging(self._conf)
            qvarn.log.set_context('setup')
            self._install_logging_plugin()
            # Error catching should also be as high as possible to catch all
            self._app.install(qvarn.ErrorTransformPlugin())
            specs = self._load_specs_from_files(specdir)
            self._add_resource_types_from_specs(specs)
            self._setup_auth(self._conf)
            self._app.install(qvarn.StringToUnicodePlugin())
            # Import is here to not fail tests and is only used on uWSGI
            import uwsgidecorators
            uwsgidecorators.postfork(self._uwsgi_postfork_setup)

    def _uwsgi_postfork_setup(self):
        '''Setup after uWSGI has forked the process.

        We create the database connection pool after uWSGI has forked the
        process to not share the pool connections between processes.

        '''
        self._connect_to_storage(self._conf)
        routes = self._prepare_resources()
        self.add_routes(routes)

    def _parse_config(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--prepare-storage',
            action='store_true',
            help='only prepare database storage')
        parser.add_argument(
            '--config',
            metavar='FILE',
            help='use FILE as configuration file')
        args = parser.parse_args()

        config = ConfigParser.RawConfigParser()
        files_read = config.read(args.config)
        if files_read != [args.config]:
            raise MissingConfigFileError(filename=args.config)
        return config, args

    def _connect_to_storage(self, conf):
        '''Prepare the database for use.'''

        args = {
            'host': conf.get('database', 'host'),
            'port': conf.get('database', 'port'),
            'db_name': conf.get('database', 'name'),
            'user': conf.get('database', 'user'),
            'min_conn': conf.get('database', 'minconn'),
            'max_conn': conf.get('database', 'maxconn'),
        }

        # Log all connection parameters except password.
        log.log('connect-to-storage', **args)
        sql = qvarn.PostgresAdapter(
            password=conf.get('database', 'password'),
            **args)

        self._dbconn = qvarn.DatabaseConnection()
        self._dbconn.set_sql(sql)

    def _load_specs_from_files(self, specdir):
        specs = []
        yamlfiles = self._find_yaml_files(specdir)
        for yamlfile in yamlfiles:
            with open(yamlfile) as f:
                spec = yaml.safe_load(f)
            specs.append(spec)
        return specs

    def _find_yaml_files(self, specdir):
        basenames = os.listdir(specdir)
        return [
            os.path.join(specdir, x) for x in basenames if x.endswith('.yaml')
        ]

    def _add_resource_types_from_specs(self, specs):
        for spec in specs:
            qvarn.add_resource_type_to_server(self, spec)

    def _prepare_storage(self, conf):
        '''Prepare the database for use.'''
        if not conf.getboolean('database', 'readonly'):
            with self._dbconn.transaction() as t:
                for vs in self._vs_list:
                    vs.prepare_storage(t)

    def _configure_logging(self, conf):
        if conf.has_option('main', 'log'):
            name = conf.get('main', 'log')
            if name == 'syslog':
                self._configure_logging_to_syslog()
            else:
                max_bytes = self._get_max_log_bytes(conf)
                self._configure_logging_to_file(name, max_bytes)

        log.log(
            'startup',
            msg_text='Program starts',
            version=qvarn.__version__,
            argv=sys.argv,
            env=dict(os.environ))

    def _configure_logging_to_syslog(self):
        writer = qvarn.SyslogSlogWriter()
        qvarn.log.set_log_writer(writer)

    def _get_max_log_bytes(self, conf):
        max_bytes = 10 * 1024**2
        if conf.has_option('main', 'log-max-bytes'):
            max_bytes = conf.getint('main', 'log-max-bytes')
        return max_bytes

    def _configure_logging_to_file(self, filename, max_bytes):
        writer = qvarn.FileSlogWriter()
        writer.set_filename_prefix(filename)
        writer.set_max_file_size(max_bytes)
        qvarn.log.set_log_writer(writer)

    def _install_logging_plugin(self):
        logging_plugin = qvarn.LoggingPlugin()
        self._app.install(logging_plugin)

    def _setup_auth(self, conf):
        validation_key = None
        issuer = None

        if conf.has_option('auth', 'token_validation_key'):
            validation_key = conf.get('auth', 'token_validation_key')

        if conf.has_option('auth', 'token_issuer'):
            issuer = conf.get('auth', 'token_issuer')

        if validation_key and issuer:
            plugin = qvarn.AuthorizationPlugin()
            plugin.set_token_validation_key(validation_key)
            plugin.set_token_issuer(issuer)
            self._app.install(plugin)
        else:
            raise MissingAuthorizationError(
                validation_key=validation_key,
                issuer=issuer)

    def _prepare_resources(self):
        routes = []
        for resource in self._resources:
            routes += resource.prepare_resource(self._dbconn)
        return routes


class MissingAuthorizationError(qvarn.QvarnException):

    msg = (u'Configuration is missing authentication fields: '
           u'token_validation_key is set to {validation_key!r}, '
           u'token_issuer is set to {issuer!r}.')


class MissingConfigFileError(qvarn.QvarnException):

    msg = u"Couldn't read configuration file {filename}"
