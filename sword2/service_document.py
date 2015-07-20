#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class to accept, parse and make queriable the Service Document response.

Example:

>>> doc = '''<?xml version="1.0" ?>
<service xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:sword="http://purl.org/net/sword/terms/"
    xmlns:atom="http://www.w3.org/2005/Atom"
    xmlns="http://www.w3.org/2007/app">

    <sword:version>2.0</sword:version>
    <sword:maxUploadSize>16777216</sword:maxUploadSize>

    <workspace>
        <atom:title>Main Site</atom:title>

        <collection href="http://swordapp.org/col-iri/43">
            <atom:title>Collection 43</atom:title>
            <accept>*/*</accept>
            <accept alternate="multipart-related">*/*</accept>
            <sword:collectionPolicy>Collection Policy</sword:collectionPolicy>
            <dcterms:abstract>Collection Description</dcterms:abstract>
            <sword:mediation>false</sword:mediation>
            <sword:treatment>Treatment description</sword:treatment>
            <sword:acceptPackaging>http://purl.org/net/sword/package/SimpleZip</sword:acceptPackaging>
            <sword:acceptPackaging>http://purl.org/net/sword/package/METSDSpaceSIP</sword:acceptPackaging>
            <sword:service>http://swordapp.org/sd-iri/e4</sword:service>
        </collection>
    </workspace>
</service>'''

>>> from sword2 import ServiceDocument
>>> s = ServiceDocument(doc)
>>> s.maxUploadSize
16777216
>>> s.workspaces
[('Main Site', [<sword2.service_document.Collection object at 0x167be10>])]

>>> for c in s.workspaces[0][1]: print c
... 
Collection: 'Collection 43' @ 'http://swordapp.org/col-iri/43'. Accept:[]
SWORD: Collection Policy - 'Collection Policy'
SWORD: Treatment - 'Treatment description'
SWORD: Accept Packaging: '['http://purl.org/net/sword/package/SimpleZip', 'http://purl.org/net/sword/package/METSDSpaceSIP']'
SWORD: Nested Service Documents - 'http://swordapp.org/sd-iri/e4'

"""

from sword2_logging import logging
sd_l = logging.getLogger(__name__)

from collection import SDCollection

from compatible_libs import etree
from utils import NS, get_text

class ServiceDocument(object):
    def __init__(self, xml_response=None, sd_uri=None):
        self.sd_uri = sd_uri     # Used mainly for debugging and logging
        self.parsed = False
        self.valid = False
        self.maxUploadSize = 0   # Zero implies no limit as default, as per spec
        self.version = None        # Default to an empty string before attempting to parse
        self.workspaces = []     # Once enumerated, this will be a list of tuples, 
                                 # of the form: ("Workspace Title", [list of SDCollection instances])
        if xml_response:
            self.load_document(xml_response)

    def load_document(self, xml_response):
        try:
            if self.sd_uri:
                sd_l.debug("Attempting to load service document for %s" % self.sd_uri)
            else:
                sd_l.debug("Attempting to load service document")
            self.raw_response = xml_response
            self.service_dom = etree.fromstring(xml_response)
            self.parsed = True
            self.valid = self.validate()
            sd_l.info("Initial SWORD2 validation checks on service document - Valid document? %s" % self.valid)
            self._enumerate_workspaces()
        except Exception, e:
            # Due to variability of underlying etree implementations, catching all
            # exceptions...
            sd_l.error("Could not parse the Service Document response from the server - %s" % e)
            sd_l.debug("Received the following raw response:")
            sd_l.debug(self.raw_response)

    def validate(self):
        valid = True
        if not self.parsed:
            return False
        # The SWORD server MUST specify the sword:version element with a value of 2.0
        # -- MUST have sword:version element
        # -- MUST have value of '2.0'
        self.version = get_text(self.service_dom, NS['sword'] % "version")
        if self.version:
            if self.version != "2.0":
                # Not a SWORD2 server...
                # Fail here?
                sd_l.error("The service document states that the server's endpoint is not SWORD 2.0 - stated version:%s" % self.version)
                valid = False
        else:
            sd_l.error("The service document did not have a sword:version")
            valid = False
        
        # The SWORD server MAY specify the sword:maxUploadSize (in kB) of content that can be uploaded in one request [SWORD003] as a child of the app:service element. If provided this MUST contain an integer.
        maxupload = get_text(self.service_dom, NS['sword'] % "maxUploadSize")
        if maxupload:
            try:
                self.maxUploadSize = int(maxupload)
            except ValueError:
                # Unparsable as an integer. Enough to fail a validation?
                # Strictly... yep
                sd_l.error("The service document did not have maximum upload size parseable as an integer.")
                valid = False
        
        # Check for the first workspace for a collection element, just to make sure there is something there.
        test_workspace = self.service_dom.find(NS['app'] % "workspace")
        if test_workspace != None:
            sd_l.debug("At least one app:workspace found, with at least one app:collection within it.")
        else:
            valid = False
            sd_l.error("Could not find a app:workspace element in the service document.")
            
        # The SWORD server MUST specify the app:accept element for the app:collection element. 
        # If the Collection can take any format content type, it should specify */* as its 
        # value [AtomPub]. It MUST also specify an app:accept element with an alternate attribute 
        # set to multipart-related as required by [AtomMultipart]. The formats specified by 
        # app:accept and app:accept@alternate="multipart-related" are RECOMMENDED to be the same.
        workspaces = self.service_dom.findall(NS['app'] % "workspace")
        if workspaces is not None:
            for workspace in workspaces:
                cols = workspace.findall(NS['app'] % "collection")
                for col in cols:
                    # the collection may contain a sub-service document, which means it is not
                    # beholden to the rules above
                    service = col.find(NS['sword'] % "service")
                    if service is not None:
                        continue
                    
                    # since we have no sub-service document, we must validate
                    accept_valid = True
                    multipart_accept_valid = True
                    accepts = col.findall(NS['app'] % "accept")
                    for accept in accepts:
                        multipart = accept.get("alternate")
                        if multipart is not None:
                            if multipart != "multipart-related" and multipart != "multipart/related":
                                multipart_accept_valid = False
                                sd_l.debug("Multipart accept alternate is incorrect: " + str(multipart))
                        else:
                            # FIXME: we could test to see if the content is viable, but probably that's pointless
                            pass
                         
                    if not multipart_accept_valid or not accept_valid:
                        sd_l.debug("Either the multipart accept or the accept fields were invalid (see above debug)")
                        valid = False
        
        return valid

    def _enumerate_workspaces(self):
        if not self.valid:
            sd_l.error("The service document didn't pass the SWORD2 validation steps ('MUST' statements in spec). The workspaces and collections will not be enumerated.")
            return
        
        if self.sd_uri:
            sd_l.info("Enumerating workspaces and collections from the service document for %s" % self.sd_uri)
        
        # Reset the internally cached set
        self.workspaces = []
        for workspace in self.service_dom.findall(NS['app'] % "workspace"):
            workspace_title = get_text(workspace, NS['atom'] % 'title')
            sd_l.debug("Found workspace '%s'" % workspace_title)
            collections = []
            for collection_element in workspace.findall(NS['app'] % 'collection'):
                # app:collection + sword extensions
                c = SDCollection()
                c.load_from_etree(collection_element)
                
                collections.append(c)
            self.workspaces.append( (workspace_title, collections) )   # Add tuple

