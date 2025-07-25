from __future__ import annotations

from pathlib import Path

from glacium.utils.current import PROJECT_TOKEN
from glacium.managers.project_manager import ProjectManager
from glacium.utils.logging import log


class RunService:
    """Execute project jobs."""

    def __init__(self, root: Path = Path("runs")) -> None:
        self.root = root

    def run(self, jobs: tuple[str], run_all: bool) -> list[str]:
        pm = ProjectManager(self.root)
        executed: list[str] = []

        if run_all:
            for uid in pm.list_uids():
                try:
                    pm.load(uid).job_manager.run(jobs or None)
                    executed.append(uid)
                except FileNotFoundError:
                    log.error(f"{uid}: not found")
                except Exception as err:  # noqa: BLE001
                    log.error(f"{uid}: {err}")
            return executed

        uid = PROJECT_TOKEN.load()
        if uid is None:
            raise RuntimeError("Kein Projekt ausgewaehlt")

        pm.load(uid).job_manager.run(jobs or None)
        executed.append(uid)
        return executed
