#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sword2_logging import logging
d_l = logging.getLogger(__name__)

from compatible_libs import etree
from utils import NS, get_text

class Deposit_Receipt(object):
    def __init__(self, xml_deposit_receipt):
        self.parsed = False
        try:
            self.dom = etree.fromstring(xml_deposit_receipt)
            self.parsed = True
        except Exception, e:
            d_l.error("Was not able to parse the deposit receipt as XML.")
            return
        self.metadata = {}
        self.links = {}
        self.edit = None
        self.edit_media = None
        self.alternate = None
        self.sword_add = None
        self.handle_metadata()
    
    def handle_metadata(self):
        for e in self.dom.getchildren():
            for nmsp, prefix in NS.iteritems():
                if str(e.tag).startswith(prefix % ""):
                    _, tagname = e.tag.rsplit("}", 1)
                    field = "%s_%s" % (nmsp, tagname)
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
                    else:
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
                self.edit_media = e.attrib.get('href', None)
            elif rel == "http://purl.org/net/sword/terms/add":
                self.sword_add = e.attrib.get('href', None)
            elif rel == "alternate":
                self.alternate = e.attrib.get('href', None)
            else:            
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
        pass
    
    def __str__(self):
        _s = []
        for k in sorted(self.metadata.keys()):
            _s.append("%s: '%s'" % (k, self.metadata[k]))
        if self.edit:
            _s.append("Edit IRI: %s" % self.edit)
        if self.edit_media:
            _s.append("Edit-Media IRI: %s" % self.edit_media)
        if self.sword_add:
            _s.append("SWORD2 Add IRI: %s" % self.sword_add)
        if self.alternate:
            _s.append("Alternate IRI: %s" % self.alternate)
        for k, v in self.links.iteritems():
            _s.append("Link rel:'%s' -- %s" % (k, v))
        return "\n".join(_s)
