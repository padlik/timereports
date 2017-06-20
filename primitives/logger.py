#!/usr/bin/env python
# Logging configuration
# Should be pretty simple

import logging
import logging.handlers
import sys

LOG_MODULE = 'tsreports'


def set_logging(config):
    logger = logging.getLogger(LOG_MODULE)
    if config.get('debug'):
        handler = logging.StreamHandler(sys.stdout)
        logger.setLevel(logging.DEBUG)
    else:
        # handler = logging.handlers.SysLogHandler('/dev/log')
        handler = logging.StreamHandler(sys.stdout)
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(name)s: %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


Logger = logging.getLogger(LOG_MODULE)
