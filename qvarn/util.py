# util.py - random utility functions
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


'''Random utility functions for the backend.'''


import re

import yaml

import qvarn


# Matches <xx> but not <xx>xx<xx>.
route_to_scope_re = re.compile(r'<[^>]*>')


def route_to_scope(route_rule, request_method):
    ''' Gives an authorization scope string for a route and a HTTP method.
    '''
    route_scope = re.sub(route_to_scope_re, 'id', route_rule)
    route_scope = route_scope.replace(u'/', u'_')
    route_scope = u'uapi%s_%s' % (route_scope, request_method)
    return route_scope.lower()


def table_name(**kwargs):
    '''Construct a table name.

    Keyword arguments are:

    * resource_type (i.e., the type field in a resource)
    * list_field, for additional tables for resource fields that are
      lists (whether lists of strings or dicts)
    * subdict_list_field, for list fields in dicts in lists of dicts
    * inner_str_list-field, for a string list field in a dict in an
      inner dict list
    * subpath, for paths for sub-resources
    * auxtable, for auxiliary tables for things not directly visible in
      the resource, such as listeners and notifications

    Example: Assume the following resource in JSON:

        {
            "type": "agent",
            "names": ["James", "Jim"],
            "age": 40,
            "aliases": [
                {
                    "active": false,
                    "names": [
                        {
                            "alias": ["Jimbo"],
                        }
                    ]
                }
            ]
        }

    The following calls might be made:

    * Main table for the resource:
      table_name(resource_type='agent')

    * Table for the list of names:
      table_name(resource_type='agent', list_field='names')

    * Table for the list of aliases dicts:
      table_name(resource_type='agent', list_field='aliases')

    * Table for the list of names for aliases:
      table_name(resource_type='agent', list_field='aliases',
                 subdict_list_field='names')

    * Table for the list of names for alias names:
      table_name(resource_type='agent', list_field='aliases',
                 subdict_list_field='names',
                 inner_dict_list_field='alias')

    * Table for listeners for the resource type:
      table_name(resource_type='agent', auxtable='listeners')

    * Table for listener listen-on values:
      table_name(resource_type='agent', auxtable='listeners',
                 list_field='listen_on')

    '''

    resource_type = kwargs.get('resource_type', u'')
    list_field = kwargs.get('list_field', u'')
    subdict_list_field = kwargs.get('subdict_list_field', u'')
    inner_dict_list_field = kwargs.get('inner_dict_list_field', u'')
    subpath = kwargs.get('subpath', u'')
    auxtable = kwargs.get('auxtable', u'')

    # A decision list: each list item is a tuple (condition, result),
    # where condition is an argument-less function that can be called
    # and returns a boolean value. If the result is true, then the
    # result is used. If result is None, then an error is raised.
    # Otherwise, the result is a format string and it is formatted and
    # the result is returned as the value of the function.
    #
    # This uses lambda functions. These are fun.

    decisions = [
        (lambda: not resource_type, None),
        (lambda: inner_dict_list_field and
         (not subdict_list_field or not list_field), None),
        (lambda: subdict_list_field and not list_field, None),
        (lambda: auxtable and subpath, None),
        (lambda: auxtable and subdict_list_field, None),
        (lambda: auxtable and list_field,
         u'{resource_type}__aux_{auxtable}_{list_field}'),
        (lambda: auxtable, u'{resource_type}__aux_{auxtable}'),
        (lambda: subpath and list_field and subdict_list_field,
         u'{resource_type}__path_{subpath}_{list_field}_{subdict_list_field}'),
        (lambda: subpath and list_field,
         u'{resource_type}__path_{subpath}_{list_field}'),
        (lambda: subpath, u'{resource_type}__path_{subpath}'),
        (lambda: list_field and subdict_list_field and inner_dict_list_field,
         u'{resource_type}_{list_field}_{subdict_list_field}'
         u'_{inner_dict_list_field}'),
        (lambda: list_field and subdict_list_field,
         u'{resource_type}_{list_field}_{subdict_list_field}'),
        (lambda: list_field, u'{resource_type}_{list_field}'),
        (lambda: resource_type, u'{resource_type}'),
    ]

    for cond, result in decisions:
        if cond():
            if result is None:
                raise ComplicatedTableNameError()
            return result.format(**kwargs)

    # This is here just to guard against the decision list being
    # broken.
    assert False  # pragma: no cover


class ComplicatedTableNameError(qvarn.QvarnException):

    msg = (u'Internal error: tried to construct a database table name '
           u'that was too complicated')


def create_tables_for_resource_type(
        transaction, resource_type, prototype_list):  # pragma: no cover
    '''Create database tables for a resource type.

    This creates all the tables for one resource type, given a list of
    prototypes and additional information. The list of prototypes is
    a list of tuples (prototype, kwargs), where kwargs are given to
    schema_from_prototype (which gives them to qvarn.table_name).

    However, the resource type is given as a separate argument, so
    that it does not need to be repeated for each kwargs.

    For example:

        resource_type = u'foo'
        prototype_list = [
            (prototype, {}),
            (photo_prototype, {u'subpath': u'photo'}),
            (qvarn.listener_prototype, {u'auxtable': u'listener'}),
            (qvarn.notification_prototype,
             {u'auxtable': u'notification'}),
        ]

        create_tables_for_resource_type(
            transaction, resource_type, prototype_list)

    '''

    for prototype, kwargs in prototype_list:
        schema = qvarn.schema_from_prototype(
            prototype, resource_type=resource_type, **kwargs)
        create_tables_from_schema(transaction, schema)


def create_tables_from_schema(transaction, schema):  # pragma: no cover
    '''Create tables from a schema.

    See schema.py for what a schema is. The tables are assumed to
    not exist yet.

    '''

    tables = {}
    for table, column, column_type in schema:
        if table not in tables:
            tables[table] = {}
        tables[table][column] = column_type

    for table in tables:
        transaction.create_table(table, tables[table])


# We want to load strings as unicode, not str.
# From http://stackoverflow.com/questions/2890146/
# It seems this will be unnecessary in Python 3.

def set_up_yaml_loader_constructors():  # pragma: no cover

    def construct_yaml_str(self, node):
        # Override the default string handling function
        # to always return unicode objects. Except if the
        # resource type field is the string "blob" in which
        # case we use a buffer().
        if node.value == 'blob':
            return buffer('')
        return self.construct_scalar(node)

    yaml.SafeLoader.add_constructor(
        u'tag:yaml.org,2002:str', construct_yaml_str)


set_up_yaml_loader_constructors()
