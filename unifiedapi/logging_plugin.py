import logging

import unifiedapi.bottle as bottle


class LoggingPlugin(object):

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            self._log_request()
            return callback(*args, **kwargs)
        return wrapper

    def _log_request(self):
        '''Log an HTTP request, with arguments and body.'''
        r = bottle.request
        logging.info(
            u'Request: %s %s (args: %r)', r.method, r.path, r.url_args)
        if r.method in ('POST', 'PUT') and r.json:
            logging.info(u'Request body (JSON): %r', r.json)
