# walker_tests.py - unit tests for ItemWalker
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


import copy
import unittest

import qvarn


class CatchingWalker(qvarn.ItemWalker):

    def __init__(self):
        self.caught = {}

    def catch_args(self, key, args):
        if key not in self.caught:
            self.caught[key] = []
        self.caught[key].append(args)

    def visit_main_dict(self, *args):
        self.catch_args(u'main_dict', args)

    def visit_main_str_list(self, *args):
        self.catch_args(u'main_str_list', args)

    def visit_main_dict_list(self, *args):
        self.catch_args(u'main_dict_list', args)

    def visit_dict_in_list(self, *args):
        self.catch_args(u'dict_in_list', args)

    def visit_dict_in_list_str_list(self, *args):
        self.catch_args(u'dict_in_list_str_list', args)

    def visit_inner_dict_list(self, *args):
        self.catch_args(u'inner_dict_list', args)

    def visit_dict_in_inner_list(self, *args):
        self.catch_args(u'dict_in_inner_list', args)

    def visit_dict_in_inner_list_str_list(self, *args):
        self.catch_args(u'dict_in_inner_list_str_list', args)


class ItemWalkerTests(unittest.TestCase):

    proto = {
        u'main_int': 0,
        u'main_str': u'',
        u'main_bool': False,
        u'main_str_list': [u'foo1', u'foo2'],
        u'main_dict_list': [
            {
                u'dict_int': 0,
                u'dict_str': u'',
                u'dict_bool': False,
                u'dict_str_list': [u'bar1', u'bar2'],
                u'inner_dict_list': [
                    {
                        u'inner_dict_str': u'yoyo1',
                        u'inner_str_list': [u'blah1', u'blah2'],
                    },
                ],
            },
            {
                u'dict2_int': 0,
                u'dict2_str': u'',
                u'dict2_bool': False,
                u'dict2_str_list': [u'yo1', u'yo2'],
                u'inner_dict_list': [
                    {
                        u'inner_dict_str': u'yoyo2',
                        u'inner_str_list': [u'meh1', u'meh2'],
                    },
                ],
            },
        ],
    }

    def setUp(self):
        self.iw = CatchingWalker()
        self.item = dict(self.proto)
        self.iw.walk_item(self.item, self.proto)

    def test_visits_top_level_simple_fields(self):
        self.assertEqual(
            self.iw.caught[u'main_dict'],
            [(self.proto, [u'main_bool', u'main_int', u'main_str'])])

    def test_visits_top_level_str_lists(self):
        self.assertEqual(
            self.iw.caught[u'main_str_list'],
            [(self.proto, u'main_str_list')])

    def test_visits_top_level_dict_lists(self):
        self.assertEqual(
            self.iw.caught[u'main_dict_list'],
            [(self.proto, u'main_dict_list',
              [u'dict_bool', u'dict_int', u'dict_str'])])

    def test_visits_dict_in_list(self):
        self.assertEqual(
            self.iw.caught[u'dict_in_list'],
            [
                (self.proto, u'main_dict_list', 0,
                 [u'dict_bool', u'dict_int', u'dict_str']),
                (self.proto, u'main_dict_list', 1,
                 [u'dict_bool', u'dict_int', u'dict_str']),
            ])

    def test_visits_dict_in_list_str_list(self):
        self.assertEqual(
            self.iw.caught[u'dict_in_list_str_list'],
            [
                (self.proto, u'main_dict_list', 0, u'dict_str_list'),
                (self.proto, u'main_dict_list', 1, u'dict_str_list'),
            ])

    def test_visits_inner_dict_list(self):
        self.maxDiff = None
        self.assertEqual(
            self.iw.caught[u'inner_dict_list'],
            [
                (self.proto, u'main_dict_list', u'inner_dict_list',
                 [u'inner_dict_str']),
            ])

    def test_visits_dict_in_inner_list(self):
        self.assertEqual(
            self.iw.caught[u'dict_in_inner_list'],
            [
                (self.proto, u'main_dict_list', 0,
                 u'inner_dict_list', 0,
                 [u'inner_dict_str']),
                (self.proto, u'main_dict_list', 1,
                 u'inner_dict_list', 0,
                 [u'inner_dict_str']),
            ])

    def tests_visits_str_list_in_inner_list(self):
        self.assertEqual(
            self.iw.caught['dict_in_inner_list_str_list'],
            [
                (self.proto, u'main_dict_list', 0,
                 u'inner_dict_list', 0, u'inner_str_list'),
                (self.proto, u'main_dict_list', 1,
                 u'inner_dict_list', 0, u'inner_str_list'),
            ])

    def test_defines_all_visitor_methods(self):
        iw = qvarn.ItemWalker()
        self.assertEqual(iw.walk_item(self.item, self.proto), None)

    def test_raises_error_if_too_deeply_nested(self):
        too_deep = {
            u'one': [
                {
                    u'two': [
                        {
                            u'three': [
                                {
                                    u'ugh': False,
                                },
                            ],
                        },
                    ],
                },
            ],
        }

        item = copy.deepcopy(too_deep)

        iw = qvarn.ItemWalker()
        with self.assertRaises(qvarn.TooDeeplyNestedPrototype):
            iw.walk_item(item, too_deep)
