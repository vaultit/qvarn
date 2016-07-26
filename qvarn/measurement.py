# measurement.py - store list of SQL statement measurements
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


import time

import qvarn


class Measurement(object):

    def __init__(self):
        self._started = time.time()
        self._ended = None
        self._steps = []

    def finish(self):
        self._ended = time.time()

    def new(self, what):
        self._steps.append(Step(what))
        return self._steps[-1]

    def note(self, **kwargs):
        self._steps[-1].note(**kwargs)

    def log(self, exc_info):
        duration = self._ended - self._started
        qvarn.log.log(
            'sql-transaction',
            duration_ms=duration * 1000.0,
            success=(exc_info is None),
            exc_info=exc_info,
            steps=[
                {
                    'what': step.what,
                    'duration_ms': step.duration * 1000.0,
                    'notes': step.notes,
                }
                for step in self._steps
            ]
        )


class Step(object):

    def __init__(self, what):
        self._started = None
        self._ended = None
        self.what = what
        self.duration = None
        self.notes = []

    def note(self, **kwargs):
        self.notes.append(kwargs)

    def __enter__(self):
        self._started = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ended = time.time()
        self.duration = self._ended - self._started
