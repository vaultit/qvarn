# slog_tests.py - unit tests for structured logging
#
# Copyright 2016  QvarnLabs Ab
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


import glob
import json
import os
import shutil
import tempfile
import unittest

import qvarn


class StructuredLogTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def create_structured_log(self):
        prefix = os.path.join(self.tempdir, 'slog')
        writer = qvarn.FileSlogWriter()
        writer.set_filename_prefix(prefix)

        slog = qvarn.StructuredLog()
        slog.set_log_writer(writer)
        return slog, writer, prefix

    def read_log_entries(self, writer):
        filename = writer.get_filename()
        with open(filename) as f:
            return [json.loads(line) for line in f]

    def test_chooses_filename_using_prefix(self):
        _, writer, prefix = self.create_structured_log()
        filename = writer.get_filename()
        self.assertTrue(filename.startswith(prefix))
        self.assertFalse(filename == prefix)
        self.assertTrue(filename.endswith('.log'))

    def test_creates_file(self):
        _, _, prefix = self.create_structured_log()
        self.assertTrue(glob.glob(prefix + '*.log'))

    def test_logs_in_json(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg', foo='foo', bar='bar', number=12765)
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj['msg_type'], 'testmsg')
        self.assertEqual(obj['foo'], 'foo')
        self.assertEqual(obj['bar'], 'bar')
        self.assertEqual(obj['number'], 12765)

    def test_logs_two_lines_in_json(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg1', foo='foo')
        slog.log('testmsg2', bar='bar')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 2)
        obj1, obj2 = objs

        self.assertEqual(obj1['msg_type'], 'testmsg1')
        self.assertEqual(obj1['foo'], 'foo')

        self.assertEqual(obj2['msg_type'], 'testmsg2')
        self.assertEqual(obj2['bar'], 'bar')

    def test_adds_some_extra_fields(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj['msg_type'], 'testmsg')
        self.assertIn('_timestamp', obj)
        self.assertIn('_process_id', obj)
        self.assertIn('_thread_id', obj)
        self.assertEqual(obj['_context'], None)

    def test_adds_context_when_given(self):
        slog, writer, _ = self.create_structured_log()
        slog.set_context('request 123')
        slog.log('testmsg')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj['_context'], 'request 123')

    def test_resets_context_when_requested(self):
        slog, writer, _ = self.create_structured_log()
        slog.set_context('request 123')
        slog.reset_context()
        slog.log('testmsg')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        obj = objs[0]
        self.assertEqual(obj['_context'], None)

    def test_counts_messages(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg')
        slog.log('testmsg')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 2)
        self.assertEqual(objs[0]['_msg_number'], 1)
        self.assertEqual(objs[1]['_msg_number'], 2)

    def test_logs_traceback(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg', exc_info=True)
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertIn('_traceback', objs[0])

    def test_rotates_after_size_limit(self):
        slog, writer, _ = self.create_structured_log()
        filename_1 = writer.get_filename()
        writer.set_max_file_size(1)
        slog.log('testmsg')
        filename_2 = writer.get_filename()
        self.assertNotEqual(filename_1, filename_2)

    def test_logs_unicode(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg', text=u'foo')
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['text'], u'foo')

    def test_logs_buffer(self):
        slog, writer, _ = self.create_structured_log()
        binary = ''.join(chr(x) for x in range(256))
        slog.log('testmsg', text=buffer(binary))
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['text'], repr(binary))

    def test_logs_nonutf8(self):
        slog, writer, _ = self.create_structured_log()
        notutf8 = '\x86'
        slog.log('blobmsg', notutf8=notutf8)
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['notutf8'], repr(notutf8))

    def test_logs_list(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg', items=[1, 2, 3])
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['items'], [1, 2, 3])

    def test_logs_tuple(self):
        slog, writer, _ = self.create_structured_log()
        slog.log('testmsg', t=(1, 2, 3))
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        # Tuples get returned as s list.
        self.assertEqual(objs[0]['t'], [1, 2, 3])

    def test_logs_dict(self):
        slog, writer, _ = self.create_structured_log()
        dikt = {
            'foo': 'bar',
            'yo': [1, 2, 3],
        }
        slog.log('testmsg', dikt=dikt)
        slog.close()

        objs = self.read_log_entries(writer)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]['dikt'], dikt)
