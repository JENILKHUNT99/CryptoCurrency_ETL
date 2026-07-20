import logging
import os


def configure_logging():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


configure_logging()


def get_logger(name):
    return logging.getLogger(name)
