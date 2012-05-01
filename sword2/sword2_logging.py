#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
`sword2` logging
"""

import imp
import os
import logging
import logging.config

_, sword2_path, _ = imp.find_module('sword2')
SWORD2_LOGGING_CONFIG = os.path.join(sword2_path, 'data', 'sword2_logging.conf')  # default

BASIC_CONFIG = """[loggers]
keys=root

[handlers]
keys=consoleHandler

[formatters]
keys=basicFormatting

[logger_root]
level=INFO
handlers=consoleHandler

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=basicFormatting
args=(sys.stdout,)

[formatter_basicFormatting]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
"""

def create_logging_config(pathtologgingconf):
    fn = open(pathtologgingconf, "w")
    fn.write(BASIC_CONFIG)
    fn.close()

if not os.path.isfile(SWORD2_LOGGING_CONFIG):
    create_logging_config(SWORD2_LOGGING_CONFIG)

logging.config.fileConfig(SWORD2_LOGGING_CONFIG)

