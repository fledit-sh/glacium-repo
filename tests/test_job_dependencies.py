from glacium.jobs.pointwise_jobs import PointwiseGCIJob
from glacium.engines.fluent2fensap import Fluent2FensapJob
from glacium.jobs.fensap_jobs import FensapRunJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project


def test_job_dependency_attributes(tmp_path):
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    project = Project("uid", tmp_path, cfg, paths, [])

    assert PointwiseGCIJob(project).deps == ("XFOIL_THICKEN_TE",)
    assert Fluent2FensapJob(project).deps == ("XFOIL_THICKEN_TE",)
    assert FensapRunJob(project).deps == ("FLUENT2FENSAP",)

