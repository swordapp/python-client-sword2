from . import TestController

from sword2 import Connection, Entry, UrlLib2Layer

PACKAGE = "/home/richard/Desktop/massive_file.zip"
PACKAGE_MIME = "application/zip"
SSS_URL = "http://localhost:5000/swordv2/service-document"
SSS_UN = "admin"
SSS_PW = "admin"
SSS_OBO = "obo"

class TestScale(TestController):
    
    def test_01_massive_file(self):
        http = UrlLib2Layer()
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, http_impl=http)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="scalability testing", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="massive_file.zip",
                            packaging='http://purl.org/net/sword/package/Binary')
                            
        assert new_receipt.code == 204
