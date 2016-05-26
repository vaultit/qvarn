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


# Pylint doesn't fully understand what bottle does and doesn't know
# about all the members in all the objects. Disable related warnigs for
# this module.
#
# pylint: disable=no-member
# pylint: disable=not-an-iterable


import logging

import bottle


class LoggingPlugin(object):

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            # Do the thing and catch any exceptions.
            try:
                self._log_request()
                data = callback(*args, **kwargs)
                self._log_response(data)
                return data
            except SystemExit:
                raise
            except BaseException as e:
                # Log an error, not critical, since we're not
                # necessarily exiting due to the exception. In fact,
                # we hopefully aren't.
                logging.error(str(e), exc_info=True)
                raise

        return wrapper

    def _log_request(self):
        '''Log an HTTP request, with arguments and body.'''
        r = bottle.request
        logging.info(u'Request: %s %s (args: %r)',
                     r.method, r.path.decode('utf-8'), r.url_args)
        # Form the header dict with list comprehension and .get() to get over
        # KeyError. The exact problem is still unknown.
        # (lighttpd + flup + bottle header dict + Content-Length -problem).
        logging.info(u'Request headers: %r', {
            key: bottle.request.headers.get(key)
            for key in bottle.request.headers
        })
        try:
            if r.method in ('POST', 'PUT') and r.json:
                logging.info(u'Request body (JSON): %r', r.json)
        except ValueError:
            # When Bottle parses the body as JSON, if it fails, it
            # raises the ValueError exception. We catch this and
            # report the API client the content is not JSON.
            #
            # Any other errors will result in HTTP status 500
            # (internal error), which is fine.
            logging.warning(u'Request body is malformed JSON (ignored)')

    def _log_response(self, data):
        r = bottle.response
        logging.info(
            u'Response: %s', r.status)
        logging.info(u'Response headers: %r', dict(r.headers))
