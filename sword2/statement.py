from datetime import datetime
from utils import NS, get_text
from atom_objects import Category
from deposit_receipt import Deposit_Receipt
from sword2_logging import logging
from compatible_libs import etree

s_l = logging.getLogger(__name__)

class Sword_Statement(object):
    def __init__(self, xml_document=None):
        self.xml_document = xml_document
        self.dom = None
        self.parsed = False
        self.valid = False
        self.original_deposits = []
        self.states = []
        self.resources = []
        
        self._parse_xml_document()
        self._validate()
        
    def _parse_xml_document(self):
        if self.xml_document is not None:
            try:
                s_l.info("Attempting to parse the Statement XML document")
                self.dom = etree.fromstring(self.xml_document)
                self.parsed = True
            except Exception, e:
                s_l.error("Failed to parse document - %s" % e)
                s_l.error("XML document begins:\n %s" % self.xml_document[:300])
    
    def _validate(self): pass

class Statement_Resource(object):
    def __init__(self, uri=None, is_original_deposit=False, deposited_on=None, 
                    deposited_by=None, deposited_on_behalf_of=None):
        self.uri = uri
        self.is_original_deposit = is_original_deposit
        self.deposited_on = deposited_on
        self.deposited_by = deposited_by
        self.deposited_on_behalf_of = deposited_on_behalf_of
        
class Atom_Statement_Entry(Deposit_Receipt, Statement_Resource):
    def __init__(self, dom):
        Deposit_Receipt.__init__(self, dom=dom)
        Statement_Resource.__init__(self)
        
        self.is_original_deposit = self._is_original_deposit()
        self._parse_depositors()
        
        # to provide a stable interface, use the content iri as the uri
        self.uri = self.cont_iri
    
    def _is_original_deposit(self):
        # is this an original deposit?
        is_original_deposit = False
        for cat in self.dom.findall(NS['atom'] % 'category'):
            if cat.get("term") == "http://purl.org/net/sword/terms/originalDeposit":
                is_original_deposit = True
                break
        return is_original_deposit
    
    def _parse_depositors(self):
        do = self.dom.find(NS['sword'] % "depositedOn")
        if do is not None and do.text is not None and do.text.strip() != "":
            try:
                self.deposited_on = datetime.strptime(do.text.strip(), "%Y-%m-%dT%H:%M:%SZ") # e.g. 2011-03-02T20:50:06Z
            except Exception, e:
                s_l.error("Failed to parse date - %s" % e)
                s_l.error("Supplied date as string was: %s" % do.text.strip())

        db = self.dom.find(NS['sword'] % "depositedBy")
        if db is not None and db.text is not None and db.text.strip() != "":
            self.deposited_by = db.text.strip()
        
        dobo = self.dom.find(NS['sword'] % "depositedOnBehalfOf")
        if dobo is not None and dobo.text is not None and db.text.strip() != "":
            self.deposited_on_behalf_of = dobo.text.strip()
    
    def validate(self):
        # don't validate statement entries
        return True

class Atom_Sword_Statement(Sword_Statement):
    def __init__(self, xml_document=None):
        Sword_Statement.__init__(self, xml_document)
        if self.valid:
            self._enumerate_feed()
        else:
            s_l.warn("Statement did not parse as valid, so the content will" +
                        " not be examined further; see the 'dom' attribute for the xml")
        
        """
        FIXME: this implementation assumes that the atom document is a single
        page, but Ben's original implementation at least started to make some
        overtures towards dealing with that.  This is the left behind code ...
        
        self.first = None
        self.next = None
        self.previous = None
        self.last = None
        self.categories = []
        self.entries = []
        try:
            coll_l.info("Attempting to parse the Feed XML document")
            self.feed = etree.fromstring(xml_document)
            self.parsed = True
        except Exception, e:
            coll_l.error("Failed to parse document - %s" % e)
            coll_l.error("XML document begins:\n %s" % xml_document[:300])
        self.enumerate_feed()
        """
    
    def _enumerate_feed(self):
        if self.dom is None:
            return
        
        # Handle Categories
        for cat in self.dom.findall(NS['atom'] % 'category'):
            if cat.get("scheme") == "http://purl.org/net/sword/terms/state":
                self.states.append((cat.get("term"), cat.text.strip()))
        
        # Handle Entries
        for entry in self.dom.findall(NS['atom'] % 'entry'):
            ase = Atom_Statement_Entry(entry)
            if ase.is_original_deposit:
                self.original_deposits.append(ase)
            self.resources.append(ase)
    
    def _validate(self):
        valid = True
        
        if self.dom is None:
            return
        
        # MUST be an ATOM Feed document
        if self.dom.tag != NS['atom'] % "feed" and self.dom.tag != "feed":
            valid = False
        
        self.valid = valid
        
        # The Feed MUST represent files contained in the item as an atom:entry element (this does not 
        # mandate that all files in the item are listed, though)

        # Each atom:entry which is an original deposit file MUST have an atom:category element with 
        # the term sword:originalDeposit (this does not mandate that all original deposits are listed as entries)

        # NOTE: neither of these requirements can easily be used to validate, since
        # a statement may have zero entries, and an entry may or may not contain
        # a category for an original deposit.  So, we'll just settle for verifying
        # that this is a feed, and be done with it.




