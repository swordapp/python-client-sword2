class HttpResponse(object):
    def __init__(self, *args, **kwargs):
        pass
        
    def __getitem__(self, att):
        # needs to behave like a dictionary
        # we need to be able to look up at least:
        
        # content-type
        # status (as an integer)
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
        self.status = int(self.resp.status)
        
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

################################################################################    
# Guest urllib2 implementation
################################################################################

import urllib2, base64

class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def http_request(self, request):
        request.add_header(self.auth_header, 'Basic %s' % base64.b64encode(self.username + ':' + self.password))
        return request
    
    https_request = http_request

class UrlLib2Response(HttpResponse):
    def __init__(self, response):
        self.response = response
        self.headers = dict(response.info())
        self.status = int(self.response.code)
    
    def __getitem__(self, att):
        # needs to behave like a dictionary
        # we need to be able to look up at least:
        
        # content-type
        # status
        # location
        if att == "status":
            return self.status
        return self.headers[att]
        
    def get(self, att, default=None):
        # same as __getattr__ but with default return
        if att == "status":
            return self.status
        return self.headers.get(att, default)
        
    def keys(self):
        return self.headers.keys() + ["status"]
    
class UrlLib2Layer(HttpLayer):
    def __init__(self, opener=None):
        self.opener = opener
        if self.opener is None:
            self.opener = urllib2.build_opener()
    
    def add_credentials(self, username, password):
        auth_handler = PreemptiveBasicAuthHandler(username, password)
        current_handlers = self.opener.handlers
        new_handlers = current_handlers + [auth_handler]
        self.opener = urllib2.build_opener(*new_handlers)
    
    def request(self, uri, method, headers=None, body=None): 
        # should return a tuple of an HttpResponse object and the content
        try:
            if method == "GET":
                req = urllib2.Request(uri, None, headers)
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            elif method == "POST":
                # FIXME: this approach doesn't scale, we need to fix this here and
                # in the python sword2 client itself
                req = urllib2.Request(uri, body, headers)
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            elif method == "PUT":
                # FIXME: this approach doesn't scale, we need to fix this here and
                # in the python sword2 client itself
                req = urllib2.Request(uri, body, headers)
                # monkey-patch the request method (which seems to be the fastest
                # way to do this)
                req.get_method = lambda: 'PUT'
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            elif method == "DELETE":
                req = urllib2.Request(uri, None, headers)
                # monkey-patch the request method (which seems to be the fastest
                # way to do this)
                req.get_method = lambda: 'DELETE'
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            else:
                raise NotImplementedError()
        except urllib2.HTTPError as e:
            try:
                # treat it like a normal response
                return UrlLib2Response(e), e.read()
            except Exception as e:
                # unable to read()
                return UrlLib2Response(e), None

