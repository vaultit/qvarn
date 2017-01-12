# Copyright 2017 QvarnLabs AB
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


class ResourceTypeStorageTests(unittest.TestCase):

    def transaction(self):
        sql = qvarn.SqliteAdapter()
        conn = qvarn.DatabaseConnection()
        conn.set_sql(sql)
        return conn.transaction()

    def test_has_no_types_initally(self):
        with self.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            self.assertEqual(rts.get_types(t), [])

    def test_adds_first_type(self):
        spec = {
            'type': 'person',
            'blah': 'BLAH',
        }
        spec_text = yaml.safe_dump(spec)

        with self.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            rts.add_or_update_spec(t, spec, spec_text)
            self.assertEqual(rts.get_types(t), [spec['type']])
            self.assertEqual(rts.get_spec(t, spec['type']), spec)

    def test_updates_existing_type(self):
        spec_v1 = {
            'type': 'person',
            'blah': 'BLAH',
        }
        spec_v1_text = yaml.safe_dump(spec_v1)

        spec_v2 = spec_v1.copy()
        spec_v2['bling'] = 'blong'
        spec_v2_text = yaml.safe_dump(spec_v2)

        with self.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            rts.add_or_update_spec(t, spec_v1, spec_v1_text)
            rts.add_or_update_spec(t, spec_v2, spec_v2_text)
            self.assertEqual(rts.get_types(t), [spec_v2['type']])
            self.assertEqual(rts.get_spec(t, spec_v2['type']), spec_v2)

    def test_delete_type(self):
        spec = {
            'type': 'person',
            'blah': 'BLAH',
        }
        spec_text = yaml.safe_dump(spec)

        with self.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            rts.add_or_update_spec(t, spec, spec_text)
            rts.delete_spec(t, spec[u'type'])
            self.assertEqual(rts.get_types(t), [])

    def test_spec_with_blob(self):
        text = '''\
path: /files
type: file
versions:
- prototype: {id: '', revision: '', type: '', foo: blob}
  version: v0
'''
        spec = yaml.safe_load(text)

        with self.transaction() as t:
            rts = qvarn.ResourceTypeStorage()
            rts.prepare_tables(t)
            rts.add_or_update_spec(t, spec, text)
            self.assertEqual(rts.get_types(t), ['file'])
