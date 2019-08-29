from __future__ import unicode_literals

import datetime
import os
import time

import jwt
import yaml
import webtest
from Crypto.PublicKey import RSA

import qvarn


ALGORITHM = 'RS512'


def get_scopes_from_resource_types(path):
    patterns = (
        'uapi_%s_get',
        'uapi_%s_post',
        'uapi_%s_id_get',
        'uapi_%s_id_put',
        'uapi_%s_id_delete',
        'uapi_%s_search_id_get',
        'uapi_%s_listeners_post',
        'uapi_%s_listeners_id_get',
        'uapi_%s_listeners_id_delete',
        'uapi_%s_listeners_id_notifications_get',
        'uapi_%s_listeners_id_notifications_id_get',
        'uapi_%s_listeners_id_notifications_id_delete',
    )
    subpath_patterns = (
        'uapi_%s_id_%s_get',
        'uapi_%s_id_%s_put',
    )
    for name in os.listdir(path):
        if name.endswith('.yaml'):
            with open(os.path.join(path, name)) as f:
                schema = yaml.safe_load(f)
            schema = schema['versions'][-1]

            resource_type = name[:-len('.yaml')]
            for pattern in patterns:
                yield pattern % resource_type

            for subpath in schema.get('subpaths', {}).keys():
                for pattern in subpath_patterns:
                    yield pattern % (resource_type, subpath)


def get_jwt_token(key, issuer, scopes):
    claims = {
        'iss': issuer,
        'sub': 'user',
        'aud': 'client',
        'exp': time.time() + datetime.timedelta(days=10).total_seconds(),
        'scope': ' '.join(scopes),
    }
    return jwt.encode(claims, key.exportKey('PEM'), algorithm=ALGORITHM)


def create_qvarn_test_app(config=None):
    # pylint: disable=protected-access

    key = RSA.generate(4096)
    issuer = 'https://auth.example.com'
    specdir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'resource_type')
    defaults = {
        'main.log': 'stdout-oneline',
        'main.enable_access_log': 'true',
        'main.specdir': specdir,
        'auth.token_issuer': issuer,
        'auth.token_validation_key': key.exportKey('OpenSSH').decode(),
    }
    _config = config or {}
    config = dict(defaults)
    config.update(_config)

    args = sum([['-o', '%s=%s' % (k, v)] for k, v in config.items()], [])

    app = qvarn.BackendApplication()
    app.run_helper(uwsgi_postfork_setup=False,
                   argv=args + ['--prepare-storage'])
    app.run_helper(uwsgi_postfork_setup=False, argv=args)
    app._uwsgi_postfork_setup()
    return app, key, issuer


class DeleteWalker(qvarn.DeleteWalker):

    def __init__(self, db, item_type):  # pylint: disable=super-init-not-called
        self._db = db
        self._item_type = item_type
        self._item_id = None

    def _delete_rows(self, table_name, item_id):
        # Some tables (like resource_files) are created on demand, so it's not
        # an error if they do not exist.
        if table_name in self._db.meta.tables:
            self._db.engine.execute(
                self._db.meta.tables[table_name].delete()
            )


class TestApp(webtest.TestApp):
    # pylint: disable=protected-access

    def __init__(self, app, *args, **kwargs):
        self._db = app._dbconn.get_sqlaconn()
        self._specs = {
            spec['path'].strip('/'): (spec['type'], spec['versions'][-1])
            for spec in app._load_specs_from_db()
        }

        super(TestApp, self).__init__(app._app, *args, **kwargs)

    def do_request(self, req, *args, **kwargs):
        # Qvarn uses REQUEST_URI to parse search URI before decoding, see
        # qvarn.list_resource.ListResource.get_matching_items.
        #
        # But REQUEST_URI is optional and  webtest does not add it to request
        # environ, see https://github.com/Pylons/webtest/issues/1.
        path = req.environ['PATH_INFO']
        qs = req.environ['QUERY_STRING']
        req.environ['REQUEST_URI'] = (path + ('?' + qs if qs else '')).encode()
        return super(TestApp, self).do_request(req, *args, **kwargs)

    def wipe(self, resource_names):
        for resource_name in resource_names:
            resource_type, spec = self._specs[resource_name]
            dw = DeleteWalker(self._db, resource_type)
            dw.walk_item(spec, spec)

            files = spec.get(u'files', [])
            subpaths = spec.get('subpaths', [])
            for subpath in subpaths:
                if subpath not in files:
                    proto = subpaths[subpath][u'prototype']
                    table_name = qvarn.table_name(resource_type=resource_type,
                                                  subpath=subpath)
                    dw = DeleteWalker(self._db, table_name)
                    dw.walk_item(proto, proto)


class DatabaseConnection(qvarn.DatabaseConnection):

    def drop_tables(self, names):
        sqla = self.get_sqlaconn()
        tables = [
            sqla.meta.tables[name]
            for name in names
            if name in sqla.meta.tables
        ]
        if tables:
            sqla.meta.drop_all(sqla.engine, tables, checkfirst=True)
            sqla.meta.clear()
            sqla.meta.reflect(sqla.engine)

        # Also remove entries from `resource_type` table.
        if 'resource_type' in sqla.meta.tables:
            for name in names:
                table = sqla.meta.tables['resource_type']
                query = table.delete().where(table.c.name == name)
                sqla.engine.execute(query)
