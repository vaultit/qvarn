# list_resource.py - implement API for multi-item resources such as /persons
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
# pylint: disable=no-member
# pylint: disable=unsubscriptable-object


'''Multi-item resources in the HTTP API.'''


import urllib
import urlparse
import json

import bottle

import qvarn


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
        self._item_validator = self._no_validator
        self._subitem_prototypes = qvarn.SubItemPrototypes()
        self._listener = None
        self._dbconn = None

    def _no_validator(self, item):  # pragma: no cover
        return

    def set_path(self, path):
        '''Set path of the top level resource, e.g., /persons.'''
        self._path = path

    def set_item_type(self, item_type):
        '''Set the type of items, e.g., u'person'.'''
        self._item_type = item_type

    def set_item_prototype(self, item_prototype):
        '''Set the prototype for each sub-item.'''
        self._item_prototype = item_prototype

    def set_item_validator(self, item_validator):  # pragma: no cover
        '''Set function to provide item-specific validation.

        Note that ``item_validator`` does not need to do generic
        validation against the prototype, as that is handled
        automatically.

        '''

        self._item_validator = item_validator or self._no_validator

    def set_subitem_prototype(
            self, subitem_name, prototype):  # pragma: no cover
        '''Set prototype for a subitem.'''
        self._subitem_prototypes.add(self._item_type, subitem_name, prototype)

    def set_listener(self, listener):
        '''Set the listener for this resource.

        A listener must have methods ``notify_create``, ``notify_update``
        and ``notify_delete``. ListenerResource implements these methods
        and has a more detailed description of them.
        '''
        self._listener = listener

    def prepare_resource(self, dbconn):  # pragma: no cover
        '''Prepare the resource for action.'''

        self._dbconn = dbconn

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
                'apply': qvarn.BasicValidationPlugin(),
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
                'apply': qvarn.BasicValidationPlugin(u'item_id'),
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
                    'apply': qvarn.BasicValidationPlugin(u'item_id'),
                }
            ])

        return item_paths + subitem_paths

    def get_items(self):  # pragma: no cover
        '''Serve GET /foos to list all items.'''
        ro = self._create_ro_storage()
        with self._dbconn.transaction() as t:
            return {
                'resources': [
                    {'id': resource_id} for resource_id in ro.get_item_ids(t)
                ],
            }

    def get_matching_items(self, search_criteria):  # pragma: no cover
        '''Serve GET /foos/search to list items matching search criteria.'''

        # We need criteria to be encoded so that when we split by slash (/),
        # we split the criteria correctly and keep the slashes in the
        # condition values.
        # We use REQUEST_URI provided by uWSGI instead of bottle's default
        # that uses decoded PATH_INFO.
        request_uri = bottle.request.environ['REQUEST_URI']
        # Split at the first "/search/" and take the part after it
        search_criteria = request_uri.split('/search/', 1)[1]

        criteria = [urllib.unquote(c).decode('utf8')
                    for c in search_criteria.split('/')]

        search_params = []
        show_params = []
        sort_params = []
        limit = None
        offset = None
        search_any = False

        any_opers = [
            u'exact',
            u'startswith',
            u'contains',
        ]

        opers = [
            u'exact',
            u'gt',
            u'ge',
            u'lt',
            u'le',
            u'ne',
            u'startswith',
            u'contains',
        ]
        i = 0
        while i < len(criteria):
            part = criteria[i]
            if part in opers:
                if i + 2 >= len(criteria):
                    raise BadSearchCondition()
                matching_rule = part
                search_field = criteria[i + 1]
                search_value = criteria[i + 2]
                if search_any:
                    try:
                        search_value = json.loads(search_value)
                    except ValueError as e:
                        raise BadAnySearchValue(error=str(e))
                    if not isinstance(search_value, list):
                        raise BadAnySearchValue(
                            error=u"%r is not a list" % search_value)
                search_param = qvarn.create_search_param(
                    matching_rule, search_field, search_value,
                    any=search_any,
                )
                search_params.append(search_param)
                search_any = False
                i += 3
            elif part == u'show_all':
                show_params.append(part)
                i += 1
            elif part == u'show':
                if i + 1 >= len(criteria):
                    raise BadSearchCondition()
                show_params.append((part, criteria[i + 1]))
                i += 2
            elif part == u'sort':
                sort_field = criteria[i + 1]
                sort_params.append(sort_field)
                i += 2
            elif part == u'limit':
                try:
                    limit = int(criteria[i + 1])
                except ValueError as e:
                    raise BadLimitValue(error=str(e))
                if limit < 0:
                    raise BadLimitValue(error="should be positive integer")
                i += 2
            elif part == u'offset':
                try:
                    offset = int(criteria[i + 1])
                except ValueError as e:
                    raise BadOffsetValue(error=str(e))
                if offset < 0:
                    raise BadOffsetValue(error="should be positive integer")
                i += 2
            elif part == u'any':
                if (i + 1) >= len(criteria):
                    raise MissingAnyOperator()
                elif criteria[i + 1] not in any_opers:
                    raise InvalidAnyOperator(
                        allowed_operators=', '.join(any_opers),
                        given_operator=criteria[i + 1],
                    )
                search_any = True
                i += 1
            else:
                raise BadSearchCondition()

        if (limit is not None or offset is not None) and not sort_params:
            raise LimitWithoutSortError()

        ro = self._create_ro_storage()
        with self._dbconn.transaction() as t:
            return ro.search(t, search_params, show_params, sort_params,
                             limit=limit, offset=offset)

    def post_item(self):  # pragma: no cover
        '''Serve POST /foos to create a new item.'''

        item = bottle.request.qvarn_json
        qvarn.add_missing_item_fields(
            self._item_type, self._item_prototype, item)

        iv = qvarn.ItemValidator()
        iv.validate_item(self._item_type, self._item_prototype, item)
        self._item_validator(item)

        # Filling in default values sets the fields to None, if
        # missing. Thus we accept that and just remove it here.
        del item[u'id']
        del item[u'revision']

        wo = self._create_wo_storage()
        with self._dbconn.transaction() as t:
            added = wo.add_item(t, item)

        self._listener.notify_create(added[u'id'], added[u'revision'])
        resource_path = u'%s/%s' % (self._path, added[u'id'])
        resource_url = urlparse.urljoin(
            bottle.request.url, resource_path)
        # FIXME: Force https scheme, until haproxy access us via https.
        resource_url = urlparse.urlunparse(
            ('https',) + urlparse.urlparse(resource_url)[1:])
        bottle.response.headers['Location'] = resource_url
        bottle.response.status = 201
        return added

    def get_item(self, item_id):  # pragma: no cover
        '''Serve GET /foos/123 to get an existing item.'''
        ro = self._create_ro_storage()
        with self._dbconn.transaction() as t:
            return ro.get_item(t, item_id)

    def get_subitem(self, item_id, subitem_path):  # pragma: no cover
        '''Serve GET /foos/123/subitem.'''
        ro = self._create_ro_storage()
        with self._dbconn.transaction() as t:
            subitem = ro.get_subitem(t, item_id, subitem_path)
            item = ro.get_item(t, item_id)

        subitem[u'revision'] = item[u'revision']
        return subitem

    def put_item(self, item_id):  # pragma: no cover
        '''Serve PUT /foos/123 to update an item.'''

        item = bottle.request.qvarn_json

        qvarn.add_missing_item_fields(
            self._item_type, self._item_prototype, item)

        iv = qvarn.ItemValidator()
        iv.validate_item(self._item_type, self._item_prototype, item)
        item[u'id'] = item_id
        self._item_validator(item)

        wo = self._create_wo_storage()
        with self._dbconn.transaction() as t:
            updated = wo.update_item(t, item)

        self._listener.notify_update(updated[u'id'], updated[u'revision'])
        return updated

    def put_subitem(self, item_id, subitem_name):  # pragma: no cover
        '''Serve PUT /foos/123/subitem to update a subitem.'''

        subitem = bottle.request.qvarn_json

        subitem_type = u'%s_%s' % (self._item_type, subitem_name)
        prototype = self._subitem_prototypes.get(self._item_type, subitem_name)
        qvarn.add_missing_item_fields(subitem_type, prototype, subitem)

        iv = qvarn.ItemValidator()
        revision = subitem.pop(u'revision')
        iv.validate_item(subitem_type, prototype, subitem)

        wo = self._create_wo_storage()
        with self._dbconn.transaction() as t:
            subitem[u'revision'] = wo.update_subitem(
                t, item_id, revision, subitem_name, subitem)

        updated = dict(subitem)
        updated.update({u'id': item_id})
        self._listener.notify_update(updated[u'id'], updated[u'revision'])
        return subitem

    def delete_item(self, item_id):  # pragma: no cover
        '''Serve DELETE /foos/123 to delete an item.'''
        wo = self._create_wo_storage()
        with self._dbconn.transaction() as t:
            wo.delete_item(t, item_id)
        self._listener.notify_delete(item_id)

    def _create_ro_storage(self):  # pragma: no cover
        ro = qvarn.ReadOnlyStorage()
        ro.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            ro.set_subitem_prototype(self._item_type, subitem_name, prototype)
        return ro

    def _create_wo_storage(self):  # pragma: no cover
        wo = qvarn.WriteOnlyStorage()
        wo.set_item_prototype(self._item_type, self._item_prototype)
        for subitem_name, prototype in self._subitem_prototypes.get_all():
            wo.set_subitem_prototype(self._item_type, subitem_name, prototype)
        return wo

    def _create_resource_ro_storage(
            self, resource_name, prototype):  # pragma: no cover
        ro = qvarn.ReadOnlyStorage()
        ro.set_item_prototype(resource_name, prototype)
        return ro

    def _create_resource_wo_storage(
            self, resource_name, prototype):  # pragma: no cover
        wo = qvarn.WriteOnlyStorage()
        wo.set_item_prototype(resource_name, prototype)
        return wo


class BadSearchCondition(qvarn.BadRequest):

    msg = u'Could not parse search condition'


class LimitError(qvarn.BadRequest):
    pass


class LimitWithoutSortError(LimitError):

    msg = u'LIMIT and OFFSET can only be used with together SORT.'


class BadLimitValue(LimitError):

    msg = u'Invalid LIMIT value: {error}.'


class BadOffsetValue(LimitError):

    msg = u'Invalid OFFSET value: {error}.'


class BadAnySearchValue(qvarn.BadRequest):

    msg = u"Can't parse ANY search value: {error}."


class InvalidAnyOperator(qvarn.BadRequest):

    msg = (
        u"Only one of {allowed_operators} operators can be used with /any/, "
        u"got /{given_operator}/."
    )


class MissingAnyOperator(qvarn.BadRequest):

    msg = u"Operator was not provided for /any/ condition."
