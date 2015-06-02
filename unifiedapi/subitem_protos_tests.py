# subitem_protos.py - unit tests for SubItemPrototypes
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


import unittest

import unifiedapi


class SubItemPrototypesTests(unittest.TestCase):

    def test_has_nothing_initially(self):
        sip = unifiedapi.SubItemPrototypes()
        self.assertEqual(sip.get_all(), [])

    def test_adds_prototype(self):
        sip = unifiedapi.SubItemPrototypes()
        prototype = {u'subifield': u''}
        sip.add(u'fooitem', u'foosub', prototype)
        self.assertEqual(sip.get_all(), [(u'foosub', prototype)])

    def test_gets_added_prototype(self):
        sip = unifiedapi.SubItemPrototypes()
        prototype = {u'subifield': u''}
        sip.add(u'fooitem', u'foosub', prototype)
        added = sip.get(u'fooitem', u'foosub')
        self.assertEqual(added, prototype)
