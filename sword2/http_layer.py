import json
from sword2_logging import logging
http_l = logging.getLogger(__name__)

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

    def __repr__(self):
        return json.dumps(self.__dict__, indent=True)

    def get(self, att, default=None):
        # same as __getattr__ but with default return
        pass

    def keys(self):
        pass


class HttpLayer(object):
    def __init__(self, *args, **kwargs): pass
    def add_credentials(self, username, password): pass
    def request(self, uri, method, headers=None, payload=None):
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
        if att == "status":
            return self.status
        return self.resp.get(att)

    def get(self, att, default=None):
        if att == "status":
            return self.status
        return self.resp.get(att, default)

    def keys(self):
        return self.resp.keys()

class HttpLib2Layer(HttpLayer):
    def __init__(self, cache_dir=".cache", timeout=30.0, ca_certs=None):
        self.h = httplib2.Http(cache_dir, timeout=timeout, ca_certs=ca_certs)

    def add_credentials(self, username, password):
        self.h.add_credentials(username, password)

    def request(self, uri, method, headers=None, payload=None):
        if hasattr(payload, 'read'):
            # Need to work out why a 401 challenge will stop httplib2 from sending the file...
            # likely need to make it re-seek to 0...
            # FIXME: In the meantime, read the file into memory... *sigh*
            payload = payload.read()
        resp, content = self.h.request(uri, method, headers=headers, body=payload)
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

# http://stackoverflow.com/questions/2502596/python-http-post-a-large-file-with-streaming
"""
import urllib2
import mmap

# Open the file as a memory mapped string. Looks like a string, but 
# actually accesses the file behind the scenes. 
f = open('somelargefile.zip','rb')
mmapped_file_as_string = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

# Do the request
request = urllib2.Request(url, mmapped_file_as_string)
request.add_header("Content-Type", "application/zip")
response = urllib2.urlopen(request)

#close everything
mmapped_file_as_string.close()
f.close()
"""

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

    def request(self, uri, method, headers=None, payload=None):
        # NOTE: payload can be a file or a string

        if headers is None:
            headers = {}
        # should return a tuple of an HttpResponse object and the content
        try:
            if method == "GET":
                req = urllib2.Request(uri, None, headers)
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            elif method == "POST":
                req = urllib2.Request(uri, payload, headers)
                response = self.opener.open(req)
                return UrlLib2Response(response), response.read()
            elif method == "PUT":
                req = urllib2.Request(uri, payload, headers)
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

