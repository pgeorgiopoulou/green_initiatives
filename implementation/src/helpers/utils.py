#!/usr/bin/env python3
# pylint: disable=fixme
"""Useful shared functionalities."""
import logging


class CustomFormatter(logging.Formatter):
    """@class subclasses `logging.Formatter` allowing the return of colorised output"""

    _grey = "\x1b[38;20m"
    _yellow = "\x1b[33;20m"
    _red = "\x1b[31;20m"
    _green = "\x1b[32;20m"
    _bold_red = "\x1b[31;1m"
    _reset = "\x1b[0m"
    _format = f"%(asctime)-15s - %(levelname)s - [%(filename)-.20s | %(funcName)s | L%(lineno)d]{_reset} - %(message)s"
    FORMATS = {
        logging.DEBUG: f"{_green}{_format}",
        logging.INFO: f"{_grey}{_format}",
        logging.WARNING: f"{_yellow}{_format}",
        logging.ERROR: f"{_red}{_format}",
        logging.CRITICAL: f"{_bold_red}{_format}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class CustomLogger(logging.Logger):
    """@class subclasses `logging.Logger` to allow the `error` method to also return the formatted string"""

    def __init__(self, name):
        """@brief Initialiser for the parent"""
        self.name = name
        super().__init__(name)

    def error(self, msg, *args, **kwargs):
        """@brief Overloaded error, that also returns the formatted string"""
        self._log(logging.ERROR, msg, args, kwargs)
        return str(msg) % args


logging.setLoggerClass(CustomLogger)


def get_logger() -> logging.Logger:
    """@brief returl a logging.Logger object to use
    @return logger  the Logger object
    """
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("greenInitiatives")

    # Remove the default handler if auto-added
    logger.root.handlers = []

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(CustomFormatter())
        logger.addHandler(handler)
    return logger
