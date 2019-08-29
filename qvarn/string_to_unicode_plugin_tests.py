# string_to_unicode_plugin_tests.py - unit tests for StringToUnicodePlugin
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


import unittest

import six

import qvarn


class StringToUnicodePluginTests(unittest.TestCase):

    def test_changes_str_args_to_unicode(self):
        def callback(arg):
            self.assertEqual(type(arg), six.text_type)
        wrapped = qvarn.StringToUnicodePlugin().apply(callback, None)
        wrapped(b'')

    def test_changes_utf8_args_to_unicode(self):
        def callback(arg):
            self.assertEqual(type(arg), six.text_type)
        wrapped = qvarn.StringToUnicodePlugin().apply(callback, None)
        wrapped(b'\xc3\xb6l\xc3\xb6l\xc3\xb6l\xc3\xb6')

    def test_does_not_break_with_non_strings(self):
        def callback(arg):
            self.assertEqual(arg, None)
        wrapped = qvarn.StringToUnicodePlugin().apply(callback, None)
        wrapped(None)

    def test_changes_kwargs_to_unicode(self):
        def callback(arg=''):
            self.assertEqual(type(arg), six.text_type)
        wrapped = qvarn.StringToUnicodePlugin().apply(callback, None)
        wrapped(arg=b'')

    def test_changes_utf8_kwargs_to_unicode(self):
        def callback(arg=''):
            self.assertEqual(type(arg), six.text_type)
        wrapped = qvarn.StringToUnicodePlugin().apply(callback, None)
        wrapped(arg=b'\xc3\xb6l\xc3\xb6l\xc3\xb6l\xc3\xb6')
