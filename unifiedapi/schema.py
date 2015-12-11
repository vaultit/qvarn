# schema.py - implement database schemas based on prototypes
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


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


class SchemaWalker(unifiedapi.ItemWalker):

    def __init__(self, schema, table_name_kwargs):
        self._schema = schema
        self._table_name_kwargs = table_name_kwargs

    def visit_main_dict(self, item, column_names):
        table_name = unifiedapi.table_name(**self._table_name_kwargs)
        for name in column_names:
            self._add_column(table_name, name, type(item[name]))

    def _add_column(self, table_name, column_name, column_type):
        self._schema.append((table_name, column_name, column_type))

    def visit_main_str_list(self, item, field):
        table_name = unifiedapi.table_name(
            list_field=field, **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'list_pos', int)
        self._add_column(table_name, field, unicode)

    def visit_main_dict_list(self, item, field, column_names):
        table_name = unifiedapi.table_name(
            list_field=field, **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'list_pos', int)
        for column_name in column_names:
            column_type = type(item[field][0][column_name])
            self._add_column(table_name, column_name, column_type)

    def visit_dict_in_list_str_list(self, item, field, pos, str_list_field):
        table_name = unifiedapi.table_name(
            list_field=field,
            subdict_list_field=str_list_field,
            **self._table_name_kwargs)
        self._add_column(table_name, u'id', unicode)
        self._add_column(table_name, u'dict_list_pos', int)
        self._add_column(table_name, u'list_pos', int)
        self._add_column(table_name, str_list_field, unicode)
