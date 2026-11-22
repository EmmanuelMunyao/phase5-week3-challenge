import logging

from settings import LOG_LEVEL


LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
    )


def get_logger(name):
    return logging.getLogger(name)