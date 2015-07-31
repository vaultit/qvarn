# list_resource.py - implement API for multi-item resources such as /persons
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


'''Multi-item resources in the HTTP API.'''


import urllib

import unifiedapi
import bottle


class ListResource(object):

    '''A multi-item resource in the HTTP API.

    A multi-item resource is one such as /persons, where the top level
    resource has any number of sub-resources, one per person, and the
    API client can access and manage the sub-items individually.

    This class is meant to be parameterised, not subclassed. Use the
    various set methods to set the parameters.

    '''

    # pylint: disable=locally-disabled,too-many-instance-attributes

    def __init__(self):
        self._path = None
        self._item_type = None
        self._item_prototype = None
        self._item_validator = None
        self._subitem_prototypes = unifiedapi.SubItemPrototypes()
        self._listener = None
        self.database = None

    def set_path(self, path):
        '''Set path of the top level resource, e.g., /persons.'''
        self._path = path

    def set_item_type(self, item_type):
        '''Set the type of items, e.g., u'person'.'''
        self._item_type = item_type

    def set_item_prototype(self, item_prototype):
        '''Set the prototype for each sub-item.'''
        self._item_prototype = item_prototype

    def set_item_validator(self, item_validator):
        '''Set function to provide item-specific validation.

        Note that ``item_validator`` does not need to do generic
        validation against the prototype, as that is handled
        automatically.

        '''

        self._item_validator = item_validator

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

    def prepare_resource(self, database):
        '''Prepare the resource for action.'''

        self.database = database

        item_paths = [
            {
                'path': self._path,
                'method': 'GET',
                'callback': self.get_items,
            },
            {
                'path': self._path,
                'method': 'POST',
                'callback': self.post_item,
                'apply': unifiedapi.BasicValidationPlugin(),
            },
            {
                'path': self._path + '/<item_id>',
                'method': 'GET',
                'callback': self.get_item,
            },
            {
                'path': self._path + '/<item_id>',
                'method': 'PUT',
                'callback': self.put_item,
                'apply': unifiedapi.BasicValidationPlugin(u'item_id'),
            },
            {
                'path': self._path + '/<item_id>',
                'method': 'DELETE',
                'callback': self.delete_item,
            },
            {
                'path': self._path + '/search/<search_criteria:path>',
                'method': 'GET',
                'callback': self.get_matching_items,
            },
        ]

        subitem_paths = []
        for subitem_name, _ in self._subitem_prototypes.get_all():
            subitem_path = self._path + '/<item_id>/' + subitem_name
            subitem_paths.extend([
                {
                    'path': subitem_path,
                    'method': 'GET',
                    'callback':
                    lambda item_id, x=subitem_name:
                    self.get_subitem(item_id, x),
                },
                {
                    'path': subitem_path,
                    'method': 'PUT',
                    'callback':
                    lambda item_id, x=subitem_name:
                    self.put_subitem(item_id, x),
                    'apply': unifiedapi.BasicValidationPlugin(u'item_id'),
                }
            ])

        return item_paths + subitem_paths

    def get_items(self):
        '''Serve GET /foos to list all items.'''
        ro = self._create_ro_storage()
        return {
            'resources': [
                {'id': resource_id} for resource_id in ro.get_item_ids()
            ],
        }

    def get_matching_items(self, search_criteria):
        '''Serve GET /foos/search to list items matching search criteria.'''
        ro = self._create_ro_storage()

        criteria = search_criteria.split('/')
        search_params = []
        show_params = []

        for i in range(len(criteria)):
            if i % 3 == 0:
                if criteria[i] in [u'exact']:
                    matching_rule = criteria[i]
                elif criteria[i] == u'show_all':
                    show_params.append(criteria[i])
                    break
                else:
                    raise bottle.HTTPError(status=400)
            elif i % 3 == 1:
                search_field = criteria[i]
            elif i % 3 == 2:
                search_value = urllib.unquote(criteria[i])
                search_param = (matching_rule, search_field, search_value)
                search_params.append(search_param)

        return ro.search(search_params, show_params)

    def post_item(self):
        '''Serve POST /foos to create a new item.'''
        item = bottle.request.json
        unifiedapi.add_missing_item_fields(
            self._item_type, self._item_prototype, item)

        iv = unifiedapi.ItemValidator()
        try:
            iv.validate_item(self._item_type, self._item_prototype, item)
            self._item_validator(item)
        except unifiedapi.ValidationError as e:
            raise bottle.HTTPError(status=400)

        # Filling in default values sets the fields to None, if
        # missing. Thus we accept that and just remove it here.
        del item[u'id']
        del item[u'revision']

        wo = self._create_wo_storage()
        added = wo.add_item(item)
        self._listener.notify_create(added[u'id'], added[u'revision'])
        return added

    def get_item(self, item_id):
        '''Serve GET /foos/123 to get an existing item.'''
        ro = self._create_ro_storage()
        try:
            return ro.get_item(item_id)
        except unifiedapi.ItemDoesNotExist as e:
            raise bottle.HTTPError(status=404)

    def get_subitem(self, item_id, subitem_path):
        '''Serve GET /foos/123/subitem.'''
        ro = self._create_ro_storage()
        try:
            subitem = ro.get_subitem(item_id, subitem_path)
        except unifiedapi.ItemDoesNotExist as e:
            raise bottle.HTTPError(status=404)

        item = ro.get_item(item_id)
        subitem[u'revision'] = item[u'revision']
        return subitem

    def put_item(self, item_id):
        '''Serve PUT /foos/123 to update an item.'''

        item = bottle.request.json

        unifiedapi.add_missing_item_fields(
            self._item_type, self._item_prototype, item)

        iv = unifiedapi.ItemValidator()
        try:
            iv.validate_item(self._item_type, self._item_prototype, item)
            item[u'id'] = item_id
            self._item_validator(item)
        except unifiedapi.ValidationError as e:
            raise bottle.HTTPError(status=400)

        try:
            wo = self._create_wo_storage()
            updated = wo.update_item(item)
        except unifiedapi.WrongRevision as e:
            raise bottle.HTTPError(status=409)

        self._listener.notify_update(updated[u'id'], updated[u'revision'])
        return updated

    def put_subitem(self, item_id, subitem_name):
        '''Serve PUT /foos/123/subitem to update a subitem.'''

        subitem = bottle.request.json

        subitem_type = u'%s_%s' % (self._item_type, subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        unifiedapi.add_missing_item_fields(subitem_type, prototype, subitem)

        iv = unifiedapi.ItemValidator()
        try:
            revision = subitem.pop(u'revision')
            iv.validate_item(subitem_type, prototype, subitem)
        except unifiedapi.ValidationError as e:
            raise bottle.HTTPError(status=400)

        try:
            wo = self._create_wo_storage()
            subitem[u'revision'] = wo.update_subitem(
                item_id, revision, subitem_name, subitem)
        except unifiedapi.WrongRevision as e:
            raise bottle.HTTPError(status=409)
        updated = dict(subitem)
        updated.update({u'id': item_id})
        self._listener.notify_update(updated[u'id'], updated[u'revision'])
        return subitem

    def delete_item(self, item_id):
        '''Serve DELETE /foos/123 to delete an item.'''
        wo = self._create_wo_storage()
        try:
            wo.delete_item(item_id)
            self._listener.notify_delete(item_id)
        except unifiedapi.ItemDoesNotExist as e:
            raise bottle.HTTPError(status=404)

    def _create_ro_storage(self):
        ro = unifiedapi.ReadOnlyStorage()
        ro.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            ro.set_subitem_prototype(self._item_type, subitem_name, prototype)
        ro.set_db(self.database)
        return ro

    def _create_wo_storage(self):
        wo = unifiedapi.WriteOnlyStorage()
        wo.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            wo.set_subitem_prototype(self._item_type, subitem_name, prototype)
        wo.set_db(self.database)
        return wo

    def _create_resource_ro_storage(self, resource_name, prototype):
        ro = unifiedapi.ReadOnlyStorage()
        ro.set_item_prototype(resource_name, prototype)
        ro.set_db(self.database)
        return ro

    def _create_resource_wo_storage(self, resource_name, prototype):
        wo = unifiedapi.WriteOnlyStorage()
        wo.set_item_prototype(resource_name, prototype)
        wo.set_db(self.database)
        return wo
