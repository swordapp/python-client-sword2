#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Provides a convenience class for handling and parsing Error Document responses.
"""

from deposit_receipt import Deposit_Receipt
from server_errors import SWORD2ERRORSBYIRI, get_error

from sword2_logging import logging
ed_l = logging.getLogger(__name__)

class Error_Document(Deposit_Receipt):
    """
Example Error document:

<?xml version="1.0" encoding="utf-8"?>
<sword:error xmlns="http://www.w3.org/2005/Atom"
       xmlns:sword="http://purl.org/net/sword/"
       xmlns:arxiv="http://arxiv.org/schemas/atom"
       href="http://example.org/errors/BadManifest">
    <author>
        <name>Example repository</name>
    </author>
    <title>ERROR</title>
    <updated>2008-02-19T09:34:27Z</updated>

    <generator uri="https://example.org/sword-app/"
               version="0.9">sword@example.org</generator>

    <summary>The manifest could be parsed, but was not valid - 
    no technical metadata was provided.</summary>
    <sword:treatment>processing failed</sword:treatment>
    <sword:verboseDescription>
        Exception at [ ... ]
    </sword:verboseDescription>
    <link rel="alternate" href="https://arxiv.org/help" type="text/html"/>

</sword:error>


Error document is an AtomPub extension:

The sword:error element MAY contain any of the elements normally used in the Deposit Receipt, but all fields are OPTIONAL.

The error document SHOULD contain an atom:summary element with a short description of the error.

The error document MAY contain a sword:verboseDescription element with a long description of the problem or any other appropriate software-level debugging output (e.g. a stack trace). Server implementations may wish to provide this for client developers' convenience, but may wish to disable such output in any production systems.

The server SHOULD specify that the Content-Type of the is text/xml or application/xml.
    """
    def __init__(self, xml_deposit_receipt=None, code=None, resp=None):
        ed_l.debug("Constructing Error Document Representation")
        if xml_deposit_receipt:
            super(Error_Document, self).__init__(xml_deposit_receipt=xml_deposit_receipt, code=code)
        else:
            super(Error_Document, self).__init__(code=code)
        self.error_href = None
        self.error_info = None
        self.verbose_description = None
        self.content = None  # for parity with the ContentWrapper
        self.response_headers = resp
        self._characterise_error()
    
    def _characterise_error(self):
        if "sword_verboseDescription" in self.metadata.keys():
            self.verbose_description = self.metadata['sword_verboseDescription']
        
        if self.dom != None:
            ed_l.debug("Error response contains document content")
            if "href" in self.dom.attrib.keys():
                self.error_href = self.dom.attrib['href']
                self.error_info = get_error(self.error_href, self.code)
        else:
            ed_l.debug("Error response does NOT contain document content")
