from . import TestController

from sword2.error_document import Error_Document
from sword2.utils import NS

ED = """<?xml version="1.0" encoding="utf-8"?>
<sword:error xmlns="http://www.w3.org/2005/Atom"
       xmlns:sword="http://purl.org/net/sword/terms/"
       xmlns:arxiv="http://arxiv.org/schemas/atom"
       href="http://example.org/errors/BadManifest">
    <author>
        <name>Example repository</name>
    </author>
    <title>ERROR</title>
    <updated>2008-02-19T09:34:27Z</updated>

    <generator uri="https://example.org/sword-app/"
               version="0.9">sword@example.org</generator>

    <summary>The manifest could be parsed, but was not valid - 
    no technical metadata was provided.</summary>
    <sword:treatment>processing failed</sword:treatment>
    <sword:verboseDescription>
        Exception at [ ... ]
    </sword:verboseDescription>
    <link rel="alternate" href="https://arxiv.org/help" type="text/html"/>

</sword:error>
"""

ED2 = """<?xml version="1.0" encoding="utf-8"?>
<sword:error xmlns="http://www.w3.org/2005/Atom"
       xmlns:sword="http://purl.org/net/sword/terms/"
       xmlns:arxiv="http://arxiv.org/schemas/atom"
       href="http://purl.org/net/sword/error/TargetOwnerUnknown">
    <author>
        <name>Example repository</name>
    </author>
    <title>ERROR</title>
    <updated>2008-02-19T09:34:27Z</updated>

    <generator uri="https://example.org/sword-app/"
               version="0.9">sword@example.org</generator>

    <summary>The manifest could be parsed, but was not valid - 
    no technical metadata was provided.</summary>
    <sword:treatment>processing failed</sword:treatment>
    <sword:verboseDescription>
        Exception at [ ... ]
    </sword:verboseDescription>
    <link rel="alternate" href="https://arxiv.org/help" type="text/html"/>

</sword:error>
"""

class TestEntry(TestController):
    def test_00_blank_init(self):
        error_d = Error_Document(code=402, resp={'content-type':'text/plain'})
        assert error_d.code == 402
        assert error_d.response_headers['content-type'] == 'text/plain'
        
    def test_01_init_with_xml(self):
        error_d = Error_Document(ED)
        assert error_d.error_href == "http://example.org/errors/BadManifest"
        assert error_d.title == "ERROR"
        assert error_d.summary == """The manifest could be parsed, but was not valid - 
    no technical metadata was provided."""
        print error_d.metadata
        assert error_d.verboseDescription.strip() == """Exception at [ ... ]"""
        
    def test_02_error_info(self):
        error_d = Error_Document(ED)
        # Error href is not a known SWORD2 error
        assert error_d.error_info['IRI'] == "http://example.org/errors/BadManifest"
        assert error_d.error_info['name'] == "UNKNOWNERROR"
        
    def test_03_init_with_known_error_iri(self):
        error_d = Error_Document(ED2)
        assert error_d.error_href == "http://purl.org/net/sword/error/TargetOwnerUnknown"
        assert error_d.error_info['name'] == "TargetOwnerUnknown"
        
    def test_04_validate_code_with_known_error_iri(self):
        error_d = Error_Document(ED2, code=403)
        assert error_d.error_href == "http://purl.org/net/sword/error/TargetOwnerUnknown"
        assert error_d.error_info['name'] == "TargetOwnerUnknown"
        assert error_d.error_info['codes'] == [403]
        
    def test_04_invalid_code_with_known_error_iri(self):
        error_d = Error_Document(ED2, code=499)
        assert error_d.error_href == "http://purl.org/net/sword/error/TargetOwnerUnknown"
        assert error_d.error_info['name'] == "UNKNOWNERROR"
        assert error_d.error_info['codes'] == [499]
