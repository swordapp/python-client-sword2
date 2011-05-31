#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sword2_logging import logging 

cl_l = logging.getLogger(__name__)

try:
    from lxml import etree
except ImportError:
    try:
        # Python >= 2.5
        from xml.etree import ElementTree as etree
    except ImportError:
        try:
            from elementtree import ElementTree as etree
        except ImportError:
            try:
                import cElementTree as etree
            except ImportError:
                cl_l.error("Couldn't find a suitable ElementTree library to use in this environment.")
                etree = None

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        cl_l.error("Couldn't find a suitable simplejson-like library to use to serialise JSON")
        json = None
