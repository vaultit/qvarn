# string_to_unicode_plugin.py - formats path (and other) string arguments given
#                               to route methods to unicode
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


class StringToUnicodePlugin(object):

    '''Bottle plugin to transform str in args and kwargs values to unicode.'''

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            new_args = self._format_args(args)
            new_kwargs = self._format_kwargs(kwargs)
            return callback(*new_args, **new_kwargs)
        return wrapper

    def _format_args(self, args):
        return (
            arg.decode('utf-8') if isinstance(arg, bytes) else arg
            for arg in args
        )

    def _format_kwargs(self, kwargs):
        return {
            key: arg.decode('utf-8') if isinstance(arg, bytes) else arg
            for key, arg in kwargs.items()
        }
