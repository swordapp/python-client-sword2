class HttpResponse(object):
    def __init__(self, *args, **kwargs):
        pass
        
    def __getitem__(self, att):
        # needs to behave like a dictionary
        # we need to be able to look up at least:
        
        # content-type
        # status
        # location
        pass
        
    def get(self, att, default=None):
        # same as __getattr__ but with default return
        pass
        
    def keys(self):
        pass
    

class HttpLayer(object):
    def __init__(self, *args, **kwargs): pass
    def add_credentials(self, username, password): pass
    def request(self, uri, method, headers=None, body=None): 
        # should return a tuple of an HttpResponse object and the content
        pass
        
################################################################################
# Default httplib2 implementation
################################################################################

import httplib2

class HttpLib2Response(HttpResponse):
    def __init__(self, response):
        self.resp = response
        self.status = self.resp.status
        
    def __getitem__(self, att):
        return self.resp[att]
    
    def get(self, att, default=None):
        return self.resp.get(att, default)
        
    def keys(self):
        return self.resp.keys()

class HttpLib2Layer(HttpLayer):
    def __init__(self, cache_dir, timeout=30):
        self.h = httplib2.Http(".cache", timeout=30.0)
        
    def add_credentials(self, username, password):
        self.h.add_credentials(username, password)
        
    def request(self, uri, method, headers=None, body=None):
        resp, content = self.h.request(uri, method, headers=headers, body=body)
        return (HttpLib2Response(resp), content)
