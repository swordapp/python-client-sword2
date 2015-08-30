#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provides `Deposit_Receipt`, a convenient class for extracting information from the Deposit Receipts sent back by the 
SWORD2-compliant server for many transactions.

#BETASWORD2URL
See Section 10. Deposit Receipt: http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#depositreceipt

"""

from sword2_logging import logging
d_l = logging.getLogger(__name__)

from atom_objects import Category

from compatible_libs import etree
from utils import NS, get_text

class Deposit_Receipt(object):
    def __init__(self, xml_deposit_receipt=None, dom=None, response_headers={}, location=None, code=0):
        """
`Deposit_Receipt` - provides convenience methods for extracting information from the Deposit Receipts sent back by the 
SWORD2-compliant server for many transactions.

#BETASWORD2URL
See Section 10. Deposit Receipt: http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#depositreceipt

Transactions carried out by `sword2.Connection` will return a `Deposit_Receipt` object, if a deposit receipt document is sent back by the server.

Usage:
    
>>> from sword2 import Deposit_Receipt

.... get the XML text for a Deposit Receipt in the variable `doc`

# Parse the response:
>>> dr = Deposit_Receipt(xml_deposit_receipt = doc)

# Check that the response is parsable (valid XML) and is SWORD2-compliant
>>> assert dr.parsed == True
>>> assert dr.valid == True

