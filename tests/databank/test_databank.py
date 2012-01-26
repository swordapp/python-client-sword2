import uuid
from . import TestController
from sword2 import Connection, Entry, Error_Document, Atom_Sword_Statement, Ore_Sword_Statement
from sword2.compatible_libs import etree

PACKAGE = "tests/databank/example.zip"
PACKAGE_MIME = "application/zip"
SSS_URL = "http://localhost:5000/swordv2/service-document"
SSS_UN = "admin"
SSS_PW = "admin"
SSS_OBO = "obo"

DC = "{http://purl.org/dc/terms/}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"

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
    
    """
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
    """
    
    def test_02_get_service_document_unauthorised(self):
        conn = Connection(SSS_URL, user_name="alsdkfjsdz", user_pass="ZAKJKLASJDF")
        conn.get_service_document()
        assert conn.sd is None
    
    """
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
    """
    
    """ 
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
                        suggested_identifier = str(uuid.uuid4()))
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True
    """
    
    """ 
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
    """
    
    """
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
                        suggested_identifier = str(uuid.uuid4()))
                        
        assert receipt.code == 201
        assert receipt.location != None
        
        # these last two assertions are contingent on if we actually get a 
        # receipt back from the server (which we might not legitimately get)
        assert receipt.dom is None or receipt.parsed == True
        assert receipt.dom is None or receipt.valid == True
    """
    
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
                    suggested_identifier = str(uuid.uuid4()))
                        
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
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        
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
        suggested_id = str(uuid.uuid4())
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e, 
                        in_progress = True,
                        suggested_identifier = suggested_id)
        
        # we're going to work with the location
        assert receipt.location != None
        
        new_receipt = conn.get_deposit_receipt(receipt.location)
        
        assert new_receipt.code == 200
        assert new_receipt.parsed == True
        assert new_receipt.valid == True
        
        print new_receipt.to_xml()
        
        # Here are some more things we can know about the receipt
        # 1 - the links will all contain the suggested identifier
        # 2 - the links will all contain the name of the silo
        # 3 - the packaging will contain DataBankBagIt
        # 4 - the DC metadata will be reflected back at us
        # 5 - the atom metadata will be populated in some way
        
        for rel, links in new_receipt.links.iteritems():
            for link in links:
                assert suggested_id in link['href']
                assert col.title in link['href']
            
        assert "http://dataflow.ox.ac.uk/package/DataBankBagIt" in new_receipt.packaging
        
        # check the atom metadata
        assert new_receipt.title == "An entry only deposit"
        assert new_receipt.summary == "abstract"
        
        # check the DC metadata
        assert "An entry only deposit" in new_receipt.metadata["dcterms_title"]
        assert "abstract" in new_receipt.metadata["dcterms_abstract"]
        assert "http://whatever/" in new_receipt.metadata["dcterms_identifier"]
            
    
    """
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
    """
    
    """
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
        
        # we're going to work with the edit_media iri
        assert receipt.edit_media is not None
        
        resource = conn.get_resource(content_iri=receipt.edit_media)
        
        assert resource.code == 200
        assert resource.content is not None
    """
    
    """
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
    """
    
    """
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
        assert response.error_href == "http://purl.org/net/sword/error/ErrorContent"
    """
    
    """
    def test_15_retrieve_content_em_iri_as_feed(self):
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
        
        # we're going to work with the edit_media_feed iri
        assert receipt.edit_media_feed is not None
        
        response = conn.get_resource(content_iri=receipt.edit_media_feed)
        
        assert response.code == 200
        assert response.content is not None
        
        # the response should be an xml document, so let's see if we can parse
        # it.  This should give us an exception which will fail the test if not
        dom = etree.fromstring(response.content)
    """
    
    def test_16_basic_replace_file_content(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="update.zip",
                            packaging='http://purl.org/net/sword/package/SimpleZip')
        
        assert new_receipt.code == 204
        assert new_receipt.dom is None
        
    def test_17_advanced_replace_file_content(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="update.zip",
                            packaging='http://purl.org/net/sword/package/SimpleZip',
                            metadata_relevant=True)
        
        assert new_receipt.code == 204
        assert new_receipt.dom is None

    """
    def test_18_basic_replace_metadata(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        ne = Entry(title="A metadata update", id="asidjasidj", dcterms_abstract="new abstract", dcterms_identifier="http://elsewhere/")
        new_receipt = conn.update(dr=receipt, metadata_entry=ne)
        
        assert new_receipt.code == 204 or new_receipt.code == 200
        if new_receipt.code == 204:
            assert new_receipt.dom is None
        if new_receipt.code == 200:
            assert new_receipt.parsed == True
            assert new_receipt.valid == True
    """
    
    """
    def test_19_advanced_replace_metadata(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        ne = Entry(title="A metadata update", id="asidjasidj", dcterms_abstract="new abstract", dcterms_identifier="http://elsewhere/")
        new_receipt = conn.update(dr=receipt, metadata_entry=ne, in_progress=True)
        
        assert new_receipt.code == 204 or new_receipt.code == 200
        if new_receipt.code == 204:
            assert new_receipt.dom is None
        if new_receipt.code == 200:
            assert new_receipt.parsed == True
            assert new_receipt.valid == True
    """
    
    """
    def test_20_basic_replace_with_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
                        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        ne = Entry(title="A multipart update", id="asidjasidj", dcterms_abstract="new abstract", dcterms_identifier="http://elsewhere/")
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            metadata_entry = ne,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="update.zip",
                            packaging='http://purl.org/net/sword/package/SimpleZip')
        
        assert new_receipt.code == 204 or new_receipt.code == 200
        if new_receipt.code == 204:
            assert new_receipt.dom is None
        if new_receipt.code == 200:
            assert new_receipt.parsed == True
            assert new_receipt.valid == True
            
    def test_21_advanced_replace_with_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
                        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now do the replace
        ne = Entry(title="A multipart update", id="asidjasidj", dcterms_abstract="new abstract", dcterms_identifier="http://elsewhere/")
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            metadata_entry = ne,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="update.zip",
                            packaging='http://purl.org/net/sword/package/SimpleZip',
                            in_progress=True)
        
        assert new_receipt.code == 204 or new_receipt.code == 200
        if new_receipt.code == 204:
            assert new_receipt.dom is None
        if new_receipt.code == 200:
            assert new_receipt.parsed == True
            assert new_receipt.valid == True
    
    def test_22_delete_content(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        # now delete the content but not the container
        new_receipt = conn.delete_content_of_resource(dr=receipt)
        
        assert new_receipt.code == 204
        assert new_receipt.dom is None
        
    def test_23_basic_add_content_to_resource_single_file(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        receipt = conn.get_deposit_receipt(receipt.location)
        
        with open(PACKAGE) as pkg:
            new_receipt = conn.add_file_to_resource(receipt.edit_media, pkg, "addition.zip", mimetype=PACKAGE_MIME)
        
        assert new_receipt.code >= 200 and new_receipt.code < 400
        assert new_receipt.location is not None
        assert new_receipt.location != receipt.edit_media

    def test_24_advanced_add_content_to_resource_single_file(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        receipt = conn.get_deposit_receipt(receipt.location)
        
        with open(PACKAGE) as pkg:
            new_receipt = conn.add_file_to_resource(receipt.edit_media, pkg, "addition.zip", 
                                                    mimetype=PACKAGE_MIME,
                                                    metadata_relevant=True)
        
        assert new_receipt.code >= 200 and new_receipt.code < 400
        assert new_receipt.location is not None
        assert new_receipt.location != receipt.edit_media

    def test_25_basic_add_content_to_resource_package(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        receipt = conn.get_deposit_receipt(receipt.location)
        
        with open(PACKAGE) as pkg:
            new_receipt = conn.add_file_to_resource(receipt.edit_media, pkg, "addition.zip", 
                                                    mimetype=PACKAGE_MIME,
                                                    packaging="http://purl.org/net/sword/package/SimpleZip")
        
        assert new_receipt.code >= 200 and new_receipt.code < 400
        assert new_receipt.location is not None
        assert new_receipt.location == receipt.edit_media

    def test_26_advanced_add_content_to_resource_package(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href, 
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        receipt = conn.get_deposit_receipt(receipt.location)
        
        with open(PACKAGE) as pkg:
            new_receipt = conn.add_file_to_resource(receipt.edit_media, pkg, "addition.zip", 
                                                    mimetype=PACKAGE_MIME,
                                                    packaging="http://purl.org/net/sword/package/SimpleZip",
                                                    metadata_relevant=True)
        
        assert new_receipt.code >= 200 and new_receipt.code < 400
        assert new_receipt.location is not None
        assert new_receipt.location == receipt.edit_media

    def test_27_basic_add_metadata(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        ne = Entry(title="Multipart deposit", id="asidjasidj", dcterms_identifier="http://another/",
                    dcterms_creator="Me!", dcterms_rights="CC0")
        new_receipt = conn.append(dr=receipt, metadata_entry=ne)        
        
        assert new_receipt.code == 200

    def test_28_advanced_add_metadata(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        ne = Entry(title="Multipart deposit", id="asidjasidj", dcterms_identifier="http://another/",
                    dcterms_creator="Me!", dcterms_rights="CC0")
        new_receipt = conn.append(dr=receipt, metadata_entry=ne, in_progress=True)        
        
        assert new_receipt.code == 200

    def test_29_basic_add_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        ne = Entry(title="Multipart deposit", id="asidjasidj", dcterms_identifier="http://another/",
                    dcterms_creator="Me!", dcterms_rights="CC0")
        with open(PACKAGE) as pkg:
            new_receipt = conn.append(dr=receipt,
                                        metadata_entry=ne,
                                        payload=pkg, 
                                        filename="addition.zip", 
                                        mimetype=PACKAGE_MIME,
                                        packaging="http://purl.org/net/sword/package/SimpleZip")
            
        assert new_receipt.code >= 200 and new_receipt.code < 400

    def test_30_advanced_add_multipart(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        ne = Entry(title="Multipart deposit", id="asidjasidj", dcterms_identifier="http://another/",
                    dcterms_creator="Me!", dcterms_rights="CC0")
        with open(PACKAGE) as pkg:
            new_receipt = conn.append(dr=receipt,
                                        metadata_entry=ne,
                                        payload=pkg, 
                                        filename="addition.zip", 
                                        mimetype=PACKAGE_MIME,
                                        packaging="http://purl.org/net/sword/package/SimpleZip",
                                        in_progress=True,
                                        metadata_relevant=True)
            
        assert new_receipt.code >= 200 and new_receipt.code < 400

    # FIXME: this test just does not work, for no discernable reason.  The 
    # final assert of a 404 fails, and the debug output of the client says
    # that the server responded with a 200.  Nonetheless, the server logs show
    # that it responded with a 404, which would suggest a caching issue in the
    # client.  I have so far been unable to figure out where, though, despite
    # having tried turning off httplib2 caching and passing cache-control
    # headers in as per the httplib2 documentation.  help?
    def test_31_delete_container(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO,
                            error_response_raises_exceptions=False)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        edit_iri = receipt.location
        receipt = conn.get_deposit_receipt(edit_iri)
        
        # delete the container
        new_receipt = conn.delete_container(dr=receipt)
        
        assert new_receipt.code == 204
        assert new_receipt.dom is None
        
        # the next check is that this 404s appropriately now
        another_receipt = conn.get_deposit_receipt(edit_iri)
        
        # FIXME: this is the broken assert
        #assert another_receipt.code == 404
    """
    
    """
    def test_32_get_atom_statement(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW, on_behalf_of=SSS_OBO)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="Multipart deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        metadata_entry = e,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        edit_iri = receipt.location
        receipt = conn.get_deposit_receipt(edit_iri)
        
        assert receipt.atom_statement_iri is not None
        
        # get the statement
        statement = conn.get_atom_sword_statement(receipt.atom_statement_iri)
        
        assert isinstance(statement, Atom_Sword_Statement)
    """
    
    def test_33_get_ore_statement(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        e = Entry(title="An entry only deposit", id="asidjasidj", dcterms_abstract="abstract", dcterms_identifier="http://whatever/")
        receipt = conn.create(col_iri = col.href, metadata_entry = e)
        with open(PACKAGE) as pkg:
            new_receipt = conn.update(dr = receipt,
                            payload=pkg,
                            mimetype=PACKAGE_MIME,
                            filename="update.zip",
                            packaging='http://purl.org/net/sword/package/SimpleZip')
        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        receipt = conn.get_deposit_receipt(receipt.location)
        
        assert receipt.ore_statement_iri is not None
        
        # get the statement
        statement = conn.get_ore_sword_statement(receipt.ore_statement_iri)
        
        assert isinstance(statement, Ore_Sword_Statement)
        
        # some specific things that we can assert about the Statement
        # 1 - it should have the original deposits listed
        # 2 - it should have the aggregated resources listed
        # 3 - it should have the correct state
        # 4 - the dom should contain all the relevant metadata
        
        # check the original deposits
        od_uri = None
        assert len(statement.original_deposits) == 1
        for od in statement.original_deposits:
            assert "update.zip" in od.uri
            assert od.is_original_deposit
            assert od.deposited_on is not None
            # assert od.deposited_by == SSS_UN # FIXME: this may not work until we get auth sorted out
            assert od.deposited_on_behalf_of is None
            od_uri = od.uri
        
        # check the aggregated resources
        assert len(statement.resources) == 1
        for ar in statement.resources:
            # should be the same resource
            assert od_uri == ar.uri
        
        # check the states
        assert len(statement.states) == 1
        assert statement.states[0][0] == "http://databank.ox.ac.uk/state/PopulatedDataset"
        
        print etree.tostring(statement.dom, pretty_print=True)
        
        # check the metadata
        md_count = 0
        for e in statement.dom.findall(RDF + "Description"):
            for element in e.getchildren():
                if element.tag == DC + "title":
                    assert element.text.strip() == "An entry only deposit"
                    md_count += 1
                elif element.tag == DC + "abstract":
                    assert element.text.strip() == "abstract"
                    md_count += 1
                elif element.tag == DC + "identifier":
                    resource = element.attrib.get(RDF + "resource", None)
                    if resource is not None: # because we know that there is going to be more than one identifier
                        assert element.attrib.get(RDF + "resource") == "http://whatever/"
                        md_count += 1
                
        print "Metadata Count: " + str(md_count)
        assert md_count == 3

    """
    def test_34_complete_deposit(self):
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
                        suggested_identifier = str(uuid.uuid4()))
                        
        # ensure that we have a receipt (the server may not give us one
        # by default)
        edit_iri = receipt.location
        receipt = conn.get_deposit_receipt(edit_iri)
        
        response = conn.complete_deposit(dr=receipt)
        
        assert response.code == 200
        
    def test_35_error_checksum_mismatch(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW,
                            error_response_raises_exceptions=False)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = True,
                        suggested_identifier = str(uuid.uuid4()),
                        md5sum="123456789")
                        
        assert receipt.code == 412
        assert isinstance(receipt, Error_Document)
        assert receipt.error_href == "http://purl.org/net/sword/error/ErrorChecksumMismatch"
        
    def test_36_error_bad_request(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW,
                            error_response_raises_exceptions=False)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = "Invalid",    # the API seems to allow this!
                        suggested_identifier = str(uuid.uuid4()))
                        
        assert receipt.code == 400
        assert isinstance(receipt, Error_Document)
        assert receipt.error_href == "http://purl.org/net/sword/error/ErrorBadRequest"
        
    def test_37_error_target_owner_unknown(self):
        conn = Connection(SSS_URL, user_name=SSS_UN, user_pass=SSS_PW,
                            error_response_raises_exceptions=False)
        conn.get_service_document()
        col = conn.sd.workspaces[0][1][0]
        with open(PACKAGE) as pkg:
            receipt = conn.create(col_iri = col.href,
                        payload=pkg, 
                        mimetype=PACKAGE_MIME, 
                        filename="example.zip",
                        packaging = 'http://purl.org/net/sword/package/SimpleZip',
                        in_progress = True,
                        suggested_identifier = str(uuid.uuid4()),
                        on_behalf_of="richard") # we expressly set the wrong obo on the request rather than the connection
                        
        assert receipt.code == 403
        assert isinstance(receipt, Error_Document)
        assert receipt.error_href == "http://purl.org/net/sword/error/TargetOwnerUnknown"
        
    def test_38_error_mediation_not_allowed(self):
        # this is a placeholder; it's not possible to reliably test for this
        pass
        
    def test_39_error_method_not_allowed(self):
        # this is a placeholder; it's not possible to reliably test for this
        pass

    def test_40_error_max_upload_size_exceeded(self):
        # this is a placeholder; it's not possible to reliably test for this
        pass
    """























