class Ore_Statement_Resource(Statement_Resource):
    def __init__(self, uri, is_original_deposit=False, packaging_uris=[], 
                    deposited_on=None, deposited_by=None, deposited_on_behalf_of=None):
        Statement_Resource.__init__(self, uri, is_original_deposit, deposited_on, 
                                    deposited_by, deposited_on_behalf_of)
        self.uri = uri
        self.packaging = packaging_uris
        
    def __str__(self):
        # FIXME: unfinished ...
        return "URI: %s ; is_original_deposit: %s ; packaging_uris: %s ; deposited_on: %s"

class Ore_Sword_Statement(Sword_Statement):
    def __init__(self, xml_document=None):
        Sword_Statement.__init__(self, xml_document)
        if self.valid:
            self._enumerate_descriptions()
        else:
            s_l.warn("Statement did not parse as valid, so the content will" +
                        " not be examined further; see the 'dom' attribute for the xml")
    
    def _enumerate_descriptions(self):
        if self.dom is None:
            return
        
        aggregated_resource_uris = []
        original_deposit_uris = []
        state_uris = []
        
        # first pass gets me the uris of all the things I care about
        for desc in self.dom.findall(NS['rdf'] % "Description"):
            # look for the aggregation
            ore_idb = desc.findall(NS['ore'] % "isDescribedBy")
            if ore_idb is None:
                continue
                
            # we are looking at the aggregation Describes itself
            for agg_uri in desc.findall(NS['ore'] % "aggregates"):
                aggregated_resource_uris.append(agg_uri.get(NS['rdf'] % "resource"))
            
            for od_uri in desc.findall(NS['sword'] % "originalDeposit"):
                original_deposit_uris.append(od_uri.get(NS['rdf'] % "resource"))
        
            for state_uri in desc.findall(NS['sword'] % "state"):
                state_uris.append(state_uri.get(NS['rdf'] % "resource"))
        
        s_l.debug("First pass on ORE statement yielded the following Aggregated Resources: " + str(aggregated_resource_uris))
        s_l.debug("First pass on ORE statement yielded the following Original Deposits: " + str(original_deposit_uris))
        s_l.debug("First pass on ORE statement yielded the following States: " + str(state_uris))
        
        # second pass, sort out the different descriptions
        for desc in self.dom.findall(NS['rdf'] % "Description"):
            about = desc.get(NS['rdf'] % "about")
            s_l.debug("Examining Described Resource: " + str(about))
            if about in state_uris:
                s_l.debug(str(about) + " is a State URI")
                # read and store the state information
                description_text = None
                sdesc = desc.find(NS['sword'] % "stateDescription")
                if sdesc is not None and sdesc.text is not None and sdesc.text.strip() != "":
                    description_text = sdesc.text.strip()
                self.states.append((about, description_text))
                # remove this uri from the list of state_uris, so that we can
                # deal with any left over later
                state_uris.remove(about)
            elif about in aggregated_resource_uris:
                s_l.debug(str(about) + " is an Aggregated Resource")
                
                is_original_deposit = about in original_deposit_uris
                s_l.debug("Is Aggregated Resource an original deposit? " + str(is_original_deposit))
                
                packaging_uris = []
                for pack in desc.findall(NS['sword'] % "packaging"):
                    pack_uri = pack.get(NS['rdf'] % "resource")
                    packaging_uris.append(pack_uri)
                    s_l.debug("Registering Packaging URI: " + pack_uri)
                
                deposited_on = None
                do = desc.find(NS['sword'] % "depositedOn")
                if do is not None and do.text is not None and do.text.strip() != "":
                    try:
                        deposited_on = datetime.strptime(do.text.strip(), "%Y-%m-%dT%H:%M:%SZ") # e.g. 2011-03-02T20:50:06Z
                        s_l.debug("Registering Deposited On: " + do.text.strip())
                    except Exception, e:
                        s_l.error("Failed to parse date - %s" % e)
                        s_l.error("Supplied date as string was: %s" % do.text.strip())

                deposited_by = None
                db = desc.find(NS['sword'] % "depositedBy")
                if db is not None and db.text is not None and db.text.strip() != "":
                    deposited_by = db.text.strip()
                    s_l.debug("Registering Deposited By: " + deposited_by)
                
                deposited_on_behalf_of = None
                dobo = desc.find(NS['sword'] % "depositedOnBehalfOf")
                if dobo is not None and dobo.text is not None and db.text.strip() != "":
                    deposited_on_behalf_of = dobo.text.strip()
                    s_l.debug("Registering Deposited On Behalf Of: " + deposited_on_behalf_of)
                    
                ose = Ore_Statement_Resource(about, is_original_deposit, packaging_uris, 
                                            deposited_on, deposited_by, deposited_on_behalf_of)
                if is_original_deposit:
                    s_l.debug("Registering Aggregated Resource as an Original Deposit")
                    self.original_deposits.append(ose)
                self.resources.append(ose)
                
                # remove this uri from the list of resource_uris, so that we can
                # deal with any left over later
                aggregated_resource_uris.remove(about)
    
        # finally, we may have aggregated resources and states which did not
        # have rdf:Description elements associated with them.  We do the minimum
        # possible here to accommodate them
        s_l.debug("Undescribed State URIs: " + str(state_uris))
        for state in state_uris:
            self.states.append((state, None))
        
        s_l.debug("Undescribed Aggregated Resource URIs: " + str(aggregated_resource_uris))
        for ar in aggregated_resource_uris:
            ose = Ore_Statement_Resource(ar)
            self.resources.append(ose)
    
    def _validate(self):
        valid = True
        
        if self.dom is None:
            return
        
        # MUST be an RDF/XML resource map
        
        # is this rdf xml:
        if self.dom.tag.lower() != NS['rdf'] % "rdf" and self.dom.tag.lower() != "rdf":
            s_l.info("Validation of Ore Statement failed, as root tag is not RDF: " + self.dom.tag)
            valid = False
        
        # does it meet the basic requirements of being a resource map, which 
        # is to have an ore:describes and and ore:isDescribedBy
        describes_uri = None
        rem_uri = None
        aggregation_uri = None
        is_described_by_uris = []
        for desc in self.dom.findall(NS['rdf'] % "Description"):
            # look for the describes tag
            ore_desc = desc.find(NS['ore'] % "describes")
            if ore_desc is not None:
                describes_uri = ore_desc.get(NS['rdf'] % "resource")
                rem_uri = desc.get(NS['rdf'] % "about")
            # look for the isDescribedBy tag
            ore_idb = desc.findall(NS['ore'] % "isDescribedBy")
            if len(ore_idb) > 0:
                aggregation_uri = desc.get(NS['rdf'] % "about")
                for idb in ore_idb:
                    is_described_by_uris.append(idb.get(NS['rdf'] % "resource"))
        
        # now check that all those uris tie up:
        if describes_uri != aggregation_uri:
            s_l.info("Validation of Ore Statement failed; ore:describes URI does not match Aggregation URI: " +
                        describes_uri + " != " + aggregation_uri)
            valid = False
        if rem_uri not in is_described_by_uris:
            s_l.info("Validation of Ore Statement failed; Resource Map URI does not match one of ore:isDescribedBy URIs: " + 
                        rem_uri + " not in " + str(is_described_by_uris))
            valid = False
        
        s_l.info("Statement validation; was it a success? " + str(valid))
        self.valid = valid




































