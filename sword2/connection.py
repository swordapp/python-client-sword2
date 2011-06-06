#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
'Connection' class provides a SWORD2 client for a given service (~= Service Document IRI)

Example usage:
>>> from sword2 import Connection
>>> conn = Connection("http://example.org/service-doc")  # An SD_IRI is required.

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
"""

from sword2_logging import logging
conn_l = logging.getLogger(__name__)

from utils import Timer, NS, get_md5, create_multipart_related

from transaction_history import Transaction_History
from service_document import ServiceDocument
from deposit_receipt import Deposit_Receipt
from error_document import Error_Document
from collection import Sword_Statement
from exceptions import *

from compatible_libs import etree

import httplib2

class Connection(object):
    def __init__(self, service_document_iri, 
                       user_name=None,
                       user_pass=None,
                       on_behalf_of=None,
                       download_service_document = False,   # Don't automagically GET the SD_IRI by default
                       keep_history=True,
                       cache_deposit_receipts=True,
                       honour_receipts=True,
                       error_response_raises_exceptions=True):
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
        self.h = httplib2.Http(".cache", timeout=30.0)
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
        if self.raise_except:
            raise cls(resp)
        else:
            if resp['content-type'] in ['text/xml', 'application/xml']:
                conn_l.info("Returning an error document, due to HTTP response code %s" % resp.status)
                e = Error_Document(content, code=resp.status, resp = resp)
                return e
            else:
                conn_l.info("Returning due to HTTP response code %s" % resp.status)
                e = Error_Document(code=resp.status, resp = resp)
                return e
    
    def _handle_error_response(self, resp, content):
        if resp['status'] == "401":
            conn_l.error("You are unauthorised (401) to access this document on the server. Check your username/password credentials and your 'On Behalf Of'")
            self._return_error_or_exception(NotAuthorised, resp, content)
        elif resp['status'] == "403":
            conn_l.error("You are Forbidden (401) to POST to '%s'. Check your username/password credentials and your 'On Behalf Of'")
            self._return_error_or_exception(Forbidden, resp, content)
        elif resp['status'] == "408":
            conn_l.error("Request Timeout (408) - error uploading.")
            self._return_error_or_exception(RequestTimeOut, resp, content)
        elif int(resp['status']) > 499:
            conn_l.error("Server error occured. Response headers from the server:\n%s" % resp)
            self._return_error_or_exception(ServerError, resp, content)
        else:
            conn_l.error("Unknown error occured. Response headers from the server:\n%s" % resp)
            self._return_error_or_exception(HTTPResponseError, resp, content)
    
    def _cache_deposit_receipt(self, d):
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
            self.cached_at = self._t.get_timestamp()
        else:
            conn_l.debug("Caching request denied - deposit receipt caching is set to 'False'")
    
    def load_service_document(self, xml_document):
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
        if resp['status'] == "200":
            conn_l.info("Received a document for %s" % self.sd_iri)
            self.load_service_document(content)
        elif resp['status'] == "401":
            conn_l.error("You are unauthorised (401) to access this document on the server. Check your username/password credentials")
        
    def reset_transaction_history(self):
        self.history = Transaction_History()

    def _make_request(self,
                      target_iri, 
                      payload=None,       # These need to be set to upload a file
                      mimetype=None,      
                      filename=None,
                      packaging=None,
                        
                      metadata_entry=None,  # a sword2.Entry needs to be here, if 
                                              # a metadata entry is to be uploaded
                        
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
        if payload:
            md5sum, f_size = get_md5(payload)
        
        # request-level headers
        headers = {}
        headers['In-Progress'] = str(in_progress).lower()
        if on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
        elif self.on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
            
        if suggested_identifier:
            headers['Slug'] = str(suggested_identifier)
            
        if suggested_identifier:
            headers['Slug'] = str(suggested_identifier)
        
        
        if hasattr(payload, 'read'):
            # Need to work out why a 401 challenge will stop httplib2 from sending the file...
            # likely need to make it re-seek to 0...
            # In the meantime, read the file into memory... *sigh*
            payload = payload.read()
        
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
            headers['Content-Type'] = "application/atom+xml;type=entry"
            data = str(metadata_entry)
            headers['Content-Length'] = str(len(data))
            
            resp, content = self.h.request(target_iri, method, headers=headers, body = data)
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
            multicontent_type, payload_data = create_multipart_related([{'key':'atom',
                                                                    'type':'application/atom+xml; charset="utf-8"',
                                                                    'data':str(metadata_entry),  # etree default is utf-8
                                                                    },
                                                                    {'key':'payload',
                                                                    'type':str(mimetype),
                                                                    'filename':filename,
                                                                    'data':payload,  
                                                                    'headers':{'Content-MD5':str(md5sum),
                                                                               'Packaging':str(packaging),
                                                                               }
                                                                    }
                                                                   ])
                                                                   
            headers['Content-Type'] = multicontent_type + '; type="application/atom+xml"'
            headers['Content-Length'] = str(len(payload_data))    # must be str, not int type
            resp, content = self.h.request(target_iri, method, headers=headers, body = payload_data)
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
            headers['Content-Disposition'] = "attachment; filename=%s" % filename   # TODO: ensure filename is ASCII
            headers['Packaging'] = str(packaging)
            
            resp, content = self.h.request(target_iri, method, headers=headers, body = payload)
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
            return (None, None)
        
        if resp['status'] == "201":
            #   Deposit receipt in content
            conn_l.info("Received a Resource Created (201) response.")
            # Check response headers for updated Location IRI
            location = resp.get('location', None)
            if len(content) > 0:
                # Fighting chance that this is a deposit receipt
                d = Deposit_Receipt(content)
                if d.parsed:
                    conn_l.info("Server response included a Deposit Receipt. Caching a copy in .resources['%s']" % d.edit)
                    self._cache_deposit_receipt(d)
                    if not location:
                        return (d.edit, d)
                return (location, d)
            else:
                return (location, None)
        elif resp['status'] == "204":
            #   Deposit receipt in content
            conn_l.info("Received a valid 'No Content' (204) response.")
            # Check response headers for updated Locatio
            return (True, True)
        elif resp['status'] == "200":
            #   Deposit receipt in content
            conn_l.info("Received a valid (200) OK response.")
            content_type = resp.get('content-type')
            if content_type == "application/atom+xml;type=entry" and len(content) > 0:
                d = Deposit_Receipt(content)
                if d.parsed:
                    conn_l.info("Server response included a Deposit Receipt. Caching a copy in .resources['%s']" % d.edit)
                    self._cache_deposit_receipt(d)
                    return (d.edit, d)
            return (True, True)
        else:
            return self._handle_error_response(resp, content)
        

    
    def create_resource(self, 
                        workspace=None,     # Either provide workspace/collection or
                        collection=None,    # the exact Col-IRI itself
                        col_iri=None,  
                        
                        payload=None,       # These need to be set to upload a file
                        mimetype=None,      
                        filename=None,
                        packaging=None,
                        
                        metadata_entry=None,  # a sword2.Entry needs to be here, if 
                                              # a metadata entry is to be uploaded
                        
                        # Set both a file and a metadata entry for the method to perform a multipart
                        # related upload.
                        
                        suggested_identifier=None,
                        in_progress=True,
                        on_behalf_of=None
                        ):
        
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
            coll_l.error("No suitable Col-IRI was found, with the given parameters.")
            return
        
        return self._make_request(target_iri = col_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  packaging=packaging,
                                  metadata_entry=metadata_entry,
                                  suggested_identifier=None,
                                  in_progress=True,
                                  on_behalf_of=on_behalf_of,
                                  method="POST",
                                  request_type='Col_IRI POST')
        
    def update_resource(self, 
                        edit_media_iri,  
                        
                        payload,       # These need to be set to upload a file      
                        filename,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                       #                     (note that this requires the filename be expressed in ASCII)."
                        mimetype=None,
                        packaging=None,
                        on_behalf_of=None,
                        in_progress=False, 
                        metadata_relevant=False
                        ):
        conn_l.info("Update Resource via Edit-Media-IRI %s" % edit_media_iri)
        return self._make_request(target_iri = edit_media_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  in_progress=in_progress, 
                                  packaging=packaging,
                                  on_behalf_of=on_behalf_of,
                                  method="PUT",
                                  metadata_relevant=metadata_relevant,
                                  request_type='EM_IRI PUT')

    def update_metadata_for_resource(self, edit_iri,
                                           metadata_entry,    # required
                                           in_progress=False,
                                           on_behalf_of=None
                                           ):
        conn_l.info("Update Resource via Edit-IRI %s" % edit_iri)
        return self._make_request(target_iri = edit_iri,
                                  metadata_entry=metadata_entry,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=in_progress, 
                                  method="PUT",
                                  request_type='Edit_IRI PUT')
        
    def add_file_to_resource(self, 
                        edit_media_iri,  
                        
                        payload,       # These need to be set to upload a file      
                        filename,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                       #                     (note that this requires the filename be expressed in ASCII)."
                        mimetype=None,
                        on_behalf_of=None,
                        in_progress=False, 
                        metadata_relevant=False
                        ):
        conn_l.info("Appending file to a deposit via Edit-Media-IRI %s" % edit_media_iri)
        return self._make_request(target_iri = edit_media_iri,
                                  payload=payload,
                                  mimetype=mimetype,
                                  filename=filename,
                                  on_behalf_of=on_behalf_of,
                                  method="POST",
                                  metadata_relevant=metadata_relevant,
                                  request_type='EM_IRI POST (APPEND)')

    def add_new_item_to_container(self, 
                        se_iri,  
                        
                        payload=None,       # These need to be set to upload a file      
                        filename=None,      # According to spec, "The client MUST supply a Content-Disposition header with a filename parameter 
                                       #                     (note that this requires the filename be expressed in ASCII)."
                        mimetype=None,
                        packaging=None,
                        on_behalf_of=None,
                        metadata_entry=None,
                        metadata_relevant=False,
                        in_progress=False
                        ):
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
                                  request_type='SE_IRI POST (APPEND PKG)')


    def delete_resource(self,
                        resource_iri,
                        on_behalf_of=None):
        conn_l.info("Deleting resource %s" % resource_iri)
        return self._make_request(target_iri = resource_iri,
                                  on_behalf_of=on_behalf_of,
                                  method="DELETE",
                                  request_type='IRI DELETE')

    def complete_deposit(self,
                        se_iri,
                        on_behalf_of=None):
        conn_l.info("Completeing the deposit of %s (Edit-Media-IRI)" % se_iri)
        return self._make_request(target_iri = se_iri,
                                  on_behalf_of=on_behalf_of,
                                  in_progress=False,
                                  method="POST",
                                  empty=True,
                                  request_type='SE_IRI Complete Deposit')

    def get_atom_sword_statement(self, sword_statement_iri):
        # get the statement first
        conn_l.debug("Trying to GET the ATOM Sword Statement at %s." % sword_statement_iri)
        response = self.get_resource(sword_statement_iri, headers = {'Accept':'application/atom+xml;type=feed'})
        if response.resp:
            #try:
            if True:
                conn_l.debug("Attempting to parse the response as a ATOM Sword Statement")
                s = Sword_Statement(response.content)
                conn_l.debug("Parsed SWORD2 Statement, returning")
                return s
            #except Exception, e:
            #    # Any error here is to do with the parsing
            #    return response.content

    def get_resource(self, content_iri, packaging=None, on_behalf_of=None, headers = {}):
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
            headers['On-Behalf-Of'] = self.on_behalf_of
        elif self.on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
        if packaging:
            headers['Accept-Packaging'] = packaging
        
        self._t.start("IRI GET resource")
        if packaging:
            conn_l.info("IRI GET resource '%s' with Accept-Packaging:%s" % (content_iri, packaging))
        else:
            conn_l.info("IRI GET resource '%s'" % content_iri)
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
        conn_l.debug(resp)
        if resp['status'] == '200':
            conn_l.debug("Cont_IRI GET resource successful - got %s bytes from %s" % (len(content), content_iri))
            class ContentWrapper(object):
                def __init__(self, resp, content):
                    self.resp = resp
                    self.content = content
                    self.code = resp.status
            return ContentWrapper(resp, content)
        elif resp['status'] == '408':   # Unavailable packaging format 
            conn_l.error("Desired packaging format '%' not available from the server.")
            return self._return_error_or_exception(PackagingFormatNotAvailable, resp, content)
        else:
            return self._handle_error_response(resp, content)
