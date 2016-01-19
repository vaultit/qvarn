# filler_tests.py - unit tests for AddMissingItemFields
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import qvarn


class AddMissingItemFieldsTests(unittest.TestCase):

    prototype = {
        u'type': u'',
        u'a-string': u'',
        u'an-int': 0,
        u'a-boolean': False,
        u'list-of-strings': [u''],
        u'list-of-dicts': [
            {
                u'inner-string': u'',
                u'inner-int': 0,
                u'inner-boolean': False,
                u'inner-list-of-strings': [u''],
            },
        ],
    }

    def test_deals_with_non_dict(self):
        self.assertEqual(
            qvarn.add_missing_item_fields(
                u'foo-type', self.prototype, None),
            None)

    def test_adds_missing_type_field(self):
        item = {}
        qvarn.add_missing_item_fields(u'foo-type', self.prototype, item)
        self.assertEqual(item[u'type'], u'foo-type')

    def test_keeps_existing_type_field_even_if_wrong(self):
        item = {
            u'type': u'this-is-wrong',
        }
        qvarn.add_missing_item_fields(u'foo-type', self.prototype, item)
        self.assertEqual(item[u'type'], u'this-is-wrong')

    def test_adds_missing_fields(self):
        item = {}
        qvarn.add_missing_item_fields(u'foo-type', self.prototype, item)
        self.assertEqual(
            item,
            {
                u'type': u'foo-type',
                u'a-string': None,
                u'an-int': None,
                u'a-boolean': None,
                u'list-of-strings': [],
                u'list-of-dicts': [],
            })

    def test_adds_missing_inner_dict_fields(self):
        item = {
            u'list-of-dicts': [
                {
                },
            ],
        }
        qvarn.add_missing_item_fields(u'foo-type', self.prototype, item)
        self.assertEqual(
            item,
            {
                u'type': u'foo-type',
                u'a-string': None,
                u'an-int': None,
                u'a-boolean': None,
                u'list-of-strings': [],
                u'list-of-dicts': [
                    {
                        u'inner-string': None,
                        u'inner-int': None,
                        u'inner-boolean': None,
                        u'inner-list-of-strings': [],
                    },
                ],
            })
