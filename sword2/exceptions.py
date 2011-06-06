#!/usr/bin/env python
# -*- coding: utf-8 -*-

class HTTPResponseError(Exception):
    """Generic exception for http codes greater than 399 and less than 599 """
    def __init__(self, response=None):
        self.response = response
        
class ServerError(HTTPResponseError):
    """ for http error codes 500 and up """
    pass

class NotAuthorised(HTTPResponseError):
    pass

class Forbidden(HTTPResponseError):
    pass

class RequestTimeOut(HTTPResponseError):
    pass

class PackagingFormatNotAvailable(HTTPResponseError):
    pass
    