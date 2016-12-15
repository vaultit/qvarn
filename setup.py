#!/usr/bin/python
#
# setup.py - standard Python build-and-package program
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


from distutils.core import setup

import qvarn


setup(
    name='qvarn',
    version=qvarn.__version__,
    description='backend service for JSON and binary data storage',
    author='Suomen Tilaajavastuu Oy',
    author_email='tilaajavastuu.hifi@tilaajavastuu.fi',
    packages=['qvarn'],
    scripts=['slog-pretty', 'slog-errors', 'qvarn-backend'],
)
