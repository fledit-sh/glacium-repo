# !/usr/bin/env python
"""Title.

Description
"""
# -----------------------------------------------------------------------------
# IMPORTS
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from itertools import count, product

from copy import deepcopy
from abc import ABC, abstractmethod
import random
import yaml
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
logger = verboselogs.VerboseLogger("[main]")
coloredlogs.install(level="spam", logger=logger)
# -----------------------------------------------------------------------------
# CLASSES
# -----------------------------------------------------------------------------
class Interface:
    @abstractmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def create_variant(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def create_template(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def register_node(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def register_data(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def list_tree(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def copy_tree(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def search_by_attr(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def search_by_value(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def node_by_attr(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def node_by_value(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def name(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def serial(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def inspect(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def generate_dict(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        raise NotImplementedError

    @abstractmethod
    def __next__(self):
        raise NotImplementedError

    @abstractmethod
    def __len__(self):
        raise NotImplementedError

    @abstractmethod
    def __repr__(self):
        raise NotImplementedError

    @abstractmethod
    def __str__(self):
        raise NotImplementedError
# -----------------------------------------------------------------------------
# FUNCTIONS
# -----------------------------------------------------------------------------
def main():
    # Read computer
    pass


if __name__ == "__main__":
    logger.critical("#"*15+"-MAIN_START-"+"#"*29)
    main()
    logger.critical("#"*15+"-MAIN_STOP-"+"#"*30)
