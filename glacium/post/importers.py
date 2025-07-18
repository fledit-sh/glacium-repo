from __future__ import annotations

from pathlib import Path

from dataclasses import dataclass
from .artifact import Artifact, ArtifactSet
from .processor import PostProcessor

__all__ = ["FensapSingleImporter", "FensapMultiImporter"]


@PostProcessor.register_importer
class FensapSingleImporter:
    """Import artifacts from single-shot FENSAP runs."""

    name = "fensap_single"

    def detect(self, root: Path) -> bool:
        return root.name in {"run_FENSAP", "run_DROP3D", "run_ICE3D"}

    def parse(self, root: Path) -> ArtifactSet:
        run_id = root.name
        aset = ArtifactSet(run_id)
        for p in root.iterdir():
            kind = p.stem
            aset.add(Artifact(p, kind))
        return aset


@PostProcessor.register_importer
class FensapMultiImporter:
    """Create Run-like objects from MULTISHOT post-processing files."""

    name = "fensap_multi"

    def detect(self, root: Path) -> bool:
        return root.name == "run_MULTISHOT"

    @dataclass
    class ImportedRun:
        airfoil: str
        parameters: dict[str, str]
        tags: list[str]

    def parse(self, root: Path) -> list[ImportedRun]:
        runs: list[FensapMultiImporter.ImportedRun] = []
        for dat in root.rglob("*.dat"):
            shot = dat.suffixes[-2][-6:] if len(dat.suffixes) >= 2 else dat.stem[-6:]
            runs.append(
                FensapMultiImporter.ImportedRun(
                    airfoil="imported",
                    parameters={"SHOT_ID": shot},
                    tags=["imported"],
                )
            )
        return runs
