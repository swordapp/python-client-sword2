#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sword2_logging import logging
from implementation_info import __version__
coll_l = logging.getLogger(__name__)

from compatible_libs import etree
from utils import NS, get_text

from deposit_receipt import Deposit_Receipt

from atom_objects import Category

from datetime import datetime


class SDCollection(object):
    def __init__(self, title=None, 
                       href=None,
                       accept=[], 
                       accept_multipart=[], 
                       categories=[],
                       collectionPolicy=None,
                       description = None,
                       mediation=None,
                       treatment=None,
                       acceptPackaging=[],
                       service=[]):
        # APP/Atom
        self.title = title
        self.href = href
        self.accept = accept
        self.accept_multipart = accept_multipart
        # SWORD
        self.mediation = mediation
        self.description = description
        self.treatment = treatment
        self.collectionPolicy = collectionPolicy
        self.acceptPackaging = acceptPackaging
        self.service = service
        self.categories = categories
    
    def _reset(self):
        self.title = None
        self.href = None
        self.accept = []
        self.accept_multipart = []
        # SWORD
        self.mediation = None
        self.description = None
        self.treatment = None
        self.collectionPolicy = None
        self.acceptPackaging = []
        self.service = None
        self.categories = []
    
    def load_from_etree(self, collection):
        self._reset()
        self.title = get_text(collection, NS['atom'] % 'title')
        # MUST have href attribute
        self.href = collection.attrib.get('href', None)
        # Accept and Accept multipart
        for accept in collection.findall(NS['app'] % 'accept'):
            if accept.attrib.get("alternate", None) == "multipart-related":
                self.accept_multipart.append(accept.text)
            else:
                self.accept.append(accept.text)
        # Categories
        for category_element in collection.findall(NS['atom'] % 'category'):
            self.categories.append(Category(dom=category_element))
        # SWORD extensions:
        self.collectionPolicy = get_text(collection, NS['sword'] % 'collectionPolicy')
                
        # Mediation: True/False
        mediation = get_text(collection, NS['sword'] % 'mediation')
        self.mediation = mediation.lower() == "true"
                
        self.treatment = get_text(collection, NS['sword'] % 'treatment')        
        self.description = get_text(collection, NS['dcterms'] % 'abstract')
        self.service = get_text(collection, NS['sword'] % 'service', plural = True)
        self.acceptPackaging = get_text(collection, NS['sword'] % 'acceptPackaging', plural = True)
        
        # Log collection details:
        coll_l.debug(str(self))
    
    def __str__(self):
        _s = ["Collection: '%s' @ '%s'. Accept:%s" % (self.title, self.href, self.accept)]
        if self.description:
            _s.append("SWORD: Description - '%s'" % self.description)
        if self.collectionPolicy:
            _s.append("SWORD: Collection Policy - '%s'" % self.collectionPolicy)
        if self.mediation:
            _s.append("SWORD: Mediation? - '%s'" % self.mediation)
        if self.treatment:
            _s.append("SWORD: Treatment - '%s'" % self.treatment)
        if self.acceptPackaging:
            _s.append("SWORD: Accept Packaging: '%s'" % self.acceptPackaging)
        if self.service:
            _s.append("SWORD: Nested Service Documents - '%s'" % self.service)
        for c in self.categories:
            _s.append(str(c))
        return "\n".join(_s)

    def to_json(self):
        from compatible_libs import json
        if json:
            # TODO categories
            _j = {'title':self.title,
                  'href':self.href,
                  'accept':self.accept,
                  'accept_multipart':self.accept_multipart,
                  'mediation':self.mediation,
                  'treatment':self.treatment,
                  'collectionPolicy':self.collectionPolicy,
                  'acceptPackaging':self.acceptPackaging,
                  'service':self.service,
                  'categories':self.categories}
            return json.dumps(_j)
        else:
            coll_l.error("Could not return information about Collection '%s' as JSON" % self.title)
            return

class Collection_Feed(object):
    def __init__(self, feed_iri=None, http_client=None):
        self.feed_xml = feed_xml
        self._cached = []
        self.h = http_client
        
class Sword_Statement(object):
    def __init__(self, xml_document):
        self.xml_document = xml_document
        self.first = None
        self.next = None
        self.previous = None
        self.last = None
        self.categories = []
        self.entries = []
        try:
            coll_l.info("Attempting to parse the Feed XML document")
            self.feed = etree.fromstring(xml_document)
        except Exception, e:
            coll_l.error("Failed to parse document")
            coll_l.error("XML document begins:\n %s" % xml_document[:300])
        self.enumerate_feed()

    def enumerate_feed(self):
        # Handle Categories
        for cate in self.feed.findall(NS['atom'] % 'category'):
            self.categories.append(Category(dom = cate))
        # handle entries - each one is compatible with a Deposit receipt, so using that
        for entry in self.feed.findall(NS['atom'] % 'entry'):
            self.entries.append(Deposit_Receipt(dom=entry))
        # TODO handle multipage first/last pagination
            

