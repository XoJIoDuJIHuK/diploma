import logging
import logging.config
import yaml

import sys
from colorlog import ColoredFormatter


class LevelFilter(logging.Filter):
    def __init__(self, level: int) -> None:
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self.level


def init_logger() -> None:
    logger = logging.getLogger('app')
    info_formatter = ColoredFormatter(
        '%(log_color)s[INFO] %(asctime)s - %(message)s',
        log_colors={'INFO': 'green'},
    )
    debug_formatter = ColoredFormatter(
        '%(log_color)s[DEBUG] %(asctime)s - '
        '%(funcName)s:%(lineno)d: %(message)s',
        log_colors={'DEBUG': 'cyan'},
    )
    error_formatter = ColoredFormatter(
        '%(log_color)s[ERROR] %(asctime)s - '
        '%(funcName)s:%(lineno)d - %(message)s',
        log_colors={'ERROR': 'red'},
    )
    warning_formatter = ColoredFormatter(
        '%(log_color)s[WARNING] %(asctime)s - %(message)s',
        log_colors={'WARNING': 'yellow'},
    )
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(make_handler(logging.INFO, info_formatter))
    logger.addHandler(make_handler(logging.DEBUG, debug_formatter))
    logger.addHandler(make_handler(logging.ERROR, error_formatter))
    logger.addHandler(make_handler(logging.WARNING, warning_formatter))


def make_handler(
    level: int, formatter: ColoredFormatter
) -> logging.StreamHandler:  # type: ignore [type-arg]
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(LevelFilter(level))
    return handler
