# exc_tests.py - unit tests for BackendException
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class DummyException(unifiedapi.BackendException):

    msg = u'dummy msg {param}'


class BackendExceptionTests(unittest.TestCase):

    def test_stores_keyword_arguments(self):
        e = DummyException(param=123)
        self.assertEqual(e.kwargs, {'param': 123})

    def test_raises_exception_if_keyword_argument_is_missing(self):
        with self.assertRaises(KeyError):
            DummyException()

    def test_formats_as_string(self):
        e = DummyException(param=123)
        self.assertIn('123', str(e))
