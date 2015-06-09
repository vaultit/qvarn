# validate.py - validate an API item against an item prototype
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unifiedapi


class ItemValidator(object):

    '''Validate an item against a prototype.

    An item prototype looks like an item, but the value of each field
    gives the type of the field as follows:

        * A string is an empty Unicode string (``u''``).
        * An integer is the constant 0.
        * A boolean value is the constant False.
        * A list of strings is a list of an empty Unicode string.
        * A list of dicgts is a list of exactly one dict that
          is that dict's prototype.

    Note that the prototype can only specify the type of a value. It
    can't specify, say, that a list must not be empty. That kind of
    validation check needs to happen outside this class.

    All fields in the prototype are mandatory. No other fields are
    allows. Lists can always be empty.

    Every time must have a type field, and it must match the type
    given to the ``validate_item`` method.

    '''

    def validate_item(self, item_type, prototype, item):
        '''Validate an item.

        If there is any problem, a subclass of the
        ``ValidatationError`` exception is raised. Otherwise, no value
        is returned.

        '''

        # We need to validate here that the prototype and item are
        # both dicts. Otherwise we can't validate the type field. This
        # is an unfortunate duplication of the code in _validate_dict;
        # the code needs to be there as well, because _validate_dict
        # gets called for the dicts in list-of-dicts attributes of
        # items.
        self._validate_is_dict(prototype)
        self._validate_is_dict(item)

        if u'type' in prototype:
            self._validate_has_type_field(item)
            self._validate_type_field(item, item_type)

        self._validate_dict(prototype, item)

    def _validate_dict(self, prototype, item):
        self._validate_is_dict(prototype)
        self._validate_is_dict(item)
        self._validate_same_fields(prototype, item)
        for field_name in prototype:
            self._validate_field(prototype, item, field_name)

    def _validate_is_dict(self, thing):
        if type(thing) is not dict:
            raise ItemMustBeDict(type=type(thing))

    def _validate_has_type_field(self, thing):
        if u'type' not in thing:
            raise MustHaveTypeField(thing=thing)

    def _validate_same_fields(self, prototype, item):
        allowed_keys = set(prototype.keys())
        actual_keys = set(item.keys())
        missing_keys = allowed_keys.difference(actual_keys)
        if missing_keys:
            raise RequiredKeysMissing(keys=missing_keys)
        extra_keys = actual_keys.difference(allowed_keys)
        if extra_keys:
            raise UnknownKeys(keys=extra_keys)

    def _validate_type_field(self, item, required_type):
        if item[u'type'] != required_type:
            raise ItemHasWrongType(
                type=item[u'type'], required_type=required_type)

    def _validate_field(self, prototype, item, field_name):
        proto_value = prototype[field_name]
        item_value = item[field_name]

        simple_types = (unicode, bool, int)
        if type(proto_value) in simple_types:
            self._validate_simple_value(proto_value, item_value)
        elif type(proto_value) is list:
            self._validate_list_value(proto_value, item_value)
        else:
            raise InvalidValueInPrototype(
                field=field_name, type=type(proto_value))

    def _validate_simple_value(self, proto_value, item_value):
        if item_value is None:
            return
        if type(proto_value) != type(item_value):
            raise WrongTypeValue(
                proto_type=type(proto_value), item_type=type(item_value))

    def _validate_list_value(self, proto_value, item_value):
        if len(proto_value) != 1:
            raise PrototypeListMustHaveOneValue(proto=proto_value)
        if type(proto_value[0]) not in (unicode, dict):
            raise PrototypeListMustHaveStringsOrDicts(proto=proto_value)
        if type(item_value) is not list:
            raise ItemMustHaveList(type=type(item_value))
        if type(proto_value[0]) is unicode:
            self._validate_list_of_strings(item_value)
        elif type(proto_value[0]) is dict:
            self._validate_list_of_dicts(proto_value, item_value)

    def _validate_list_of_strings(self, item_value):
        for i, value in enumerate(item_value):
            if type(value) is not unicode:
                raise ItemListMustContainStrings(pos=i, value=value)

    def _validate_list_of_dicts(self, proto_value, item_value):
        for i, value in enumerate(item_value):
            if type(value) is not dict:
                raise ItemListMustContainStrings(pos=i, value=value)
            self._validate_dict(proto_value[0], value)


class ValidationError(unifiedapi.BackendException):

    pass


class ItemMustBeDict(ValidationError):

    msg = u'The item must be a mapping object (dict), not {type}'


class RequiredKeysMissing(ValidationError):

    msg = u'Required keys missing from item: {keys}'


class UnknownKeys(ValidationError):

    msg = u'Unknown keys in item: {keys}'


class WrongTypeValue(ValidationError):

    msg = (u'Item has a value of the wrong type: '
           '{proto_type} expected, instead of {item_type}.')


class PrototypeListMustHaveOneValue(ValidationError):

    msg = u'Prototype lists must have exactly one item: {proto}'


class PrototypeListMustHaveStringsOrDicts(ValidationError):

    msg = u'Prototype lists must have a string or dict value: {proto}'


class ItemMustHaveList(ValidationError):

    msg = u'Item must have a list value, not {type}'


class ItemListMustContainStrings(ValidationError):

    msg = (u'The list must contain strings, '
           u'but position {pos} has value {value}')


class ItemHasWrongType(ValidationError):

    msg = u'Item has type {type}, but {required_type} was expected'


class MustHaveTypeField(ValidationError):

    msg = u'Type field is missing: {thing!r}'


class InvalidValueInPrototype(ValidationError):

    msg = u'Item prototype has field {field} with bad type {type}'