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
                       label=None,
                       text=None,
                       dom=None):
        self.term = term
        self.scheme = scheme
        self.label = label
        self.text = text
        if dom != None:
            self.dom = dom
            self._from_element(self.dom)
    
    def _from_element(self, e):
        for item in e.attrib.keys():
            if item.endswith("scheme"):
                self.scheme = e.attrib[item]
            elif item.endswith("term"):
                self.term = e.attrib[item]
            elif item.endswith("label"):
                self.label = e.attrib[item]
        if e.text:
            self.text = e.text

    def __str__(self):
        return "Category scheme:%s term:%s label:%s text:'%s'" % (self.scheme, 
                                                                  self.term,
                                                                  self.label,
                                                                  self.text)


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
        xml_str = etree.tostring(self.entry)
        if not xml_str.startswith('<?xml version="1.0"?>'):
            xml_str = '<?xml version="1.0"?>' + xml_str
        return xml_str
        
    def pretty_print(self):
        return etree.tostring(self.entry, pretty_print=True)
