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
        filename = os.path.join(self.tempdir, 'slog.log')
        writer = qvarn.FileSlogWriter()
        writer.set_filename(filename)

        slog = qvarn.StructuredLog()
        slog.add_log_writer(writer)
        return slog, writer, filename

    def read_log_entries(self, writer):
        filename = writer.get_filename()
        with open(filename) as f:
            return [json.loads(line) for line in f]

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

    def test_logs_to_two_files(self):
        filename1 = os.path.join(self.tempdir, 'slog1XS')
        writer1 = qvarn.FileSlogWriter()
        writer1.set_filename(filename1)

        filename2 = os.path.join(self.tempdir, 'slog2')
        writer2 = qvarn.FileSlogWriter()
        writer2.set_filename(filename2)

        slog = qvarn.StructuredLog()
        slog.add_log_writer(writer1)
        slog.add_log_writer(writer2)

        slog.log('test', msg_text='hello')
        objs1 = self.read_log_entries(writer1)
        objs2 = self.read_log_entries(writer2)

        self.assertEqual(objs1, objs2)


class FileSlogWriterTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_gets_initial_filename_right(self):
        fw = qvarn.FileSlogWriter()
        fw.set_filename('foo.log')
        self.assertEqual(fw.get_filename(), 'foo.log')

    def test_gets_rotated_filename_right(self):
        fw = qvarn.FileSlogWriter()
        fw.set_filename('foo.log')
        self.assertEqual(
            fw.get_rotated_filename(now=(1969, 9, 1, 14, 30, 42)),
            'foo-19690901T143042.log'
        )

    def test_creates_file(self):
        fw = qvarn.FileSlogWriter()
        filename = os.path.join(self.tempdir, 'slog.log')
        fw.set_filename(filename)
        self.assertTrue(os.path.exists(filename))

    def test_rotates_after_size_limit(self):
        fw = qvarn.FileSlogWriter()
        filename = os.path.join(self.tempdir, 'slog.log')
        fw.set_filename(filename)
        fw.set_max_file_size(1)
        fw.write({'foo': 'bar'})
        filenames = glob.glob(self.tempdir + '/*.log')
        self.assertEqual(len(filenames), 2)
        self.assertTrue(filename in filenames)

        rotated_filename = [x for x in filenames if x != filename][0]
        objs1 = self.load_log_objs(filename)
        objs2 = self.load_log_objs(rotated_filename)

        self.assertEqual(len(objs1), 0)
        self.assertEqual(len(objs2), 1)

    def load_log_objs(self, filename):
        with open(filename) as f:
            return [json.loads(line) for line in f]
