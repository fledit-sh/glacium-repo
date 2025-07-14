import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.utils.JobIndex import JobFactory


def test_missing_dependency_runtime_error(tmp_path, monkeypatch):
    pkg = tmp_path / "fake_pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "bad_job.py").write_text(
        "import nonexistent_dependency\nfrom glacium.models.job import Job\nclass BadJob(Job):\n    name = 'BAD_JOB'\n"
    )

    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.setattr(JobFactory, "_PACKAGES", ["fake_pkg"])
    monkeypatch.setattr(JobFactory, "_jobs", None)
    monkeypatch.setattr(JobFactory, "_loaded", False)
    monkeypatch.setattr(JobFactory, "_import_errors", None)

    with pytest.raises(RuntimeError) as exc:
        JobFactory.create("BAD_JOB", None)

    msg = str(exc.value)
    assert "fake_pkg.bad_job" in msg
    assert "BAD_JOB" in msg
