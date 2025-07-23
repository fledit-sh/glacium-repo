"""String helper functions used across the project."""

from __future__ import annotations

import re

__all__ = ["normalise_key"]

_RE_NON_ALNUM = re.compile(r"[^0-9A-Za-z]+")


def normalise_key(label: str) -> str:
    """Return ``label`` in uppercase with non-alphanumeric characters replaced.

    Any sequence of characters other than letters or digits is replaced by a
    single underscore. Leading and trailing underscores are stripped before the
    result is uppercased.
    """

    key = _RE_NON_ALNUM.sub("_", label.strip())
    return key.strip("_").upper()
