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
            raise bottle.HTTPError(status=415)

    def _check_create_json(self):
        try:
            item = bottle.request.json
            if u'id' in item:
                raise NewItemHasIdAlready(id=item[u'id'])
            if u'revision' in item:
                raise NewItemHasRevisionAlready(revision=item[u'revision'])
        except unifiedapi.ValidationError:
            raise bottle.HTTPError(status=400)

    def _check_update_json(self, kwargs):
        try:
            item = bottle.request.json
            item_route_id = kwargs[self._id_field_name]
            if u'id' in item and item[u'id'] != item_route_id:
                raise ItemHasConflictingId(
                    id=item[u'id'], wanted=item_route_id)
            if u'revision' not in item:
                raise NoItemRevision(id=item_route_id)
        except NoItemRevision:
            raise bottle.HTTPError(status=409)
        except unifiedapi.ValidationError:
            raise bottle.HTTPError(status=400)


class NewItemHasIdAlready(unifiedapi.ValidationError):

    msg = u'New item has id already set ({id!r}), which is not allowed'


class NewItemHasRevisionAlready(unifiedapi.ValidationError):

    msg = (
        u'New item has revision already set ({revision!r}), '
        u'which is not allowed')


class ItemHasConflictingId(unifiedapi.ValidationError):

    msg = u'Updated item {wanted} has conflicting id {id}'


class NoItemRevision(unifiedapi.ValidationError):

    msg = u'Item {id} has no revision'
