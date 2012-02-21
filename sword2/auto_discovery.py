from sword2_logging import logging
ad_l = logging.getLogger(__name__)

# FIXME: sgmllib is deprecated, and removed from Python 3.  If moving to
# Python 3 will need to look at http.parser instead or etree.HTMLParser
import sgmllib, http_layer

class AutoDiscovery(sgmllib.SGMLParser):

    def __init__(self, url=None, http_impl=None):
        sgmllib.SGMLParser.__init__(self)
        
        self.url = url
        self.service_document = None
        self.collection = None
        self.entry = None
        self.statement = []
        self.data = None
        self.response = None
        
        if http_impl is None:
            ad_l.info("Loading default HTTP layer")
            self.http = http_layer.HttpLib2Layer(".cache", timeout=30.0)
        else:
            ad_l.info("Using provided HTTP layer")
            self.http = http_impl
        
        if url is not None:
            self.discover(url)

    def discover(self, url):
        resp, content = self.http.request(url, "GET")
        self.response = resp
        self.data = content
        if content is not None:
            self.feed(content)

    def _extract_attribute(self, attr, attributes):
        for name, value in attributes:
            if name == attr:
                return value
        return None

    def _expand_href(self, href):
        if href.startswith("http://"):
            return href
        base_url = self.url
        if not base_url.endswith("/"):
            base_url += "/"
        if href.startswith("/"):
            href = href[1:]
        return base_url + href

    def start_link(self, attributes):
        for name, value in attributes:
            # we're looking up the rel value first
            if name != "rel":
                continue
                
            if (value == "http://purl.org/net/sword/discovery/service-document" or
                value == "sword"):
                # we have found the service document link
                self.service_document = self._expand_href(self._extract_attribute("href", attributes))
            elif value == "http://purl.org/net/sword/terms/deposit":
                # we have found the collection link
                self.collection = self._expand_href(self._extract_attribute("href", attributes))
            elif value == "http://purl.org/net/sword/terms/edit":
                # we have found the entry link
                self.entry = self._expand_href(self._extract_attribute("href", attributes))
            elif value == "http://purl.org/net/sword/terms/statement":
                # we have found the statement link
                state_url = self._expand_href(self._extract_attribute("href", attributes))
                state_type = self._extract_attribute("type", attributes)
                self.statement.append((state_url, state_type))

