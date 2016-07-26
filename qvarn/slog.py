# slog.py - structured logging
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


import datetime
import json
import math
import os
import syslog
import thread
import time
import traceback

import qvarn


class StructuredLog(object):

    '''A structuctured logging system.

    A structured log is one that can be easily parsed
    programmatically. Traditional logs are free form text, usually
    with a weakly enforced line structure and some minimal metadata
    prepended to each file. This class produces JSON records instead.

    See the separate manual for more background and examples of how to
    use this system.

    '''

    def __init__(self):
        self._msg_counter = qvarn.Counter()
        self._context = {}
        self._writer = None

    def close(self):
        self._writer.close()

    def set_log_writer(self, writer):
        self._writer = writer

    def set_context(self, new_context):
        thread_id = self._get_thread_id()
        self._context[thread_id] = new_context

    def reset_context(self):
        thread_id = self._get_thread_id()
        self._context[thread_id] = None

    def log(self, msg_type, **kwargs):
        exc_info = kwargs.pop('exc_info', False)

        log_obj = {
            'msg_type': msg_type,
        }
        log_obj.update(kwargs)
        self._add_extra_fields(log_obj, exc_info)
        self._writer.write(log_obj)

    def _add_extra_fields(self, log_obj, stack_info):
        log_obj['_msg_number'] = self._get_next_message_number()
        log_obj['_timestamp'] = self._get_current_timestamp()
        log_obj['_process_id'] = self._get_process_id()
        log_obj['_thread_id'] = self._get_thread_id()
        log_obj['_context'] = self._context.get(self._get_thread_id())
        if stack_info:
            log_obj['_traceback'] = self._get_traceback()

    def _get_next_message_number(self):
        return self._msg_counter.increment()

    def _get_current_timestamp(self):
        return datetime.datetime.utcnow().isoformat(' ')

    def _get_process_id(self):
        return os.getpid()

    def _get_thread_id(self):
        return thread.get_ident()

    def _get_traceback(self):
        return traceback.format_exc()


class SlogWriter(object):  # pragma: no cover

    def write(self, log_obj):
        raise NotImplementedError()

    def close(self):
        raise NotImplementedError()


class NullSlogWriter(SlogWriter):  # pragma: no cover

    def write(self, log_obj):
        pass

    def close(self):
        pass


class FileSlogWriter(SlogWriter):

    def __init__(self):
        self._prefix = None
        self._log_filename = None
        self._log_file = None
        self._bytes_max = None
        self._bytes_written = 0

    def set_filename_prefix(self, prefix):
        self._prefix = prefix
        self._open_log_file()

    def set_max_file_size(self, bytes_max):
        self._bytes_max = bytes_max

    def get_filename(self):
        return self._log_filename

    def _open_log_file(self):
        self._log_filename = self._choose_new_filename()
        self._log_file = open(self.get_filename(), 'a')

    def _choose_new_filename(self):
        new_filename = self._construct_filename()
        while new_filename == self._log_filename:
            t = time.time()
            fraction, _ = math.modf(t)
            suffix = str(fraction).lstrip('0')
            new_filename = self._construct_filename(suffix=suffix)
        return new_filename

    def _construct_filename(self, suffix=''):
        middle = time.strftime('-%Y-%m-%dT%H%M%S')
        return self._prefix + middle + suffix + '.log'

    def write(self, log_obj):
        if self._log_file:
            encoder = SlogEncoder(sort_keys=True)
            s = encoder.encode(log_obj)
            self._log_file.write(s + '\n')
            self._log_file.flush()
            self._bytes_written += len(s) + 1
            if self._bytes_max is not None:
                if self._bytes_written >= self._bytes_max:
                    self._open_log_file()
                    self._bytes_written = 0

    def close(self):
        self._log_file.close()
        self._log_file = None


class SyslogSlogWriter(SlogWriter):  # pragma: no cover

    def write(self, log_obj):
        encoder = SlogEncoder(sort_keys=True)
        s = encoder.encode(log_obj)
        syslog.syslog(s)

    def close(self):
        pass


class SlogEncoder(json.JSONEncoder):  # pragma: no cover

    # pylint: disable=method-hidden
    def default(self, o):
        if isinstance(o, buffer):
            return str(o)
        return json.JSONEncoder.default(self, o)
