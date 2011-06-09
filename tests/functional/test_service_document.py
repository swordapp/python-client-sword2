from . import TestController

from sword2 import SDCollection, ServiceDocument
from sword2.compatible_libs import json

class TestSDCollection(TestController):
    def test_01_blank_init(self):
        c = SDCollection()
        assert c.title == None
        assert c.href == None
    
    def test_02_init(self):
        c = SDCollection(title="My test collection", href="http://example.org")
        assert c.title == "My test collection"
        assert c.href == "http://example.org"
        
    def test_03_init_and_update(self):
        c = SDCollection(title="My test collection", href="http://example.org")
        assert c.title == "My test collection"
        assert c.href == "http://example.org"
        c.title = "Altered Title"
        assert c.title == "Altered Title"
        
    def test_04_init_and_update_json_test(self):
        c = SDCollection(title="My test collection", href="http://example.org")
        assert c.title == "My test collection"
        assert c.href == "http://example.org"
        c.title = "Altered Title"
        assert c.title == "Altered Title"
        j = c.to_json()
        j_data = json.loads(j)
        assert j_data['title'] == "Altered Title"
        assert j_data['href'] == "http://example.org"
        assert j_data['accept'] == []

short_service_doc = '''<?xml version="1.0" ?>
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

long_service_doc = '''<?xml version="1.0" ?>
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
    <workspace>
        <atom:title>Sub-site</atom:title>

        <collection href="http://swordapp.org/col-iri/44">
            <atom:title>Collection 44</atom:title>
            <accept>*/*</accept>
            <accept alternate="multipart-related">*/*</accept>
            <sword:collectionPolicy>Collection Policy</sword:collectionPolicy>
            <dcterms:abstract>Collection Description</dcterms:abstract>
            <sword:mediation>true</sword:mediation>
            <sword:treatment>Treatment description</sword:treatment>
            <sword:acceptPackaging>http://purl.org/net/sword/package/SimpleZip</sword:acceptPackaging>
            <sword:service>http://swordapp.org/sd-iri/e5</sword:service>
            <sword:service>http://swordapp.org/sd-iri/e6</sword:service>
            <sword:service>http://swordapp.org/sd-iri/e7</sword:service>
            <sword:service>http://swordapp.org/sd-iri/e8</sword:service>
        </collection>
        <collection href="http://swordapp.org/col-iri/46">
            <atom:title>Collection 46</atom:title>
            <accept>application/zip</accept>
            <accept alternate="multipart-related">application/zip</accept>
            <sword:collectionPolicy>Only Theses</sword:collectionPolicy>
            <dcterms:abstract>Theses dropbox</dcterms:abstract>
            <sword:mediation>true</sword:mediation>
            <sword:treatment>Treatment description</sword:treatment>
            <sword:acceptPackaging>http://purl.org/net/sword/package/SimpleZip</sword:acceptPackaging>
        </collection>
    </workspace>
</service>'''

class TestServiceDocument(TestController):
    def test_01_blank_init(self):
        s = ServiceDocument()
        assert s.version == None
        assert s.parsed == False
        assert s.valid == False    # Invalid document as should be blank
        
    def test_02_init_and_load_simple(self):
        s = ServiceDocument()
        s.load_document(short_service_doc)
        assert s.version == "2.0"
        assert s.valid == True
        assert s.maxUploadSize == 16777216   # check int()
        
    def test_03_load_on_init(self):
        s = ServiceDocument(xml_response = short_service_doc)
        assert s.version == "2.0"
        assert s.valid == True
        assert s.maxUploadSize == 16777216   # check int()
                
    def test_04_init_and_load_long(self):
        s = ServiceDocument()
        s.load_document(long_service_doc)
        assert s.version == "2.0"
        assert s.valid == True
        assert s.maxUploadSize == 16777216   # check int()
        
    def test_05_long_load_on_init(self):
        s = ServiceDocument(xml_response = long_service_doc)
        assert s.version == "2.0"
        assert s.valid == True
        assert s.maxUploadSize == 16777216   # check int()
    
    def test_06_workspaces_short(self):
        s = ServiceDocument(xml_response = short_service_doc)
        assert len(s.workspaces) == 1
        assert s.workspaces[0][0] == "Main Site"
        assert len(s.workspaces[0][1]) == 1
        
    def test_07_workspaces_long(self):
        s = ServiceDocument(xml_response = long_service_doc)
        assert len(s.workspaces) == 2
        assert s.workspaces[0][0] == "Main Site"
        assert s.workspaces[1][0] == "Sub-site"
        assert len(s.workspaces[1][1]) == 2
    
    def test_08_collection_information_long(self):
        s = ServiceDocument(xml_response = long_service_doc)
        sub_workspace = s.workspaces[1]
        assert sub_workspace[0] == "Sub-site"
        sub_collections = sub_workspace[1]
        for c in sub_collections:
            if c.title == "Collection 44":
                assert c.href == "http://swordapp.org/col-iri/44"
                assert len(c.service) == 4
                assert c.mediation == True
            if c.href == "http://swordapp.org/col-iri/46":
                assert c.title == "Collection 46"
                assert c.service == None
                assert c.collectionPolicy == "Only Theses"    

    def test_09_accept_information_long(self):
        s = ServiceDocument(xml_response = long_service_doc)
        sub_workspace = s.workspaces[1]
        assert sub_workspace[0] == "Sub-site"
        sub_collections = sub_workspace[1]
        for c in sub_collections:
            if c.title == "Collection 44":
                assert "*/*" in c.accept
            if c.href == "http://swordapp.org/col-iri/46":
                assert "application/zip" in c.accept
                assert "http://purl.org/net/sword/package/SimpleZip" in c.acceptPackaging

