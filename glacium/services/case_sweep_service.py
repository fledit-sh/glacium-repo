from __future__ import annotations

import itertools
from pathlib import Path
import yaml

from glacium.managers.project_manager import ProjectManager
from glacium.services.project_service import ProjectService

DEFAULT_AIRFOIL = Path(__file__).resolve().parents[1] / "data" / "AH63K127.dat"


class CaseSweepService:
    """Create multiple projects from parameter sweeps."""

    def __init__(self, root: Path = Path("runs")) -> None:
        self.root = root
        self.project_service = ProjectService(root)

    def create_projects(
        self,
        params: tuple[str],
        recipe: str,
        *,
        multishots: int | None = None,
    ) -> list[str]:
        def _parse(v: str):
            try:
                return yaml.safe_load(v)
            except Exception:
                return v

        param_map: dict[str, list] = {}
        for item in params:
            if "=" not in item:
                raise ValueError(f"Invalid parameter: {item}")
            key, values = item.split("=", 1)
            param_map[key] = [_parse(x) for x in values.split(",")]

        keys = list(param_map)
        pm = ProjectManager(self.root)
        uids: list[str] = []

        for combo in itertools.product(*(param_map[k] for k in keys)):
            proj = pm.create("case", recipe, DEFAULT_AIRFOIL, multishots=multishots)
            proj.config.dump(proj.paths.global_cfg_file())
            case_file = proj.root / "case.yaml"
            case = yaml.safe_load(case_file.read_text()) or {}
            for k, v in zip(keys, combo):
                case[k] = v
            case_file.write_text(yaml.safe_dump(case, sort_keys=False))
            self.project_service.update_config(proj.uid, None)
            uids.append(proj.uid)

        return uids
