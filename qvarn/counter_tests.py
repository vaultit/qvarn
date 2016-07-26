# Copyright 2016 QvarnLabs Ltd
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


import threading
import unittest

import qvarn


class CounterTests(unittest.TestCase):

    def test_counts_to_a_million_in_ten_threads(self):
        max_count = 100000
        num_threads = 2
        counter = qvarn.Counter()

        threads = []
        for _ in range(num_threads):
            ct = CountThread(max_count, counter)
            ct.start()
            threads.append(ct)
        for ct in threads:
            ct.join()

        self.assertEqual(counter.get(), max_count * num_threads)


class CountThread(threading.Thread):

    def __init__(self, n, counter):
        super(CountThread, self).__init__()
        self.n = n
        self.counter = counter

    def run(self):
        for _ in range(self.n):
            self.counter.increment()
