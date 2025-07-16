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


class Pipeline:
    """Ordered collection of :class:`Run` objects."""

    def __init__(self, runs: Iterable[Run] | None = None) -> None:
        self._runs: list[Run] = []
        self._results: dict[str, RunResult] = {}
        if runs:
            self.add_many(runs)

    # ------------------------------------------------------------------
    def add(self, run: Run) -> "Pipeline":
        if any(r.id == run.id for r in self._runs):
            raise ValueError(f"Duplicate run id: {run.id}")
        self._runs.append(run)
        return self

    def add_many(self, runs: Iterable[Run]) -> "Pipeline":
        for r in runs:
            self.add(r)
        return self

    def remove(self, run_or_id: Run | str) -> "Pipeline":
        rid = run_or_id.id if isinstance(run_or_id, Run) else str(run_or_id)
        self._runs = [r for r in self._runs if r.id != rid]
        for r in self._runs:
            r.dependencies.discard(rid)
        self._results.pop(rid, None)
        return self

    def combine(self, other: "Pipeline") -> "Pipeline":
        for r in other:
            self.add(r)
        return self

    # ------------------------------------------------------------------
    def repeat(
        self,
        template: Run,
        param: str,
        values: Iterable[Any],
        *,
        tag_format: str = "{param}={value}",
    ) -> "Pipeline":
        for v in values:
            clone = template.clone()
            clone.set(param, v)
            clone.tag(tag_format.format(param=param, value=v))
            self.add(clone)
        return self

    def param_grid(
        self,
        *,
        airfoils: Iterable[str] | None = None,
        common: Mapping[str, Any] | None = None,
        jobs: Iterable[str] | None = None,
        **param_axes: Iterable[Any],
    ) -> "Pipeline":
        import itertools

        common_params = dict(common) if common else {}
        axes_keys = list(param_axes)
        axes_values = [list(param_axes[k]) for k in axes_keys]

        for combo in itertools.product(*axes_values):
            params = dict(zip(axes_keys, combo))
            params.update(common_params)
            targets = airfoils or [None]
            for af in targets:
                run = Run(airfoil=af, parameters=params, jobs=list(jobs) if jobs else None)
                self.add(run)
        return self

    # ------------------------------------------------------------------
    def filter(self, predicate) -> "Pipeline":
        return Pipeline(r for r in self._runs if predicate(r))

    def tags(self, labels: str | Iterable[str]) -> "Pipeline":
        if isinstance(labels, str):
            required = {labels}
        else:
            required = set(labels)
        return self.filter(lambda r: required.issubset(r.tags))

    # ------------------------------------------------------------------
    def preview(
        self,
        fmt: Literal["table", "dict", "json", "yaml"] = "table",
        max_rows: int | None = 20,
    ):
        rows = [
            {
                "id": r.id,
                "tags": sorted(r.tags),
                "airfoil": r.airfoil,
                "params": sorted(r.parameters),
                "jobs": len(r.jobs),
                "deps": sorted(r.dependencies),
            }
            for r in self._runs
        ]
        if fmt == "dict":
            return rows
        if fmt == "json":
            return json.dumps(rows, indent=2)
        if fmt == "yaml":
            return yaml.safe_dump(rows, sort_keys=False)

        header = f"{'ID':8}  {'TAGS':20}  {'AIRFOIL':10}  {'PARAMS':10}  {'JOBS':4}  {'DEPS':4}"
        lines = [header]
        for idx, row in enumerate(rows):
            if max_rows is not None and idx >= max_rows:
                lines.append("…")
                break
            lines.append(
                f"{row['id'][:8]:8}  "
                f"{','.join(row['tags'])[:20]:20}  "
                f"{(row['airfoil'] or '')[:10]:10}  "
                f"{','.join(row['params'])[:10]:10}  "
                f"{row['jobs']:4d}  "
                f"{len(row['deps']):4d}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _topological_sort(self) -> list[Run]:
        from collections import defaultdict, deque

        graph = defaultdict(set)
        indeg = defaultdict(int)
        for r in self._runs:
            indeg[r.id] = 0
        for r in self._runs:
            for d in r.dependencies:
                graph[d].add(r.id)
                indeg[r.id] += 1

        q = deque([rid for rid, deg in indeg.items() if deg == 0])
        order: list[str] = []
        while q:
            n = q.popleft()
            order.append(n)
            for m in graph.get(n, set()):
                indeg[m] -= 1
                if indeg[m] == 0:
                    q.append(m)

        if len(order) != len(indeg):
            raise RuntimeError("Circular dependency detected")

        id_map = {r.id: r for r in self._runs}
        return [id_map[i] for i in order]

    def execute(
        self,
        *,
        concurrency: int = 1,
        stop_on_error: bool = False,
        dry_run: bool = False,
    ) -> list[RunResult]:
        import time
        from concurrent.futures import ThreadPoolExecutor

        self.validate()
        order = self._topological_sort()

        def _run(r: Run) -> RunResult:
            start = time.perf_counter()
            error = None
            success = True
            try:
                if not dry_run:
                    pass
            except Exception as exc:  # pragma: no cover - placeholder
                success = False
                error = exc
            elapsed = time.perf_counter() - start
            result = RunResult(r.id, success, elapsed, {}, error)
            self._results[r.id] = result
            return result

        results: list[RunResult] = []
        if concurrency <= 1:
            for r in order:
                res = _run(r)
                results.append(res)
                if stop_on_error and not res.success:
                    break
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as ex:
                futs = {ex.submit(_run, r): r for r in order}
                for fut in futs:
                    res = fut.result()
                    results.append(res)
                    if stop_on_error and not res.success:
                        for f in futs:
                            if not f.done():
                                f.cancel()
                        break
        return results

    # ------------------------------------------------------------------
    def save_layout(
        self,
        path: str | Path,
        *,
        format: Literal["yaml", "json"] | None = None,
        include_results: bool = False,
    ) -> Path:
        path = Path(path)
        fmt = format or path.suffix.lstrip(".")
        data: dict[str, Any] = {"runs": [r.to_dict() for r in self._runs]}
        if include_results:
            data["results"] = {
                rid: {
                    "success": res.success,
                    "elapsed": res.elapsed,
                    "error": str(res.error) if res.error else None,
                }
                for rid, res in self._results.items()
            }
        if fmt == "json":
            path.write_text(json.dumps(data, indent=2))
        else:
            path.write_text(yaml.safe_dump(data, sort_keys=False))
        return path

    @classmethod
    def load_layout(
        cls,
        path: str | Path,
        *,
        format: Literal["yaml", "json"] | None = None,
    ) -> "Pipeline":
        path = Path(path)
        fmt = format or path.suffix.lstrip(".")
        text = path.read_text()
        if fmt == "json":
            data = json.loads(text)
        else:
            data = yaml.safe_load(text)
        runs = [Run.from_dict(d) for d in data.get("runs", data)]
        pipe = cls(runs)
        return pipe

    # ------------------------------------------------------------------
    def size(self) -> int:
        return len(self._runs)

    def dependency_graph(self):
        try:
            import networkx as nx  # type: ignore
        except Exception as exc:  # pragma: no cover - optional
            raise RuntimeError("networkx required for dependency_graph") from exc
        g = nx.DiGraph()
        for r in self._runs:
            g.add_node(r.id)
            for d in r.dependencies:
                g.add_edge(d, r.id)
        return g

    def validate(self) -> None:
        ids: set[str] = set()
        for r in self._runs:
            if r.id in ids:
                raise ValueError(f"Duplicate run id: {r.id}")
            ids.add(r.id)
        id_set = ids
        for r in self._runs:
            for dep in r.dependencies:
                if dep not in id_set:
                    raise ValueError(f"Unknown dependency {dep} for run {r.id}")
        for r in self._runs:
            r.validate()
        self._topological_sort()

    # ------------------------------------------------------------------
    def __iter__(self):  # pragma: no cover - trivial
        return iter(self._runs)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._runs)

    def __getitem__(self, key):  # pragma: no cover - simple
        if isinstance(key, int):
            return self._runs[key]
        for r in self._runs:
            if r.id == key:
                return r
        raise KeyError(key)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"Pipeline({len(self._runs)} runs)"


def sweep(
    base: Run,
    param: str,
    values: Iterable[Any],
    *,
    tag_format: str = "{param}={value}",
) -> list[Run]:
    pipe = Pipeline().repeat(base, param, values, tag_format=tag_format)
    return list(pipe)


def grid(
    *,
    airfoils: Iterable[str] | None = None,
    common: Mapping[str, Any] | None = None,
    jobs: Iterable[str] | None = None,
    **param_axes: Iterable[Any],
) -> Pipeline:
    pipe = Pipeline()
    pipe.param_grid(airfoils=airfoils, common=common, jobs=jobs, **param_axes)
    return pipe


def load(path: str | Path) -> Pipeline:
    return Pipeline.load_layout(path)


def run(layout: str | Path, **execute_kwargs) -> list[RunResult]:
    pipe = load(layout)
    pipe.preview()
    return pipe.execute(**execute_kwargs)


__all__ = [
    "Run",
    "Pipeline",
    "sweep",
    "grid",
    "load",
    "run",
]

