from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .indexer import FileMeta, Indexer


@dataclass
class H5Indexer(Indexer):
    store: Path

    def index(self) -> list[FileMeta]:
        import h5py

        files: list[FileMeta] = []

        with h5py.File(self.store, "r") as h5:
            def visit(name: str, obj: Any) -> None:
                attrs = dict(obj.attrs)
                filetype = self._filetype_from_attrs(name, attrs)
                filedate = self._filedate_from_attrs(attrs)
                shot = self._shot_from_attrs(attrs)
                files.append(
                    FileMeta(
                        filepath=Path(name),
                        filetype=filetype,
                        filedate=filedate,
                        shot=shot,
                    )
                )

            h5.visititems(lambda name, obj: visit(name, obj))

        return files

    def _filetype_from_attrs(self, name: str, attrs: dict[str, Any]) -> str:
        filetype = attrs.get("filetype")
        if isinstance(filetype, bytes):
            filetype = filetype.decode(errors="replace")
        if isinstance(filetype, str) and filetype:
            return filetype
        return Path(name).name

    def _filedate_from_attrs(self, attrs: dict[str, Any]) -> datetime:
        filedate = attrs.get("filedate") or attrs.get("mtime")
        if isinstance(filedate, datetime):
            return filedate
        if isinstance(filedate, (float, int)):
            return datetime.fromtimestamp(filedate)
        if isinstance(filedate, bytes):
            filedate = filedate.decode(errors="replace")
        if isinstance(filedate, str):
            try:
                return datetime.fromisoformat(filedate)
            except ValueError:
                pass
        return datetime.fromtimestamp(0)

    def _shot_from_attrs(self, attrs: dict[str, Any]) -> int | None:
        shot = attrs.get("shot")
        if isinstance(shot, (float, int)):
            return int(shot)
        if isinstance(shot, bytes):
            shot = shot.decode(errors="replace")
        if isinstance(shot, str) and shot.isdigit():
            return int(shot)
        return None
