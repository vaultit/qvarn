# util.py - random utility functions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


'''Random utility functions for the backend.'''


import logging

import unifiedapi.bottle as bottle


def log_request():
    '''Log an HTTP request, with arguments and body.'''
    r = bottle.request
    logging.info(
        u'Request: %s %s (args: %r)', r.method, r.path, r.url_args)
    if r.method in ('POST', 'PUT') and r.json:
        logging.info(u'Request body (JSON): %r', r.json)
