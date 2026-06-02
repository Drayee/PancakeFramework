import os
import logging

def check_dlc(check_method):
    logger = logging.getLogger("check")
    try:
        check_method()
    except ValueError as e:
        logger.error(e)
        raise e
