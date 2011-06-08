#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
`sword2` logging
"""

import logging
import logging.config
from os import path as os_path

SWORD2_LOGGING_CONFIG = "./sword2_logging.conf"  # default

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

if not os_path.isfile(SWORD2_LOGGING_CONFIG):
    create_logging_config(SWORD2_LOGGING_CONFIG)

logging.config.fileConfig(SWORD2_LOGGING_CONFIG)

