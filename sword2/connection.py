#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provides the 'Connection' class, a SWORD2 client.

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD for information
about the SWORD2 AtomPub profile.
 
"""
from sword2_logging import logging
conn_l = logging.getLogger(__name__)

from utils import Timer, NS, get_md5, create_multipart_related

from transaction_history import Transaction_History
from service_document import ServiceDocument
from deposit_receipt import Deposit_Receipt
from error_document import Error_Document
from statement import Atom_Sword_Statement, Ore_Sword_Statement
from exceptions import *

from compatible_libs import etree

# import httplib2
import http_layer
import urllib

class Connection(object):
    """
`Connection` - SWORD2 client

This connection is predicated on having a Service Document (SD), preferably by an instance being constructed with
the Service Document IRI (SD-IRI) which can dereference to the XML document itself.


Contructor parameters:
    
There are a number of flags that can be set when getting an instance of this class that affect the behaviour 
of the client. See the help for `self.__init__` for more details.

Example usage:
    
>>> from sword2 import Connection
>>> conn = Connection("http://example.org/service-doc")  # An SD-IRI is required.




# Get, validate and parse the document at the SD_IRI:
>>> conn.get_service_document()

# Load a Service Document from a string:
>>> conn.load_service_document(xml_service_doc)
2011-05-30 01:06:13,251 - sword2.service_document - INFO - Initial SWORD2 validation checks on service document - Valid document? True

# View transaction history (if enabled)
>>> print conn.history.to_pretty_json()
[
 {
  "sd_iri": "http://example.org/service-doc", 
  "timestamp": "2011-05-30T01:05:54.071042", 
  "on_behalf_of": null, 
  "type": "init", 
  "user_name": null
 }, 
 {
  "IRI": "http://example.org/service-doc", 
  "valid": true, 
  "sword_version": "2.0", 
  "duration": 0.0029349327087402344, 
  "timestamp": "2011-05-30T01:06:13.253907", 
  "workspaces_found": [
   "Main Site", 
   "Sub-site"
  ], 
  "type": "SD Parse", 
  "maxUploadSize": 16777216
 }
]

# Start a connection and do not maintain a transaction history
# Useful for bulk-testing where the history might grow exponentially
>>> conn = Connection(...... , keep_history=False, ....)

# Initialise a connection and get the document at the SD IRI:
# (Uses the Simple Sword Server as an endpoint - sss.py

>>> from sword2 import Connection
>>> c = Connection("http://localhost:8080/sd-uri", download_service_document=True)
2011-05-30 02:04:24,179 - sword2.connection - INFO - keep_history=True--> This instance will keep a JSON-compatible transaction log of all (SWORD/APP) activities in 'self.history'
2011-05-30 02:04:24,215 - sword2.connection - INFO - Received a document for http://localhost:8080/sd-uri
2011-05-30 02:04:24,216 - sword2.service_document - INFO - Initial SWORD2 validation checks on service document - Valid document? True
>>> print c.history
--------------------
Type: 'init' [2011-05-30T02:04:24.180182]
Data:
user_name:   None
on_behalf_of:   None
sd_iri:   http://localhost:8080/sd-uri
--------------------
Type: 'SD_IRI GET' [2011-05-30T02:04:24.215661]
Data:
sd_iri:   http://localhost:8080/sd-uri
response:   {'status': '200', 'content-location': 'http://localhost:8080/sd-uri', 'transfer-encoding': 'chunked', 'server': 'CherryPy/3.1.2 WSGI Server', 'date': 'Mon, 30 May 2011 01:04:24 GMT', 'content-type': 'text/xml'}
process_duration:   0.0354170799255
--------------------
Type: 'SD Parse' [2011-05-30T02:04:24.220798]
Data:
maxUploadSize:   16777216
sd_iri:   http://localhost:8080/sd-uri
valid:   True
sword_version:   2.0
workspaces_found:   ['Main Site']
process_duration:   0.00482511520386

Please see the testsuite for this class for more examples of the sorts of transactions that can be done. (tests/test_connection*.py)
"""

    def __init__(self, service_document_iri=None, 
                       user_name=None,
                       user_pass=None,
                       on_behalf_of=None,
                       download_service_document = False,   # Don't automagically GET the SD_IRI by default
                       keep_history=True,
                       cache_deposit_receipts=True,
                       honour_receipts=True,
                       error_response_raises_exceptions=True,
                       
                       # http layer implementation if different from default
                       http_impl=None,
                       ca_certs=None):
        """
Creates a new Connection object.

Parameters:

     Connection(service_document_iri,       <--- REQUIRED - use a dummy string here if the SD is local only.
                
                # OPTIONAL parameters (default values are shown below)
                
                # Authentication parameters:   (can use any method that `httplib2` provides)
                
                user_name=None,     
                user_pass=None,
                
                # Set the SWORD2 On Behalf Of value here, for it to be included as part of every transaction
                # Can be passed to every transaction method (update resource, delete deposit, etc) otherwise
                
                on_behalf_of=None,
                
                ## Behaviour Flags
                # Try to GET the service document from the provided SD-IRI in `service_document_iri` if True
                
                download_service_document = False,   # Don't automagically GET the SD_IRI by default
                
                # Keep a history of all transactions made with the SWORD2 Server
                # Records details like the response headers, sent headers, times taken and so forth
                # Kept in a `sword2.transaction_history:Transaction_History` object but can be treated like an ordinary `list`
                keep_history=True,
                
                # Keep a cache of all deposit receipt responses from the server and provide an 'index' to these `sword2.Deposit_Receipt` objects
                # by Edit-IRI, Content-IRI and Sword-Edit-IRI. (ie given an Edit-IRI, find the deposit receipt for the last received response containing
                # that IRI.
                # If the following flag, `honour_receipts` is set to True, packaging checks and other limits set in these receipts will be
                # honoured.
                # For example, a request for an item with an invalid packaging type will never reach the server, but throw an exception.
                
                cache_deposit_receipts=True,
                
                # Make sure to behave as required by the SWORD2 server - not sending too large a file, not asking for invalid packaging types and so on. 
                
                honour_receipts=True,
                
                # Two means of handling server error responses:
                #   If set to True - An exception will be thrown from `sword2.exceptions` (caused by any server error response w/ 
                #      HTTP code greater than or equal to 400)
                #   OR
                #   If set to False - A `sword2.error_document:Error_Document` object will be returned.
                
                error_response_raises_exceptions=True
                )
                
If a `Connection` is created with the parameter `download_service_document` set to `False`, then no attempt
to dereference the `service_document_iri` (SD-IRI) will be made at this stage.

To cause it to get or refresh the service document from this IRI, call `self.get_service_document()`

Loading in a locally held Service Document:
    
>>> conn = Connection(....)

