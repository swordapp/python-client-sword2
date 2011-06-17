from . import TestController

from sword2 import Connection, Entry
from sword2.exceptions import PackagingFormatNotAvailable
from sword2.compatible_libs import json

SSS_PY_URL="http://sword-app.svn.sourceforge.net/viewvc/sword-app/sss/trunk/sss.py?revision=HEAD"
PORT_NUMBER="8081"

import subprocess, urllib, tempfile
import os

import atexit

from time import sleep

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


f, sss_path = tempfile.mkstemp(suffix=".py")
os.close(f)

urllib.urlretrieve(SSS_PY_URL, sss_path)
sss_pid = subprocess.Popen(['python', sss_path, PORT_NUMBER])
sleep(1)

atexit.register(sss_pid.kill)

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
        
    def test_04_init_from_sss_then_get_doc(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword")
        assert conn.sd_iri == "http://localhost:%s/sd-uri" % PORT_NUMBER
        assert conn.sd == None    # Not asked to get sd doc yet
        conn.get_service_document()
        assert conn.sd != None
        assert conn.sd.parsed == True
        assert conn.sd.valid == True
        assert len(conn.sd.workspaces) == 1
        
    def test_05_init_from_sss(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        assert conn.sd_iri == "http://localhost:%s/sd-uri" % PORT_NUMBER
        assert conn.sd != None
        assert conn.sd.parsed == True
        assert conn.sd.valid == True
        assert len(conn.sd.workspaces) == 1
   
    def test_06_Simple_POST_to_sss(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        resp = conn.create(payload = "Payload is just a load of text", 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary', 
                                    workspace = 'Main Site', 
                                    collection = conn.sd.workspaces[0][1][0].title, 
                                    in_progress=True, 
                                    metadata_entry=None)
        assert resp.code == 201
   
    def test_07_Multipart_POST_to_sss(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        resp = conn.create(payload = "Multipart payload here", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary', 
                                    workspace='Main Site', 
                                    collection=conn.sd.workspaces[0][1][0].title, 
                                    in_progress=True)
        assert resp.code == 201

      
    def test_08_Simple_POST_to_sss_w_coliri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        resp = conn.create(payload = "Payload is just a load of text", 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True, 
                                    metadata_entry=None)
        assert resp.code == 201
   
    def test_09_Multipart_POST_to_sss_w_coliri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        resp = conn.create(payload = "Multipart payload here", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert resp != None


    def test_10_Multipart_POST_then_update_on_EM_IRI(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert deposit_receipt.edit_media != None
        dr = conn.update(payload = "Multipart_POST_then_update_on_EM_IRI  -- updated resource",
                                              mimetype = "text/plain",
                                              filename = "readthis.txt",
                                              packaging = "http://purl.org/net/sword/package/Binary",
                                              edit_media_iri = deposit_receipt.edit_media)
        assert dr.code == 204       # empty response
        
    def test_11_Multipart_POST_then_update_metadata_on_Edit_IRI(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert deposit_receipt.code == 201    # new resource
        
        e.add_fields(dcterms_newfield = "blah de blah")
        dr = conn.update_metadata_for_resource(edit_iri = deposit_receipt.edit,
                                                        metadata_entry = e)
        assert (dr.code == 200 or dr.code == 204)
        

    def test_12_Metadata_POST_to_sss(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        resp = conn.create(metadata_entry = e,
                                    workspace='Main Site', 
                                    collection=conn.sd.workspaces[0][1][0].title, 
                                    in_progress=True)
        assert resp != None
    
    
    def test_13_Metadata_POST_to_sss_altering_entry(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        e.add_fields(dcterms_identifier="doi://somerubbish", dcterms_foo="blah blah")
        resp = conn.create(metadata_entry = e,
                                    workspace='Main Site', 
                                    collection=conn.sd.workspaces[0][1][0].title, 
                                    in_progress=False)
        assert resp != None

    def test_14_Invalid_Packaging_cached_receipt(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True, honour_receipts=True)
        col_iri = conn.sd.workspaces[0][1][0].href  # pick the first collection
        dr = conn.create(payload = "Payload is just a load of text", 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = col_iri, 
                                    in_progress=True)
        # Now to GET that resource with invalid packaging
        try:
            content = conn.get_resource(dr.cont_iri, packaging="foofar")
            assert 1 == 0   # fail
        except PackagingFormatNotAvailable:
            # test the 'honour_receipts' flag and cached deposit 
            pass
      
    def test_15_Metadata_POST_to_sss_w_coliri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        dr = conn.create(metadata_entry = e,
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert dr.code == 201
    
    def test_16_Invalid_Packaging_cached_receipt(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True, honour_receipts=True)
        col_iri = conn.sd.workspaces[0][1][0].href  # pick the first collection
        dr = conn.create(payload = "Payload is just a load of text", 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = col_iri, 
                                    in_progress=True, 
                                    metadata_entry=None)
        # Now to GET that resource with invalid packaging
        try:
            content = conn.get_resource(dr.cont_iri, packaging="foofar")
            assert 1 == 0   # fail
        except PackagingFormatNotAvailable:
            # test the 'honour_receipts' flag and cached deposit 
            pass

    def test_17_Simple_POST_and_GET(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        col_iri = conn.sd.workspaces[0][1][0].href  # pick the first collection
        dr = conn.create(payload = "Simple_POST_and_GET", 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = col_iri, 
                                    in_progress=True, 
                                    metadata_entry=None)
        assert dr.code == 201
        # Now to GET that resource with no prescribed for packaging
        content_object = conn.get_resource(dr.cont_iri)
        # Can't guarantee that sss.py won't mangle submissions, so can't validate response at this moment
        assert content_object != None
        
      
    def test_18_Metadata_POST_to_se_iri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
                                    
        assert deposit_receipt.se_iri != None
        e.add_fields(dcterms_identifier="doi://somerubbish", dcterms_foo="blah blah")
        dr = conn.append(se_iri = deposit_receipt.se_iri,
                                              metadata_entry = e,
                                              in_progress=False)
        assert dr.code == 201       

    def test_19_File_POST_to_se_iri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
                                    
        assert deposit_receipt.se_iri != None
        dr = conn.append(se_iri = deposit_receipt.se_iri,
                                              payload = "Multipart_POST_then_appending_file_on_SE_IRI  -- updated resource",
                                              mimetype = "text/plain",
                                              filename = "readthisextrafile.txt",
                                              packaging = "http://purl.org/net/sword/package/Binary")
        assert dr.code == 201

    def test_20_Multipart_POST_to_se_iri(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
                                    
        assert deposit_receipt.se_iri != None
        e.add_fields(dcterms_identifier="doi://multipart_update_to_SE_IRI")
        dr = conn.append(se_iri = deposit_receipt.se_iri,
                                              payload = "Multipart_POST_then_appending_file_on_SE_IRI  -- updated resource",
                                              mimetype = "text/plain",
                                              filename = "readthisextrafile.txt",
                                              packaging = "http://purl.org/net/sword/package/Binary",
                                              metadata_entry = e)
        print dr.code
        assert dr.code == 201


    def test_21_Create_deposit_and_delete_content(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert deposit_receipt.edit_media != None
        dr = conn.delete(resource_iri = deposit_receipt.edit_media)
        assert dr.code == 204 or dr.code == 200


    def test_22_Create_deposit_and_delete_deposit(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert deposit_receipt.edit != None
        dr = conn.delete(resource_iri = deposit_receipt.edit)
        assert dr.code == 204 or dr.code == 200
        
        
    def test_23_Finish_in_progress_deposit(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        assert deposit_receipt.edit != None
        dr = conn.complete_deposit(se_iri = deposit_receipt.se_iri)
        print "This will fail until the sss.py SWORD2 server responds properly, rather than with code 201"
        assert dr.code == 200
        
    def test_24_get_sword_statement(self):
        conn = Connection("http://localhost:%s/sd-uri" % PORT_NUMBER, user_name="sword", user_pass="sword", download_service_document=True)
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        deposit_receipt = conn.create(payload = "Multipart_POST_then_update_on_EM_IRI", 
                                    metadata_entry = e, 
                                    mimetype = "text/plain", 
                                    filename = "readme.txt", 
                                    packaging = 'http://purl.org/net/sword/package/Binary',
                                    col_iri = conn.sd.workspaces[0][1][0].href, 
                                    in_progress=True)
        ss_iri = None
        for item_dict in deposit_receipt.links['http://purl.org/net/sword/terms/statement']:
            if item_dict.has_key('type') and item_dict.get('type', None) == "application/atom+xml;type=feed":
                ss_iri = item_dict.get('href')
        assert ss_iri != None
        ss = conn.get_atom_sword_statement(ss_iri)
        assert ss != None
        assert ss.entries[0].metadata.get('sword_depositedBy') == 'sword'
