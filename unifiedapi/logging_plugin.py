import logging

import bottle


class LoggingPlugin(object):

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            data = callback(*args, **kwargs)
            self._log_request()
            self._log_response(data)
            return data
        return wrapper

    def _log_request(self):
        '''Log an HTTP request, with arguments and body.'''
        r = bottle.request
        logging.info(
            u'Request: %s %s (args: %r)', r.method, r.path, r.url_args)
        logging.info(u'Request headers: %r', dict(r.headers))
        try:
            if r.method in ('POST', 'PUT') and r.json:
                logging.info(u'Request body (JSON): %r', r.json)
        except:  # pylint: disable=locally-disabled,bare-except
            # Invalid JSON TODO?
            pass
        logging.info(u'Request authorization client scopes: %r',
                     bottle.request.environ.get(u'scopes'))
        logging.info(u'Request authorization client id: %r',
                     bottle.request.environ.get(u'client_id'))
        logging.info(u'Request authorization user id: %r',
                     bottle.request.environ.get(u'user_id'))

    def _log_response(self, data):
        r = bottle.response
        logging.info(
            u'Response: %s', r.status)
        logging.info(u'Response headers: %r', dict(r.headers))
        if type(data) is dict:
            logging.info(u'Response body (JSON): %r', data)
