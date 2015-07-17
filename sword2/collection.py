#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Collection classes

These classes are used in their documented manner but most collect or group various other items
to make them suitable for use.

The key class is `Collection`, which is presents a simple read-only object which represents the
information held within a collection element in a SWORD2 document such as the Service Document.

Two other classes, `Collection_Feed` and `Sword_Statement` are works in progress for now, with limited support
for the things they logically handle.

"""

from sword2_logging import logging
from implementation_info import __version__
coll_l = logging.getLogger(__name__)

from compatible_libs import etree
from utils import NS, get_text

from deposit_receipt import Deposit_Receipt

from datetime import datetime


class SDCollection(object):
    """
    `Collection` - holds, parses and presents simple attributes with information taken from a collection entry
    within a SWORD2 Service Document.

    This will be instanciated by a `sword2.Service_Document` and as such, is unlikely to be called explicitly.

    Usage:

    >>> from sword2 import SDCollection
    >>> c = SDCollection()

    .... pull an `etree.SubElement` from a service document into `collection_node`

    >>> c.load_from_etree(collection_node)
    >>> c.collectionPolicy
    "This collection has the following policy for deposits"
    >>> c.title
    "Thesis Deposit"
    """
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
                       service=[],
                       dom=None):
        """
        Creates a `Collection` object - as used by `sword2.Service_Document`

        #BETASWORD2URL
        See http://sword-app.svn.sourceforge.net/viewvc/sword-app/spec/trunk/SWORDProfile.html?revision=HEAD#protocoloperations_retreivingservicedocument
        for more details about the SWORD2 Service Document.

        Usage:

        Read useful information from the attributes of this object once loaded.

        Attributes::

        title                --  <atom:title> - Title of collection, (`str`)
        href                 --  <collection href=... > - Collection IRI (`str`)
        accept               --  <accept>*</accept> - the formats which this collection can take in (`list` of `str`)
        accept_multipart     --  <accept alternate="multipart-related">*</accept> - the formats which this collection can take
                                                                                               in via multipart-related (`list` of `str`)
        categories           --  <atom:catogory> - Collection category (`list` of `sword2.Category`'s)
        collectionPolicy     --  <sword:collectionPolicy> - Collection policy (`str`)
        description          --  <dcterms:description> - Collection descriptive text (`str`)
        mediation            --  <sword:mediation> - Support for mediated deposit (`True` or `False`)
        treatment            --  <sword:treatment> - from the SWORD2 specifications:
                                            ".. either a human-readable statement describing treatment the deposited resource
                                            has received or a IRI that dereferences to such a description."
        acceptPackaging      --  <sword:acceptPackaging> - Accepted package types (`list` of `str`)
                                            from the SWORD2 specifications: "The value SHOULD be a IRI for a known packaging format"
        service              --  <sword:service> - References to nested service descriptions (`list` of `str`)

        Example XML fragment that is expected:  (xmlns="http://www.w3.org/2007/app")

        ...

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
        ...

        Parsing this fragment:

        Again, this step is done by the `sword2.Service_Document`, but if the above XML was in the `doc` variable:

            # Get an etree-compatible library, such as from `lxml.etree`, `xml.etree` or `elementtree.ElementTree`
            >>> from sword2.compatible_libs import etree
            >>> from sword2 import SDCollection
            >>> dom = etree.fromstring(doc)

            # create an `SDCollection` instance from this XML document
            >>> c = SDCollection(dom = dom)

            # query it
            >>> c.treatment
            "Treatment description"
            # Non-unique elements, for example:
            >>> c.service
            ["http://swordapp.org/sd-iri/e4"]
            >>> c.accept
            ["*/*"]

        """
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
        if dom != None:
            # Allow constructor variables to provide defaults, but information within the
            # XML element overwrites or appends.
            self.load_from_etree(dom)

    def _reset(self):
        """Blank this instance of `SDCollection`"""
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
        """
        Parse an `etree.SubElement` into attributes in this object.

        Also, caches the most recently used DOM object it is passed in
        `self.dom`
        """
        self._reset()
        self.dom = collection
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
        coll_l.debug(unicode(self))

    def __str__(self):
        """Provides a simple display of the pertinent information in this object suitable for CLI logging."""
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

    def __repr__(self):
        """Provides the atom.title of the collection as part of the repr reply"""
        return "<sword2.SDCollection - title: %s>" % self.title

    def to_json(self):
        """Provides a simple means to turn the important parsed information into a simple JSON-encoded form.

        NB this uses the attributes of the object, not the cached DOM object, so information can be altered/added
        on the fly."""
        from compatible_libs import json
        if json:
            _j = {'title':self.title,
                  'href':self.href,
                  'description':self.description,
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
    """Nothing to see here yet. Move along."""
    def __init__(self, feed_iri=None, http_client=None, feed_xml=None):
        self.feed_xml = feed_xml
        self.feed_iri = feed_iri
        self._cached = []
        self.h = http_client