>>> with open("service_doc.xml", "r") as f:
...     conn.load_service_document(f.read())

         
                """
        self.sd_iri = service_document_iri
        self.sd = None
        
        # Client behaviour flags:
        # Honour deposit receipts - eg raise exceptions if interactions are attempted that the service document
        #                              does not allow without bothering the server - invalid packaging types, max upload sizes, etc
        self.honour_receipts = honour_receipts   
        
        # When error_response_raises_exceptions == True:
        # Error responses (HTTP codes >399) will raise exceptions (from sword2.exceptions) in response
        # when False:
        # Error Responses, if Content-Type is text/xml or application/xml, a sword2.error_document.Error_Document will be the 
        # return - No Exception will be raised!
        # Check Error_Document.code to get the response code, regardless to whether a valid Sword2 error document was received.
        self.raise_except = error_response_raises_exceptions
        
        self.keep_cache = cache_deposit_receipts
        
        # set the http layer
        if http_impl is None:
            conn_l.info("Loading default HTTP layer")
            self.h = http_layer.HttpLib2Layer(".cache", timeout=30.0, ca_certs=ca_certs)
        else:
            conn_l.info("Using provided HTTP layer")
            self.h = http_impl
        
        self.user_name = user_name
        self.on_behalf_of = on_behalf_of
        
        # Cached Deposit Receipt 'indexes'  *cough, cough*
        self.edit_iris = {}          # Key = IRI, Value = ref to latest Deposit Receipt for the resource
        self.cont_iris = {}          # Key = IRI, Value = ref to latest Deposit Receipt
        self.se_iris = {}            # Key = IRI, Value = ref to latest Deposit Receipt
        self.cached_at = {}          # Key = Edit-IRI, Value = Timestamp for when receipt was cached
        
        # Transaction history hooks
        self.history = None
        self._t = Timer()
        self.keep_history = keep_history
        if keep_history:
            conn_l.info("keep_history=True--> This instance will keep a JSON-compatible transaction log of all (SWORD/APP) activities in 'self.history'")
            self.reset_transaction_history()
            self.history.log('init',
                             sd_iri = self.sd_iri,
                             user_name = self.user_name,
                             on_behalf_of = self.on_behalf_of )
        # Add credentials to http client
        if user_name:
            conn_l.info("Adding username/password credentials for the client to use.")
            self.h.add_credentials(user_name, user_pass)
        
        if self.sd_iri and download_service_document:
            self._t.start("get_service_document")
            self.get_service_document()
            conn_l.debug("Getting service document and dealing with the response: %s s" % self._t.time_since_start("get_service_document")[1])
    
    def _return_error_or_exception(self, cls, resp, content):
        """Internal method for reporting errors, behaving as the `self.raise_except` flag requires.
        
        `self.raise_except` can be altered at any time to affect this methods behaviour."""
        if self.raise_except:
            raise cls(resp, content)
        else:
            # content type can contain both the mimetype and the charset (e.g. text/xml; charset=utf-8)
            if resp.get('content-type', "").startswith("text/xml") or resp.get('content-type', "").startswith("application/xml"):
                conn_l.info("Returning an error document, due to HTTP response code %s" % resp.status)
                e = Error_Document(content, code=resp.status, resp = resp)
                return e
            else:
                conn_l.info("Returning due to HTTP response code %s" % resp.status)
                e = Error_Document(code=resp.status, resp = resp)
                return e
    
    def _handle_error_response(self, resp, content):
        """Catch a number of general HTTP error responses from the server, based on HTTP code
        
        401 - Unauthorised.
            Will throw a `sword2.exceptions.NotAuthorised` exception, if exceptions are set to be on.
            Otherwise will return a `sword2.Error_Document` (likewise for the rest of these)
        
        403 - Forbidden.
            Will throw a `sword2.exceptions.Forbidden` exception
        
        404 - Not Found.
            Will throw a `sword2.exceptions.NotFound` exception
            
        406 - Not Acceptable.
            Will throw a `sword2.exceptions.NotAcceptable` exception
        
        408 - Request Timeout
            Will throw a `sword2.exceptions.RequestTimeOut` exception
        
        500-599 errors:
            Will throw a general `sword2.exceptions.ServerError` exception
        
        4XX not listed:
            Will throw a general `sword2.exceptions.HTTPResponseError` exception
        """
        conn_l.debug("Error body received from server: " + str(content))
        
        if resp['status'] == 401:
            conn_l.error("You are unauthorised (401) to access this document on the server. Check your username/password credentials and your 'On Behalf Of'")
            return self._return_error_or_exception(NotAuthorised, resp, content)
        elif resp['status'] == 403:
            conn_l.error("You are Forbidden (403) to POST to '%s'. Check your username/password credentials and your 'On Behalf Of'")
            return self._return_error_or_exception(Forbidden, resp, content)
        elif resp['status'] == 406:
            conn_l.error("Cannot negotiate for desired format/packaging on '%s'.")
            return self._return_error_or_exception(NotAcceptable, resp, content)
        elif resp['status'] == 408:
            conn_l.error("Request Timeout (408) - error uploading.")
            return self._return_error_or_exception(RequestTimeOut, resp, content)
        elif int(resp['status']) > 499:
            conn_l.error("Server error occured. Response headers from the server:\n%s" % resp)
            return self._return_error_or_exception(ServerError, resp, content)
        else:
            conn_l.error("Unknown error occured. Response headers from the server:\n%s\n%s" % (resp, content))
            return self._return_error_or_exception(HTTPResponseError, resp, content)
    
    def _cache_deposit_receipt(self, d):
        """Method for storing the deposit receipts, and also for providing lookup dictionaries that
        reference these objects.
        
        (only provides cache if `self.keep_cache` is `True` [via the `cache_deposit_receipts` init parameter flag])
        
        Provides and maintains:
            self.edit_iris -- a `dict`, keys: Edit-IRI hrefs, values: `sword2.Deposit_Receipt` objects they appear in
            
            self.cont_iris -- a `dict`, keys: Content-IRI hrefs, values: `sword2.Deposit_Receipt` objects they appear in
            
            self.se_iris -- a `dict`, keys: Sword-Edit-IRI hrefs, values: `sword2.Deposit_Receipt` objects they appear in
            
            self.cached_at -- a `dict`, keys: Edit-IRIs, values: timestamp when receipt was last cached.
        """
        if self.keep_cache:
            timestamp = self._t.get_timestamp()
            conn_l.debug("Caching document (Edit-IRI:%s) - at %s" % (d.edit, timestamp))
            self.edit_iris[d.edit] = d
            if d.cont_iri:   # SHOULD exist within receipt
                self.cont_iris[d.cont_iri] = d
            if d.se_iri:     
                # MUST exist according to the spec, but as it can be the same as the Edit-IRI
                # it seems likely that a server implementation might ignore the 'MUST' part.
                self.se_iris[d.se_iri] = d
            self.cached_at[d.edit] = self._t.get_timestamp()
        else:
            conn_l.debug("Caching request denied - deposit receipt caching is set to 'False'")
    
    def load_service_document(self, xml_document):
        """Load the Service Document XML from bytestring, `xml_document`
        
        Useful if SD-IRI is non-existant or invalid.
        
        Will set the following convenience attributes:
            
            `self.sd` -- the `sword2.ServiceDocument` instance
            
            `self.workspaces` -- a `list` of workspace tuples, of the form:
                            ('Workspace atom:title', [<`sword2.Collection` object>, ....]),
            
            `self.maxUploadSize` -- the maximum filesize for a deposit, if given in the service document
        """
        self._t.start("SD Parse")
        self.sd = ServiceDocument(xml_document)
        _, took_time = self._t.time_since_start("SD Parse")
        # Set up some convenience references
        self.workspaces = self.sd.workspaces
        self.maxUploadSize = self.sd.maxUploadSize
        
        if self.history:
            if self.sd.valid:
                self.history.log('SD Parse', 
                                 sd_iri = self.sd_iri,
                                 valid = self.sd.valid,
                                 workspaces_found = [k for k,v in self.sd.workspaces],
                                 sword_version = self.sd.version,
                                 maxUploadSize = self.sd.maxUploadSize,
                                 process_duration = took_time)
            else:
                self.history.log('SD Parse', 
                                 sd_iri = self.sd_iri,
                                 valid = self.sd.valid,
                                 process_duration = took_time)
    
    def get_service_document(self):
        """Perform an HTTP GET on the Service Document IRI (SD-IRI) and attempt to parse the result as
        a SWORD2 Service Document (using `self.load_service_document`)
        """
        headers = {}
        if self.on_behalf_of:
            headers['on-behalf-of'] = self.on_behalf_of
        self._t.start("SD_URI request")
        resp, content = self.h.request(self.sd_iri, "GET", headers=headers)
        _, took_time = self._t.time_since_start("SD_URI request")
        if self.history:
            self.history.log('SD_IRI GET', 
                             sd_iri = self.sd_iri,
                             response = resp, 
                             process_duration = took_time)
        if resp['status'] == 200:
            conn_l.info("Received a document for %s" % self.sd_iri)
            self.load_service_document(content)
        elif resp['status'] == 401:
            conn_l.error("You are unauthorised (401) to access this document on the server. Check your username/password credentials")
        else:
            conn_l.error("Unexpected response status: " + str(resp['status']))
        
    def reset_transaction_history(self):
        """ Clear the transaction history - `self.history`"""
        del self.history
        self.history = Transaction_History()

    def _make_request(self,
                      target_iri, 
                      payload=None,       # These need to be set to upload a file
                      mimetype=None,      
                      filename=None,
                      packaging=None,
                      md5sum=None,
                        
                      metadata_entry=None,  # a sword2.Entry needs to be here, if 
                                              # a metadata entry is to be uploaded
                      entry_content_type="application/atom+xml; type=entry",        # content type to use for the atom entry
                                                                                    # which means it can be overridden if the server has some special
                                                                                    # requirements (see: EPrints)
                                                                                    # Only works for singlepart deposit, multipart will have atom-specified mimetype in all cases

                      # Set both a file and a metadata entry for the method to perform a multipart
                      # related upload.
                      suggested_identifier=None,   # 'slug'
                      in_progress=True,
                      on_behalf_of=None,
                      metadata_relevant=False,
                      
                      # flags:
                      empty = None,     # If this is True, then the POST/PUT is sent with an empty body
                                        # and the 'Content-Length' header explicitly set to 0
                      method = "POST",
                      request_type=""       # text label for transaction history reports
                      ):
        """Performs an HTTP request, as defined by the parameters. This is an internally used method and it is best that it
        is not called directly.
        
        target_iri -- IRI that will be the target of the HTTP call
        
        # File upload parameters:
        payload   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
        mimetype  - MIMEType of the payload
        filename  - filename. Most SWORD2 uploads have this as being mandatory.
        packaging - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
        
        # NB to work around a possible bug in httplib2 0.6.0, the file-like object is read into memory rather than streamed
        # from disc, so is not as efficient as it should be. That said, it is recommended that file handles are passed to 
        # the _make_request method, as this is hoped to be a temporary situation.
        
        metadata_entry  - a `sword2.Entry` to be uploaded with metadata fields set as desired.
        
        # If there is both a payload and a metadata_entry, then the request will be made as a Multipart-related request
        # Otherwise, it will be a normal request for whicever type of upload.
        
        empty   - a flag to specify that an empty request should be made. A blank body and a 'Content-Length:0' header will be explicitly added
                  and any payload or metadata_entry passed in will be ignored.
        
        
        # Header flags:
        suggested_identifier    -- set the 'Slug' header
        in_progress             --         'In-Progress'
        on_behalf_of            --         'On-Behalf-Of' 
        metadata_relevant       --         'Metadata-Relevant'
        
        # HTTP settings:
        method          -- "GET", "POST", etc
        request_type    -- A label to be used in the transaction history for this particular operation. 
        
        Response:
        
        A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
        not a Deposit Response, then only a few attributes will be populated:
            
        `code` -- HTTP code of the response
        `response_headers`  -- `dict` of the reponse headers
        `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
        If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
        then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
        response_headers, etc)
        """
        if payload:
            md5, f_size = get_md5(payload)
            # this allows the user to pass in their own md5sum (this doesn't save
            # any time, though, because of the above operation - useful mainly for
            # testing at this stage
            if md5sum is None:
                md5sum = md5
        
        # request-level headers
        headers = {}
        headers['In-Progress'] = str(in_progress).lower()
        if on_behalf_of:
            headers['On-Behalf-Of'] = on_behalf_of
        elif self.on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
            
        if suggested_identifier:
            headers['Slug'] = str(suggested_identifier)
            
        if metadata_relevant:
            headers['Metadata-Relevant'] = str(metadata_relevant).lower()
        
        self._t.start(request_type)
        if empty:
            # NULL body with explicit zero length.
            headers['Content-Length'] = "0"
            resp, content = self.h.request(target_iri, method, headers=headers)
            _, took_time = self._t.time_since_start(request_type)
            if self.history:
                self.history.log(request_type + ": Empty request", 
                                 sd_iri = self.sd_iri,
                                 target_iri = target_iri,
                                 method = method,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)  
        elif method == "DELETE":
            resp, content = self.h.request(target_iri, method, headers=headers)
            _, took_time = self._t.time_since_start(request_type)
            if self.history:
                self.history.log(request_type + ": DELETE request", 
                                 sd_iri = self.sd_iri,
                                 target_iri = target_iri,
                                 method = method,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)
            
        elif metadata_entry and not (filename and payload):
            # Metadata-only resource creation
            headers['Content-Type'] = entry_content_type # "application/atom+xml;type=entry"
            data = str(metadata_entry)
            headers['Content-Length'] = str(len(data))
            
            resp, content = self.h.request(target_iri, method, headers=headers, payload=data)
            _, took_time = self._t.time_since_start(request_type)
            if self.history:
                self.history.log(request_type + ": Metadata-only resource request", 
                                 sd_iri = self.sd_iri,
                                 target_iri = target_iri,
                                 method = method,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)
            
        elif metadata_entry and filename and payload:
            # Multipart resource creation
            my_headers = {"Content-MD5" : str(md5sum)}
            if packaging is not None:
                my_headers['Packaging'] = str(packaging)
            multicontent_type, payload_data = create_multipart_related([{'key':'atom',
                                                                    'type':'application/atom+xml; charset="utf-8"',
                                                                    'data':str(metadata_entry),  # etree default is utf-8
                                                                    },
                                                                    {'key':'payload',
                                                                    'type':str(mimetype),
                                                                    'filename':filename,
                                                                    'data':payload,  
                                                                    'headers':my_headers
                                                                    }
                                                                   ])
                                                                   
            headers['Content-Type'] = multicontent_type + '; type="application/atom+xml"'
            headers['Content-Length'] = str(len(payload_data))    # must be str, not int type
            resp, content = self.h.request(target_iri, method, headers=headers, payload=payload_data)
            _, took_time = self._t.time_since_start(request_type)
            if self.history:
                self.history.log(request_type + ": Multipart resource request",
                                 sd_iri = self.sd_iri,
                                 target_iri = target_iri,
                                 response = resp,
                                 headers = headers,
                                 method = method,
                                 multipart = [{'key':'atom',
                                               'type':'application/atom+xml; charset="utf-8"'
                                              },
                                              {'key':'payload',
                                               'type':str(mimetype),
                                               'filename':filename,
                                               'headers':{'Content-MD5':str(md5sum),
                                                          'Packaging':str(packaging),
                                                         }
                                               }],   # record just the headers used in multipart construction
                                 process_duration = took_time)
        elif filename and payload:
            headers['Content-Type'] = str(mimetype)
            headers['Content-MD5'] = str(md5sum)
            headers['Content-Length'] = str(f_size)
            headers['Content-Disposition'] = "attachment; filename=%s" % urllib.quote(filename)
            if packaging is not None:
                headers['Packaging'] = str(packaging)
            
            resp, content = self.h.request(target_iri, method, headers=headers, payload=payload)
            _, took_time = self._t.time_since_start(request_type)
            if self.history:
                self.history.log(request_type + ": simple resource request",
                                 sd_iri = self.sd_iri,
                                 target_iri = target_iri,
                                 method = method,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)
        else:
            conn_l.error("Parameters were not complete: requires a metadata_entry, or a payload/filename/packaging or both")
            raise Exception("Parameters were not complete: requires a metadata_entry, or a payload/filename/packaging or both")
        
        if resp['status'] == 201:
            #   Deposit receipt in content
            conn_l.info("Received a Resource Created (201) response.")
            # Check response headers for updated Location IRI
            location = resp.get('location', None)
            if len(content) > 0:
                # Fighting chance that this is a deposit receipt
                d = Deposit_Receipt(xml_deposit_receipt = content)
                if d.parsed:
                    conn_l.info("Server response included a Deposit Receipt. Caching a copy in .resources['%s']" % d.edit)
                d.response_headers = dict(resp)
                d.location = location
                d.code = 201
                self._cache_deposit_receipt(d)
                return d
            else:
                # No body...
                d = Deposit_Receipt()
                conn_l.info("Server response dir not include a Deposit Receipt.")
                d.response_headers = dict(resp)
                d.code = 201
                d.location = location
                return d
        elif resp['status'] == 204:
            #   Deposit receipt in content
            conn_l.info("Received a valid 'No Content' (204) response.")
            location = resp.get('location', None)
            # Check response headers for updated Locatio
            return Deposit_Receipt(response_headers = dict(resp), location=location, code=204)
        elif resp['status'] == 200:
            #   Deposit receipt in content
            conn_l.info("Received a valid (200) OK response.")
            content_type = resp.get('content-type')
            location = resp.get('location', None)
            # content type header may also includ charset
            if self._normalise_mime(content_type).startswith("application/atom+xml;type=entry") and len(content) > 0: 
                d = Deposit_Receipt(content)
                if d.parsed:
                    conn_l.info("Server response included a Deposit Receipt. Caching a copy in .resources['%s']" % d.edit)
                    d.response_headers = dict(resp)
                    d.location = location
                    d.code = 200
                    self._cache_deposit_receipt(d)
                    return d
            else:
                # No atom entry...
                d = Deposit_Receipt()
                conn_l.info("Server response dir not include a Deposit Receipt Entry.")
                d.response_headers = dict(resp)
                d.location = location
                d.content = content
                d.code = 200
                return d
        else:
            return self._handle_error_response(resp, content)
        

    
    def create(self, 
                        workspace=None,     # Either provide workspace/collection or
                        collection=None,    # the exact Col-IRI itself
                        col_iri=None,  
                        
                        payload=None,       # These need to be set to upload a file
                        mimetype=None,      
                        filename=None,
                        packaging=None,
                        md5sum=None,               # optional; will be calculated for you otherwise
                        
                        metadata_entry=None,  # a sword2.Entry needs to be here, if 
                                              # a metadata entry is to be uploaded
                        entry_content_type="application/atom+xml; type=entry",      # atom mimetype to use for singlepart deposit
                        
                        # Set both a file and a metadata entry for the method to perform a multipart
                        # related upload.
                        
                        suggested_identifier=None,
                        in_progress=False,
                        on_behalf_of=None,
                        ):
        """
Creating a Resource
===================
                
#BETASWORD2URL
See 6.3 Creating a Resource http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_creatingresource

Basic parameters:

This method can create a new resource in a Collection on a SWORD2 server, given suitable authentication to do so.
        
Select a collection to send a request to by either:
            
    setting the param `col_iri` to its Collection-IRI or Col-IRI 
    
        or
    
    setting 'workspace' and 'collection' to the labels for the desired workspace and collection.

SWORD2 request parameters:

    `suggested_identifier`              -- the suggested identifier of this resource (HTTP header of 'Slug'), 

    `in_progress` (`True` or `False`)   -- whether or not the deposit should be considered by the 
                                           server to be in progress ('In-Progress') 
    `on_behalf_of`                      -- if this is a mediated deposit ('On-Behalf-Of') 
                                           (the client-wide setting `self.on_behalf_of will be used otherwise)    

        
