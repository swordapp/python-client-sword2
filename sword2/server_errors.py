#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dictionary of SWORD2-specific IRI errors to simple description and expected accompanying HTTP codes.
"""

from sword2_logging import logging
sworderror_l = logging.getLogger(__name__)

SWORD2ERRORSBYNAME = {}
SWORD2ERRORSBYIRI = {}

SWORD2ERRORSBYNAME["ErrorContent"] = {   "name":"ErrorContent",
                                         "IRI":"http://purl.org/net/sword/error/ErrorContent",
                                         "description": "The supplied format is not the same as that identified in the Packaging header and/or that supported by the server",
                                         "codes": [406, 415] }


SWORD2ERRORSBYNAME["ErrorChecksumMismatch"] = { "name":"ErrorChecksumMismatch",
                                                "IRI":"http://purl.org/net/sword/error/ErrorChecksumMismatch",
                                                "description": "Checksum sent does not match the calculated checksum.",
                                                "codes":[412] }

SWORD2ERRORSBYNAME["ErrorBadRequest"] = {   "name":"ErrorBadRequest",
                                            "IRI":"http://purl.org/net/sword/error/ErrorBadRequest",
                                            "description":"Some parameters sent with the POST were not understood. ",
                                            "codes":[400] }
                    
SWORD2ERRORSBYNAME["TargetOwnerUnknown"] = {"name":"TargetOwnerUnknown",
                                            "IRI":"http://purl.org/net/sword/error/TargetOwnerUnknown",
                                            "description":"Used in mediated deposit when the server does not know the identity of the On-Behalf-Of user.",
                                            "codes":[403] }

SWORD2ERRORSBYNAME["MediationNotAllowed"] = {   "name":"MediationNotAllowed",
                                                "IRI":"http://purl.org/net/sword/error/MediationNotAllowed",
                                                "description":"Used where a client has attempted a mediated deposit, but this is not supported by the server. ",
                                                "codes":[412] }

SWORD2ERRORSBYNAME["MethodNotAllowed"] = {  "name":"MethodNotAllowed",
                                            "IRI":"http://purl.org/net/sword/error/MethodNotAllowed",
                                            "description":"Used when the client has attempted one of the HTTP update verbs (POST, PUT, DELETE) but the server has decided not to respond to such requests on the specified resource at that time. ",
                                            "codes":[405] }

SWORD2ERRORSBYNAME["MaxUploadSizeExceeded"] = { "name":"MaxUploadSizeExceeded",
                                                "IRI":"http://purl.org/net/sword/error/MaxUploadSizeExceeded",
                                                "description":"Used when the client has attempted to supply to the server a file which exceeds the server's maximum upload size limit.",
                                                "codes":[413] }


SWORD2ERRORSBYNAME["UNKNOWNERROR"] = { "name":"UNKNOWNERROR",
                                       "IRI":"",
                                       "description":"Error IRI is not within the SWORD2 specification and so, is not enumerated by this constant",
                                       "codes":[] }

for k,v in SWORD2ERRORSBYNAME.iteritems():
    SWORD2ERRORSBYIRI[v['IRI']] = v

def get_error(iri, code=None):
    sworderror_l.debug("Attempting to match %s to a known SWORD2 error IRI" % iri)
    if iri in SWORD2ERRORSBYIRI.keys():
        if code != None:
            if code in SWORD2ERRORSBYIRI[iri]['codes']:
                sworderror_l.info("Matched '%s' to a known SWORD2 error IRI, and HTTP response code is one of the IRI's' expected response codes." % iri)
                return SWORD2ERRORSBYIRI[iri]
            else:
                sworderror_l.error("Matched '%s' to a known SWORD2 error IRI, but the HTTP response code is NOT one of the IRI's' expected response codes." % iri)
                ue = SWORD2ERRORSBYNAME["UNKNOWNERROR"].copy()
                ue['IRI'] = iri
                ue['codes'] = [code]
                return ue
        sworderror_l.info("Matched '%s' to a known error IRI." % iri)
        return SWORD2ERRORSBYIRI[iri]
    else:
        sworderror_l.info("Could not match '%s' to a known SWORD2 error IRI." % iri)
        ue = SWORD2ERRORSBYNAME["UNKNOWNERROR"].copy()
        ue['IRI'] = iri
        ue['codes'] = [code]
        return ue
