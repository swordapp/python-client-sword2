"""
Test framework - basic skeleton to simplify loading testsuite-wide data/config or even
starting up a local SWORD2 server if later tests require this.
"""
from unittest import TestCase

class TestController(TestCase):

    def __init__(self, *args, **kwargs):
        # Load some config if required...
        TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        pass
        
    def tearDown(self):
        pass
