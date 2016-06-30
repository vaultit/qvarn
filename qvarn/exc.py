# exc.py - base class for application specific exceptions
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


class BackendException(Exception):

    '''Base class for backend specific exceptions.

    Every other exception defined by the backend should be a subclass
    of this one. Subclasses MUST define an attribute ``msg``, that contains
    a general error message. The initialiser saves all keyword arguments
    which can contain more specific information about the error.

    This makes it nearly effortless to define very specific
    exceptions, and that, in turn, often makes it easier to debug a
    problem.

    The messages should be written in a way that make sense to API
    client developers as well as sysadmins, and backend developers.
    The message string should be one line, but can be arbitrarily long.
    (It's the job of the presentation layer to break it into lines, if
    need be.)

    All BackendExceptions are converted to user and machine readable messages
    with matching HTTP status codes. This error should not be used directly
    which is why its status code is set to 500 (internal server error).
    '''

    status_code = 500
    msg = u'Internal server error'

    def __init__(self, **kwargs):
        super(BackendException, self).__init__(self)
        self.error = kwargs
        self.error.update({
            u'error_code': self.__class__.__name__,
            u'message': self.msg
        })

    def __str__(self):  # pragma: no cover
        return self.msg.format(**self.error)
