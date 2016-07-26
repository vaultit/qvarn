# exc_tests.py - unit tests for QvarnException
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

import qvarn


class DummyException(qvarn.QvarnException):

    msg = u'dummy msg'


class AnotherDummyException(qvarn.QvarnException):

    msg = u'another dummy msg'


class QvarnExceptionTests(unittest.TestCase):

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

    def test_stringifies(self):
        e = DummyException()
        self.assertTrue(isinstance(str(e), str))
