# args_format_plugin.py - transforms unifiedapi.HTTPError subclass based
#                         exceptions to HTTP JSON responses
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

import bottle

import unifiedapi


class ErrorTransformPlugin(object):

    '''Catches unifiedapi HTTPErrors and returns error as JSON instead.'''

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            try:
                result = callback(*args, **kwargs)
                return result
            except unifiedapi.HTTPError, e:
                bottle.response.status = e.status_code
                return {u'error': u'error'}
        return wrapper
