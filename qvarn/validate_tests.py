# validate_tests.py - unit tests for ItemValidator
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


class ItemValidatorTests(unittest.TestCase):

    def assertValidItem(self, item_type, prototype, item):
        iv = qvarn.ItemValidator()

        # We check that validation succeeds by making sure
        # validat_item returns from the call. Any validation errors
        # result in an exception, so a return means valid. The method
        # returns no value, so we compare to None.
        self.assertEqual(iv.validate_item(item_type, prototype, item), None)

    def assertNotValidItem(self, item_type, prototype, item):
        iv = qvarn.ItemValidator()
        with self.assertRaises(qvarn.ValidationError):
            iv.validate_item(item_type, prototype, item)

    def test_rejects_prototype_that_is_not_a_dict(self):
        self.assertNotValidItem(
            u'foo-type',
            [],
            {
                u'type': u'foo-type',
            })

    def test_rejects_prototype_with_field_that_has_bad_type(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': 1.0,
            },
            {
                u'type': u'foo-type',
                u'foo': 1.0,
            })

    def test_rejects_prototype_with_empty_list(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': []
            },
            {
                u'type': u'foo-type',
                u'foo': []
            })

    def test_rejects_prototype_with_long_list(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'', u'']
            },
            {
                u'type': u'foo-type',
                u'foo': []
            })

    def test_rejects_prototype_with_list_of_not_strings_or_dicts(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [0]
            },
            {
                u'type': u'foo-type',
                u'foo': []
            })

    def test_rejects_non_dictionary_item(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
            },
            [])

    def test_rejects_non_minimal_item_with_minimal_prototype(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
            },
            {
                u'type': 'foo-type',
                u'foo': u'bar'
            })

    def test_rejects_item_with_extra_field(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': u'',
            },
            {
                u'type': u'foo-type',
                u'foo': u'this is foo',
                u'bar': u'this is bar',
            })

    def test_rejects_item_with_missing_field(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': u''
            },
            {
                u'type': u'foo-type',
            })

    def test_accepts_item_with_correct_type(self):
        self.assertValidItem(
            u'bar',
            {
                u'type': u''
            },
            {
                u'type': u'bar'
            })

    def test_rejects_item_without_type(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
            },
            {
            })

    def test_rejects_item_with_wrong_type(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
            },
            {
                u'type': u'bar',
            })

    def test_accepts_simple_string_field(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': u''
            },
            {
                u'type': u'foo-type',
                u'foo': u'foo'
            })

    def test_accepts_missing_string_value(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': u''
            },
            {
                u'type': u'foo-type',
                u'foo': None
            })

    def test_rejects_field_value_that_is_not_a_string(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': u''
            },
            {
                u'type': u'foo-type',
                u'foo': 123
            })

    def test_accepts_simple_integer_field(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': 0
            },
            {
                u'type': u'foo-type',
                u'foo': 42
            })

    def test_accepts_missing_integer_value(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': 0
            },
            {
                u'type': u'foo-type',
                u'foo': None
            })

    def test_rejects_field_value_that_is_not_an_integer(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': 0
            },
            {
                u'type': u'foo-type',
                u'foo': u''
            })

    def test_accepts_simple_boolean_field(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': False
            },
            {
                u'type': u'foo-type',
                u'foo': True
            })

    def test_accepts_missing_boolean_value(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': True
            },
            {
                u'type': u'foo-type',
                u'foo': None
            })

    def test_rejects_field_value_that_is_not_boolean(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': True
            },
            {
                u'type': u'foo-type',
                u'foo': 123
            })

    def test_accepts_list_of_strings(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': [u'this is foo']
            })

    def test_accepts_empty_list_of_strings(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': []
            })

    def test_rejects_None_as_list_of_strings(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': None
            })

    def test_rejects_string_as_list_of_strings(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': u'this-looks-too-much-like-a-list',
            })

    def test_rejects_list_of_integers(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': [0]
            })

    def test_rejects_list_of_dicts(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [u'']
            },
            {
                u'type': u'foo-type',
                u'foo': [{}]
            })

    def test_accepts_list_of_dicts(self):
        self.assertValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [
                    {
                        u'bar': u''
                    }
                ],
            },
            {
                u'type': u'foo-type',
                u'foo': [
                    {
                        u'bar': u'this is bar'
                    }
                ],
            })

    def test_rejects_list_of_not_dicts(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [
                    {
                        u'bar': u''
                    }
                ],
            },
            {
                u'type': u'foo-type',
                u'foo': [u'yo'],
            })

    def test_reject_if_internal_dicts_do_not_match(self):
        self.assertNotValidItem(
            u'-foo-type',
            {
                u'type': u'',
                u'foo': [
                    {
                        u'bar': u''
                    }
                ],
            },
            {
                u'type': u'foo-type',
                u'foo': [
                    {
                        u'yo': u'this is yo'
                    }
                ],
            })

    def test_reject_if_prototype_has_empty_list(self):
        self.assertNotValidItem(
            u'foo-type',
            {
                u'type': u'',
                u'foo': [],
            },
            {
                u'type': u'foo-type',
                u'foo': [],
            })
