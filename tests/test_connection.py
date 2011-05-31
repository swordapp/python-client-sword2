from . import TestController

from sword2 import Connection
from sword2.compatible_libs import json

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

class TestConnection(TestController):
    def test_01_blank_init(self):
        conn = Connection("http://example.org/service-doc")
        assert conn.sd_iri == "http://example.org/service-doc"
        assert conn.sd == None

    def test_02_init_then_load_from_string(self):
        conn = Connection("http://example.org/service-doc")
        assert conn.sd_iri == "http://example.org/service-doc"
        assert conn.sd == None
        conn.load_service_document(long_service_doc)
        assert conn.sd != None
        assert len(conn.sd.workspaces) == 2
        assert len(conn.workspaces) == 2
        assert conn.sd.workspaces[0][0] == "Main Site"
        assert conn.sd.workspaces[1][0] == "Sub-site"
        assert len(conn.sd.workspaces[1][1]) == 2
        
    def test_03_init_then_load_from_string_t_history(self):
        conn = Connection("http://example.org/service-doc")
        assert conn.sd_iri == "http://example.org/service-doc"
        assert conn.sd == None
        conn.load_service_document(long_service_doc)
        # Should have made a two client 'transactions', the init and subsequent XML load
        assert len(conn.history) == 2
        assert conn.history[0]['type'] == "init"
        assert conn.history[1]['type'] == "SD Parse"
