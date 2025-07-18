from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, List, NamedTuple
import yaml

class RunResult(NamedTuple):
    run_id: str
    success: bool
    elapsed: float
    artifacts: dict[str, Path]
    error: Exception | None

class Run:
    def __init__(self, *, airfoil: str | None = None, parameters: Mapping[str, Any] | None = None,
                 jobs: Sequence[str] | None = None, tags: Iterable[str] | None = None) -> None:
        self.id = str(uuid.uuid4())
        self.airfoil = airfoil
        self.parameters: dict[str, Any] = dict(parameters or {})
        self.jobs: List[str] = list(jobs or [])
        self.tags: List[str] = list(tags or [])
        self._deps: List[Run] = []

    # fluent helpers -----------------------------------------------------
    def select_airfoil(self, name: str) -> "Run":
        self.airfoil = name
        return self

    def set(self, key: str, value: Any) -> "Run":
        self.parameters[key] = value
        return self

    def set_bulk(self, params: Mapping[str, Any]) -> "Run":
        for k, v in params.items():
            self.set(k, v)
        return self

    def add_job(self, name: str) -> "Run":
        self.jobs.append(name)
        return self

    def jobs(self, names: Iterable[str]) -> "Run":
        for n in names:
            self.add_job(n)
        return self

    def clear_jobs(self) -> "Run":
        self.jobs.clear()
        return self

    def tag(self, label: str) -> "Run":
        if label not in self.tags:
            self.tags.append(label)
        return self

    def tags(self, labels: Iterable[str]) -> "Run":
        for l in labels:
            self.tag(l)
        return self

    def remove_tag(self, label: str) -> "Run":
        if label in self.tags:
            self.tags.remove(label)
        return self

    def depends_on(self, other: "Run") -> "Run":
        if other not in self._deps:
            self._deps.append(other)
        return self

    def clone(self, deep: bool = True) -> "Run":
        copy = Run(airfoil=self.airfoil, parameters=self.parameters, jobs=self.jobs, tags=self.tags)
        if deep:
            copy._deps = list(self._deps)
        return copy

    # presentation -------------------------------------------------------
    def preview(self, fmt: str = "str") -> str | dict:
        data = self.to_dict()
        if fmt == "dict":
            return data
        if fmt == "json":
            return json.dumps(data)
        if fmt == "yaml":
            return yaml.dump(data)
        return str(data)

    # execution ----------------------------------------------------------
    def execute(self, *, dry_run: bool = False) -> RunResult:
        self.validate()
        return RunResult(self.id, True, 0.0, {}, None)

    # validation ---------------------------------------------------------
    def validate(self) -> None:
        if not self.jobs:
            raise ValueError("no jobs")

    # serialization ------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "airfoil": self.airfoil,
            "parameters": dict(self.parameters),
            "jobs": list(self.jobs),
            "tags": list(self.tags),
            "deps": [r.id for r in self._deps],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict())

class Pipeline:
    def __init__(self, runs: Iterable[Run] | None = None) -> None:
        self._runs: List[Run] = []
        self._map: dict[str, Run] = {}
        if runs:
            self.add_many(runs)

    # collection helpers -------------------------------------------------
    def add(self, run: Run) -> "Pipeline":
        if run.id in self._map:
            raise ValueError("duplicate run id")
        self._runs.append(run)
        self._map[run.id] = run
        return self

    def add_many(self, runs: Iterable[Run]) -> "Pipeline":
        for r in runs:
            self.add(r)
        return self

    def remove(self, run_or_id: Run | str) -> "Pipeline":
        rid = run_or_id.id if isinstance(run_or_id, Run) else run_or_id
        run = self._map.pop(rid)
        self._runs.remove(run)
        for r in self._runs:
            if run in r._deps:
                r._deps.remove(run)
        return self

    def _topological_sort(self) -> List[Run]:
        result: List[Run] = []
        temp = list(self._runs)
        indeg = {r: 0 for r in temp}
        for r in temp:
            for dep in r._deps:
                indeg[r] += 1
        ready = [r for r in temp if indeg[r] == 0]
        while ready:
            r = ready.pop(0)
            result.append(r)
            for n in temp:
                if r in n._deps:
                    indeg[n] -= 1
                    if indeg[n] == 0 and n not in result and n not in ready:
                        ready.append(n)
        return result

    def execute(self, *, concurrency: int = 1, stop_on_error: bool = False, dry_run: bool = False) -> List[RunResult]:
        results = []
        for r in self._topological_sort():
            results.append(r.execute(dry_run=dry_run))
        return results

# helper functions -------------------------------------------------------------
def sweep(base: Run, param: str, values: Iterable[Any], *, tag_format: str = "{param}={value}") -> List[Run]:
    runs = []
    for v in values:
        r = base.clone()
        r.set(param, v)
        r.tag(tag_format.format(param=param, value=v))
        runs.append(r)
    return runs


def grid(*, airfoils: Sequence[str] | None = None, common: Mapping[str, Any] | None = None,
         jobs: Sequence[str] | None = None, **param_axes: Sequence[Any]) -> Pipeline:
    pipe = Pipeline()
    airfoils = airfoils or [None]
    common = common or {}
    axes = list(param_axes.items())
    def build(idx: int, params: dict[str, Any]):
        if idx == len(axes):
            for af in airfoils:
                r = Run(airfoil=af, parameters=params, jobs=jobs or [])
                pipe.add(r)
            return
        key, values = axes[idx]
        for v in values:
            params[key] = v
            build(idx+1, params)
    build(0, dict(common))
    return pipe


def load(path: str) -> Pipeline:
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    runs = []
    for entry in data.get("runs", []):
        r = Run(
            airfoil=entry.get("airfoil"),
            parameters=entry.get("parameters"),
            jobs=entry.get("jobs"),
            tags=entry.get("tags"),
        )
        runs.append(r)
    return Pipeline(runs)


def run(layout: str | Path, **execute_kwargs: Any) -> list[RunResult]:
    pipe = load(str(layout))
    pipe.preview()
    return pipe.execute(**execute_kwargs)


