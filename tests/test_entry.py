from . import TestController

from sword2.collection import Entry
from sword2.utils import NS

class TestEntry(TestController):
    def test_01_blank_init(self):
        e = Entry()
        assert len(e.entry.getchildren()) == 0
    
    def test_02_init_without_author(self):
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", dcterms_title="foo bar")
        assert e.entry.find(NS['atom'] % 'title') != None
        assert e.entry.find(NS['dcterms'] % 'appendix') != None
        assert e.entry.find(NS['dcterms'] % 'nonexistant_term') == None
        
    def test_03_init_with_author(self):
        e = Entry(title="Foo", id="asidjasidj", dcterms_appendix="blah blah", author={'name':'Ben', 'email':'foo@bar.com'})
        assert e.entry.find(NS['atom'] % 'title') != None
        a = e.entry.find(NS['atom'] % 'author')
        name = a.find(NS['atom'] % 'name')
        assert name.text == "Ben"
