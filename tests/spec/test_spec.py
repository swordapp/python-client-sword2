from . import TestController
from sword2 import Connection, Entry, Error_Document

PACKAGE = "tests/spec/example.zip"
PACKAGE_MIME = "application/zip"
SSS_URL = "http://localhost:8080/sd-uri"
SSS_UN = "sword"
SSS_PW = "sword"
SSS_OBO = "obo"

class TestConnection(TestController):
    def test_01_get_service_document(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        
        # given that the client is fully functional, testing that the
        # service document parses and is valid is sufficient.  This, obviously,
        # doesn't test the validation routine itself.
        assert conn.sd != None
        assert conn.sd.parsed == True
        assert conn.sd.valid == True 
        assert len(conn.sd.workspaces) == 1
        
    def test_02_get_service_document_on_behalf_of(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        
        # given that the client is fully functional, testing that the
        # service document parses and is valid is sufficient.  This, obviously,
        # doesn't test the validation routine itself.
        assert conn.sd != None
        assert conn.sd.parsed == True
        assert conn.sd.valid == True 
        assert len(conn.sd.workspaces) == 1
        
    def test_03_basic_create_resource_with_package(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True
        
    def test_04_advanced_create_resource_with_package(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = True,
                        suggested_identifier = "abcdefghijklmnop")
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True
        
    def test_05_basic_create_resource_with_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Foo", id="asidjasidj", dcterms_abstract="abstract", dcterms_title="my title")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True
        
    def test_06_advanced_create_resource_with_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Foo", id="asidjasidj", dcterms_abstract="abstract", dcterms_title="my title")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = True,
                        suggested_identifier = "zyxwvutsrq")
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True

    def test_07_basic_create_resource_with_entry(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href,
                    metadata_entry = e)
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True

    def test_08_advanced_create_resource_with_entry(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href,
                    metadata_entry = e,
                    in_progress = True,
                    suggested_identifier = "1234567890")
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True

    def test_09_basic_retrieve_deposit_receipt(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # we're going to work with the location
        assert receipt.location != None
        
        new_receipt = conn.get_deposit_receipt(receipt.location)
        
        assert new_receipt.code == 200
        assert new_receipt.parsed == True
        assert new_receipt.valid == True
        
    def test_10_advanced_retrieve_deposit_receipt(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = True,
                        suggested_identifier = "0987654321")
        
        # we're going to work with the location
        assert receipt.location != None
        
        new_receipt = conn.get_deposit_receipt(receipt.location)
        
        assert new_receipt.code == 200
        assert new_receipt.parsed == True
        assert new_receipt.valid == True

    def test_11_basic_retrieve_content_cont_iri(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging='http://purl.org/net/sword/package/SimpleZip')
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # we're going to work with the cont_iri
        assert receipt.cont_iri is not None
        
        resource = conn.get_resource(content_iri=receipt.cont_iri)
        
        assert resource.code == 200
        assert resource.content is not None
        
    def test_12_basic_retrieve_content_em_iri(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging='http://purl.org/net/sword/package/SimpleZip')
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # we're going to work with the cont_iri
        assert receipt.edit_media is not None
        
        resource = conn.get_resource(content_iri=receipt.edit_media)
        
        assert resource.code == 200
        assert resource.content is not None
        
    def test_13_advanced_retrieve_content_em_iri(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging='http://purl.org/net/sword/package/SimpleZip')
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        packaging = 'http://purl.org/net/sword/package/SimpleZip'
        if receipt.packaging is not None and len(receipt.packaging) > 0:
            packaging = receipt.packaging[0]
        
        resource = conn.get_resource(content_iri=receipt.edit_media, packaging=packaging, on_behalf_of=SSS_OBO)
        
        assert resource.code == 200
        assert resource.content is not None
   
    def test_14_error_retrieve_content_em_iri(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW,
                            error_response_raises_exceptions=False)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging='http://purl.org/net/sword/package/SimpleZip')
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        error = 'http://purl.org/net/sword/package/IJustMadeThisUp'
        response = conn.get_resource(content_iri=receipt.edit_media, packaging=error)
        
        assert response.code == 406
        assert isinstance(response, Error_Document)
        










































