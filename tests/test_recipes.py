import pytest

from glacium.recipes.fensap import FensapRecipe
from glacium.jobs.fensap_jobs import FensapRunJob
from glacium.models.config import GlobalConfig
from glacium.managers.path_manager import PathBuilder
from glacium.models.project import Project


def test_fensap_recipe_build(tmp_path):
    cfg = GlobalConfig(project_uid="uid", base_dir=tmp_path)
    paths = PathBuilder(tmp_path).build()
    project = Project("uid", tmp_path, cfg, paths, [])

    recipe = FensapRecipe()
    jobs = recipe.build(project)

    assert len(jobs) == 1
    assert isinstance(jobs[0], FensapRunJob)
