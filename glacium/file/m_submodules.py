# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

from itertools import count
from abc import abstractmethod
import coloredlogs
import verboselogs
from interface import Interface
# -----------------------------------------------------------------------------
# COPYRIGHT
# -----------------------------------------------------------------------------

__author__ = "Noel Ernsting Luz"
__copyright__ = "Copyright (C) 2022 Noel Ernsting Luz"
__license__ = "Public Domain"
__version__ = "1.0"

# -----------------------------------------------------------------------------
# GLOBALS
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# LOGGER
# -----------------------------------------------------------------------------
DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'},
                        'hostname': {'color': 'magenta'},
                        'levelname': {'bold': True,
                                      'color': 'black',
                                      'inverse': True},
                        'name': {'color': 'blue',
                                 'bold': True},
                        'programname': {'color': 'cyan'},
                        'username': {'color': 'yellow'}}
DEFAULT_LEVEL_STYLES = {'critical': {'bold': True,
                                     'color': 'red',
                                     'inverse': True},
                        'debug': {'color': 'green'},
                        'error': {'color': 'red'},
                        'info': {'color': 'black'},
                        'notice': {'color': 'magenta'},
                        'spam': {'color': 'green',
                                 'faint': True},
                        'success': {'bold': True,
                                    'color': 'green'},
                        'verbose': {'color': 'blue'},
                        'warning': {'color': 'yellow'}}
DEFAULT_LOG_FORMAT = '%(asctime)s ' \
                     '%(name)-10s ' \
                     '%(levelname)-8s ' \
                     ' %(message)s'


def setup_coloredlogs():
    coloredlogs.DEFAULT_FIELD_STYLES = DEFAULT_FIELD_STYLES
    coloredlogs.DEFAULT_LEVEL_STYLES = DEFAULT_LEVEL_STYLES
    coloredlogs.DEFAULT_LOG_FORMAT = DEFAULT_LOG_FORMAT

setup_coloredlogs()
verboselogs.install()
logger = verboselogs.VerboseLogger("[main]")
coloredlogs.install(level="spam", logger=logger)


# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


class MetaGetter(type):
    """
    Metaclass enabling context-sensitive class usage.

    Allows syntax like `Logger[MyContext]` to inject a class-level context
    into another class dynamically at definition time.
    """
    def __getitem__(cls, context):
        cls._context = context
        return cls


class SubModule(metaclass=MetaGetter):
    """
    Abstract base class for all submodules.

    Provides unified access to shared context set via `MetaGetter`.
    """
    @abstractmethod
    def __init__(self):
        pass

    @property
    def context(self):
        return self._context


class Identify(SubModule, metaclass=MetaGetter):
    """
    Designed to be used in another classes __init__ method. Sample Usage:

    Creates a simple DogTag tuple. If no nickname (nn) provided, it falls back
    to the default "nn_unnamed"
    """

    # Counter should be class specific.
    # Each instance gets to trigger the counter
    iter_count = count(0)

    def __init__(self, name=None):
        # Executing iter trigger (yield mechanism)
        self.serial = next(self.iter_count)

        # Nickname evaluation
        if not name:
            name = "unnamed_node"
        self.name = name

        # DogTag Assembly
        self.dogtag = (self.serial, self.name)

    def rename(self, name):
        self.name = name
        self.dogtag = (self.serial, self.name)

    def __repr__(self):
        return f"[DogTag: {self.dogtag}]".ljust(25)[:25]


class Logger(SubModule, metaclass=MetaGetter):

    def __init__(self):
        context_name = type(self.context).__name__.lower()
        logger_name = f"[{context_name[:8]}]"
        style = DEFAULT_FIELD_STYLES.update({'name':
                                                 {'color': 'blue',
                                                  'bold': True,
                                                  'inverse': True}
                                             })
        context_logger = verboselogs.VerboseLogger(logger_name)
        coloredlogs.install(level="spam",
                            logger=context_logger,
                            field_styles=style)
        self.context_logger = context_logger
        # self.context_logger.debug("SubModule Logger attached to context")

    @classmethod
    def __getitem__(cls, item):
        cls.nn = item
        return cls

    def set_level(self, level):
        self.context_logger.setLevel(level)

    def spam(self, msg):
        self.context_logger.spam(msg)

    def debug(self, msg):
        self.context_logger.debug(msg)

    def verbose(self, msg):
        self.context_logger.verbose(msg)

    def info(self, msg):
        self.context_logger.info(msg)

    def notice(self, msg):
        self.context_logger.notice(msg)

    def warning(self, msg):
        self.context_logger.warning(msg)

    def success(self, msg):
        self.context_logger.success(msg)

    def error(self, msg):
        self.context_logger.error(msg)

    def critical(self, msg):
        self.context_logger.critical(msg)




# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def colortest():
    logger.critical("#" * 15 + "-COLORTEST-" + "#" * 30)
    logger.spam("Demo just a demo message")
    logger.debug("Demo just a demo message")
    logger.verbose("Demo just a demo message")
    logger.info("Demo just a demo message")
    logger.notice("Demo just a demo message")
    logger.warning("Demo just a demo message")
    logger.success("Demo just a demo message")
    logger.error("Demo just a demo message")
    logger.critical("Demo just a demo message")
    logger.critical("#" * 15 + "-COLORTEST-" + "#" * 30)


def main():
    pass


if __name__ == "__main__":
    colortest()
    main()
