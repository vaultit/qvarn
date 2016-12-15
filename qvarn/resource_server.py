# resource_server.py - generic "main program" for a Qvarn resource server
#
# Copyright 2015, 2016 Suomen Tilaajavastuu Oy
# Copyright 2016  QvarnLabs Ltd
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


import qvarn


class ResourceServer(object):

    def __init__(self):
        self._path = None
        self._type = None
        self._latest_version = None
        self._app = None
        self._vs = qvarn.VersionedStorage()

    def set_backend_app(self, app):
        self._app = app
        self._app.add_versioned_storage(self._vs)

    def set_resource_path(self, path):
        self._path = path

    def set_resource_type(self, resource_type):
        self._type = resource_type
        self._vs.set_resource_type(resource_type)

    def add_resource_type_versions(self, versions):
        for version in versions:
            self._add_resource_type_version(version)

        self._latest_version = versions[-1]

    def _add_resource_type_version(self, version):
        self._vs.start_version(version[u'version'], None)
        self._vs.add_prototype(version[u'prototype'])

        self._add_subresources(version)

        self._vs.add_prototype(qvarn.listener_prototype, auxtable=u'listener')
        self._vs.add_prototype(
            qvarn.notification_prototype, auxtable=u'notification')

    def _add_subresources(self, version):
        subpaths = version.get(u'subpaths', [])
        for subpath in subpaths:
            proto = subpaths[subpath][u'prototype']
            self._vs.add_prototype(proto, subpath=subpath)

    def create_resource(self):
        listener = self._create_listener()
        self._create_list_resource(listener)
        self._create_file_resources(listener)

    def _create_listener(self):
        listener = qvarn.ListenerResource()
        listener.set_top_resource_path(self._type, self._path)
        self._app.add_resource(listener)
        return listener

    def _create_list_resource(self, listener):
        resource = qvarn.ListResource()
        resource.set_path(self._path)
        resource.set_item_type(self._type)
        resource.set_item_prototype(self._latest_version[u'prototype'])
        resource.set_listener(listener)

        resource.set_item_validator(self._latest_version.get(u'validator'))

        subpaths = self._latest_version.get(u'subpaths', [])
        files = self._latest_version.get(u'files', [])
        for subpath in subpaths:
            if subpath not in files:
                proto = subpaths[subpath][u'prototype']
                resource.set_subitem_prototype(subpath, proto)

        self._app.add_resource(resource)

    def _create_file_resources(self, listener):
        for subpath in self._latest_version.get(u'files', []):
            self._create_file_resource(listener, subpath)

    def _create_file_resource(self, listener, subpath):
        file_resource = qvarn.FileResource()
        file_resource.set_item_prototype(self._latest_version[u'prototype'])
        file_resource.set_top_resource_path(self._path)
        file_resource.set_item_type(self._type)
        file_resource.set_file_resource_name(subpath)
        file_resource.set_listener(listener)
        self._app.add_resource(file_resource)

    def prepare_for_uwsgi(self):
        return self._app.prepare_for_uwsgi()


def add_resource_type_to_server(app, resource_type_spec):
    server = ResourceServer()
    server.set_backend_app(app)
    server.set_resource_path(resource_type_spec[u'path'])
    server.set_resource_type(resource_type_spec[u'type'])
    server.add_resource_type_versions(resource_type_spec[u'versions'])
    server.create_resource()
