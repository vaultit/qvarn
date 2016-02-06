# file_resource.py - implements API for a file subresource such as
#                    /contracts/<id>/document
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


'''File resources in the HTTP API.'''


import qvarn
import bottle


class FileResource(object):

    '''A file resource in the HTTP API.

    A file resource is one such as /contracts/<id>/document, that allows a
    file to be associated with a top level resource.

    This class is meant to be parameterised, not subclassed. Use the
    various set methods to set the parameters.

    '''

    def __init__(self):
        self._path = None
        self._listener = None
        self._dbconn = None
        self._item_type = None
        self._item_prototype = None
        self._subitem_prototypes = qvarn.SubItemPrototypes()
        self._file_resource_name = None

    def set_top_resource_path(self, path):
        '''Set path of the top level resource, e.g., /persons.'''
        self._path = path

    def set_item_type(self, item_type):
        '''Set the type of items, e.g., u'person'.'''
        self._item_type = item_type

    def set_item_prototype(self, item_prototype):
        '''Set the prototype for each sub-item.'''
        self._item_prototype = item_prototype

    def set_subitem_prototype(self, subitem_name, prototype):
        '''Set prototype for a subitem.'''
        self._subitem_prototypes.add(self._item_type, subitem_name, prototype)

    def set_listener(self, listener):
        '''Set the listener for this resource.

        A listener must have methods ``notify_create``, ``notify_update``
        and ``notify_delete``. ListenerResource implements these methods
        and has a more detailed description of them.
        '''
        self._listener = listener

    def set_file_resource_name(self, resource_name):
        '''Set the file resource name.'''
        self._file_resource_name = resource_name

    def prepare_resource(self, dbconn):
        '''Prepare the resource for action.'''

        self._dbconn = dbconn

        file_paths = []
        if self._file_resource_name:
            self.set_subitem_prototype(self._file_resource_name, {
                u'body': u'', u'content_type': u''
            })
            resource_name = self._file_resource_name
            file_paths = [
                {
                    'path': self._path + '/<item_id>/' + resource_name,
                    'method': 'GET',
                    'callback': self.get_file,
                },
                {
                    'path': self._path + '/<item_id>/' + resource_name,
                    'method': 'PUT',
                    'callback': self.put_file,
                },
            ]

        return file_paths

    def get_file(self, item_id):
        '''Serve GET /foos/123/<file_resource_name> to get a file.'''
        ro = self._create_ro_storage()
        with self._dbconn.transaction() as t:
            subitem = ro.get_subitem(t, item_id, self._file_resource_name)
            item = ro.get_item(t, item_id)

        bottle.response.set_header('Revision', item[u'revision'])
        bottle.response.set_header('Content-Type', subitem[u'content_type'])
        return subitem[u'body']

    def put_file(self, item_id):
        '''Serve PUT /foos/123/<file_resource_name> to update a file.'''

        if bottle.request.content_length < 0:
            raise ContentLengthMissing(item_id=item_id)
        if not bottle.request.content_type:
            raise InvalidContentType(item_id=item_id)
        if u'revision' not in bottle.request.headers:
            raise qvarn.NoItemRevision(item_id=item_id)
        revision = bottle.request.headers[u'revision']

        subitem = {
            u'id': item_id,
            u'body': buffer(bottle.request.body.read()),
            u'content_type': unicode(bottle.request.content_type)
        }

        added = {u'id': item_id}

        wo = self._create_wo_storage()
        with self._dbconn.transaction() as t:
            added[u'revision'] = wo.update_subitem(
                t, item_id, revision, self._file_resource_name, subitem)
        self._listener.notify_update(added[u'id'], added[u'revision'])
        return added

    def _create_ro_storage(self):
        ro = qvarn.ReadOnlyStorage()
        ro.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            ro.set_subitem_prototype(self._item_type, subitem_name, prototype)
        return ro

    def _create_wo_storage(self):
        wo = qvarn.WriteOnlyStorage()
        wo.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            wo.set_subitem_prototype(self._item_type, subitem_name, prototype)
        return wo


class ContentLengthMissing(qvarn.LengthRequired):

    msg = u'Content-Length header is missing'


class InvalidContentType(qvarn.UnsupportedMediaType):

    msg = u'Content-Type header is invalid'
