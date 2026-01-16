# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

import typing as tp

import coloredlogs
import verboselogs

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

verboselogs.install()
logger = verboselogs.VerboseLogger("module_logger")
coloredlogs.install(level="CRITICAL", logger=logger)

# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------


class ClassStatistics(type):
    """For a quick tour:

    # >>> Usage: AnyClass.instance_counter
    Returns the amount of created instances

        - Class name -> args[0]
        - Class parents -> args[1]
        - Class __dict__ -> kwargs:

            - "__module__" : "__main__"
            - "__qualname__" : ClassName
            - attr_names : values
            - mth_names : method_objects

    Use __new__ for child class attributes.\n
    Use __init__ for child instance attributes\n
    Use __call__ for child class call alterations.\n
    \n
    Happy now?
    """

    global_instance_counter = 0

    def __new__(cls, *args, **kwargs):
        logger.verbose(f"metaclass: {cls.__name__} running __new__")

        cls.instance_counter = 0  # Initiates the class ticker

        return super().__new__(cls, *args, **kwargs)  # Construct class by type

    def __call__(cls, *args, **kwargs):  # Each class call counts up.
        logger.verbose(f"metaclass: {cls.__name__} running __call__")

        cls.instance_counter += 1  # Each time an individual class is called

        return super().__call__(*args, **kwargs)


class EntrySettings(ClassStatistics):
    def __new__(cls, *args, **kwargs):
        cls.entry_key_type = str
        cls.entry_value_default = object

        return super().__new__(cls, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        print(args)
        print(kwargs)
        print(self.__dict__)
        return super().__call__(*args, **kwargs)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args,
                                                                     **kwargs)
        return cls._instances[cls]

# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
