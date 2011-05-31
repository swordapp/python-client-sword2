#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dictionary of SWORD2-specific IRI errors to simple description and expected accompanying HTTP codes.
"""

SWORD2ERRORS = {}

SWORD2ERRORS["ErrorContent"] = { "IRI":"http://purl.org/net/sword/error/ErrorContent",
                                 "description": "The supplied format is not the same as that identified in the Packaging header and/or that supported by the server",
                                 "codes": [406, 415] }


SWORD2ERRORS["ErrorChecksumMismatch"] = { "IRI":"http://purl.org/net/sword/error/ErrorChecksumMismatch",
                                          "description": "Checksum sent does not match the calculated checksum."
                                          "codes":[412] }

SWORD2ERRORS["ErrorBadRequest"] = { "IRI":"http://purl.org/net/sword/error/ErrorBadRequest",
                                    "description":"Some parameters sent with the POST were not understood. ",
                                    "codes":[400] }
                    
SWORD2ERRORS["TargetOwnerUnknown"] = { "IRI":"http://purl.org/net/sword/error/TargetOwnerUnknown",
                                       "description":"Used in mediated deposit when the server does not know the identity of the On-Behalf-Of user.",
                                       "codes":[403] }

SWORD2ERRORS["MediationNotAllowed"] = { "IRI":"http://purl.org/net/sword/error/MediationNotAllowed",
                                        "description":"Used where a client has attempted a mediated deposit, but this is not supported by the server. ",
                                        "codes":[412] }

SWORD2ERRORS["MethodNotAllowed"] = { "IRI":"http://purl.org/net/sword/error/MethodNotAllowed",
                                     "description":"Used when the client has attempted one of the HTTP update verbs (POST, PUT, DELETE) but the server has decided not to respond to such requests on the specified resource at that time. ",
                                     "codes":[405] }

SWORD2ERRORS["MaxUploadSizeExceeded"] = { "IRI":"http://purl.org/net/sword/error/MaxUploadSizeExceeded",
                                          "description":"Used when the client has attempted to supply to the server a file which exceeds the server's maximum upload size limit.",
                                          "codes":[413] }


