# filler.py - fill an item's missing fields with default values
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


def add_missing_item_fields(item_type, prototype, item):

    '''Add missing fields to an item, with default values.'''

    # If the item is not a dict, it's not a valid item, and so we
    # don't fill in any defaults. The actual error will be caught by
    # validation, so we don't need to react to it here. (Famous last
    # words.)

    if not isinstance(item, dict):
        return

    if u'type' not in item and u'type' in prototype:
        item[u'type'] = item_type

    _fill_in_dict_fields(prototype, item)


def _fill_in_dict_fields(proto_dict, some_dict):
    for field_name in proto_dict:
        if field_name not in some_dict:
            some_dict[field_name] = _default_value(proto_dict, field_name)

    for field_name in proto_dict:
        if _is_list_of_dicts(proto_dict[field_name]):
            for field in some_dict[field_name]:
                if isinstance(field, dict):
                    _fill_in_dict_fields(proto_dict[field_name][0], field)


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
    return isinstance(value, list) and value and isinstance(value[0], dict)
