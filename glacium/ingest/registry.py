from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable

from . import workday

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestResult:
    provider: str
    canonical_key: str
    normalized_id: str
    fields: dict[str, str | None] | None = None


class IngestionDispatchError(ValueError):
    """Raised when no ingestion module supports a URL."""

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


_INGESTERS: list[
    tuple[
        str,
        Callable[[str], bool],
        Callable[[str], workday.WorkdayCanonicalURL],
        Callable[[str], dict[str, str | None]],
    ]
] = [
    (
        "workday",
        workday.can_handle,
        workday.canonicalize_url,
        workday.extract_fields,
    ),
]


def canonicalize_job_url(url: str) -> IngestResult:
    for provider, predicate, canonicalizer, _parser in _INGESTERS:
        if predicate(url):
            canonical = canonicalizer(url)
            return IngestResult(
                provider=provider,
                canonical_key=canonical.canonical_key,
                normalized_id=canonical.job_id,
            )

    raise IngestionDispatchError(
        "No ingester registered for URL host. Supported providers: workday (*.myworkdayjobs.com).",
        reason="unsupported_domain",
    )


def ingest_job_url(
    url: str,
    *,
    fetcher: Callable[[str], str],
) -> IngestResult:
    logger.info("ingest.url_accepted", extra={"url": url})

    selected_adapter: tuple[
        str,
        Callable[[str], bool],
        Callable[[str], workday.WorkdayCanonicalURL],
        Callable[[str], dict[str, str | None]],
    ] | None = None
    for provider, predicate, canonicalizer, parser in _INGESTERS:
        if predicate(url):
            selected_adapter = (provider, predicate, canonicalizer, parser)
            break

    if selected_adapter is None:
        logger.warning("ingest.adapter_not_found", extra={"url": url})
        raise IngestionDispatchError(
            "No ingester registered for URL host. Supported providers: workday (*.myworkdayjobs.com).",
            reason="unsupported_domain",
        )

    provider, _predicate, canonicalizer, parser = selected_adapter
    logger.info("ingest.adapter_selected", extra={"provider": provider})

    try:
        canonical = canonicalizer(url)
    except workday.WorkdayURLValidationError as exc:
        logger.warning(
            "ingest.invalid_url",
            extra={"provider": provider, "error": str(exc)},
        )
        raise IngestionDispatchError(str(exc), reason="invalid_workday_url") from exc

    logger.info(
        "ingest.normalized_id",
        extra={"provider": provider, "normalized_id": canonical.job_id},
    )

    logger.info("ingest.fetch_attempted", extra={"provider": provider})
    payload = fetcher(url)

    fields = parser(payload)
    if not fields.get("title"):
        logger.warning("ingest.parse_failed", extra={"provider": provider})
        raise IngestionDispatchError(
            "Parser did not extract required fields from payload.",
            reason="parse_error",
        )

    logger.info("ingest.parse_succeeded", extra={"provider": provider})
    return IngestResult(
        provider=provider,
        canonical_key=canonical.canonical_key,
        normalized_id=canonical.job_id,
        fields=fields,
    )
