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

import ast
from setuptools import setup, find_packages


def read_version(filename):
    with open(filename) as f:
        for line in f:
            if line.startswith('__version__'):
                return ast.literal_eval(line.partition('=')[-1].strip())


def read_requirements(filename):
    with open(filename) as f:
        return [req for req in (req.partition('#')[0].strip() for req in f) if req]


setup(
    name='qvarn',
    version=read_version('qvarn/version.py'),
    description='backend service for JSON and binary data storage',
    author='Suomen Tilaajavastuu Oy',
    author_email='tilaajavastuu.hifi@tilaajavastuu.fi',
    packages=find_packages(),
    scripts=[
        'slog-pretty',
        'slog-errors',
        'qvarn-backend',
        'qvarn-run',
    ],
    install_requires=read_requirements('requirements.in'),
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
