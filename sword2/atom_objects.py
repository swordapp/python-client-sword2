#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Non-SWORD2 specific Atom/APP helper classes. 

Most often used class will be 'Entry' - it provides an easy means to make an atom:entry 
document which can be used directly as the metadata entry.

Also provides Category, which is a convenience function to simplify reading in category information from an atom:entry
"""

from sword2_logging import logging
from implementation_info import __version__
coll_l = logging.getLogger(__name__)

from compatible_libs import etree
from utils import NS, get_text

from datetime import datetime

class Category(object):
    """Convenience class to aid in the intepreting of atom:category elements in XML. Currently, this is read-only.
    
    Usage:
    
    >>> from sword2 import Category
    
    ... # `Category` expects an etree.SubElement node (`c_node` in this example) referencing an <atom:category> element:
    <atom:category term="...." scheme="...." label="....."> .... </atom:category>
    
    # Load a `Category` instance:
    >>> c = Category(dom = c_node)
    
    # Overrides `__str__` to provide a simple means to view the content
    >>> print c
    "Category scheme:http://purl.org/net/sword/terms/ term:http://purl.org/net/sword/terms/originalDeposit label:Orignal Deposit text:'None'"
    
    # Element attributes appear as object attibutes:
    >>> c.scheme
    'http://purl.org/net/sword/terms/'
    
    # Element text will be in the text attribute, if text is present
    >>> c.text
    None
    
    """
    def __init__(self, term=None,
                       scheme=None,
                       label=None,
                       text=None,
                       dom=None):
        """Init a `Category` class - 99% of the time, this will be done by setting the dom parameter.
        
        However, if (for testing) there is a need to 'fake' a `Category`, all the attributes can be set in the constructor."""
        self.term = term
        self.scheme = scheme
        self.label = label
        self.text = text
        if dom != None:
            self.dom = dom
            self._from_element(self.dom)
    
    def _from_element(self, e):
        """ Load the `Category`'s internal attributes using the information within an `etree.SubElement`
        
        """
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
        """Rudimentary way to display the data held, in a way amenable to stdout."""
        return "Category scheme:%s term:%s label:%s text:'%s'" % (self.scheme, 
                                                                  self.term,
                                                                  self.label,
                                                                  self.text)


class Entry(object):
    """Used to create `Entry`s - for multipart/metadata submission. Has a simple and extendable way to add in
    namespace-aware key-value pairs.
    
    Example of use:

    >>> from sword2 import Entry
    >>> e = Entry()   # it can be opened blank, but more usefully...
    >>> e = Entry(id="atom id",
                  title="atom title",
                  dcterms_identifier="some other id")

    # Getting the bytestring document
    >>> print str(e)
    <?xml version="1.0"?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:dcterms="http://purl.org/dc/terms/">
        <generator uri="http://bitbucket.org/beno/python-sword2" version="0.1"/>
    <updated>2011-06-05T16:20:34.914474</updated><dcterms:identifier>some other id</dcterms:identifier><id>atom id</id><title>atom title</title></entry>


    # Adding fields to the metadata entry
    # dcterms (and other, non-atom fields) can be used by passing in a parameter with an underscore between the 
    # prefix and element name, eg:
    >>> e.add_fields(dcterms_title= "dcterms title", dcterms_some_other_field = "other")

    # atom:author field is treated slightly differently than all the other fields:
    # dictionary is required
    >>> e.add_fields(author={"name":"Ben", "email":"foo@example.org"})
    >>> print str(e)
    <?xml version="1.0"?>
    <entry xmlns="http://www.w3.org/2005/Atom" xmlns:dcterms="http://purl.org/dc/terms/">
        <generator uri="http://bitbucket.org/beno/python-sword2" version="0.1"/>
        <updated>2011-06-05T16:20:34.914474</updated>
        <dcterms:identifier>some other id</dcterms:identifier>
        <id>atom id</id><title>atom title</title>
        <author>
            <name>Ben</name>
            <email>foo@example.org</email>
        </author>
        <dcterms:some_other_field>other</dcterms:some_other_field>
        <dcterms:title>dcterms title</dcterms:title>
    </entry>
    >>> 

    # Other namespaces - use `Entry.register_namespace` to add them to the list of those considered  (prefix, URL):
    >>> e.register_namespace("myschema", "http://example.org")
    >>> e.add_fields(myschema_foo = "bar")
    >>> print str(e)
    <?xml version="1.0"?><entry xmlns="http://www.w3.org/2005/Atom" xmlns:dcterms="http://purl.org/dc/terms/">
        <generator uri="http://bitbucket.org/beno/python-sword2" version="0.1"/>
        <updated>2011-06-05T16:20:34.914474</updated>
        <dcterms:identifier>some other id</dcterms:identifier>
        <id>atom id</id><title>atom title</title>
        <author>
            <name>Ben</name>
            <email>foo@example.org</email>
        </author>
        <dcterms:some_other_field>other</dcterms:some_other_field>
        <dcterms:title>dcterms title</dcterms:title>
        <myschema:foo xmlns:myschema="http://example.org">bar</myschema:foo>
    </entry>

    This class doesn't provide editing/updating functions as the full etree API is exposed through the
    attribute 'entry'. For example:

    >>> len(e.entry.getchildren())
    14