Availible attributes:
    
    Atom convenience attribs -- corresponds to (type of object that is held)
    `self.title`            -- <atom:title>   (`str`)
    `self.id`               -- <id>           (`str`)
    `self.updated`          -- <updated>      (`str`)
    `self.summary`          -- <atom:summary> (`str`)
    `self.categories`       -- <category>     (`list` of `sword2.Category`)
        
    IRI/URIs
    `self.edit`             -- The Edit-IRI         (`str`)
                                <link rel="edit">
    `self.edit_media`       -- The Edit-Media-IRI   (`str`)
                                <link rel="edit-media">
    `self.edit_media_feed`  -- The Edit-Media-IRI [Atom Feed]  (`str`)
                                <link rel="edit-media" type="application/atom+xml;type=feed">
    `self.alternate`        -- A link which, according to the spec,                     (`str`)
                               "points to the splash page of the item on the server"
    `self.se_iri`           -- The SWORD2 Edit IRI (SE-IRI), defined by                 (`str`)
                                <link rel="http://purl.org/net/sword/terms/add"> 
                                which MAY be the same as the Edit-IRI

    `self.cont_iri`         -- The Content-IRI     (`str`)
                                eg `src` from <content type="application/zip" src="http://swordapp.org/cont-IRI/43/my_deposit"/>
    `self.content`          -- All Content-IRIs    (`dict` with the src or Content-IRI as the key, with a `dict` of the other attributes as its value
    
    `self.links`            -- All links elements in a `dict`, with the 'rel' value being used as its key. The values of this are `list`s 
                                with a `dict` of attributes for each item, corresponding to the information in a single <link> element.
                                
                                SWORD2 links for "http://purl.org/net/sword/terms/originalDeposit" and "http://purl.org.net/sword/terms/derivedResource"
                                are to be found in `self.links`
                                
                                eg
                                >>> dr.links.get("http://purl.org.net/sword/terms/derivedResource")
                                {'href': "....", 'type':'application/pdf'}
    

    General metadata:
    `self.metadata`         -- Simple metadata access. 
                                A `dict` where the keys are equivalent to the prefixed element names, with an underscore(_) replacing the colon (:)
                                eg "<dcterms:title>" in the deposit receipt would be accessible in this attribute, under
                                the key of 'dcterms_title'
                                
                                eg
                                >>> dr.metadata.get("dcterms_title")
                                "The Origin of Species"
                                
                                >>> dr.metadata.get("dcterms_madeupelement")
                                `None`
    
    `self.packaging`        -- sword:packaging elements declaring the formats that the Media Resource can be retrieved in   (`list` of `str`)
    
    `self.response_headers` -- The HTTP response headers that accompanied this receipt
    
    `self.location`         -- The location, if given (from HTTP Header: "Location: ....")
    """
        self.dom = None     # this will be populated below
        self.parsed = False
        self.valid = False
        self.response_headers=response_headers
        self.location = location
        self.content = None
        self.code = code
        self.metadata = {}
        self.links = {}
        self.edit = location # default to the location, which should always be the same as the edit-iri
        self.edit_media = None
        self.edit_media_feed = None
        self.alternate = None
        self.se_iri = None 
        self.atom_statement_iri = None
        self.ore_statement_iri = None
        # Atom convenience attribs
        self.title = None
        self.id = None
        self.updated = None
        self.summary = None
        
        self.packaging = []
        self.categories = []
        self.content = {}
        self.cont_iri = None
        
        # first construct or set the dom
        if xml_deposit_receipt:
            try:
                # convert the string to a byte array so that it doesn't matter whether it has encoding declared or not
                self.dom = etree.fromstring(bytes(xml_deposit_receipt))
                self.parsed = True    
            except Exception, e:
                d_l.error("Was not able to parse the deposit receipt as XML.")
                return
        elif dom != None:
            self.dom = dom
            self.parsed = True
        
        # allow for the possibility that we are not given a body for the deposit
        # receipt (explicitly allowed by the spec)
        if self.dom != None:
            # now validate the deposit receipt
            # Validation doesn't stop anything happening, it just lets the client
            # user know what to expect (note that Error_Document sub classes Deposit_Receipt
            # and that will almost always fail the validation)
            self.valid = self.validate()
            d_l.info("Initial SWORD2 validation checks on deposit receipt - Valid document? %s" % self.valid)
            
            # finally, handle the metadata
            self.handle_metadata()
    
    def validate(self):
        valid = True
        
        # LINK REQUIREMENTS
        
        # It MUST contain a Media Entry IRI (Edit-IRI), defined by atom:link@rel="edit"
        has_edit = False
        # It MUST contain a Media Resource IRI (EM-IRI), defined by atom:link@rel="edit-media"
        has_em = False
        # It MUST contain a SWORD Edit IRI (SE-IRI), defined by atom:link@rel=""" 
        # which MAY be the same as the Edit-IRI
        has_se = False
        
        links = self.dom.findall(NS['atom'] % "link")
        for link in links:
            rel = link.get("rel")
            if rel == "edit":
                has_edit = True
            elif rel == "edit-media":
                has_em = True
            elif rel == "http://purl.org/net/sword/terms/add":
                has_se = True
        
        if not has_edit or not has_em or not has_se:
            d_l.debug("Validation Fail: has_edit: " + str(has_edit) + "; has_em: " + str(has_em) + "; has_se: " + str(has_se))
            valid = False
        
        # It MUST contain a single sword:treatment element [SWORD003] which contains either a human-readable 
        # statement describing treatment the deposited resource has received or a IRI that dereferences to such a description.
        treatment = self.dom.findall(NS['sword'] % "treatment")
        if treatment == None or len(treatment) == 0:
            d_l.debug("Validation Fail: no treatment or treatment invalid: " + str(treatment))
            valid = False
        
        return valid
    
    def handle_metadata(self):
        """Method that walks the `etree.SubElement`, assigning the information to the objects attributes."""
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
                        self.metadata[field] = [e.text.strip()]
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
                                self.metadata[field] += [e.text]
                        else:
                            self.metadata[field] = [e.text]
                    
    def handle_link(self, e):
        """Method that handles the intepreting of <atom:link> element information and placing it into the anticipated attributes."""
        # MUST have rel
        rel = e.attrib.get('rel', None)
        if rel:
            if rel == "edit":
                self.edit = e.attrib.get('href', None)
            elif rel == "edit-media":
                # only put the edit-media iri in the convenience attribute if
                # there is no 'type'
                if self._normalise_mime(e.attrib.get('type')) == "application/atom+xml;type=feed":
                    self.edit_media_feed = e.attrib.get('href', None)
                else:
                    self.edit_media = e.attrib.get('href', None)
            elif rel == "http://purl.org/net/sword/terms/add":
                self.se_iri = e.attrib.get('href', None)
            elif rel == "alternate":
                self.alternate = e.attrib.get('href', None)
            elif rel == "http://purl.org/net/sword/terms/statement":
                t = self._normalise_mime(e.attrib.get("type"))
                if t is not None and t == "application/atom+xml;type=feed":
                    self.atom_statement_iri = e.attrib.get('href', None)
                elif t is not None and t == "application/rdf+xml":
                    self.ore_statement_iri = e.attrib.get('href', None)
                    
            # Put all links into .links attribute, with all element attribs
            attribs = {}
            for k,v in e.attrib.iteritems():
                if k != "rel":
                    attribs[k] = v
            if self.links.has_key(rel): 
                self.links[rel].append(attribs)
            else:
                self.links[rel] = [attribs]            
    
    def _normalise_mime(self, mime):
        if mime is None:
            return None
        return mime.lower().replace(" ", "")
        
    def handle_content(self, e):
        """Method to intepret the <atom:content> elements."""
        # eg <content type="application/zip" src="http://swordapp.org/cont-IRI/43/my_deposit"/>
        if e.attrib.has_key("src"):
            src = e.attrib['src']
            info = dict(e.attrib).copy()
            del info['src']
            self.content[src] = info
            self.cont_iri = src
            
    def to_xml(self):
        """Convenience method for outputing the DOM as a (byte)string."""
        return etree.tostring(self.dom)
    
    def __str__(self):
        """Method for producing a human-readable report about the information in this object, suitable
        for CLI or other logging.
        
        NB does not report all information, just key parts."""
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
