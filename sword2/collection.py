#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sword2_logging import logging
from implementation_info import __version__
coll_l = logging.getLogger(__name__)

from compatible_libs import etree
from utils import NS, get_text

from datetime import datetime

class Category(object):
    def __init__(self, term=None,
                       scheme=None,
                       label=None):
        self.term = term
        self.scheme = scheme
        self.label = label

class SDCollection(object):
    def __init__(self, title=None, 
                       href=None,
                       accept=[], 
                       accept_multipart=[], 
                       # TODO: categories=[],
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
        # TODO Categories
    
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
        # TODO categories
            
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
                  'service':self.service}
            return json.dumps(_j)
        else:
            coll_l.error("Could not return information about Collection '%s' as JSON" % self.title)
            return

class Collection_Feed(object):
    def __init__(self, feed_iri=None, http_client=None):
        self.feed_xml = feed_xml
        self._cached = []
        self.h = http_client
        
class Collection_Feed_Document(object):
    def __init__(self, xml_document):
        self.xml_document = xml_document
        self.first = None
        self.next = None
        self.previous = None
        self.last = None
        self.entries = []
        try:
            coll_l.info("Attempting to parse the Feed XML document")
            self.feed = etree.fromstring(xml_document)
            self.enumerate_feed()
        except Exception, e:
            coll_l.error("Failed to parse document")
            coll_l.error("XML document begins:\n %s" % xml_document[:300])

    def enumerate_feed(self):
        pass

class Entry(object):
    """Used to create Entrys - for multipart/metadata submission"""
    atom_fields = ['title','id','updated','summary']
    add_ns = ['dcterms']
    bootstrap = """<?xml version="1.0"?>
<entry xmlns="http://www.w3.org/2005/Atom"
        xmlns:dcterms="http://purl.org/dc/terms/">
    <generator uri="http://bitbucket.org/beno/python-sword2" version="%s"/>
</entry>""" % __version__
    def __init__(self, **kw):
        self.entry = etree.fromstring(self.bootstrap)
        if not 'updated' in kw.keys():
            kw['updated'] = datetime.now().isoformat()
        self.add_fields(**kw)
    
    def register_namespace(self, prefix, uri):
        etree.register_namespace(prefix, uri)
        self.add_ns.append(prefix)
        if prefix not in NS.keys():
            NS[prefix] = "{%s}%%s" % uri
            
    def add_field(self, k, v):
        if k in self.atom_fields:
            # These should be unique!
            old_e = self.entry.find(NS['atom'] % k)
            if old_e == None:
                e = etree.SubElement(self.entry, NS['atom'] % k)
                e.text = v
            else:
                old_e.text = v
        elif "_" in k:
            # possible XML namespace, eg 'dcterms_title'
            nmsp, tag = k.split("_", 1)
            if nmsp in self.add_ns:
                e = etree.SubElement(self.entry, NS[nmsp] % tag)
                e.text = v
        elif k == "author" and isinstance(v, dict):
            self.add_author(**v)

    def add_fields(self, **kw):
        for k,v in kw.iteritems():
            self.add_field(k,v)

    def add_author(self, name, uri=None, email=None):
        a = etree.SubElement(self.entry, NS['atom'] % 'author')
        n = etree.SubElement(a, NS['atom'] % 'name')
        n.text = name
        if uri:
            u = etree.SubElement(a, NS['atom'] % 'uri')
            u.text = uri
        if email:
            e = etree.SubElement(a, NS['atom'] % 'email')
            e.text = email

    def __str__(self):
        return etree.tostring(self.entry)
        
    def pretty_print(self):
        return etree.tostring(self.entry, pretty_print=True)