1. "Binary File Deposit in a given Collection"
----------------------------------------------
            
Set the following parameters in addition to the basic parameters:

    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
        
Response:

A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

2. "Creating a Resource with an Atom Entry"
-------------------------------------------

create a container within a SWORD server and optionally provide it with metadata without adding any binary content to it. 

Set the following parameters in addition to the basic parameters:
    
    `metadata_entry`  - An instance of `sword2.Entry`, set with the metadata required.
    
for example:
    # conn = `sword2.Connection`, collection_iri = Collection-IRI
    >>> from sword2 import Entry
    >>> entry = Entry(title = "My new deposit",
    ...               id = "foo:id",
    ...               dcterms_abstract = "My Thesis",
    ...               dcterms_author = "Me",
    ...               dcterms_issued = "2009")
    
    >>> conn.create(col_iri = collection_iri,
    ...                      metadata_entry = entry,
    ...                      in_progress = True)          
    # likely to want to add the thesis files later for example but get the identifier for the deposit now

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

3. "Creating a Resource with a Multipart Deposit"
-------------------------------------------------

Create a resource in a given collection by uploading a file AND the metadata about this resource.

To make this sort of request, just set the parameters as shown for both the binary upload and the metadata upload.

eg:
    
    >>> conn.create(col_iri = collection_iri,
    ...                      metadata_entry = entry,
    ...                      payload = open("foo.zip", "r"),
    ...                      mimetype =  
                .... and so on

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

(under the hood, this request uses Atom Multipart-related)

From the spec:

"In order to ensure that all SWORD clients and servers can exchange a full range of file content and metadata, the use of Atom Multipart [AtomMultipart] is permitted to combine a package (possibly a simple ZIP) with a set of Dublin Core metadata terms [DublinCore] embedded in an Atom Entry.

The SWORD server is not required to support packaging formats, but this profile RECOMMENDS that the server be able to accept a ZIP file as the Media Part of an Atom Multipart request (See Section 5: IRIs and Section 7: Packaging for more details)."
        """
        conn_l.debug("Create Resource")
        if not col_iri:
            for w, collections in self.workspaces:
                if w == workspace:
                    for c in collections:
                        if c.title == collection:
                            conn_l.debug("Matched: Workspace='%s', Collection='%s' ==> Col-IRI='%s'" % (workspace, 
                                                                                                        collection, 
                                                                                                        c.href))
                            col_iri = c.href
                            break

        if not col_iri:   # no col_iri provided and no valid workspace/collection given
            conn_l.error("No suitable Col-IRI was found, with the given parameters.")
            return
        
        return self._make_request(target_iri = col_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  packaging=packaging,
                                  metadata_entry=metadata_entry,
                                  suggested_identifier=suggested_identifier,
                                  in_progress=in_progress,
                                  on_behalf_of=on_behalf_of,
                                  method="POST",
                                  request_type='Col_IRI POST',
                                  md5sum=md5sum,
                                  entry_content_type=entry_content_type)
        
    def update(self, metadata_entry = None,    # required for a metadata update
                             payload = None,            # required for a file update      
                             filename = None,           # required for a file update
                             mimetype=None,             # required for a file update
                             packaging=None,            # required for a file update
                             md5sum=None,               # optional; will be calculated for you otherwise
                             
                             dr = None,     # Important! Without this, you will have to set the edit_iri AND the edit_media_iri parameters.
                             
                             edit_iri = None,
                             edit_media_iri = None,

                             metadata_relevant=False,
                             in_progress=False,
                             on_behalf_of=None,
                      ):
        """
Replacing the Metadata and/or Files of a Resource

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_editingcontent_multipart

Replace the metadata and/or files of a resource.

This wraps a number of methods and relies on being passed the Deposit Receipt, as the target IRI changes depending 
on whether the metadata, the files or both are to be updated by the request. 

This method has the same functionality as the following methods:
    update_files_for_resource
    update_metadata_for_resource
    update_metadata_and_files_for_resource

Usage:
------

Set the target for this request:
--------------------------------

You MUST pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen based on what combination of files you want to upload.

Then, add in the metadata and/or file information as desired:
-------------------------------------------------------------

File information requires:

    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
                    
    `metadata_relevant` - This should be set to `True` if the server should consider the file a potential source of metadata extraction, 
                          or `False` if the server should not attempt to extract any metadata from the deposi
    
Metadata information requires:

    `metadata_entry`  - An instance of `sword2.Entry`, set with the metadata required.
    
for example, to create a metadata entry
    >>> from sword2 import Entry
    >>> entry = Entry(title = "My new deposit",
    ...               id = "new:id",    # atom:id
    ...               dcterms_abstract = "My Thesis",
    ...               dcterms_author = "Ben",
    ...               dcterms_issued = "2010")

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)
        """
        target_iri = None
        request_type = "Update PUT"
        if metadata_entry != None:
            metadata_relevant = True    # set this definitively, although the server shouldn't actually care
            # Metadata or Metadata + file --> Edit-IRI
            conn_l.info("Using the Edit-IRI - Metadata or Metadata + file multipart-related uses a PUT request to the Edit-IRI")
            if payload != None and filename != None:
                request_type = "Update Multipart PUT"
            else:
                request_type = "Update Metadata PUT"
            if dr != None and dr.edit != None:
                conn_l.info("Using the deposit receipt to get the Edit-IRI: %s" % dr.edit)
                target_iri = dr.edit
            elif edit_iri != None:
                conn_l.info("Using the %s receipt as the Edit-IRI" % edit_iri)
                target_iri = edit_iri
            else:
                conn_l.error("Metadata or Metadata + file multipart-related update: Cannot find the Edit-IRI from the parameters supplied.")
        elif payload != None and filename != None:
            # File-only --> Edit-Media-IRI
            conn_l.info("Using the Edit-Media-IRI - File update uses a PUT request to the Edit-Media-IRI")
            request_type = "Update File PUT"
            if dr != None and dr.edit_media != None:
                conn_l.info("Using the deposit receipt to get the Edit-Media-IRI: %s" % dr.edit_media)
                target_iri = dr.edit_media
            elif edit_media_iri != None:
                conn_l.info("Using the %s receipt as the Edit-Media-IRI" % edit_media_iri)
                target_iri = edit_media_iri
            else:
                conn_l.error("File update: Cannot find the Edit-Media-IRI from the parameters supplied.")
            
        if target_iri == None:
            raise Exception("No suitable IRI was found for the request needed.")

        return self._make_request(target_iri = target_iri,
                                  metadata_entry=metadata_entry, 
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  packaging=packaging,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress,
                                  metadata_relevant=str(metadata_relevant),
                                  method="PUT",
                                  request_type=request_type,
                                  md5sum=md5sum)


        
    def add_file_to_resource(self, 
                        edit_media_iri,
                        payload,       # These need to be set to upload a file      
                        filename,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                       #                     (note that this requires the filename be expressed in ASCII)."  
                        mimetype=None,
                        packaging=None,
                        md5sum=None,               # optional; will be calculated for you otherwise
                        
                        on_behalf_of=None,
                        in_progress=False, 
                        metadata_relevant=False
                        ):
        """
