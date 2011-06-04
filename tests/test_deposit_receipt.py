from . import TestController

from sword2.deposit_receipt import Deposit_Receipt
from sword2.utils import NS

DR = """<?xml version="1.0" ?>
<entry xmlns:dcterms="http://purl.org/dc/terms/"
    xmlns:sword="http://purl.org/net/sword/terms/"
    xmlns="http://www.w3.org/2005/Atom"
    xmlns:app="http://www.w3.org/2007/app">

    <title>My Deposit</title>
    <id>info:something:1</id>
    <updated>2008-08-18T14:27:08Z</updated>
    <summary type="text">A summary</summary>
    <generator uri="http://www.myrepository.ac.uk/sword-plugin" version="1.0"/>

    <!-- the item's metadata -->
    <dcterms:abstract>The abstract</dcterms:abstract>
    <dcterms:accessRights>Access Rights</dcterms:accessRights>
    <dcterms:alternative>Alternative Title</dcterms:alternative>
    <dcterms:available>Date Available</dcterms:available>
    <dcterms:bibliographicCitation>Bibliographic Citation</dcterms:bibliographicCitation>
    <dcterms:contributor>Contributor</dcterms:contributor>
    <dcterms:description>Description</dcterms:description>
    <dcterms:hasPart>Has Part</dcterms:hasPart>
    <dcterms:hasVersion>Has Version</dcterms:hasVersion>
    <dcterms:identifier>Identifier</dcterms:identifier>
    <dcterms:isPartOf>Is Part Of</dcterms:isPartOf>
    <dcterms:publisher>Publisher</dcterms:publisher>
    <dcterms:references>References</dcterms:references>
    <dcterms:rightsHolder>Rights Holder</dcterms:rightsHolder>
    <dcterms:source>Source</dcterms:source>
    <dcterms:title>Title</dcterms:title>
    <dcterms:type>Type</dcterms:type>

    <sword:verboseDescription>Verbose description</sword:verboseDescription>
    <sword:treatment>Unpacked. JPEG contents converted to JPEG2000.</sword:treatment>

    <link rel="alternate" href="http://www.swordserver.ac.uk/col1/mydeposit.html"/>
    <content type="application/zip" src="http://www.swordserver.ac.uk/col1/mydeposit"/>
    <link rel="edit-media" href="http://www.swordserver.ac.uk/col1/mydeposit"/>
    <link rel="edit" href="http://www.swordserver.ac.uk/col1/mydeposit.atom" />
    <link rel="http://purl.org/net/sword/terms/add" href="http://www.swordserver.ac.uk/col1/mydeposit.atom" />
    <sword:packaging>http://purl.org/net/sword/package/BagIt</sword:packaging>

    <link rel="http://purl.org/net/sword/terms/originalDeposit" 
            type="application/zip" 
            href="http://www.swordserver.ac.uk/col1/mydeposit/package.zip"/>
    <link rel="http://purl.org/net/sword/terms/derivedResource" 
            type="application/pdf" 
            href="http://www.swordserver.ac.uk/col1/mydeposit/file1.pdf"/>
    <link rel="http://purl.org/net/sword/terms/derivedResource" 
            type="application/pdf" 
            href="http://www.swordserver.ac.uk/col1/mydeposit/file2.pdf"/>

    <link rel="http://purl.org/net/sword/terms/statement" 
            type="application/atom+xml;type=feed" 
            href="http://www.swordserver.ac.uk/col1/mydeposit.feed"/>
    <link rel="http://purl.org/net/sword/terms/statement" 
            type="application/rdf+xml" 
            href="http://www.swordserver.ac.uk/col1/mydeposit.rdf"/>


</entry>"""

class TestDepositReceipt(TestController):
    def test_01_init(self):
        dr = Deposit_Receipt(DR)
        assert dr.metadata['dcterms_title'] == "Title"
        assert dr.metadata['atom_id'] == "info:something:1"
        assert dr.id == "info:something:1"
        assert dr.title == "My Deposit"
        assert dr.metadata['sword_verboseDescription'] == "Verbose description"
        
    def test_02_edit(self):
        dr = Deposit_Receipt(DR)
        assert dr.edit == "http://www.swordserver.ac.uk/col1/mydeposit.atom"
        assert dr.edit_media == "http://www.swordserver.ac.uk/col1/mydeposit"
        
    def test_03_content_iri(self):
        dr = Deposit_Receipt(DR)
        assert dr.edit == "http://www.swordserver.ac.uk/col1/mydeposit.atom"
        assert "http://www.swordserver.ac.uk/col1/mydeposit" in dr.content.keys()
        assert dr.content["http://www.swordserver.ac.uk/col1/mydeposit"]['type'] == "application/zip"
        # Check convenience attribute 'cont_iri'
        assert dr.cont_iri == "http://www.swordserver.ac.uk/col1/mydeposit"
        
    def test_04_packaging(self):
        dr = Deposit_Receipt(DR)
        assert "http://purl.org/net/sword/package/BagIt" in dr.packaging
        assert len(dr.packaging) == 1
    
