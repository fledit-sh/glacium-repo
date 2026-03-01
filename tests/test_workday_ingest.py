import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from glacium.ingest.registry import IngestionDispatchError, canonicalize_job_url
from glacium.ingest.workday import (
    WorkdayURLValidationError,
    canonicalize_url,
    extract_fields,
)


def test_airbus_sample_url_canonicalization():
    url = (
        "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
        "?locationCountry=2fcb99c455831013ea52fb338f2932d8"
    )

    canonical = canonicalize_url(url)

    assert canonical.job_id == "JR10284481"
    assert canonical.canonical_key == "workday:airbus.wd3.myworkdayjobs.com/Airbus/JR10284481"


def test_locale_variants_map_to_same_canonical_key():
    en_url = (
        "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
    )
    de_url = (
        "https://airbus.wd3.myworkdayjobs.com/de-DE/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
    )

    assert canonicalize_url(en_url).canonical_key == canonicalize_url(de_url).canonical_key


def test_query_parameters_are_ignored_for_canonicalization():
    plain_url = (
        "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
    )
    filtered_url = (
        "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
        "?locationCountry=2fcb99c455831013ea52fb338f2932d8&jobFamilyGroup=3f19119f9a1a"
    )

    assert canonicalize_url(plain_url).canonical_key == canonicalize_url(filtered_url).canonical_key


def test_invalid_workday_url_shapes_raise_clear_error_messages():
    with_error = "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/jobs/Toulouse-Area"
    with_domain_error = "https://jobs.airbus.com/en-US/Airbus/job/Toulouse-Area/JR10284481"

    with pytest.raises(WorkdayURLValidationError, match="could not locate Workday requisition"):
        canonicalize_url(with_error)

    with pytest.raises(WorkdayURLValidationError, match="host must end with"):
        canonicalize_url(with_domain_error)


def test_registry_dispatches_workday_and_rejects_unsupported_hosts():
    workday_url = (
        "https://airbus.wd3.myworkdayjobs.com/en-US/Airbus/job/"
        "Toulouse-Area/Flight-Physics-Engineer_JR10284481"
    )

    dispatch_result = canonicalize_job_url(workday_url)
    assert dispatch_result.provider == "workday"
    assert dispatch_result.canonical_key.endswith("JR10284481")

    with pytest.raises(IngestionDispatchError, match="No ingester registered"):
        canonicalize_job_url("https://example.com/jobs/123")


def test_extract_structured_fields_from_workday_payload():
    html = """
    <html>
      <head>
        <title>Flight Physics Engineer</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "title": "Flight Physics Engineer",
          "description": " Build and validate high fidelity models. ",
          "identifier": {"value": "JR10284481"},
          "hiringOrganization": {"name": "Airbus"},
          "jobLocation": {"address": {"addressLocality": "Toulouse, France"}}
        }
        </script>
      </head>
      <body></body>
    </html>
    """

    extracted = extract_fields(html)

    assert extracted == {
        "title": "Flight Physics Engineer",
        "company": "Airbus",
        "location": "Toulouse, France",
        "description": "Build and validate high fidelity models.",
        "requisition_id": "JR10284481",
    }
