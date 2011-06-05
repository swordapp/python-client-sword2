#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sword2_logging import logging
d_l = logging.getLogger(__name__)

from atom_objects import Category

from compatible_libs import etree
from utils import NS, get_text

class Deposit_Receipt(object):
    def __init__(self, xml_deposit_receipt=None, dom=None):
        self.parsed = False
        if xml_deposit_receipt:
            try:
                self.dom = etree.fromstring(xml_deposit_receipt)
                self.parsed = True
            except Exception, e:
                d_l.error("Was not able to parse the deposit receipt as XML.")
                return
        elif dom != None:
            self.dom = dom
            self.parsed = True
        self.metadata = {}
        self.links = {}
        self.edit = None
        self.edit_media = None
        self.edit_media_feed = None
        self.alternate = None
        self.se_iri = None 
        # Atom convenience attribs
        self.title = None
        self.id = None
        self.updated = None
        self.summary = None
        
        self.packaging = []
        self.categories = []
        self.content = {}
        self.cont_iri = None
        self.handle_metadata()
    
    def handle_metadata(self):
        for e in self.dom.getchildren():
            for nmsp, prefix in NS.iteritems():
                if str(e.tag).startswith(prefix % ""):
                    _, tagname = e.tag.rsplit("}", 1)
                    field = "%s_%s" % (nmsp, tagname)
                    d_l.debug("Attempting to intepret field: '%s'" % field)
                    if field == "atom_link":
                        self.handle_link(e)
                    elif field == "atom_content":
                        self.handle_content(e)
                    elif field == "atom_generator":
                        for ak,av in e.attrib.iteritems():
                            if not e.text:
                                e.text = ""
                            e.text += " %s:\"%s\"" % (ak, av)
                        self.metadata[field] = e.text.strip()
                    elif field == "sword_packaging":
                        self.packaging.append(e.text)
                    else:
                        if field == "atom_title":
                            self.title = e.text
                        if field == "atom_id":
                            self.id = e.text
                        if field == "atom_updated":
                            self.updated = e.text
                        if field == "atom_summary":
                            self.summary = e.text
                        if field == "atom_category":
                            self.categories.append(Category(dom=e))
                        if self.metadata.has_key(field):
                            if isinstance(self.metadata[field], list):
                                self.metadata[field].append(e.text)
                            else:
                                self.metadata[field] = [self.metadata[field], e.text]
                        else:
                            self.metadata[field] = e.text
                    
    def handle_link(self, e):
        # MUST have rel
        rel = e.attrib.get('rel', None)
        if rel:
            if rel == "edit":
                self.edit = e.attrib.get('href', None)
            elif rel == "edit-media":
                # only put the edit-media iri in the convenience attribute if
                # there is no 'type'
                if not ('type' in e.attrib.keys()):
                    self.edit_media = e.attrib.get('href', None)
                elif e.attrib['type'] == "application/atom+xml;type=feed":
                    self.edit_media_feed = e.attrib.get('href', None)
            elif rel == "http://purl.org/net/sword/terms/add":
                self.se_iri = e.attrib.get('href', None)
            elif rel == "alternate":
                self.alternate = e.attrib.get('href', None)
            # Put all links into .links attribute, with all element attribs
            attribs = {}
            for k,v in e.attrib.iteritems():
                if k != "rel":
                    attribs[k] = v
            if self.links.has_key(rel): 
                self.links[rel].append(attribs)
            else:
                self.links[rel] = [attribs]            
            
        
    def handle_content(self, e):
        # TODO handle atom:content 
        # eg <content type="application/zip" src="http://swordapp.org/cont-IRI/43/my_deposit"/>
        if e.attrib.has_key("src"):
            src = e.attrib['src']
            info = dict(e.attrib).copy()
            del info['src']
            self.content[src] = info
            self.cont_iri = src
            
    def to_xml(self):
        return etree.tostring(self.dom)
    
    def __str__(self):
        _s = []
        for k in sorted(self.metadata.keys()):
            _s.append("%s: '%s'" % (k, self.metadata[k]))
        if self.edit:
            _s.append("Edit IRI: %s" % self.edit)
        if self.edit_media:
            _s.append("Edit-Media IRI: %s" % self.edit_media)
        if self.se_iri:
            _s.append("SWORD2 Add IRI: %s" % self.se_iri)
        for c in self.categories:
            _s.append(str(c))
        if self.packaging:
            _s.append("SWORD2 Package formats available: %s" % self.packaging)
        if self.alternate:
            _s.append("Alternate IRI: %s" % self.alternate)
        for k, v in self.links.iteritems():
            _s.append("Link rel:'%s' -- %s" % (k, v))
        return "\n".join(_s)
