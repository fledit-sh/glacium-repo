# pyside6_h5_skeleton_poc.py
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import h5py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
)


SKELETON_SLOTS = ["file1.bin", "file2.bin", "file3.bin", "file4.bin", "file5.bin"]


def _ensure_parent_group(h5: h5py.File, path: str) -> h5py.Group:
    # path like /skeleton/files/file1.bin
    parent = str(Path(path).parent).replace("\\", "/")
    if parent in ("", "."):
        return h5["/"]
    return h5.require_group(parent)


def _touch_placeholder_bytes(h5: h5py.File, path: str) -> None:
    if path in h5:
        return
    _ensure_parent_group(h5, path)
    ds = h5.create_dataset(path, data=np.void(b""))  # empty bytes placeholder
    ds.attrs["status"] = "missing"
    ds.attrs["source"] = ""


def init_skeleton(h5_path: Path) -> None:
    h5_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(h5_path, "a") as h5:
        root = h5.require_group("/skeleton")
        root.attrs.setdefault("status", "skeleton")

        for name in SKELETON_SLOTS:
            _touch_placeholder_bytes(h5, f"/skeleton/files/{name}")


def write_bytes_to_slot(h5_path: Path, slot_name: str, file_on_disk: Path) -> None:
    if slot_name not in SKELETON_SLOTS:
        raise ValueError(f"Unknown slot: {slot_name}")

    data = file_on_disk.read_bytes()
    dset_path = f"/skeleton/files/{slot_name}"

    with h5py.File(h5_path, "a") as h5:
        _ensure_parent_group(h5, dset_path)
        if dset_path in h5:
            del h5[dset_path]
        ds = h5.create_dataset(dset_path, data=np.void(data))
        ds.attrs["status"] = "present"
        ds.attrs["source"] = str(file_on_disk)


@dataclass(frozen=True)
class SlotState:
    slot: str
    status: str
    source: str
    size_bytes: int


def read_slots_state(h5_path: Path) -> List[SlotState]:
    states: List[SlotState] = []
    if not h5_path.exists():
        return [SlotState(s, "missing", "", 0) for s in SKELETON_SLOTS]

    with h5py.File(h5_path, "r") as h5:
        for slot in SKELETON_SLOTS:
            p = f"/skeleton/files/{slot}"
            if p not in h5:
                states.append(SlotState(slot, "missing", "", 0))
                continue

            ds = h5[p]
            status = str(ds.attrs.get("status", "missing"))
            source = str(ds.attrs.get("source", ""))
            # For scalar np.void bytes, ds[()] is np.void; len(bytes(ds[()])) gives size
            try:
                size = len(bytes(ds[()]))
            except Exception:
                size = 0
            states.append(SlotState(slot, status, source, size))
    return states


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("HDF5 Skeleton POC (5 files)")

        self.h5_path_edit = QLineEdit(str(Path.cwd() / "test.h5"))
        self.h5_path_edit.setPlaceholderText("Path to .h5 file (e.g. test.h5)")

        self.init_btn = QPushButton("Init skeleton (create 5 placeholders)")
        self.refresh_btn = QPushButton("Refresh")
        self.pick_h5_btn = QPushButton("Choose .h5...")

        top = QHBoxLayout()
        top.addWidget(QLabel("H5 file:"))
        top.addWidget(self.h5_path_edit, 1)
        top.addWidget(self.pick_h5_btn)
        top.addWidget(self.init_btn)
        top.addWidget(self.refresh_btn)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Slot", "Status", "Source", "Size (bytes)", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        layout = QVBoxLayout()
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        self.setLayout(layout)

        self.pick_h5_btn.clicked.connect(self.on_pick_h5)
        self.init_btn.clicked.connect(self.on_init)
        self.refresh_btn.clicked.connect(self.refresh_table)

        self.refresh_table()

    def h5_path(self) -> Path:
        return Path(self.h5_path_edit.text().strip()).expanduser()

    def on_pick_h5(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Choose HDF5 file",
            str(self.h5_path()),
            "HDF5 (*.h5 *.hdf5);;All files (*.*)",
        )
        if path:
            self.h5_path_edit.setText(path)
            self.refresh_table()

    def on_init(self) -> None:
        try:
            init_skeleton(self.h5_path())
        except Exception as e:
            QMessageBox.critical(self, "Init failed", str(e))
            return
        self.refresh_table()

    def refresh_table(self) -> None:
        states = read_slots_state(self.h5_path())
        self.table.setRowCount(len(states))

        for row, st in enumerate(states):
            self._set_item(row, 0, st.slot)
            self._set_item(row, 1, st.status)
            self._set_item(row, 2, st.source)
            self._set_item(row, 3, str(st.size_bytes))

            btn = QPushButton("Pick file…")
            btn.clicked.connect(lambda _=False, slot=st.slot: self.on_pick_file_for_slot(slot))
            self.table.setCellWidget(row, 4, btn)

            # light visual hint
            if st.status == "present":
                for col in range(4):
                    self.table.item(row, col).setBackground(Qt.lightGray)

    def _set_item(self, row: int, col: int, text: str) -> None:
        item = QTableWidgetItem(text)
        self.table.setItem(row, col, item)

    def on_pick_file_for_slot(self, slot: str) -> None:
        if not self.h5_path().exists():
            QMessageBox.information(self, "Info", "Create the skeleton first (Init skeleton).")
            return

        src, _ = QFileDialog.getOpenFileName(self, f"Select file for slot {slot}", str(Path.cwd()))
        if not src:
            return

        try:
            write_bytes_to_slot(self.h5_path(), slot, Path(src))
        except Exception as e:
            QMessageBox.critical(self, "Write failed", str(e))
            return

        self.refresh_table()


def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1000, 360)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())