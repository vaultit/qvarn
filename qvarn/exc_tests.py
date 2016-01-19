# exc_tests.py - unit tests for BackendException
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import qvarn


class DummyException(qvarn.BackendException):

    msg = u'dummy msg'


class AnotherDummyException(qvarn.BackendException):

    msg = u'another dummy msg'


class BackendExceptionTests(unittest.TestCase):

    def test_stores_keyword_arguments_in_error(self):
        e = DummyException(param=123)
        self.assertIn(u'param', e.error)
        self.assertEqual(e.error[u'param'], 123)

    def test_generates_error_code(self):
        e = DummyException()
        self.assertIn(u'error_code', e.error)

    def test_generates_same_error_code_for_objects_of_same_class(self):
        e = DummyException()
        e2 = DummyException(test=u'Nope')
        self.assertEqual(e.error[u'error_code'], e2.error[u'error_code'])

    def test_generates_different_error_codes_for_different_subclass_objs(self):
        e = DummyException()
        e2 = AnotherDummyException()
        self.assertNotEqual(e.error[u'error_code'], e2.error[u'error_code'])