Adding Files to the Media Resource

From the spec, paraphrased:
    
    "This feature is for use when clients wish to send individual files to the server and to receive back the IRI for the created resource. [Adding new items to the deposit container] will not give back the location of the deposited resources, so in cases where the server does not provide the (optional) Deposit Receipt, it is not possible for the client to ascertain the location of the file actually deposited - the Location header in that operation is the Edit-IRI. By POSTing to the EM-IRI, the Location header will return the IRI of the deposited file itself, rather than that of the container.

As the EM-IRI represents the Media Resource itself, rather than the Container, this operation will not formally support metadata handling, and therefore also offers no explicit support for packaging either since packages may be both content and metadata. Nonetheless, for files which may contain extractable metadata, there is a Metadata-Relevant header which can be defined to indicate whether the deposit can be used to augment the metadata of the container."

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_addingcontent_mediaresource


Set the following parameters in addition to the basic parameters:

    `edit_media_iri` - The Edit-Media-IRI
    
    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
        
Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

        """
        conn_l.info("Appending file to a deposit via Edit-Media-IRI %s" % edit_media_iri)
        return self._make_request(target_iri = edit_media_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  packaging=packaging,
                                  filename=filename,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress,
                                  method="POST",
                                  metadata_relevant=metadata_relevant,
                                  request_type='EM_IRI POST (APPEND)',
                                  md5sum=md5sum)

    def append(self, 
                        se_iri = None,  
                        
                        payload = None,       # These need to be set to upload a file      
                        filename = None,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                            #                     (note that this requires the filename be expressed in ASCII)."
                        mimetype = None,
                        packaging = None,
                        md5sum=None,               # optional; will be calculated for you otherwise
                        
                        on_behalf_of = None,
                        metadata_entry = None,
                        metadata_relevant = False,
                        in_progress = False,
                        dr = None
                        ):
        """
