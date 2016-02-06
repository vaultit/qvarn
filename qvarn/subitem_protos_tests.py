# subitem_protos.py - unit tests for SubItemPrototypes
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


class SubItemPrototypesTests(unittest.TestCase):

    def test_has_nothing_initially(self):
        sip = qvarn.SubItemPrototypes()
        self.assertEqual(sip.get_all(), [])

    def test_adds_prototype(self):
        sip = qvarn.SubItemPrototypes()
        prototype = {u'subifield': u''}
        sip.add(u'fooitem', u'foosub', prototype)
        self.assertEqual(sip.get_all(), [(u'foosub', prototype)])

    def test_gets_added_prototype(self):
        sip = qvarn.SubItemPrototypes()
        prototype = {u'subifield': u''}
        sip.add(u'fooitem', u'foosub', prototype)
        added = sip.get(u'fooitem', u'foosub')
        self.assertEqual(added, prototype)
