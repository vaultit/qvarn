# walker_tests.py - unit tests for ItemWalker
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class CatchingWalker(unifiedapi.ItemWalker):

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
            },
            {
                u'dict2_int': 0,
                u'dict2_str': u'',
                u'dict2_bool': False,
                u'dict2_str_list': [u'yo1', u'yo2'],
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

    def test_defines_all_visitor_methods(self):
        iw = unifiedapi.ItemWalker()
        self.assertEqual(iw.walk_item(self.item, self.proto), None)
