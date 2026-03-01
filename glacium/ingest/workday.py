from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import urlparse

_WORKDAY_DOMAIN_SUFFIX = ".myworkdayjobs.com"
_LOCALE_PATTERN = re.compile(r"^[a-z]{2}-[A-Z]{2}$")
_JOB_ID_PATTERN = re.compile(r"([A-Z]{2}\d{5,})")
_SCRIPT_PATTERN = re.compile(
    r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
_INITIAL_STATE_PATTERN = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
    re.DOTALL,
)


@dataclass(frozen=True)
class WorkdayCanonicalURL:
    """Canonical representation of a Workday job posting URL."""

    source_url: str
    canonical_key: str
    host: str
    site: str
    job_id: str


class WorkdayURLValidationError(ValueError):
    """Raised when a URL cannot be interpreted as a supported Workday job URL."""


def can_handle(url: str) -> bool:
    """Return ``True`` when ``url`` points to a Workday-hosted job site."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    return bool(parsed.netloc) and parsed.netloc.lower().endswith(_WORKDAY_DOMAIN_SUFFIX)


def canonicalize_url(url: str) -> WorkdayCanonicalURL:
    """Canonicalize supported Workday posting URLs to a stable key.

    Canonicalization rules:
    - Hostname is normalized to lowercase.
    - Locale prefixes (``/de-DE/``, ``/en-US/``, ...) are ignored.
    - Non-essential query parameters are ignored.
    - The canonical key is built from host + site segment + job identifier.
    """

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if not host:
        raise WorkdayURLValidationError(
            "Unsupported URL form: missing host in Workday URL."
        )
    if not host.endswith(_WORKDAY_DOMAIN_SUFFIX):
        raise WorkdayURLValidationError(
            "Unsupported URL form: host must end with '.myworkdayjobs.com'."
        )

    raw_segments = [segment for segment in parsed.path.split("/") if segment]
    segments = list(raw_segments)

    if segments and _LOCALE_PATTERN.match(segments[0]):
        segments = segments[1:]

    if len(segments) < 2:
        raise WorkdayURLValidationError(
            "Unsupported URL form: expected '/<site>/.../<job-id>' path segments."
        )

    site = segments[0]
    job_id = _extract_job_id_from_segments(segments)
    if not job_id:
        raise WorkdayURLValidationError(
            "Unsupported URL form: could not locate Workday requisition/job identifier in URL path."
        )

    canonical_key = f"workday:{host}/{site}/{job_id}"

    return WorkdayCanonicalURL(
        source_url=url,
        canonical_key=canonical_key,
        host=host,
        site=site,
        job_id=job_id,
    )


def extract_fields(payload: str | dict[str, Any]) -> dict[str, str | None]:
    """Extract key job fields from Workday HTML or JSON payloads."""

    candidates: list[Any] = []

    if isinstance(payload, dict):
        candidates.append(payload)
    else:
        text = payload
        candidates.extend(_extract_json_blocks_from_html(text))

        title_match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if title_match:
            candidates.append({"title": unescape(title_match.group(1)).strip()})

    result = {
        "title": _pick_first(candidates, ["title", "jobTitle", "postingTitle"]),
        "company": _pick_first(candidates, ["hiringOrganization.name", "company", "employer", "companyName"]),
        "location": _pick_first(candidates, ["jobLocation.address.addressLocality", "location", "locationsText", "primaryLocation"]),
        "description": _pick_first(candidates, ["description", "jobDescription", "externalDescription"]),
        "requisition_id": _pick_first(candidates, ["identifier.value", "requisitionId", "jobReqId", "jobPostingInfo.jobReqId"]),
    }

    if result["description"]:
        result["description"] = re.sub(r"\s+", " ", str(result["description"]).strip())

    return result


def _extract_job_id_from_segments(segments: list[str]) -> str | None:
    for segment in reversed(segments):
        match = _JOB_ID_PATTERN.search(segment)
        if match:
            return match.group(1)
    return None


def _extract_json_blocks_from_html(html: str) -> list[Any]:
    blocks: list[Any] = []

    for raw in _SCRIPT_PATTERN.findall(html):
        raw = raw.strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    initial_state_match = _INITIAL_STATE_PATTERN.search(html)
    if initial_state_match:
        raw_state = initial_state_match.group(1)
        try:
            blocks.append(json.loads(raw_state))
        except json.JSONDecodeError:
            pass

    return blocks


def _pick_first(candidates: list[Any], paths: list[str]) -> str | None:
    for candidate in candidates:
        for path in paths:
            value = _dig(candidate, path)
            if value is not None and str(value).strip():
                return str(value).strip()
    return None


def _dig(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        return _dig_recursive(current, dotted_path.split("."))
    return current


def _dig_recursive(value: Any, parts: list[str]) -> Any:
    if not parts:
        return value

    key = parts[0]
    rest = parts[1:]

    if isinstance(value, dict):
        if key in value:
            return _dig_recursive(value[key], rest)
        for nested in value.values():
            found = _dig_recursive(nested, parts)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _dig_recursive(item, parts)
            if found is not None:
                return found

    return None
