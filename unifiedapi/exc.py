# exc.py - base class for application specific exceptions
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.


class BackendException(Exception):

    '''Base class for backend specific exceptions.

    Every other exception defined by the backend should be a subclass
    of this one. Subclasses MUST define an attribute ``msg``, which is
    a template that's suitable for the ``format`` method. The
    initialiser saves all keyword arguments and when the exception is
    formatted as a string, the result is the message formatted with
    the keyword arguments.

    This makes it nearly effortless to define very specific
    exceptions, and that, in turn, often makes it easier to debug a
    problem.

    The messages should be written in a way that make sense to API
    client developers as well as sysadmins, and backend developers.
    The format string should be one line, but can be arbitrarily long.
    (It's the job of the presentation layer to break it into lines, if
    need be.)

    '''

    def __init__(self, **kwargs):
        super(BackendException, self).__init__(self)
        self.kwargs = kwargs
        assert str(self)

    def __str__(self):
        return self.msg.format(**self.kwargs)