Adding Content to a Resource

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_addingcontent

Usage:
------

Set the target for this request:
--------------------------------

Set `se_iri` to be the SWORD2-Edit-IRI for a given deposit. (This can be found in `sword2.Deposit_Receipt.se_iri`)


    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

Then:
-----

1. "Adding New Packages or Files to a Container"
------------------------------------------------
            
Set the following parameters in addition to the basic parameters:

    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
        
Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)


2. "Adding New Metadata to a Container"
-------------------------------------def _normalise_mime(self, mime):
        if mime is None:
            return None
        return mime.lower().replace(" ", "")--

NB SWORD2 does not instruct the server on the best way to handle metadata, only that metadata SHOULD be 
added and not overwritten; in certain circumstances this may not produce the desired behaviour. 

Set the following parameters in addition to the basic parameters:
    
    `metadata_entry`  - An instance of `sword2.Entry`, set with the metadata required.
    
for example:
    # conn = `sword2.Connection`, se_iri = SWORD2-Edit-IRI
    >>> from sword2 import Entry
    >>> entry = Entry(dcterms:identifier = "doi://......")
    >>> conn.add_new_item_to_container(se_iri = se_iri,
    ...                                metadata_entry = entry)
              
Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

3. "Adding New Metadata and Packages or Files to a Container with Multipart"
----------------------------------------------------------------------------

