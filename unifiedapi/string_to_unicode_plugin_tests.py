# string_to_unicode_plugin_tests.py - unit tests for StringToUnicodePlugin
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

import unittest

import unifiedapi


class StringToUnicodePluginTests(unittest.TestCase):

    def test_changes_str_args_to_unicode(self):
        def callback(arg):
            self.assertEqual(type(arg), unicode)
        wrapped = unifiedapi.StringToUnicodePlugin().apply(callback, None)
        wrapped('')

    def test_does_not_break_with_non_strings(self):
        def callback(arg):
            self.assertEqual(arg, None)
        wrapped = unifiedapi.StringToUnicodePlugin().apply(callback, None)
        wrapped(None)

    def test_changes_kwargs_to_unicode(self):
        def callback(arg=''):
            self.assertEqual(type(arg), unicode)
        wrapped = unifiedapi.StringToUnicodePlugin().apply(callback, None)
        wrapped(arg='')
