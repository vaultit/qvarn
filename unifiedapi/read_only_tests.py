# read_only_tests.py - unit tests for ReadOnlyStorage
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class ReadOnlyStorageTests(unittest.TestCase):

    prototype = {
        u'type': u'',
        u'id': u'',
        u'foo': u'',
        u'bar': u'',
        u'bars': [u''],
        u'dicts': [
            {
                u'baz': u'',
                u'foobars': [u''],
                u'foo': [u''],
                u'bar': u'',
            },
        ],
    }

    item = {
        u'type': u'yo',
        u'foo': u'foobar',
        u'bar': u'barbaz',
        u'bars': [u'bar1', u'bar2'],
        u'dicts': [
            {
                u'baz': u'bling',
                u'foobars': [],
                u'foo': [],
                u'bar': u'bong',
            },
        ],
    }

    def create_tables(self, db):
        db.create_table(
            u'yo',
            (u'type', unicode),
            (u'id', unicode),
            (u'foo', unicode),
            (u'bar', unicode))
        db.create_table(
            u'yo_bars',
            (u'id', unicode),
            (u'list_pos', int),
            (u'bars', unicode))
        db.create_table(
            u'yo_dicts',
            (u'id', unicode),
            (u'list_pos', int),
            (u'baz', unicode),
            (u'bar', unicode))
        db.create_table(
            u'yo_dicts_foo',
            (u'id', unicode),
            (u'dict_list_pos', int),
            (u'list_pos', int),
            (u'foo', unicode))
        db.create_table(
            u'yo_dicts_foobars',
            (u'id', unicode),
            (u'dict_list_pos', int),
            (u'list_pos', int),
            (u'foobars', unicode))

    def setUp(self):
        db = unifiedapi.open_memory_database()

        self.ro = unifiedapi.ReadOnlyStorage()
        self.ro.set_db(db)
        self.ro.set_item_prototype(self.item[u'type'], self.prototype)

        prep = unifiedapi.StoragePreparer()
        prep.add_step(u'create-tables', self.create_tables)

        self.wo = unifiedapi.WriteOnlyStorage()
        self.wo.set_db(db)
        self.wo.set_item_prototype(self.item[u'type'], self.prototype)
        self.wo.set_preparer(prep)
        self.wo.prepare()

    def test_lists_no_items_initially(self):
        self.assertEqual(self.ro.get_item_ids(), [])

    def test_error_mentions_id(self):
        obj_id = u'this string is unlikely in an error message'
        e = unifiedapi.ItemDoesNotExist(id=obj_id)
        self.assertIn(obj_id, unicode(e))

    def test_raises_error_when_item_does_not_exist(self):
        with self.assertRaises(unifiedapi.ItemDoesNotExist):
            self.ro.get_item(u'does-not-exist')

    def test_lists_added_item(self):
        added = self.wo.add_item(self.item)
        self.assertIn(added[u'id'], self.ro.get_item_ids())

    def test_gets_added_item(self):
        added = self.wo.add_item(self.item)
        self.assertEqual(added, self.ro.get_item(added[u'id']))

    def test_search_main_item(self):
        added = self.wo.add_item(self.item)
        new_id = added[u'id']
        search_result = self.ro.get_search_matches(['exact'],
                                                   [u'foo'],
                                                   [u'foobar'])
        self.assertIn(new_id, search_result[u'matches'][0][u'id'])

    def test_search_main_list(self):
        added = self.wo.add_item(self.item)
        new_id = added[u'id']
        search_result = self.ro.get_search_matches(['exact'],
                                                   [u'bars'],
                                                   [u'bar1'])
        self.assertIn(new_id, search_result[u'matches'][0][u'id'])

    def test_search_multiple_conditions(self):
        added = self.wo.add_item(self.item)
        new_id = added[u'id']
        search_result = self.ro.get_search_matches(['exact', 'exact'],
                                                   [u'foo', u'bars'],
                                                   [u'foobar', u'bar1'])
        self.assertIn(new_id, search_result[u'matches'][0][u'id'])

    def test_search_multiple_conditions_from_same_table(self):
        added = self.wo.add_item(self.item)
        new_id = added[u'id']
        search_result = self.ro.get_search_matches(['exact', 'exact'],
                                                   [u'foo', u'type'],
                                                   [u'foobar', u'yo'])
        self.assertIn(new_id, search_result[u'matches'][0][u'id'])

    def test_search_condition_with_multiple_targets(self):
        added = self.wo.add_item(self.item)
        new_id = added[u'id']
        search_result = self.ro.get_search_matches(['exact', 'exact'],
                                                   [u'bar'],
                                                   [u'barbaz'])
        match_list = search_result[u'matches']
        self.assertIsNot(0, len(match_list))
        self.assertIn(new_id, match_list[0][u'id'])
