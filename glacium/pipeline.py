from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, Literal, NamedTuple

import yaml


class RunResult(NamedTuple):
    run_id: str
    success: bool
    elapsed: float
    artifacts: dict[str, Path]
    error: Exception | None


class Run:
    """Declarative description of a simulation run."""

    def __init__(
        self,
        *,
        airfoil: str | None = None,
        parameters: dict[str, Any] | None = None,
        jobs: list[str] | None = None,
        tags: set[str] | None = None,
    ) -> None:
        self._id = str(uuid.uuid4())
        self._airfoil = airfoil
        self._parameters: dict[str, Any] = dict(parameters) if parameters else {}
        self._jobs: list[str] = list(jobs) if jobs else []
        self._tags: set[str] = set(tags) if tags else set()
        self._dependencies: set[str] = set()

    # ------------------------------------------------------------------
    def select_airfoil(self, name: str) -> "Run":
        self._airfoil = name
        return self

    def set(self, key: str, value: Any) -> "Run":
        self._parameters[key] = value
        return self

    def set_bulk(self, params: Mapping[str, Any]) -> "Run":
        for k, v in params.items():
            self._parameters[k] = v
        return self

    def add_job(self, name: str) -> "Run":
        self._jobs.append(name)
        return self

    def jobs(self, names: Iterable[str]) -> "Run":
        for n in names:
            self._jobs.append(n)
        return self

    def clear_jobs(self) -> "Run":
        self._jobs.clear()
        return self

    def tag(self, label: str) -> "Run":
        self._tags.add(label)
        return self

    def tags(self, labels: Iterable[str]) -> "Run":
        for l in labels:
            self._tags.add(l)
        return self

    def remove_tag(self, label: str) -> "Run":
        self._tags.discard(label)
        return self

    def depends_on(self, other: "Run") -> "Run":
        self._dependencies.add(other.id)
        return self

    # ------------------------------------------------------------------
    def clone(self, deep: bool = True) -> "Run":
        import copy

        params = copy.deepcopy(self._parameters) if deep else dict(self._parameters)
        jobs = copy.deepcopy(self._jobs) if deep else list(self._jobs)
        tags = copy.deepcopy(self._tags) if deep else set(self._tags)
        clone = Run(airfoil=self._airfoil, parameters=params, jobs=jobs, tags=tags)
        clone._dependencies = set()
        return clone

    # ------------------------------------------------------------------
    def preview(self, fmt: Literal["str", "dict", "json", "yaml"] = "str"):
        data = self.to_dict()
        if fmt == "dict":
            return data
        if fmt == "json":
            return json.dumps(data, indent=2)
        if fmt == "yaml":
            return yaml.safe_dump(data, sort_keys=False)

        parts = [
            f"Run {self._id}",
            f"  airfoil: {self._airfoil}",
            f"  parameters: {self._parameters}",
            f"  jobs: {self._jobs}",
            f"  tags: {sorted(self._tags)}",
            f"  dependencies: {sorted(self._dependencies)}",
        ]
        return "\n".join(parts)

    # ------------------------------------------------------------------
    def execute(self, *, dry_run: bool = False) -> RunResult:
        from .pipeline import Pipeline  # type: ignore

        pipe = Pipeline([self])
        results = pipe.execute(dry_run=dry_run)
        return results[0]

    # ------------------------------------------------------------------
    def validate(self) -> None:
        if not self._airfoil:
            raise ValueError("Airfoil not selected")
        try:
            json.dumps(self._parameters)
        except TypeError as err:
            raise TypeError(f"Parameters not serialisable: {err}") from None
        if not self._jobs:
            raise ValueError("At least one job required")
        if self._id in self._dependencies:
            raise ValueError("Run cannot depend on itself")

    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self._id,
            "airfoil": self._airfoil,
            "parameters": json.loads(json.dumps(self._parameters)),
            "jobs": list(self._jobs),
            "tags": sorted(self._tags),
            "dependencies": sorted(self._dependencies),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.to_dict(), sort_keys=False)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Run":
        run = cls(
            airfoil=data.get("airfoil"),
            parameters=dict(data.get("parameters", {})),
            jobs=list(data.get("jobs", [])),
            tags=set(data.get("tags", [])),
        )
        if "id" in data:
            run._id = str(data["id"])
        run._dependencies = set(data.get("dependencies", []))
        return run

    # ------------------------------------------------------------------
    @property
    def id(self) -> str:  # pragma: no cover - trivial
        return self._id

    @property
    def airfoil(self) -> str | None:  # pragma: no cover - trivial
        return self._airfoil

    @property
    def parameters(self) -> dict[str, Any]:  # pragma: no cover - trivial
        return self._parameters

    @property
    def jobs(self) -> list[str]:  # pragma: no cover - trivial
        return self._jobs

    @property
    def tags(self) -> set[str]:  # pragma: no cover - trivial
        return self._tags

    @property
    def dependencies(self) -> set[str]:  # pragma: no cover - trivial
        return self._dependencies

