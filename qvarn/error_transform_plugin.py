# error_transform_plugin.py - transforms qvarn.BackendExceptions
#                             to HTTP JSON responses
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

import bottle

import qvarn


class ErrorTransformPlugin(object):

    '''Catches a qvarn.BackendException and returns error as dict instead.

    Uses BackendException error attribute as the to-be-JSONified dict and also
    sets the response error status code to HTTPError status_code.
    '''

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            try:
                result = callback(*args, **kwargs)
                return result
            except qvarn.BackendException, e:
                bottle.response.status = e.status_code
                return e.error
        return wrapper
