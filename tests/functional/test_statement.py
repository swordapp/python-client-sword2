from . import TestController

from sword2 import Atom_Sword_Statement, Ore_Sword_Statement
from sword2.utils import NS
from datetime import datetime

ATOM_TEST_STATEMENT = """<atom:feed xmlns:sword="http://purl.org/net/sword/terms/" 
            xmlns:atom="http://www.w3.org/2005/Atom">

    <atom:category scheme="http://purl.org/net/sword/terms/state"
        term="http://purl.org/net/sword/terms/state/Testing"
        label="Testing">
            The work has passed through review and is now in the archive
    </atom:category>

    <atom:entry>
        <atom:category scheme="http://purl.org/net/sword/terms/" 
	        term="http://purl.org/net/sword/terms/originalDeposit" 
	        label="Orignal Deposit"/>
        <atom:content type="application/zip" 
                    src="http://localhost:8080/part-IRI/43/my_deposit/example.zip"/>
        <sword:packaging>http://purl.org/net/sword/package/SimpleZip</sword:packaging>
        <sword:depositedOn>2011-03-02T20:50:06Z</sword:depositedOn>
        <sword:depositedBy>sword</sword:depositedBy>
        <sword:depositedOnBehalfOf>jbloggs</sword:depositedOnBehalfOf>
    </atom:entry>

</atom:feed>
"""

ORE_TEST_STATEMENT = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" 
        xmlns:ore="http://www.openarchives.org/ore/terms/"
        xmlns:sword="http://purl.org/net/sword/terms/">

    <rdf:Description rdf:about="http://localhost:8080/edit-IRI/43/my_deposit">
        <ore:describes rdf:resource="http://localhost:8080/agg-IRI/43/my_deposit"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://localhost:8080/agg-IRI/43/my_deposit">
        <ore:isDescribedBy rdf:resource="http://localhost:8080/edit-IRI/43/my_deposit"/>
        <ore:aggregates rdf:resource="http://localhost:8080/part-IRI/43/my_deposit/example.zip"/>
        <sword:originalDeposit rdf:resource="http://localhost:8080/part-IRI/43/my_deposit/example.zip"/>
        <sword:state rdf:resource="http://purl.org/net/sword/terms/state/Testing"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://localhost:8080/part-IRI/43/my_deposit/example.zip">
        <sword:packaging rdf:resource="http://purl.org/net/sword/package/SimpleZip"/>
        <sword:depositedOn rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">
            2011-03-02T20:50:06Z
        </sword:depositedOn>
        <sword:depositedBy rdf:datatype="http://www.w3.org/2001/XMLSchema#string">
            sword
        </sword:depositedBy>
        <sword:depositedOnBehalfOf>jbloggs</sword:depositedOnBehalfOf>
    </rdf:Description>

    <rdf:Description rdf:about="http://purl.org/net/sword/terms/state/Testing">
        <sword:stateDescription>
            The work has passed through review and is now in the archive
        </sword:stateDescription>
    </rdf:Description>

</rdf:RDF>
"""

class TestStatement(TestController):
    def test_01_atom_blank_init(self):
        s = Atom_Sword_Statement()
        
        assert len(s.original_deposits) == 0
        assert len(s.resources) == 0
        assert len(s.states) == 0
        assert s.xml_document == None
        assert s.dom == None
        assert not s.parsed
        assert not s.valid
    
    def test_02_atom_init_with_statement(self):
        s = Atom_Sword_Statement(ATOM_TEST_STATEMENT)
        
        assert len(s.states) == 1
        assert len(s.original_deposits) == 1
        assert len(s.resources) == 1
        assert s.xml_document != None
        assert s.dom != None
        assert s.parsed
        assert s.valid
        
        uri, description = s.states[0]
        assert uri == "http://purl.org/net/sword/terms/state/Testing"
        assert description == "The work has passed through review and is now in the archive"
        
        
        t = datetime.strptime("2011-03-02T20:50:06Z", "%Y-%m-%dT%H:%M:%SZ")
        entry = s.resources[0]
        assert len(entry.packaging) == 1
        assert entry.deposited_by == "sword"
        assert entry.deposited_on_behalf_of == "jbloggs"
        assert entry.deposited_on == t
        assert entry.uri == "http://localhost:8080/part-IRI/43/my_deposit/example.zip"
        assert entry.packaging[0] == "http://purl.org/net/sword/package/SimpleZip"
        
    def test_03_ore_blank_init(self):
        s = Ore_Sword_Statement()
        
        assert len(s.original_deposits) == 0
        assert len(s.resources) == 0
        assert len(s.states) == 0
        assert s.xml_document == None
        assert s.dom == None
        assert not s.parsed
        assert not s.valid
    
    def test_04_ore_init_with_statement(self):
        s = Ore_Sword_Statement(ORE_TEST_STATEMENT)
        
        assert len(s.states) == 1
        assert len(s.original_deposits) == 1
        assert len(s.resources) == 1
        assert s.xml_document != None
        assert s.dom != None
        assert s.parsed
        assert s.valid
        
        uri, description = s.states[0]
        assert uri == "http://purl.org/net/sword/terms/state/Testing"
        assert description == "The work has passed through review and is now in the archive"
        
        
        t = datetime.strptime("2011-03-02T20:50:06Z", "%Y-%m-%dT%H:%M:%SZ")
        entry = s.resources[0]
        assert len(entry.packaging) == 1
        assert entry.deposited_by == "sword"
        assert entry.deposited_on_behalf_of == "jbloggs"
        assert entry.deposited_on == t
        assert entry.uri == "http://localhost:8080/part-IRI/43/my_deposit/example.zip"
        assert entry.packaging[0] == "http://purl.org/net/sword/package/SimpleZip"
    
