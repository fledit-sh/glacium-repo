from __future__ import annotations
from controlledvar import VarPool, ControlledVar
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
import logging

log = logging.getLogger("sim")


class Repo(ABC):
    @abstractmethod
    def create_case_file(self, case_id: str) -> FileHandle: ...
    @abstractmethod
    def save_case(self, case: "Case") -> None: ...
    @abstractmethod
    def load_case(self, case_path: str) -> "Case": ...


@dataclass(frozen=True)
class Case:
    id: str
    vars: "VarPool"
    name: str = "Unnamed Case"


@dataclass
class H5Repo(Repo):
    root: Path

    def _path(self, case_id: str) -> Path:
        return self.root / f"{case_id}.h5"

    def create_case_file(self, case_id: str) -> Path:
        path = self._path(case_id)
        log.info("h5 file created: %s", path)
        return path

    def save_case(self, case: Case) -> None:
        path = self._path(case.id)
        log.info("h5 open: %s", path)
        log.info("case saved: %s", case.id)

    def load_case(self, case_path: str) -> Case:
        path = self._path(case_path)
        log.info("h5 open: %s", path)
        log.info("case loaded: %s", case_path)
        raise NotImplementedError


@dataclass
class CaseService:
    repo: Repo

    def create_case(self, case_id: str, vars: "VarPool", name: str = "Unnamed Case") -> Case:
        self.repo.create_case_file(case_id)
        case = Case(id=case_id, vars=vars, name=name)
        log.info("case created: %s", case.id)
        return case

    def save(self, case: Case) -> None:
        self.repo.save_case(case)

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

repo = H5Repo(root=Path("cases"))
service = CaseService(repo=repo)

pool = VarPool(name="Main")
pool.attach(ControlledVar[int](key="alpha_deg", _value=3, min=-10, max=20))

case = service.create_case("case_001", pool, name="Demo")
service.save(case)
