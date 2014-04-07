#!/usr/bin/env python
#Logging configuration
#Should be pretty simple

import logging.handlers
import logging
import sys

LOG_MODULE = 'tsreports'


def set_logging(config):
    logger = logging.getLogger(LOG_MODULE)
    if config['debug']:
        handler = logging.StreamHandler(sys.stdout)
        logger.setLevel(logging.DEBUG)
    else:
        handler = logging.handlers.SysLogHandler('/dev/log')
        logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(name)s: %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

Logger = logging.getLogger(LOG_MODULE)


