from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from . import workday


@dataclass(frozen=True)
class IngestResult:
    provider: str
    canonical_key: str


class IngestionDispatchError(ValueError):
    """Raised when no ingestion module supports a URL."""


_INGESTERS: list[tuple[str, Callable[[str], bool], Callable[[str], str]]] = [
    (
        "workday",
        workday.can_handle,
        lambda url: workday.canonicalize_url(url).canonical_key,
    ),
]


def canonicalize_job_url(url: str) -> IngestResult:
    for provider, predicate, canonicalizer in _INGESTERS:
        if predicate(url):
            return IngestResult(provider=provider, canonical_key=canonicalizer(url))

    raise IngestionDispatchError(
        "No ingester registered for URL host. Supported providers: workday (*.myworkdayjobs.com)."
    )
