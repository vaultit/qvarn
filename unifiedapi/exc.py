# exc.py - base class for application specific exceptions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


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
            u'error_code': self._get_error_code(),
            u'message': self.msg
        })

    def _get_error_code(self):
        error_hash = hash(self.__class__.__name__)
        error_code = u'E'
        if error_hash < 0:
            error_code += str(error_hash).replace('-', 'N')
        else:
            error_code += u'P' + str(error_hash)
        error_code += u'R'
        return error_code