Create a resource in a given collection by uploading a file AND the metadata about this resource.

To make this sort of request, just set the parameters as shown for both the binary upload and the metadata upload.

eg:
    
    >>> conn.add_new_item_to_container(se_iri = se_iri,
    ...                      metadata_entry = entry,
    ...                      payload = open("foo.zip", "r"),
    ...                      mimetype =  
                .... and so on

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)

        """
        
        if not se_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the SWORD2-Edit-IRI")
                se_iri = dr.se_iri
                if se_iri:
                    conn_l.info("Update Resource via SWORD2-Edit-IRI %s" % se_iri)
                else:
                    # we could try the edit IRI although technically that's not what it's for
                    se_iri = dr.edit
                    if se_iri:
                        conn_l.info("Complete deposit using the Edit-IRI %s as SWORD2-Edit-IRI not available" % se_iri)
                    else:
                        raise Exception("No SWORD2-Edit-IRI was given and no suitable IRI was found in the deposit receipt.")
            else:
                raise Exception("No SWORD2-Edit-IRI was given")
        else:
            conn_l.info("Update Resource via SWORD2-Edit-IRI %s" % se_iri)

        conn_l.info("Adding new file, metadata or both to a SWORD deposit via SWORD-Edit-IRI %s" % se_iri)
        return self._make_request(target_iri = se_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  packaging=packaging,
                                  filename=filename,
                                  metadata_entry=metadata_entry,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress, 
                                  method="POST",
                                  metadata_relevant=metadata_relevant,
                                  request_type='SE_IRI POST (APPEND PKG)',
                                  md5sum=md5sum)


    def delete(self,
                        resource_iri,
                        on_behalf_of=None):
        """
Delete resource

Generic method to send an HTTP DELETE request to a given IRI.

Can be given the optional parameter of `on_behalf_of`.
        """
        conn_l.info("Deleting resource %s" % resource_iri)
        return self._make_request(target_iri = resource_iri,
                                  on_behalf_of=on_behalf_of,
                                  method="DELETE",
                                  request_type='IRI DELETE',
                                  in_progress=False)

    def delete_content_of_resource(self, edit_media_iri = None,
                                         on_behalf_of = None,
                                         dr = None):
    
        """
Deleting the Content of a Resource    
    
Remove all the content of a resource without removing the resource itself

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_deletingcontent

Usage:
------

Set the target for this request:
--------------------------------

Set `edit_media_iri` to be the Edit-Media-IRI for a given resource.


    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.
        """
        if not edit_media_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the Edit-Media-IRI")
                edit_media_iri = dr.edit_media
                if edit_media_iri:
                    conn_l.info("Deleting Resource via Edit-Media-IRI %s" % edit_media_iri)
                else:
                    raise Exception("No Edit-Media-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Edit-Media-IRI was given")
        else:
            conn_l.info("Deleting Resource via Edit-Media-IRI %s" % edit_media_iri)

        return self.delete(edit_media_iri,
                                    on_behalf_of = on_behalf_of)





    def delete_container(self, edit_iri = None,
                               on_behalf_of = None,
                               dr = None):
    
        """
Deleting the Container    
    
Delete the entire object on the server, effectively removing the deposit entirely.

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_deleteconteiner

Usage:
------

Set the target for this request:
--------------------------------

Set `edit_iri` to be the Edit-IRI for a given resource.


    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

        """
        if not edit_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the Edit-IRI")
                edit_iri = dr.edit
                if edit_iri:
                    conn_l.info("Deleting Container via Edit-IRI %s" % edit_iri)
                else:
                    raise Exception("No Edit-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Edit-IRI was given")
        else:
            conn_l.info("Deleting Container via Edit-IRI %s" % edit_iri)

        return self.delete(edit_iri,
                                    on_behalf_of = on_behalf_of)
            
    def complete_deposit(self,
                        se_iri = None,
                        on_behalf_of=None,
                        dr = None):
        """
Completing a Previously Incomplete Deposit

Use this method to indicate to a server that a deposit which was 'in progress' is now complete. In other words, complete a deposit
which had the 'In-Progress' flag set to True.

#BETASWORD2URL
http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#continueddeposit_complete

Usage:
------

Set the target for this request:
--------------------------------

Set `se_iri` to be the SWORD2-Edit-IRI for a given resource.


    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.
        """
        
        if not se_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the SWORD2-Edit-IRI")
                se_iri = dr.se_iri
                if se_iri:
                    conn_l.info("Complete deposit using the SWORD2-Edit-IRI %s" % se_iri)
                else:
                    # we could try the edit-media IRI although technically that's not what it's for
                    se_iri = dr.edit
                    if se_iri:
                        conn_l.info("Complete deposit using the Edit-IRI %s as SWORD2-Edit-IRI not available" % se_iri)
                    else:
                        raise Exception("No SWORD2-Edit-IRI was given and no suitable IRI was found in the deposit receipt.")
            else:
                raise Exception("No SWORD2-Edit-IRI was given")
        else:
            conn_l.info("Complete deposit using the SWORD2-Edit-IRI %s" % se_iri)
        
        return self._make_request(target_iri = se_iri,
                                  on_behalf_of=on_behalf_of,
                                  in_progress='false',
                                  method="POST",
                                  empty=True,
                                  request_type='SE_IRI Complete Deposit')

    def update_files_for_resource(self, 
                        payload,       # These need to be set to upload a file      
                        filename,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                       #                     (note that this requires the filename be expressed in ASCII)."
                        mimetype=None,
                        packaging=None,
                        md5sum=None,               # optional; will be calculated for you otherwise
                        
                        edit_media_iri = None,
                        
                        on_behalf_of=None,
                        in_progress=False, 
                        metadata_relevant=False,
                        # Pass back the deposit receipt to automatically get the right IRI to use
                        dr = None
                        ):
        """
