# basic_validation_plugin.py - does basic validation for JSON resources
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

# Pylint doesn't fully understand what bottle does and doesn't know
# about all the members in all the objects. Disable related warnigs for
# this module.
#
# pylint: disable=unsubscriptable-object
# pylint: disable=unsupported-membership-test

import json

import bottle

import qvarn


class BasicValidationPlugin(object):

    '''Perform basic validation for JSON resource POST and PUT.

    This is a Bottle plugin.

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
        if bottle.request.content_type != 'application/json':
            raise ContentIsNotJSON()
        try:
            obj = json.load(bottle.request.body)
        except ValueError:
            raise ContentIsNotJSON()

        bottle.request.qvarn_json = obj
        qvarn.log.log(
            'json-parse',
            obj_repr=repr(obj),
            qvarn_json_repr=repr(bottle.request.qvarn_json))

    def _check_create_json(self):
        item = bottle.request.qvarn_json
        if u'id' in item:
            raise NewItemHasIdAlready(item_id=item[u'id'])
        if u'revision' in item:
            raise NewItemHasRevisionAlready(revision=item[u'revision'])

    def _check_update_json(self, kwargs):
        item = bottle.request.qvarn_json
        item_route_id = kwargs[self._id_field_name]
        if u'id' in item and item[u'id'] != item_route_id:
            raise ItemHasConflictingId(
                item_id=item[u'id'], wanted_id=item_route_id)
        if u'revision' not in item:
            raise NoItemRevision(item_id=item_route_id)


class ContentIsNotJSON(qvarn.BadRequest):

    msg = u'Request content is not valid JSON'


class ContentTypeIsNotJSON(qvarn.UnsupportedMediaType):

    msg = u'Content-Type must be application/json'


class NewItemHasIdAlready(qvarn.ValidationError):

    msg = u'New item has id already set'


class NewItemHasRevisionAlready(qvarn.ValidationError):

    msg = u'New item has revision already set'


class ItemHasConflictingId(qvarn.ValidationError):

    msg = u'Updated item has conflicting id'


class NoItemRevision(qvarn.Conflict):

    msg = u'Item has no revision'
