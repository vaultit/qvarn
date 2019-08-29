# Copyright 2018 Vaultit AB
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


import io
import unittest

import bottle
import six

import qvarn


# pylint: disable=protected-access
class BasicValidationPluginTests(unittest.TestCase):

    def setUp(self):
        self.plugin = qvarn.BasicValidationPlugin()

    def tearDown(self):
        # Reset bottle request.
        bottle.request = bottle.LocalRequest()

    def _set_request_body(self, body, content_type):
        bottle.request.environ['CONTENT_TYPE'] = content_type
        bottle.request.environ['CONTENT_LENGTH'] = len(body)
        bottle.request.environ['wsgi.input'] = io.BytesIO(body)

    def test_json_decoding(self):
        self._set_request_body(b'{"json": "data"}', 'application/json')
        self.plugin._parse_json()
        self.assertEqual(bottle.request.qvarn_json, {u"json": u"data"})
        self.assertIsInstance(list(bottle.request.qvarn_json)[0],
                              six.text_type)
        self.assertIsInstance(bottle.request.qvarn_json[u"json"],
                              six.text_type)

    def test_invalid_json(self):
        self._set_request_body(b'{"json": "data"', 'application/json')
        self.assertRaises(qvarn.ContentIsNotJSON, self.plugin._parse_json)

    def test_invalid_json_enxoding(self):
        self._set_request_body(b'{"json": "\xff"}', 'application/json')
        self.assertRaises(qvarn.ContentIsNotJSON, self.plugin._parse_json)

    def test_invalid_content_type(self):
        self._set_request_body(b'{"json": "data"}', 'text/plain')
        self.assertRaises(qvarn.ContentTypeIsNotJSON, self.plugin._parse_json)