Replacing the File Content of a Resource

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_editingcontent_binary

The `Connection` can replace the file content of a resource, given the Edit-Media-IRI for this resource. This can be found
from the `sword2.Deposit_Receipt.edit_media` attribute of a previous deposit, or directly from the deposit receipt XML response.

Usage:
------

Set the target for this request:
--------------------------------

Set the `edit_media_iri` parameter to the Edit-Media-IRI.

    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

Then, add in the payload:
-------------------------

Set the following parameters in addition to the basic parameters (see `self.create_resource`):

    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
                    
    `metadata_relevant` - This should be set to `True` if the server should consider the file a potential source of metadata extraction, 
                          or `False` if the server should not attempt to extract any metadata from the deposi

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)
        """
        if not edit_media_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the Edit-Media-IRI")
                edit_media_iri = dr.edit_media
                if edit_media_iri:
                    conn_l.info("Update Resource via Edit-Media-IRI %s" % edit_media_iri)
                else:
                    raise Exception("No Edit-Media-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Edit-Media-IRI was given")
        else:
            conn_l.info("Update Resource via Edit-Media-IRI %s" % edit_media_iri)
            
        return self._make_request(target_iri = edit_media_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  in_progress=in_progress, 
                                  packaging=packaging,
                                  on_behalf_of=on_behalf_of,
                                  method="PUT",
                                  metadata_relevant=str(metadata_relevant),
                                  request_type='EM_IRI PUT',
                                  md5sum=md5sum)

    def update_metadata_for_resource(self, metadata_entry,    # required
                                           edit_iri = None,
                                           in_progress=False,
                                           on_behalf_of=None,
                                           dr = None
                                           ):
        """
Replacing the Metadata of a Resource

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_editingcontent_metadata

Replace the metadata of a resource as identified by its Edit-IRI. 

Note, from the specification: "The client can only be sure that the server will support this process when using the default format supported by SWORD: Qualified Dublin Core XML embedded directly in the atom:entry. Other metadata formats MAY be supported by a particular server, but this is not covered by the SWORD profile"

Usage:
------

Set the target for this request:
--------------------------------

Set the `edit_iri` parameter to the Edit-IRI.

    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

Then, add in the metadata:
--------------------------

Set the following in addition to the basic parameters:

    `metadata_entry`  - An instance of `sword2.Entry`, set with the metadata required.
    
for example, to replace the metadata for a given:
    # conn = `sword2.Connection`, edit_iri = Edit-IRI
    
    >>> from sword2 import Entry
    >>> entry = Entry(title = "My new deposit",
    ...               id = "new:id",    # atom:id
    ...               dcterms_abstract = "My Thesis",
    ...               dcterms_author = "Ben",
    ...               dcterms_issued = "2010")
    
    >>> conn.update_metadata_for_resource(edit_iri = edit_iri,
    ...                                   metadata_entry = entry)
              

Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)
        """
        if not edit_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the Edit-IRI")
                edit_iri = dr.edit
                if edit_iri:
                    conn_l.info("Update Resource via Edit-IRI %s" % edit_iri)
                else:
                    raise Exception("No Edit-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Edit-IRI was given")
        else:
            conn_l.info("Update Resource via Edit-IRI %s" % edit_iri)

        return self._make_request(target_iri = edit_iri,
                                  metadata_entry=metadata_entry,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress, 
                                  method="PUT",
                                  request_type='Edit_IRI PUT')

    def update_metadata_and_files_for_resource(self, metadata_entry,    # required
                                                     payload,       # These need to be set to upload a file      
                                                     filename,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                                                    #                     (note that this requires the filename be expressed in ASCII)."
                                                     mimetype=None,
                                                     packaging=None,
                                                     md5sum=None,               # optional; will be calculated for you otherwise
                                                     
                                                     edit_iri = None,
                        
                                                     metadata_relevant=False,
                                                     in_progress=False,
                                                     on_behalf_of=None,
                                                     dr = None
                                              ):
        """
Replacing the Metadata and Files of a Resource

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_editingcontent_multipart

Replace the metadata and files of a resource as identified by its Edit-IRI. 

Usage:
------

Set the target for this request:
--------------------------------

Set the `edit_iri` parameter to the Edit-IRI.

    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

Then, add in the file and metadata information:
-----------------------------------------------
Set the following in addition to the basic parameters:

File information:

    `payload`   - the payload to send. Can be either a bytestring or a File-like object that supports `payload.read()`
    `mimetype`  - MIMEType of the payload
    `filename`  - filename. Most SWORD2 uploads have this as being mandatory.
    `packaging` - the SWORD2 packaging type of the payload. 
                    eg packaging = 'http://purl.org/net/sword/package/Binary'
                    
    `metadata_relevant` - This should be set to `True` if the server should consider the file a potential source of metadata extraction, 
                          or `False` if the server should not attempt to extract any metadata from the deposi
    
Metadata information:

    `metadata_entry`  - An instance of `sword2.Entry`, set with the metadata required.
    
for example, to create a metadata entry
    >>> from sword2 import Entry
    >>> entry = Entry(title = "My new deposit",
    ...               id = "new:id",    # atom:id
    ...               dcterms_abstract = "My Thesis",
    ...               dcterms_author = "Ben",
    ...               dcterms_issued = "2010")
    
Response:
    
A `sword2.Deposit_Receipt` object containing the deposit receipt data. If the response was blank or 
not a Deposit Response, then only a few attributes will be populated:
            
    `code` -- HTTP code of the response
    `response_headers`  -- `dict` of the reponse headers
    `content`  --  (Optional) in case the response body is not empty but the response is not a Deposit Receipt
        
If exception-throwing is turned off (`error_response_raises_exceptions = False` or `self.raise_except = False`)
then the response will be a `sword2.Error_Document`, but will still have the aforementioned attributes set, (code,
response_headers, etc)
        """
        if not edit_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the Edit-IRI")
                edit_iri = dr.edit
                if edit_iri:
                    conn_l.info("Update Resource via Edit-IRI %s" % edit_iri)
                else:
                    raise Exception("No Edit-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Edit-IRI was given")
        else:
            conn_l.info("Update Resource via Edit-IRI %s" % edit_iri)

        return self._make_request(target_iri = edit_iri,
                                  metadata_entry=metadata_entry, 
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  packaging=packaging,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress,
                                  metadata_relevant=str(metadata_relevant),
                                  method="PUT",
                                  request_type='Edit_IRI PUT',
                                  md5sum=md5sum)


    def get_deposit_receipt(self, edit_iri):
        """
Getting a copy of the Entry Document/Deposit Receipt

FIXME: this explicitly requests the receipt from the server, but there is a
cache of deposit receipts - how should we access this?

