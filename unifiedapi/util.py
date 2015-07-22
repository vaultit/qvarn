# util.py - random utility functions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


'''Random utility functions for the backend.'''


import re


def route_to_scope(route_rule, request_method):
    ''' Gives an authorization scope string for a route and a HTTP method.
    '''
    # Replace <xx> with id, non greedy (?) so we don't replace <xx>XX<xx>.
    route_scope = re.sub(r'<.+?>', 'id', route_rule)
    route_scope = route_scope.replace(u'/', u'_')
    route_scope = u'uapi%s_%s' % (route_scope, request_method)
    return route_scope.lower()
