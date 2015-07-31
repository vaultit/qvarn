# http_statuses.py - exceptions for HTTP error statuses
#
# Copyright 2015 Suomen Tilaajavastuu Oy
# All rights reserved.

'''See http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html'''

import unifiedapi


class HTTPError(unifiedapi.BackendException):

    '''Base class for HTTP client errors (4xx).

    Subclasses MUST define an attribute ``status_code``.
    '''

    msg = u'Internal server error'


class BadRequest(HTTPError):

    '''
     The request could not be understood by the server due to malformed syntax.
     The client SHOULD NOT repeat the request without modifications.
    '''

    status_code = 400
    msg = u'Bad request'


class Unauthorized(HTTPError):

    '''
    The request requires user authentication. The response MUST include a
    WWW-Authenticate header field containing a challenge applicable to the
    requested resource. The client MAY repeat the request with a suitable
    Authorization header field. If the request already included Authorization
    credentials, then the 401 response indicates that authorization has been
    refused for those credentials. If the 401 response contains the same
    challenge as the prior response, and the user agent has already attempted
    authentication at least once, then the user SHOULD be presented the entity
    that was given in the response, since that entity might include relevant
    diagnostic information.
    '''

    status_code = 401
    msg = u'Unauthorized'


class Forbidden(HTTPError):

    '''
    The server understood the request, but is refusing to fulfill it.
    Authorization will not help and the request SHOULD NOT be repeated. If the
    request method was not HEAD and the server wishes to make public why the
    request has not been fulfilled, it SHOULD describe the reason for the
    refusal in the entity. If the server does not wish to make this information
    available to the client, the status code 404 (Not Found) can be used
    instead.
    '''

    status_code = 403
    msg = u'Forbidden'


class NotFound(HTTPError):

    '''
    The server has not found anything matching the Request-URI. No indication
    is given of whether the condition is temporary or permanent. The 410 (Gone)
    status code SHOULD be used if the server knows, through some internally
    configurable mechanism, that an old resource is permanently unavailable
    and has no forwarding address. This status code is commonly used when the
    server does not wish to reveal exactly why the request has been refused,
    or when no other response is applicable.
    '''

    status_code = 404
    msg = u'Not found'


class Conflict(HTTPError):

    '''
     The request could not be completed due to a conflict with the current
     state of the resource. This code is only allowed in situations where it is
     expected that the user might be able to resolve the conflict and resubmit
     the request. The response body SHOULD include enough information for the
     user to recognize the source of the conflict. Ideally, the response entity
     would include enough information for the user or user agent to fix the
     problem; however, that might not be possible and is not required.

     Conflicts are most likely to occur in response to a PUT request. For
     example, if versioning were being used and the entity being PUT included
     changes to a resource which conflict with those made by an earlier
     (third-party) request, the server might use the 409 response to indicate
     that it can't complete the request. In this case, the response entity
     would likely contain a list of the differences between the two versions in
     a format defined by the response Content-Type.
    '''

    status_code = 409
    msg = u'Conflict'


class LengthRequired(HTTPError):

    '''
    The server refuses to accept the request without a defined Content- Length.
    The client MAY repeat the request if it adds a valid Content-Length header
    field containing the length of the message-body in the request message.
    '''

    status_code = 411
    msg = u'Length required'


class UnsupportedMediaType(HTTPError):

    '''
    The server is refusing to service the request because the entity of the
    request is in a format not supported by the requested resource for the
    requested method.
    '''

    status_code = 415
    msg = u'Unsupported media type'
