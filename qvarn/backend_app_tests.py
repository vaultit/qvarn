# Copyright 2017 QvarnLabs Ltd
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

import yaml

import qvarn


# pylint: disable=protected-access
class BackendApplicationTests(unittest.TestCase):
    spec_text = '''\
    path: /orgs
    type: org
    versions:
      - version: v0
        prototype: {id: '', revision: '', type: '', param: ''}
    '''

    def setUp(self):
        self.app = qvarn.BackendApplication()
        self.app._dbconn = qvarn.DatabaseConnection()
        self.app._dbconn.set_sql(qvarn.SqliteAdapter())
        self.spec = yaml.safe_load(self.spec_text)

        with self.app._dbconn.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            rts.add_or_update_spec(t, self.spec, self.spec_text)

    def test_get_spec_for_resource_type(self):
        path = u'/'
        self.assertEqual(self.app._get_spec_for_resource_type(path), None)

        path = u'/orgs'
        self.assertEqual(self.app._get_spec_for_resource_type(path), self.spec)

        path = u'/orgs/0035-2e003ccf3de917b9e2ff61b1917749bd-0ceab24e'
        self.assertEqual(self.app._get_spec_for_resource_type(path), self.spec)
