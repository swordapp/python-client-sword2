from . import TestController
from sword2 import Connection, Entry

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
