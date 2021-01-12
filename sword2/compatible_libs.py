#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provides the module with access to certain libraries that have more than one suitable implementation, in a optimally
degredating manner.

Provides - `etree`

`etree` can be from any of the following, if found in the local environment:
    `lxml`
    `xml.etree`
    `elementtree`
    `cElementTree`

If no suitable library is found, then it will pass back `None`
"""

from .sword2_logging import logging 

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
