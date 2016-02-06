# simple_resource.py - a simple API resource
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


import qvarn


class SimpleResource(object):

    '''Implement a simple resource such as /version.

    A simple resource can only ever be retrieved by GET. It can't be
    manipulated in any way.

    Parameterise this class with the ``set_path`` method.

    !IMPORTANT! Authorization to simple resources is not checked. They should
                only contain public information.

    '''

    def __init__(self):
        self._path = None
        self._callback = None

    def set_path(self, path, callback):
        self._path = path
        self._callback = callback

    def prepare_resource(self, database_url):
        return [
            {
                'path': self._path,
                'method': 'GET',
                'callback': self._callback,
                # Do not check authorization for simple resources
                'skip': [
                    qvarn.AuthorizationPlugin
                ]
            },
        ]
