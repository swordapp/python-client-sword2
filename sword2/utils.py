#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods used within the module
"""

from sword2_logging import logging
utils_l = logging.getLogger(__name__)

from time import time
from datetime import datetime

from base64 import b64encode

try:
    from hashlib import md5
except ImportError:
    import md5

import mimetypes

NS = {}
NS['dcterms'] = "{http://purl.org/dc/terms/}%s"
NS['sword'] ="{http://purl.org/net/sword/terms/}%s"
NS['atom'] = "{http://www.w3.org/2005/Atom}%s"
NS['app'] = "{http://www.w3.org/2007/app}%s"
NS['rdf'] = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}%s"
NS['ore'] = "{http://www.openarchives.org/ore/terms/}%s"

def get_text(parent, tag, plural = False):
    """Takes an `etree.Element` and a tag name to search for and retrieves the text attribute from any
    of the parent element's direct children.
    
    Returns a simple `str` if only a single element is found, or a list if multiple elements with the
    same tag. Ignores element attributes, returning only the text."""
    text = None
    for item in parent.findall(tag):
        t = item.text
        if not text:
            if plural:
                text = [t]
            else:
                text = t
        elif isinstance(text, list):
            text.append(t)
        else:
            text = [text, t]
    return text

def get_md5(data):
    """Takes either a `str` or a file-like object and passes back a tuple containing (md5sum, filesize)
    
    The file is streamed as 1Mb chunks so should work for large files. File-like object must support `seek()`
    """
    if hasattr(data, "read") and hasattr(data, 'seek'):
        m = md5()
        chunk = data.read(1024*1024)   # 1Mb
        f_size = 0
        while(chunk):
            f_size += len(chunk)
            m.update(chunk)
            chunk = data.read(1024*1024)
        data.seek(0)
        return m.hexdigest(), f_size
    else:       # normal str
        m = md5()
        f_size = len(data)
        m.update(data)
        return m.hexdigest(), f_size
        

class Timer(object):
    """Simple timer, providing a 'stopwatch' mechanism.
    
    Usage example:
        
    >>> from sword2.utils import Timer
    >>> from time import sleep
    >>> t = Timer()
    >>> t.get_timestamp()
    datetime.datetime(2011, 6, 7, 7, 40, 53, 87248)
    >>> t.get_loggable_timestamp()
    '2011-06-07T07:40:53.087516'

    >>> # Start a few timers
    ... t.start("kaylee", "river", "inara")
    >>> sleep(3)   # wait a little while
    >>> t.time_since_start("kaylee")
    (0, 3.0048139095306396)

    # tuple -> (index of the logged .duration, time since the .start method was called)
    # eg 't.duration['kaylee'][0]' would equal 3.00481.... 

    >>> sleep(2)
    >>> t.time_since_start("kaylee", "inara")
    [(1, 5.00858998298645), (0, 5.00858998298645)]
    >>> sleep(5)
    >>> t.time_since_start("kaylee", "river")
    [(2, 10.015379905700684), (0, 10.015379905700684)]
    >>> sleep(4)
    >>> t.time_since_start("kaylee", "inara", "river")
    [(3, 14.021538972854614), (1, 14.021538972854614), (1, 14.021538972854614)]
    
    # The order of the response is the same as the order of the names in the method call.
    
    >>> # report back
    ... t.duration['kaylee']
    [3.0048139095306396, 5.00858998298645, 10.015379905700684, 14.021538972854614]
    >>> t.duration['inara']
    [5.00858998298645, 14.021538972854614]
    >>> t.duration['river']
    [10.015379905700684, 14.021538972854614]
    >>> 
    """
    def __init__(self):
        self.reset_all()
        
    def reset_all(self):
        self.counts = {}    
        self.duration = {}
        self.stop = {}

    def reset(self, name):
        if name in self.counts:
            self.counts[name] = 0
    
    def read_raw(self, name):
        return self.counts.get(name, None)
    
    def read(self, name):
        if name in self.counts:
            return datetime.fromtimestamp(self.counts[name])
        else:
            return None

    def start(self, *args):
        st_time = time()
        for arg in args:
            self.counts[arg] = st_time

    def stop(self, *args):
        st_time = time()
        for arg in args:
            self.stop[arg] = st_time
    
    def get_timestamp(self):
        # Convenience function
        return datetime.now()
    
    def get_loggable_timestamp(self):
        """Human-readable by intent"""
        return datetime.now().isoformat()
        
    def time_since_start(self, *args):
        r = []
        st_time = time()
        for name in args:
            if name in self.counts:
                duration = st_time - self.counts[name]
                if not self.duration.has_key(name):
                    self.duration[name] = []
                self.duration[name].append(duration)
                r.append((len(self.duration[name]) - 1, duration))
            else:
                r.append((0, 0))
        if len(r) == 1:
            return r.pop()
        else:
            return r
            

def get_content_type(filename):
    # Does a simple .ext -> mimetype mapping.
    # Generally better to specify the mimetype upfront.
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def create_multipart_related(payloads):
    """ Expected: list of dicts with keys 'key', 'type'='content type','filename'=optional,'data'=payload, 'headers'={} 
    
    TODO: More mem-efficient to spool this to disc rather than hold in RAM, but until Httplib2 bug gets fixed (issue 151)
    this might be in vain.
    
    Can handle more than just two files. 
    
    SWORD2 multipart POST/PUT expects two attachments - key = 'atom' w/ Atom Entry (metadata)
                                                        key = 'payload' (file)
    """
    # Generate random boundary code
    # TODO check that it does not occur in the payload data
    bhash = md5(datetime.now().isoformat()).hexdigest()    # eg 'd8bb3ea6f4e0a4b4682be0cfb4e0a24e'
    BOUNDARY = '===========%s_$' % bhash
    CRLF = '\r\n'   # As some servers might barf without this.
    body = []
    for payload in payloads:   # predicatable ordering...
        body.append('--' + BOUNDARY)
        if payload.get('type', None):
            body.append('Content-Type: %(type)s' % payload)
        else:
            body.append('Content-Type: %s' % get_content_type(payload.get("filename")))
            
        if payload.get('filename', None):
            body.append('Content-Disposition: attachment; name="%(key)s"; filename="%(filename)s"' % (payload))
        else:
            body.append('Content-Disposition: attachment; name="%(key)s"' % (payload))
        
        if payload.has_key("headers"):
            for f,v in payload['headers'].iteritems():
                body.append("%s: %s" % (f, v))     # TODO force ASCII?
        
        body.append('MIME-Version: 1.0')
        if payload['key'] == 'payload':
            body.append('Content-Transfer-Encoding: base64')
            body.append('')
            if hasattr(payload['data'], 'read'):
                body.append(b64encode(payload['data'].read()))
            else:
                body.append(b64encode(payload['data']))
        else:
            body.append('')
            if hasattr(payload['data'], 'read'):
                body.append(b64encode(payload['data'].read()))
            else:
                body.append(b64encode(payload['data']))
    body.append('--' + BOUNDARY + '--')
    body.append('')
    body_bytes = CRLF.join(body)
    content_type = 'multipart/related; boundary="%s"' % BOUNDARY
    return content_type, body_bytes
