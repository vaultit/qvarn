# storage_prep_tests.py - unit tests for StoragePreparer
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class CallCatcher(object):

    def __init__(self, order=None):
        self.called = False
        self.order = [] if order is None else order

    def run(self, db):
        self.order.append(self)
        self.called = True


class StoragePreparerTests(unittest.TestCase):

    def setUp(self):
        self.step = CallCatcher()
        self.prep = unifiedapi.StoragePreparer()
        self.db = unifiedapi.open_memory_database()

    def test_has_no_steps_by_default(self):
        self.assertEqual(self.prep.step_names, [])

    def test_adds_step(self):
        self.prep.add_step(u'catcher', self.step)
        self.assertEqual(self.prep.step_names, [u'catcher'])

    def test_raises_error_when_adding_duplicate_step_name(self):
        self.prep.add_step(u'catcher', self.step)
        with self.assertRaises(unifiedapi.BackendException):
            self.prep.add_step(u'catcher', self.step)

    def test_always_runs_mandatory_steps(self):
        self.prep.set_mandatory_steps([(u'catcher', self.step)])
        with self.db:
            self.prep.run(self.db)
        self.assertTrue(self.step.called)

    def test_runs_added_function_step(self):
        self.prep.add_step(u'catcher', self.step.run)
        with self.db:
            self.prep.run(self.db)
        self.assertTrue(self.step.called)

    def test_calls_added_objects_run_method(self):
        self.prep.add_step(u'catcher', self.step)
        with self.db:
            self.prep.run(self.db)
        self.assertTrue(self.step.called)

    def test_only_runs_step_if_needed(self):
        self.prep.add_step(u'catcher', self.step)

        with self.db:
            self.prep.run(self.db)
        self.assertTrue(self.step.called)

        self.step.called = False
        self.assertFalse(self.step.called)
        with self.db:
            self.prep.run(self.db)
        self.assertFalse(self.step.called)

    def test_runs_tests_in_order(self):
        order = []

        catcher1 = CallCatcher(order=order)
        catcher2 = CallCatcher(order=order)
        self.prep.add_step(u'catcher1', catcher1)
        self.prep.add_step(u'catcher2', catcher2)

        with self.db:
            self.prep.run(self.db)

        self.assertTrue(catcher1.called)
        self.assertTrue(catcher2.called)
        self.assertEqual(order, [catcher1, catcher2])
