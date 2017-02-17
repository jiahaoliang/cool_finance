import datetime
import logging
import traceback
import os
import sys

from cool_finance import constants

# create logger
logger = logging.getLogger(__name__)
if constants.DEBUG_LOG_DIR:
    logger.setLevel(constants.DEBUG_LOG_LEVEL)
else:
    logger.setLevel(constants.LOG_LEVEL)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(constants.LOG_LEVEL)
# create formatter and add it to the handlers
formatter = logging.Formatter(constants.LOG_FORMAT)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)

# create file handler which logs even debug messages
if constants.DEBUG_LOG_DIR:
    filename = "debug-" + \
               datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".log"
    fh = logging.FileHandler(os.path.join(constants.DEBUG_LOG_DIR, filename))
    fh.setLevel(constants.DEBUG_LOG_LEVEL)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def log_uncaught_exceptions(ex_cls, ex, tb):
    logger.error(''.join(traceback.format_tb(tb)))
    logger.error('{0}: {1}'.format(ex_cls, ex))

sys.excepthook = log_uncaught_exceptions

