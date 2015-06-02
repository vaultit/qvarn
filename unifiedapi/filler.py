# filler.py - fill an item's missing fields with default values
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


def add_missing_item_fields(item_type, prototype, item):

    '''Add missing fields to an item, with default values.'''

    # If the item is not a dict, it's not a valid item, and so we
    # don't fill in any defaults. The actual error will be caught by
    # validation, so we don't need to react to it here. (Famous last
    # words.)

    if type(item) is not dict:
        return

    if u'type' not in item and u'type' in prototype:
        item[u'type'] = item_type

    _fill_in_dict_fields(prototype, item)

    for field_name in prototype:
        if _is_list_of_dicts(prototype[field_name]):
            for some_dict in item[field_name]:
                if type(some_dict) is dict:
                    _fill_in_dict_fields(prototype[field_name][0], some_dict)


def _fill_in_dict_fields(proto_dict, some_dict):
    for field_name in proto_dict:
        if field_name not in some_dict:
            some_dict[field_name] = _default_value(proto_dict, field_name)


def _default_value(proto, field_name):
    # There is no default value for a dict: we never, ever allow an
    # empty dict in an item, so it's not possible to need a default
    # dict value. The defaults come via the prototype. If we ever get
    # this far and the prototype field is a dict, something's wrong
    # and we crash so that there's a stacktrace to aid debugging.

    defaults_by_type = {
        int: None,
        unicode: None,
        bool: None,
        list: [],
    }

    return defaults_by_type[type(proto[field_name])]


def _is_list_of_dicts(value):
    return type(value) is list and value and type(value[0]) is dict