"""
    atom_fields = ['title','id','updated','summary']
    add_ns = ['dcterms', 'atom', 'app']
    bootstrap = """<?xml version="1.0"?>
<entry xmlns="http://www.w3.org/2005/Atom"
        xmlns:dcterms="http://purl.org/dc/terms/">
    <generator uri="http://bitbucket.org/beno/python-sword2" version="%s"/>
</entry>""" % __version__
    def __init__(self, atomEntryXml=None, **kw):
        """Create a basic `Entry` document, setting the generator and a timestamp for the updated element value.
        
        Any keyword parameters passed in will be passed to the add_fields method and added to the entry
        bootstrap document. It's currently not possible to add a namespace and use it within the init call."""
        
        # create a namespace map which we'll use in all of the elements
        self.nsmap = {"dcterms" : "http://purl.org/dc/terms/", "atom" : "http://www.w3.org/2005/Atom"}
        self.entry = etree.fromstring(self.bootstrap if not atomEntryXml else atomEntryXml)
        if not 'updated' in kw.keys():
            kw['updated'] = datetime.now().isoformat()
        self.add_fields(**kw)
    
    def register_namespace(self, prefix, uri):
        """Registers a namespace,, making it available for use when adding subsequent fields to the entry.
        
        Registration will also affect the XML export, adding in the xmlns:prefix="url" attribute when required."""
        try:
            etree.register_namespace(prefix, uri)
        except AttributeError as e:
            # the etree implementation we're using doesn't support register_namespace
            # (probably lxml)
            pass
        self.add_ns.append(prefix)
        if prefix not in NS.keys():
            NS[prefix] = "{%s}%%s" % uri
            
        # we also have to handle namespaces internally, for etree implementations which
        # don't support register_namespace
        if prefix not in self.nsmap.keys():
            self.nsmap[prefix] = uri
            
    def add_field(self, k, v, attrs=None):
        """Append a single key-value pair to the `Entry` document. 
        
        eg
        
        >>> e.add_field("myprefix_fooo", "value")
        
        It is advisable to use the `Entry.add_fields` method instead as this is neater and simplifies element entry.
        
        Note that the atom:author field is handled differently, as it requires certain fields from the author:
        
        >>> e.add_field("author", {'name':".....",
                                   'email':"....",
                                   'uri':"...."} )
        
        Note that this means of entry is not supported for other elements."""
        if k in self.atom_fields:
            # These should be unique!
            old_e = self.entry.find(NS['atom'] % k)
            if old_e == None:
                e = etree.SubElement(self.entry, NS['atom'] % k, nsmap=self.nsmap) # Notice we explicitly declare the nsmap
                e.text = v
            else:
                old_e.text = v
        elif "_" in k:
            # possible XML namespace, eg 'dcterms_title'
            nmsp, tag = k.split("_", 1)
            if nmsp in self.add_ns:
                e = etree.SubElement(self.entry, NS[nmsp] % tag, nsmap=self.nsmap) # Notice we explicitly declare the nsmap
                e.text = v
                if attrs is not None:
                    for an, av in attrs.iteritems():
                        e.set(an, av)
        elif k == "author" and isinstance(v, dict):
            self.add_author(**v)

    def add_fields(self, **kw):
        """Add in multiple elements in one method call. 
        
        Eg:
        
        >>> e.add_fields(dcterms_title="Origin of the Species",
                        dcterms_contributor="Darwin, Charles")
        """
        for k,v in kw.iteritems():
            self.add_field(k,v)

    def add_author(self, name, uri=None, email=None):
        """Convenience function to add in the atom:author elements in the fashion
        required for Atom"""
        a = etree.SubElement(self.entry, NS['atom'] % 'author', nsmap=self.nsmap)
        n = etree.SubElement(a, NS['atom'] % 'name', nsmap=self.nsmap)
        n.text = name
        if uri:
            u = etree.SubElement(a, NS['atom'] % 'uri', nsmap=self.nsmap)
            u.text = uri
        if email:
            e = etree.SubElement(a, NS['atom'] % 'email', nsmap=self.nsmap)
            e.text = email

    def add_contributor(self, name, uri=None, email=None):
        """Convenience function to add in the atom:contributor elements in the fashion
        required for Atom"""
        a = etree.SubElement(self.entry, NS['atom'] % 'contributor', nsmap=self.nsmap)
        n = etree.SubElement(a, NS['atom'] % 'name', nsmap=self.nsmap)
        n.text = name
        if uri:
            u = etree.SubElement(a, NS['atom'] % 'uri', nsmap=self.nsmap)
            u.text = uri
        if email:
            e = etree.SubElement(a, NS['atom'] % 'email', nsmap=self.nsmap)
            e.text = email

    def __str__(self):
        """Export the XML to a bytestring, ready for use"""
        xml_str = etree.tostring(self.entry)
        if not xml_str.startswith('<?xml version="1.0"?>'):
            xml_str = '<?xml version="1.0"?>' + xml_str
        return xml_str
        
    def pretty_print(self):
        """A version of the XML document which should be slightly more readable on the command line."""
        return etree.tostring(self.entry, pretty_print=True)
