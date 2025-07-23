from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.utils.JobIndex import JobFactory


def test_analysis_jobs_registered():
    jobs = JobFactory.list()
    assert "FENSAP_ANALYSIS" in jobs
    assert "MESH_ANALYSIS" in jobs
