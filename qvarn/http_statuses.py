# http_statuses.py - exceptions for HTTP error statuses
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


'''Define exceptions for various HTTP errors.

See http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html for
definitions of the errors.

'''


import qvarn


class HTTPError(qvarn.QvarnException):

    '''Base class for HTTP client errors (4xx).

    Subclasses MUST define an attribute ``status_code``.
    '''


class BadRequest(HTTPError):

    status_code = 400
    msg = u'Bad request'


class Unauthorized(HTTPError):

    status_code = 401
    msg = u'Unauthorized'


class Forbidden(HTTPError):

    status_code = 403
    msg = u'Forbidden'


class NotFound(HTTPError):

    status_code = 404
    msg = u'Not found'


class Conflict(HTTPError):

    status_code = 409
    msg = u'Conflict'


class LengthRequired(HTTPError):

    status_code = 411
    msg = u'Length required'


class UnsupportedMediaType(HTTPError):

    status_code = 415
    msg = u'Unsupported media type'
