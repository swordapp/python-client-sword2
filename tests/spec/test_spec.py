from . import TestController
from sword2 import Connection, Entry

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
