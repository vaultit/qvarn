# string_to_unicode_plugin.py - formats path (and other) string arguments given
#                               to route methods to unicode
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


class StringToUnicodePlugin(object):

    '''Currently only transforms str args and kwargs to unicode.'''

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            new_args = self._format_args(args)
            new_kwargs = self._format_kwargs(kwargs)
            return callback(*new_args, **new_kwargs)
        return wrapper

    def _format_args(self, args):
        return (
            unicode(arg) if isinstance(arg, str) else arg
            for arg in args
        )

    def _format_kwargs(self, kwargs):
        return {
            key: unicode(arg) if isinstance(arg, str) else arg
            for key, arg in kwargs.iteritems()
        }
