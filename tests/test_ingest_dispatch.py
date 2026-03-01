import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from glacium.ingest.registry import IngestionDispatchError, ingest_job_url


AIRBUS_WORKDAY_URL = (
    "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
    "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
    "?locationCountry=2fcb99c455831013ea52fb338f2932d8"
)


def test_ingest_routes_workday_domain_and_normalizes_id(caplog):
    payload = """
    <html>
      <head>
        <script type=\"application/ld+json\">
        {"title": "Flight Physics Engineer", "identifier": {"value": "JR10284481"}}
        </script>
      </head>
    </html>
    """

    with caplog.at_level(logging.INFO):
        result = ingest_job_url(AIRBUS_WORKDAY_URL, fetcher=lambda _url: payload)

    assert result.provider == "workday"
    assert result.normalized_id == "JR10284481"
    assert result.canonical_key == "workday:airbus.wd3.myworkdayjobs.com/Airbus/JR10284481"

    messages = [record.msg for record in caplog.records]
    assert "ingest.url_accepted" in messages
    assert "ingest.adapter_selected" in messages
    assert "ingest.fetch_attempted" in messages
    assert "ingest.parse_succeeded" in messages
    assert "ingest.normalized_id" in messages


def test_ingest_unsupported_domain_returns_machine_readable_reason():
    with pytest.raises(IngestionDispatchError) as exc:
        ingest_job_url("https://example.com/jobs/123", fetcher=lambda _url: "")

    assert exc.value.reason == "unsupported_domain"


def test_ingest_invalid_workday_url_returns_machine_readable_reason():
    invalid_workday_url = "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/jobs/Toulouse-Area"

    with pytest.raises(IngestionDispatchError) as exc:
        ingest_job_url(invalid_workday_url, fetcher=lambda _url: "")

    assert exc.value.reason == "invalid_workday_url"


def test_ingest_parse_failure_returns_machine_readable_reason(caplog):
    payload_without_title = "<html><head></head><body>No structured content</body></html>"

    with caplog.at_level(logging.WARNING):
        with pytest.raises(IngestionDispatchError) as exc:
            ingest_job_url(AIRBUS_WORKDAY_URL, fetcher=lambda _url: payload_without_title)

    assert exc.value.reason == "parse_error"
    assert any(record.msg == "ingest.parse_failed" for record in caplog.records)


def test_airbus_workday_regression_url_is_still_ingested():
    payload = """
    <html>
      <head>
        <script type=\"application/ld+json\">
        {"title": "Flight Physics Engineer", "identifier": {"value": "JR10284481"}}
        </script>
      </head>
    </html>
    """

    result = ingest_job_url(AIRBUS_WORKDAY_URL, fetcher=lambda _url: payload)

    assert result.normalized_id == "JR10284481"
    assert result.canonical_key == "workday:airbus.wd3.myworkdayjobs.com/Airbus/JR10284481"
