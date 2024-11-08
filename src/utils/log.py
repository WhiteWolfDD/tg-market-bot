import logging
from rich.console import Console
from rich.logging import RichHandler
from src.utils.singleton import SingletonMeta


class AppLogger(metaclass=SingletonMeta):
    _logger = None

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def get_logger(self):
        return self._logger


class RichConsoleHandler(RichHandler):
    def __init__(self, width=200, style=None, **kwargs):
        super().__init__(
            console=Console(color_system="256", width=width, style=style), **kwargs
        )


def get_logger():
    logger = AppLogger()
    return logger.get_logger()


def setup_logging():
    logger = get_logger()
    # logger.setLevel(logging.DEBUG)

    # Check if handlers are already set to avoid adding duplicates
    if not logger.hasHandlers():
        handler = RichConsoleHandler()
        # handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Set styles for different log levels
    logging.addLevelName(logging.DEBUG, "\033[34m%s\033[0m" % logging.getLevelName(logging.DEBUG))  # Blue
    logging.addLevelName(logging.INFO, "\033[32m%s\033[0m" % logging.getLevelName(logging.INFO))  # Green
    logging.addLevelName(logging.WARNING, "\033[33m%s\033[0m" % logging.getLevelName(logging.WARNING))  # Yellow
    logging.addLevelName(logging.ERROR, "\033[31m%s\033[0m" % logging.getLevelName(logging.ERROR))  # Red
    logging.addLevelName(logging.CRITICAL,
                         "\033[41m%s\033[0m" % logging.getLevelName(logging.CRITICAL))  # Red background

    return logger