FIXME: there's also something funny going on with get_resource remembering
old headers, but not quite sure where that's coming from.  Have to pass in
packaging and headers explicitly to overcome
        """
        conn_l.debug("Trying to GET the ATOM Entry Document at %s." % edit_iri)
        response = self.get_resource(edit_iri, packaging=None, headers={})
        if response.code == 200:
            conn_l.debug("Attempting to parse the response as a Deposit Receipt")
            d = Deposit_Receipt(xml_deposit_receipt = response.content)
            if d.parsed:
                conn_l.info("Server responsed with a Deposit Receipt. Caching a copy in .resources['%s']" % d.edit)
            d.response_headers = dict(response.response_headers)
            d.code = 200
            self._cache_deposit_receipt(d)
            return d
        elif response.code == 404:
            d = Deposit_Receipt()
            d.code = 404
            return d

    def get_ore_sword_statement(self, sword_statement_iri):
        """
Getting the Sword Statement.
        """
        # get the statement first
        conn_l.debug("Trying to GET the ORE Sword Statement at %s." % sword_statement_iri)
        response = self.get_resource(sword_statement_iri, headers = {'Accept':'application/rdf+xml'})
        if response.code == 200:
            #try:
            if True:
                conn_l.debug("Attempting to parse the response as a ORE Sword Statement")
                s = Ore_Sword_Statement(response.content)
                conn_l.debug("Parsed SWORD2 Statement, returning")
                return s
            #except Exception, e:
            #    # Any error here is to do with the parsing
            #    return response.content

    def get_atom_sword_statement(self, sword_statement_iri):
        """
Getting the Sword Statement.
        """
        # get the statement first
        conn_l.debug("Trying to GET the ATOM Sword Statement at %s." % sword_statement_iri)
        response = self.get_resource(sword_statement_iri, headers = {'Accept':'application/atom+xml;type=feed'})
        if response.code == 200:
            #try:
            if True:
                conn_l.debug("Attempting to parse the response as a ATOM Sword Statement")
                s = Atom_Sword_Statement(response.content)
                conn_l.debug("Parsed SWORD2 Statement, returning")
                return s
            #except Exception, e:
            #    # Any error here is to do with the parsing
            #    return response.content

    def get_resource(self, content_iri = None, 
                           packaging=None, 
                           on_behalf_of=None, 
                           headers = {},
                           dr = None):
        """
Retrieving the content

Get the file or package from the SWORD2 server.

From the specification:
    "The Deposit Receipt contains two IRIs which can be used to retrieve content from the server: Cont-IRI and EM-IRI. These are provided in the atom:content@src element and the atom:link@rel="edit-media" elements respectively. Their only functional difference is that the client MUST NOT carry out any HTTP operations other than GET on the Cont-IRI, while all operations are permitted on the EM-IRI. It is acceptable, but not required, that both IRIs to be the same, and in this section we refer only to the EM-IRI but in all cases it can be substituted for the Cont-IRI."

#BETASWORD2URL
See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_retrievingcontent

Usage:
------

Set the target for this request:
--------------------------------

Set `content_iri` to be the Content-IRI for a given resource (or to the IRI of any resource you wish to HTTP GET)


    OR 

you can pass back the `sword2.Deposit_Receipt` object you got from a previous transaction as the `dr` parameter, 
and the correct IRI will automatically be chosen.

Response:
    
    A `ContentWrapper` - 
        `ContentWrapper.response_headers`    -- response headers
        `ContentWrapper.content` -- body of response from server (the file or package)
        `ContentWrapper.code`    -- status code ('200' on success.)

        """
        if not content_iri:
            if dr != None:
                conn_l.info("Using the deposit receipt to get the SWORD2-Edit-IRI")
                content_iri = dr.cont_iri
                if content_iri:
                    conn_l.info("Getting the resource at Content-IRI %s" % content_iri)
                else:
                    raise Exception("No Content-IRI was given and no suitable IRI was found in the deposit receipt.")   
            else:
                raise Exception("No Content-IRI was given")
        else:
            conn_l.info("Getting the resource at Content-IRI %s" % content_iri)
        
        # 406 - PackagingFormatNotAvailable
        if self.honour_receipts and packaging:
            # Make sure that the packaging format is available from the deposit receipt, if loaded
            conn_l.debug("Checking that the packaging format '%s' is available." % content_iri)
            conn_l.debug("Cached Cont-IRI Receipts: %s" % self.cont_iris.keys())
            if content_iri in self.cont_iris.keys():
                if not (packaging in self.cont_iris[content_iri].packaging):
                    conn_l.error("Desired packaging format '%' not available from the server, according to the deposit receipt. Change the client parameter 'honour_receipts' to False to avoid this check.")
                    return self._return_error_or_exception(PackagingFormatNotAvailable, {}, "")
        if on_behalf_of:
            headers['On-Behalf-Of'] = on_behalf_of
        elif self.on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
        if packaging:
            headers['Accept-Packaging'] = packaging
        
        self._t.start("IRI GET resource")
        if packaging:
            conn_l.info("IRI GET resource '%s' with Accept-Packaging:%s" % (content_iri, packaging))
        else:
            conn_l.info("IRI GET resource '%s'" % content_iri)
        conn_l.debug("Using headers: " + str(headers))
        resp, content = self.h.request(content_iri, "GET", headers=headers)
        _, took_time = self._t.time_since_start("IRI GET resource")
        if self.history:
            self.history.log('Cont_IRI GET resource', 
                             sd_iri = self.sd_iri,
                             content_iri = content_iri,
                             packaging = packaging,
                             on_behalf_of = self.on_behalf_of,
                             response = resp,
                             headers = headers,
                             process_duration = took_time)
        conn_l.info("Server response: %s" % resp['status'])
        conn_l.debug(dict(resp))
        if resp['status'] == 200:
            conn_l.debug("Cont_IRI GET resource successful - got %s bytes from %s" % (len(content), content_iri))
            class ContentWrapper(object):
                def __init__(self, resp, content):
                    self.response_headers = dict(resp)
                    self.content = content
                    self.code = resp.status
            return ContentWrapper(resp, content)
        # NOTE: let the core error handling deal with this
        #elif resp['status'] == 406:   # Unavailable packaging format 
        #    conn_l.error("Desired packaging format '%' not available from the server.")
        #    return self._return_error_or_exception(PackagingFormatNotAvailable, resp, content)
        else:
            return self._handle_error_response(resp, content)
    
    def replace_file(self, file_edit_media, payload, mimetype, packaging=None, on_behalf_of=None, metadata_relevant=False):
        """
        API Sugar for replacing any given file (such as that retrieved from a feed of the media resource)
        This supports all the headers required by 6.11 of the spec
        """
        return self._make_request(file_edit_media, payload=payload, mimetype=mimetype, filename="unnamed",
                                    packaging=packaging, on_behalf_of=on_behalf_of, metadata_relevant=metadata_relevant,
                                    method="PUT")
    
    def delete_file(self, file_edit_media, on_behalf_of=None):
        """
        API sugar for deleting a given file (such as that retrieved from a feed of the media resource).
        This supports all the headers required by 6.11 of the spec
        """
        return self._make_request(file_edit_media, on_behalf_of=on_behalf_of, method="DELETE")
    
    def _normalise_mime(self, mime):
        if mime is None:
            return None
        return mime.lower().replace(" ", "")

