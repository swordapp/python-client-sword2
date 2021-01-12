#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Provides a class to hold the `sword2.Connection` transaction history and give simple means for export (JSON) and reporting.
"""

import json
from datetime import datetime

from .sword2_logging import logging

th_l = logging.getLogger(__name__)


class Transaction_History(list):
    def log(self, event_type, **kw):
        self.append({'type':event_type,
                     'timestamp':datetime.now().isoformat(),
                     'payload':kw})

    def __str__(self):
        _s = []
        for item in self:
            _s.append("-"*20)
            _s.append("Type: '%s' [%s]\nData:" % (item['type'], item['timestamp']))
            for key, value in item['payload'].items():
                _s.append("%s:   %s" % (key, value))
        
        return "\n".join(_s)

    def to_json(self):
        th_l.debug("Attempting to dump %s history items to JSON" % len(self))
        return json.dumps(self)

    def to_pretty_json(self):
        th_l.debug("Attempting to dump %s history items to indented, readable JSON" % len(self))
        return json.dumps(self, indent=True)

