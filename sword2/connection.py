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

from compatible_libs import etree

import httplib2

class Connection(object):
    def __init__(self, service_document_iri, 
                       user_name=None,
                       user_pass=None,
                       on_behalf_of=None,
                       download_service_document = False,   # Don't automagically GET the SD_IRI by default
                       keep_history=True,
                       honour_sd=True):
        self.sd_iri = service_document_iri
        self.sd = None
        self.h_sd = honour_sd        #  Honour the SD - ie maxuploadsize, collection must exist, etc
        self.h = httplib2.Http()
        self.user_name = user_name
        self.on_behalf_of = on_behalf_of
        
        # Workspace/Collection 'cursors'
        self.current_workspace = None
        self.current_collection = None
        self.resources = {}          # Key = IRI, Value = latest Deposit Receipt
        self.cached_at = {}          # Key = IRI, Value = Timestamp for when receipt was cached
        
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
            self.h.add_credentials(user_name, user_pass)
        
        if self.sd_iri and download_service_document:
            self._t.start("get_service_document")
            self.get_service_document()
            conn_l.debug("Getting service document and dealing with the response: %s s" % self._t.time_since_start("get_service_document")[1])
        
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
    
    def create_resource(self, payload,
                        mimetype,
                        filename,
                        packaging,
                        workspace=None,     # Either provide workspace/collection or
                        collection=None,    # the exact Col-IRI itself
                        col_iri=None,  
                        suggested_identifier=None,
                        in_progress=True,
                        metadata_entry=None,
                        ):
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
        md5sum, f_size = get_md5(payload)
        
        # request-level headers
        headers = {}
        headers['In-Progress'] = str(in_progress).lower()
        if self.on_behalf_of:
            headers['On-Behalf-Of'] = self.on_behalf_of
        if suggested_identifier:
            headers['Slug'] = str(suggested_identifier)
        
        
        if hasattr(payload, 'read'):
            # Need to work out why a 401 challenge will stop httplib2 from sending the file...
            # likely need to make it re-seek to 0...
            # In the meantime, read the file into memory... *sigh*
            payload = payload.read()
        
        self._t.start("Col_IRI create new resource")
        if metadata_entry:
            multicontent_type, payload_data = create_multipart_related([{'key':'atom',
                                                                    'type':'application/atom+xml; charset="utf-8"',
                                                                    'data':str(metadata_entry),  # etree default is utf-8
                                                                    },
                                                                    {'key':'payload',
                                                                    'type':str(mimetype),
                                                                    'filename':filename,
                                                                    'data':payload,  # etree default is utf-8
                                                                    'headers':{'Content-MD5':str(md5sum),
                                                                               'Packaging':str(packaging),
                                                                               }
                                                                    }
                                                                   ])
                                                                   
            headers['Content-Type'] = multicontent_type + '; type="application/atom+xml"'
            headers['Content-Length'] = str(len(payload_data))    # must be str, not int type
            resp, content = self.h.request(col_iri, "POST", headers=headers, body = payload_data)
            _, took_time = self._t.time_since_start("Col_IRI create new resource")
            if self.history:
                self.history.log('Col_IRI Multipart POST', 
                                 sd_iri = self.sd_iri,
                                 col_iri = col_iri,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)
        else:
            headers['Content-Type'] = str(mimetype)
            headers['Content-MD5'] = str(md5sum)
            headers['Content-Length'] = str(f_size)
            headers['Content-Disposition'] = "attachment; filename=%s" % filename   # TODO: ensure filename is ASCII
            headers['Packaging'] = str(packaging)
            
            resp, content = self.h.request(col_iri, "POST", headers=headers, body = payload)
            _, took_time = self._t.time_since_start("Col_IRI create new resource")
            if self.history:
                self.history.log('Col_IRI POST', 
                                 sd_iri = self.sd_iri,
                                 col_iri = col_iri,
                                 response = resp,
                                 headers = headers,
                                 process_duration = took_time)
        
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
                    self.resources[d.edit] = d
                    self.cached_at = self._t.get_timestamp()
                    if not location:
                        return (d.edit, d)
                return (location, d)
            else:
                return (location, None)
        elif resp['status'] == "401":
            conn_l.error("You are unauthorised (401) to access this document on the server. Check your username/password credentials and your 'On Behalf Of'")
            return (None, None)
        elif resp['status'] == "403":
            conn_l.error("You are Forbidden (401) to POST to '%s'. Check your username/password credentials and your 'On Behalf Of'")
            return (None, None)
        elif resp['status'] == "408":
            conn_l.error("Request Timeout (408) - error uploading.")
            return (None, None)
        elif int(resp['status']) > 399:
            conn_l.error("Error occured. Response headers from the server:\n%s" % resp)
            return (None, None)

