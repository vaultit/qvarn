# schema.py - implement database schemas based on prototypes
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


import qvarn


def schema_from_prototype(prototype, resource_type=None, **kwargs):
    '''Produce a schema (list of triplets) from a resource prototype.

    The list has triplets of the form (table name, column name, column
    type). The resource_type keyword argument MUST be given.

    If the prototype does not have an "id" field, an "id" column is
    added to the schema anyway. Sub-resources shouldn't have a
    resource identifier, but their database schema needs one anyway,
    so that they can be found given the main resource.

    '''

    assert resource_type is not None
    kwargs['resource_type'] = prototype.get(u'type', None) or resource_type

    # Add id field if missing.
    if u'id' not in prototype:
        prototype = dict(prototype)
        prototype[u'id'] = u''

    schema = []
    walker = SchemaWalker(schema, kwargs)
    walker.walk_item(prototype, prototype)
    return schema


class SchemaWalker(qvarn.ItemWalker):

    def __init__(self, schema, table_name_kwargs):
        self._schema = schema
        self._table_name_kwargs = table_name_kwargs

    def visit_main_dict(self, item, column_names):
        table_name = qvarn.table_name(**self._table_name_kwargs)
        for name in column_names:
            self._add_column(table_name, name, type(item[name]))

    def _add_column(self, table_name, column_name, column_type):
        self._schema.append((table_name, column_name, column_type))

    def visit_main_str_list(self, item, field):
        table_name = qvarn.table_name(
            list_field=field, **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'list_pos', int)
        self._add_column(table_name, field, unicode)

    def visit_main_dict_list(self, item, field, column_names):
        table_name = qvarn.table_name(
            list_field=field, **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'list_pos', int)
        for column_name in column_names:
            column_type = type(item[field][0][column_name])
            self._add_column(table_name, column_name, column_type)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = qvarn.table_name(
            list_field=field,
            subdict_list_field=str_list_field,
            **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'dict_list_pos', int)
        self._add_column(table_name, u'list_pos', int)
        self._add_column(table_name, str_list_field, unicode)

    def visit_inner_dict_list(self, item, field, inner_field, simple_columns):
        table_name = qvarn.table_name(
            list_field=field,
            subdict_list_field=inner_field,
            **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'dict_list_pos', int)
        self._add_column(table_name, u'list_pos', int)
        for column_name in simple_columns:
            column_type = type(item[field][0][inner_field][0][column_name])
            self._add_column(table_name, column_name, column_type)
