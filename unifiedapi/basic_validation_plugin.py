# basic_validation_plugin.py - does basic validation for JSON resources
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

import bottle

import unifiedapi


class BasicValidationPlugin(object):

    '''Perform basic validation for JSON resource POST and PUT.

    Checks that content type is application/json

    Checks that new resources have no id or revision.

    Checks that resource updates have revision.

    Checks that when resource updates have id
    then that id matches the route id.
    '''

    def __init__(self, id_field_name=None):
        self._id_field_name = id_field_name

    def apply(self, callback, route):
        method = route['method']
        if method == 'POST':
            def post_wrapper(*args, **kwargs):
                self._check_json()
                self._check_create_json()
                return callback(*args, **kwargs)
            return post_wrapper
        elif method == 'PUT':
            def put_wrapper(*args, **kwargs):
                self._check_json()
                self._check_update_json(kwargs)
                return callback(*args, **kwargs)
            return put_wrapper
        return callback

    def _check_json(self):
        if bottle.request.json is None:
            raise ContentTypeIsNotJSON()

    def _check_create_json(self):
        item = bottle.request.json
        if u'id' in item:
            raise NewItemHasIdAlready(item_id=item[u'id'])
        if u'revision' in item:
            raise NewItemHasRevisionAlready(revision=item[u'revision'])

    def _check_update_json(self, kwargs):
        item = bottle.request.json
        item_route_id = kwargs[self._id_field_name]
        if u'id' in item and item[u'id'] != item_route_id:
            raise ItemHasConflictingId(
                item_id=item[u'id'], wanted_id=item_route_id)
        if u'revision' not in item:
            raise NoItemRevision(item_id=item_route_id)


class ContentTypeIsNotJSON(unifiedapi.UnsupportedMediaType):

    msg = u'Content-Type must be application/json'


class NewItemHasIdAlready(unifiedapi.ValidationError):

    msg = u'New item has id already set'


class NewItemHasRevisionAlready(unifiedapi.ValidationError):

    msg = u'New item has revision already set'


class ItemHasConflictingId(unifiedapi.ValidationError):

    msg = u'Updated item has conflicting id'


class NoItemRevision(unifiedapi.Conflict):

    msg = u'Item has no revision'
