Below is a **single, self‑contained specification file** you can paste straight into your coding‑agent prompt.
It **supersedes** all earlier drafts and already incorporates the new rule:

> *Only the **run\_MULTISHOT** directory contains six‑digit‑numbered files; `run_FENSAP`, `run_DROP3D`, `run_ICE3D` each hold a single, un‑numbered shot.*

---

# Glacium — High‑Level API + Post‑Processing Specification (rev 2025‑07‑17)

---

## 1  Directory conventions

```
project/
 ├─ _cfg/ _data/ _tmpl/ …                # internal cfg stuff
 ├─ mesh/ pointwise/ analysis/ …         # common folders
 ├─ run_FENSAP/                          # single‑shot
 │    ├─ grid.ice
 │    ├─ converg.fensap
 │    └─ soln.fensap
 ├─ run_DROP3D/                          # single‑shot
 │    ├─ converg.drop
 │    └─ droplet.drop
 ├─ run_ICE3D/                           # single‑shot
 │    ├─ iceconv.dat.ice
 │    └─ swimsol.ice
 ├─ run_MULTISHOT/                       # **multi‑shot**
 │    ├─ grid.ice.000001
 │    ├─ converg.fensap.000001
 │    ├─ soln.fensap.000001
 │    ├─ droplet.drop.000001
 │    ├─ swimsol.ice.000001
 │    └─ … (000002, 000003, …)
 └─ case.yaml
```

---

## 2  Pipeline DSL (Run / Pipeline)

> **Unchanged** from earlier spec, included here for completeness.

### 2.1 Public surface

```python
from glacium.pipeline import Run, Pipeline
```

| Object       | Core mutators                                                                                              | Helpers                                              | Serialisers                                                   |
| ------------ | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| **Run**      | `select_airfoil`, `set`, `set_bulk`, `add_job`, `jobs`, `tag`, `tags`, `depends_on`, `clone`, `clear_jobs` | `preview`, `execute`, `validate`                     | `to_dict`, `to_json`, `to_yaml`, `from_dict`                  |
| **Pipeline** | `add`, `add_many`, `remove`, `repeat`, `param_grid`, `combine`, `filter`, `tags`                           | `preview`, `execute`, `dependency_graph`, `validate` | `save_layout`, `load_layout`, `to_dict`, `to_json`, `to_yaml` |

See tables in previous message for full method signatures and behavioural contracts.

---

## 3  Post‑processing layer

### 3.1 Artifact primitives

| Class           | Fields                   | Key methods                                              |
| --------------- | ------------------------ | -------------------------------------------------------- |
| `Artifact`      | `path, kind, meta`       | `.open()`, `.to_dict()`                                  |
| `ArtifactSet`   | `run_id, artifacts`      | `.add()`, `.filter()`, `.get_first()`, `.to_dataframe()` |
| `ArtifactIndex` | `Dict[str, ArtifactSet]` | dict‑like                                                |

### 3.2 PostProcessor

```python
PostProcessor(source, *, importers=None, recursive=True)
```

| Group     | Methods                                            |
| --------- | -------------------------------------------------- |
| Discovery | `.map(pattern="*.dat") → list[Path]`               |
| Access    | `.index`, `.get(run_or_id)`                        |
| Visuals   | `.plot(var, run_or_id)`                            |
| Export    | `.export(dest, format="zip")`                      |
| I/O       | `.to_dict()`, `.to_yaml()`, `.register_importer()` |

---

## 4  Converters (new structure)

### 4.1 `SingleShotConverter`

Handles `run_FENSAP`, `run_DROP3D`, `run_ICE3D`.

```python
@dataclass
class SingleShotConverter:
    root: Path                               # run_FENSAP/ etc.
    exe: Path = Path("nti2tecplot.exe")
    overwrite: bool = False

    MAP = {
        "run_FENSAP":  ("SOLN",   "grid.ice", "soln.fensap",   "soln.dat"),
        "run_DROP3D":  ("DROPLET","grid.ice", "droplet.drop",  "droplet.drop.dat"),
        "run_ICE3D":   ("SWIMSOL","grid.ice", "swimsol.ice",   "swimsol.ice.dat"),
    }

    def convert(self) -> Path:
        run_dir = self.root.name
        mode, grid_name, src_name, dst_name = self.MAP[run_dir]
        grid = self.root.parent / "mesh" / grid_name         # shared mesh
        src  = self.root / src_name
        dst  = self.root / dst_name
        if dst.exists() and not self.overwrite:
            return dst
        subprocess.run([self.exe, mode, grid, src, dst], check=True)
        return dst
```

### 4.2 `MultiShotConverter`

Processes **only** the `run_MULTISHOT` directory.

