# idgen_tests.py - unit tests for ResourceIdGenerator
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import qvarn


class ResourceIdGeneratorTests(unittest.TestCase):

    def test_returns_a_unicode_string(self):
        rig = qvarn.ResourceIdGenerator()
        resource_id = rig.new_id(u'person')
        self.assertEqual(type(resource_id), unicode)

    def test_returns_new_values_each_time(self):
        rig = qvarn.ResourceIdGenerator()
        id_1 = rig.new_id(u'person')
        id_2 = rig.new_id(u'person')
        self.assertNotEqual(id_1, id_2)