```python
@dataclass
class MultiShotConverter:
    root: Path                       # …/run_MULTISHOT
    exe: Path = Path("nti2tecplot.exe")
    overwrite: bool = False
    concurrency: int = 4             # thread‑pool workers

    PATTERNS = {
        "SOLN":    ("soln.fensap.{id}",   "soln.fensap.{id}.dat"),
        "DROPLET": ("droplet.drop.{id}",  "droplet.drop.{id}.dat"),
        "SWIMSOL": ("swimsol.ice.{id}",   "swimsol.ice.{id}.dat"),
    }

    def _convert_one(self, shot: str) -> list[Path]:
        grid = self.root.parent.parent / "mesh" / f"grid.ice.{shot}"
        out: list[Path] = []
        for mode,(src_tpl,dst_tpl) in self.PATTERNS.items():
            src = self.root / src_tpl.format(id=shot)
            dst = self.root / dst_tpl.format(id=shot)
            if not src.exists():
                continue
            if dst.exists() and not self.overwrite:
                out.append(dst); continue
            subprocess.run([self.exe, mode, grid, src, dst], check=True)
            out.append(dst)
        return out

    def convert_all(self) -> ArtifactIndex:
        shots = sorted({p.suffix[-6:] for p in self.root.glob("*.??????")})
        with ThreadPoolExecutor(max_workers=self.concurrency) as ex:
            ex.map(self._convert_one, shots)
        return PostProcessor(self.root.parent).index
```

---

## 5  Importer plug‑ins

### 5.1 `FensapSingleImporter`

Detects single‑shot runs:

```python
class FensapSingleImporter:
    name = "fensap_single"

    def detect(self, root: Path) -> bool:
        return root.name in {"run_FENSAP","run_DROP3D","run_ICE3D"}

    def parse(self, root: Path) -> ArtifactSet:
        run_id = root.name
        aset = ArtifactSet(run_id)
        for p in root.iterdir():
            kind = p.stem                      # simple kind mapping
            aset.add(Artifact(p, kind))
        return aset
```

### 5.2 `FensapMultiImporter`

Detects and parses `run_MULTISHOT`:

```python
class FensapMultiImporter:
    name = "fensap_multi"

    def detect(self, root: Path) -> bool:
        return root.name == "run_MULTISHOT"

    def parse(self, root: Path) -> Pipeline:
        pipe = Pipeline()
        for dat in root.rglob("*.dat"):
            shot = dat.suffix[-6:]
            run = (
                Run()
                .select_airfoil("imported")
                .set("SHOT_ID", shot)
                .tag("imported")
            )
            pipe.add(run)
        return pipe
```

---

## 6  Optional post‑processing jobs

| Job name                    | Purpose                                                                                     | Implementation hint                                |
| --------------------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `POSTPROCESS_SINGLE_FENSAP` | Calls `SingleShotConverter(root).convert()` *once* per single‑shot run directory.           | Waits for `DROP3D_RUN` and `ICE3D_RUN` when present; otherwise runs after `FENSAP_RUN`. |
| `FENSAP_ANALYSIS`           | Create slice screenshots from `run_FENSAP/soln.dat` using `fensap_analysis`. Results are written to `analysis/FENSAP`. | Attach after `POSTPROCESS_SINGLE_FENSAP`. |
| `POSTPROCESS_MULTISHOT`     | Calls `MultiShotConverter(root / "run_MULTISHOT").convert_all()` after the solver finishes. | Attach at pipeline end.                            |
| `ANALYZE_MULTISHOT`         | Run analysis helpers on MULTISHOT data and store plots in `analysis/MULTISHOT`. | Attach after `POSTPROCESS_MULTISHOT`. |
| `MESH_ANALYSIS`             | Create mesh quality screenshots and an HTML report using `mesh_analysis`. Results are written to `analysis/MESH`. | Run after meshing is complete. |

Example dependency order:

```python
# FENSAP only
proj.add_job("FENSAP_RUN")
proj.add_job("POSTPROCESS_SINGLE_FENSAP")  # runs after FENSAP_RUN

# With extra solvers
proj.add_job("FENSAP_RUN")
proj.add_job("DROP3D_RUN")
proj.add_job("ICE3D_RUN")
proj.add_job("POSTPROCESS_SINGLE_FENSAP")  # waits for DROP3D_RUN and ICE3D_RUN
```

POSTPROCESS jobs create a manifest (`manifest.json`) so the PostProcessor loads instantly:

```python
pp = PostProcessor(project_path)  # auto‑reads manifest if exists
```

---

## 7  Bulk processing script (example)

```python
from pathlib import Path
from glacium.post.convert.multishot import MultiShotConverter
from glacium.post.convert.single import SingleShotConverter

root = Path("/sim/projects")
for prj in root.glob("2025*/"):
    ms_dir = prj / "run_MULTISHOT"
    if ms_dir.exists():
        MultiShotConverter(ms_dir).convert_all()

    for single in ["run_FENSAP","run_DROP3D","run_ICE3D"]:
        d = prj / single
        if d.exists():
            SingleShotConverter(d).convert()
```

---

## 8  Minimal user workflow

```python
# --- run solver(s) via Pipeline API ---------------------------------------
pipe.execute()

# --- optional automatic post‑processing -----------------------------------
# (if jobs were added, nothing else to do)

# --- manual post‑processing ----------------------------------------------
from glacium.post import PostProcessor
pp = PostProcessor("/sim/projects/20250715-130806-677407-CE0B",
                   importers=[FensapSingleImporter, FensapMultiImporter])

pp.plot("Cl", next(iter(pp.index)))      # first run
pp.export("/tmp/results.zip")
```

---

**End of specification** – ready for code generation.
