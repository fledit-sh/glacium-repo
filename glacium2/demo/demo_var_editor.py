from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


# ----------------------------
# Core model
# ----------------------------

@dataclass(frozen=True)
class SchemaVar:
    stype: str = ""
    dtype: str = ""
    n: int | None = None
    default: Any = None
    description: str = ""
    vmin: int | float | None = None
    vmax: int | float | None = None
    quoted: bool = False
    options: tuple[Any, ...] | None = None


DEFAULT_SCHEMA_VAR = SchemaVar(dtype="str")  # minimal baseline


def _var_to_yaml_dict(v: SchemaVar) -> dict[str, Any]:
    d = asdict(v)
    # always include all fields; normalize options for YAML
    if d.get("options") is None:
        d["options"] = None
    else:
        d["options"] = list(d["options"])
    return d


def _var_from_yaml_dict(d: dict[str, Any]) -> SchemaVar:
    merged = {**asdict(DEFAULT_SCHEMA_VAR), **d}

    # normalize options to tuple/None
    opts = merged.get("options")
    if opts is None:
        merged["options"] = None
    elif isinstance(opts, (list, tuple)):
        merged["options"] = tuple(opts)
    else:
        merged["options"] = (opts,)

    return SchemaVar(**merged)


# ----------------------------
# YAML IO
# ----------------------------

class YamlRepo:
    def load_yaml(self, path: Path) -> Any:
        if not path.exists():
            return None
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def dump_yaml(self, path: Path, data: Any) -> None:
        path.write_text(
            yaml.safe_dump(data, sort_keys=True, allow_unicode=True),
            encoding="utf-8",
        )


class SchemaWorkspace:
    """
    NEW (full) format (preferred):
      variables.yaml: {"version": 1, "variables": {VAR: {all fields ...}, ...}}
      schema.yaml:    {"version": 1, "variables": {VAR: {all fields ...}, ...}}  # same shape

    Backward compatible loaders:
      variables.yaml: {"variables": [VAR, VAR, ...]}
      schema.yaml:    {"version": 1, "overrides": {VAR: {patch fields...}}}
    """
    def __init__(self, root: Path):
        self.root = root
        self.repo = YamlRepo()

        self.variables_path = root / "variables.yaml"
        self.schema_path = root / "schema.yaml"
        self.config_path = root / "config.yaml"

        # full variable definitions
        self.vars: dict[str, SchemaVar] = {}

    @property
    def inventory(self) -> list[str]:
        return sorted(self.vars.keys())

    def load(self) -> None:
        inv = self.repo.load_yaml(self.variables_path)
        sch = self.repo.load_yaml(self.schema_path)

        # 1) try new full variables.yaml
        full_vars: dict[str, SchemaVar] = {}

        if isinstance(inv, dict) and isinstance(inv.get("variables"), dict):
            for k, vd in inv["variables"].items():
                if isinstance(vd, dict):
                    full_vars[str(k)] = _var_from_yaml_dict(vd)
                else:
                    full_vars[str(k)] = DEFAULT_SCHEMA_VAR

        # 2) if variables.yaml is old inventory list, seed with DEFAULT_SCHEMA_VAR
        if not full_vars:
            if isinstance(inv, dict) and isinstance(inv.get("variables"), list):
                for k in inv["variables"]:
                    full_vars[str(k)] = DEFAULT_SCHEMA_VAR

        # 3) schema.yaml new full format (can override variables.yaml if present)
        if isinstance(sch, dict) and isinstance(sch.get("variables"), dict):
            for k, vd in sch["variables"].items():
                if isinstance(vd, dict):
                    full_vars[str(k)] = _var_from_yaml_dict(vd)
                else:
                    full_vars[str(k)] = DEFAULT_SCHEMA_VAR

        # 4) schema.yaml old patch format: apply overrides onto whatever we have
        if isinstance(sch, dict) and isinstance(sch.get("overrides"), dict):
            overrides = sch["overrides"]
            for k, patch in overrides.items():
                key = str(k)
                base = full_vars.get(key, DEFAULT_SCHEMA_VAR)
                if isinstance(patch, dict):
                    merged = {**_var_to_yaml_dict(base), **patch}
                    # merged contains "options" list maybe
                    full_vars[key] = _var_from_yaml_dict(merged)
                else:
                    full_vars[key] = base

        self.vars = dict(sorted(full_vars.items(), key=lambda kv: kv[0]))

    def save_variables_full(self) -> None:
        payload = {
            "version": 1,
            "variables": {k: _var_to_yaml_dict(v) for k, v in sorted(self.vars.items())},
        }
        self.repo.dump_yaml(self.variables_path, payload)

    def save_schema_full(self) -> None:
        # same shape, separate file for your pipeline expectations
        payload = {
            "version": 1,
            "variables": {k: _var_to_yaml_dict(v) for k, v in sorted(self.vars.items())},
        }
        self.repo.dump_yaml(self.schema_path, payload)

    def resolved_var(self, key: str) -> SchemaVar:
        return self.vars.get(key, DEFAULT_SCHEMA_VAR)

    def set_var(self, key: str, var: SchemaVar) -> None:
        self.vars[str(key)] = var

    def remove_key(self, key: str) -> None:
        self.vars.pop(key, None)

    def rename_key(self, old: str, new: str, config: dict[str, Any] | None = None) -> None:
        old = old.strip()
        new = new.strip()
        if not old or not new:
            return
        if old == new:
            return
        if new in self.vars:
            raise ValueError(f"Key already exists: {new}")
        if old not in self.vars:
            # if missing, still allow renaming inventory-like key
            self.vars[old] = DEFAULT_SCHEMA_VAR
        self.vars[new] = self.vars.pop(old)

        if config is not None and old in config:
            config[new] = config.pop(old)

    def generate_config(self, existing: dict[str, Any] | None = None, mode: str = "defaults") -> dict[str, Any]:
        """
        mode:
          - "defaults": output ALL keys; value = existing if set else schema default
          - "empty": output ALL keys; value = null
        """
        existing = existing or {}
        out: dict[str, Any] = {}
        for k in self.inventory:
            if mode == "empty":
                out[k] = None
                continue
            if k in existing and existing[k] is not None:
                out[k] = existing[k]
                continue
            sv = self.resolved_var(k)
            out[k] = sv.default
        return out

    def load_config(self) -> dict[str, Any]:
        cfg = self.repo.load_yaml(self.config_path)
        return cfg if isinstance(cfg, dict) else {}

    def save_config(self, cfg: dict[str, Any]) -> None:
        self.repo.dump_yaml(self.config_path, cfg)


# ----------------------------
# Helpers
# ----------------------------

def _safe_float(x: str) -> float | None:
    s = x.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _safe_int(x: str) -> int | None:
    s = x.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _parse_default(dtype: str, text: str, quoted: bool) -> Any:
    t = text.strip()
    if t == "":
        return None
    if dtype == "bool":
        low = t.lower()
        if low in ("true", "1", "yes", "y", "on"):
            return True
        if low in ("false", "0", "no", "n", "off"):
            return False
        return None
    if dtype == "int":
        return _safe_int(t)
    if dtype == "float":
        return _safe_float(t)
    return t


def _default_to_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


# ----------------------------
# UI Widgets (Schema editor)
# ----------------------------

class SchemaEditorPane(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("SchemaVar editor")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        form_box = QGroupBox("Fields")
        form = QFormLayout(form_box)

        self.ed_key = QLineEdit()
        self.ed_key.setPlaceholderText("Variable name (editable)")

        self.cb_dtype = QComboBox()
        self.cb_dtype.addItems(["str", "int", "float", "bool"])
        self.cb_stype = QComboBox()
        self.cb_stype.addItems(["", "enum", "path", "vector"])

        self.ed_n = QSpinBox()
        self.ed_n.setRange(0, 10_000)
        self.ed_n.setSpecialValueText("")  # treat 0 as unset

        self.ed_default = QLineEdit()
        self.ed_desc = QLineEdit()

        self.ed_vmin = QLineEdit()
        self.ed_vmax = QLineEdit()

        self.cb_quoted = QCheckBox("quoted")

        self.ed_options = QPlainTextEdit()
        self.ed_options.setPlaceholderText("Enum options, one per line")

        form.addRow("key", self.ed_key)
        form.addRow("dtype", self.cb_dtype)
        form.addRow("stype", self.cb_stype)
        form.addRow("n", self.ed_n)
        form.addRow("default", self.ed_default)
        form.addRow("description", self.ed_desc)
        form.addRow("vmin", self.ed_vmin)
        form.addRow("vmax", self.ed_vmax)
        form.addRow("", self.cb_quoted)
        form.addRow("options", self.ed_options)

        layout.addWidget(form_box)

        self.lbl_hint = QLabel("")
        self.lbl_hint.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_hint)

        layout.addStretch(1)

        self.cb_stype.currentTextChanged.connect(self._refresh_enabled)
        self.cb_dtype.currentTextChanged.connect(self._refresh_enabled)
        self._refresh_enabled()

    def _refresh_enabled(self) -> None:
        stype = self.cb_stype.currentText()
        dtype = self.cb_dtype.currentText()

        is_enum = (stype == "enum")
        is_vector = (stype == "vector")

        self.ed_options.setEnabled(is_enum)
        self.ed_n.setEnabled(is_vector)

        numeric = dtype in ("int", "float")
        self.ed_vmin.setEnabled(numeric)
        self.ed_vmax.setEnabled(numeric)

        if is_enum:
            self.lbl_hint.setText("Enum: dtype i.d.R. 'str' und options müssen gesetzt sein.")
        elif is_vector:
            self.lbl_hint.setText("Vector: n setzen (default kann null bleiben).")
        else:
            self.lbl_hint.setText("")

    def set_var(self, key: str, var: SchemaVar) -> None:
        self.ed_key.setText(key)
        self.cb_dtype.setCurrentText(var.dtype or "str")
        self.cb_stype.setCurrentText(var.stype or "")

        self.ed_n.setValue(var.n or 0)
        self.ed_default.setText(_default_to_text(var.default))
        self.ed_desc.setText(var.description or "")

        self.ed_vmin.setText("" if var.vmin is None else str(var.vmin))
        self.ed_vmax.setText("" if var.vmax is None else str(var.vmax))

        self.cb_quoted.setChecked(bool(var.quoted))

        if var.options:
            self.ed_options.setPlainText("\n".join(str(o) for o in var.options))
        else:
            self.ed_options.setPlainText("")

        self._refresh_enabled()

    def get_key(self) -> str:
        return self.ed_key.text().strip()

    def get_var(self) -> SchemaVar:
        dtype = self.cb_dtype.currentText().strip()
        stype = self.cb_stype.currentText().strip()

        n = self.ed_n.value()
        n_out = None
        if stype == "vector":
            n_out = n if n > 0 else None

        quoted = self.cb_quoted.isChecked()

        default = _parse_default(dtype=dtype, text=self.ed_default.text(), quoted=quoted)
        desc = self.ed_desc.text()

        vmin = _safe_float(self.ed_vmin.text()) if dtype in ("int", "float") else None
        vmax = _safe_float(self.ed_vmax.text()) if dtype in ("int", "float") else None
        if dtype == "int":
            vmin = int(vmin) if vmin is not None else None
            vmax = int(vmax) if vmax is not None else None

        options: tuple[Any, ...] | None = None
        if stype == "enum":
            lines = [ln.strip() for ln in self.ed_options.toPlainText().splitlines()]
            vals = [ln for ln in lines if ln]
            options = tuple(vals) if vals else None

        return SchemaVar(
            stype=stype,
            dtype=dtype,
            n=n_out,
            default=default,
            description=desc,
            vmin=vmin,
            vmax=vmax,
            quoted=quoted,
            options=options,
        )


# ----------------------------
# UI Widgets (Config editor)
# ----------------------------

class ConfigEditorPane(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Config editor (value)")
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        title.setFont(f)
        layout.addWidget(title)

        form_box = QGroupBox("Value")
        form = QFormLayout(form_box)

        self.ed_key = QLineEdit()
        self.ed_key.setReadOnly(True)

        self.lbl_dtype = QLabel("")
        self.lbl_stype = QLabel("")

        self.widget_container = QWidget()
        self.widget_layout = QHBoxLayout(self.widget_container)
        self.widget_layout.setContentsMargins(0, 0, 0, 0)

        self.value_widget: QWidget | None = None

        form.addRow("key", self.ed_key)
        form.addRow("dtype", self.lbl_dtype)
        form.addRow("stype", self.lbl_stype)
        form.addRow("value", self.widget_container)

        layout.addWidget(form_box)
        layout.addStretch(1)

    def set_entry(self, key: str, sv: SchemaVar, value: Any) -> None:
        self.ed_key.setText(key)
        self.lbl_dtype.setText(sv.dtype or "")
        self.lbl_stype.setText(sv.stype or "")

        if self.value_widget is not None:
            self.value_widget.setParent(None)
            self.value_widget = None

        w = self._make_value_widget(sv, value)
        self.value_widget = w
        self.widget_layout.addWidget(w)

    def _make_value_widget(self, sv: SchemaVar, value: Any) -> QWidget:
        # enum -> combobox
        if sv.stype == "enum" and sv.options:
            cb = QComboBox()
            cb.addItems([str(x) for x in sv.options])
            if value is None and sv.default is not None:
                value = sv.default
            if value is not None:
                idx = cb.findText(str(value))
                if idx >= 0:
                    cb.setCurrentIndex(idx)
            cb.setProperty("_editor_kind", "enum")
            return cb

        # bool -> checkbox
        if sv.dtype == "bool":
            c = QCheckBox("enabled")
            if value is None and isinstance(sv.default, bool):
                value = sv.default
            c.setChecked(bool(value))
            c.setProperty("_editor_kind", "bool")
            return c

        # numeric -> line edit (coerce on save)
        if sv.dtype in ("int", "float"):
            le = QLineEdit()
            if value is None and sv.default is not None:
                value = sv.default
            le.setText("" if value is None else str(value))
            le.setProperty("_editor_kind", sv.dtype)
            return le

        # string/path -> line edit
        le = QLineEdit()
        if value is None and sv.default is not None:
            value = sv.default
        le.setText("" if value is None else str(value))
        le.setProperty("_editor_kind", "str")
        return le

    def get_value(self, sv: SchemaVar) -> Any:
        w = self.value_widget
        if w is None:
            return None

        kind = w.property("_editor_kind")

        if kind == "enum":
            assert isinstance(w, QComboBox)
            return w.currentText()

        if kind == "bool":
            assert isinstance(w, QCheckBox)
            return bool(w.isChecked())

        if kind == "int":
            assert isinstance(w, QLineEdit)
            t = w.text().strip()
            return None if t == "" else _safe_int(t)

        if kind == "float":
            assert isinstance(w, QLineEdit)
            t = w.text().strip()
            return None if t == "" else _safe_float(t)

        assert isinstance(w, QLineEdit)
        t = w.text()
        return None if t.strip() == "" else t


# ----------------------------
# Main window
# ----------------------------

class MainWindow(QMainWindow):
    def __init__(self, workspace: SchemaWorkspace):
        super().__init__()
        self.ws = workspace
        self.ws.load()

        self.setWindowTitle("Schema + Config GUI (PySide6)")
        self.resize(1200, 800)

        root = QWidget()
        root_layout = QVBoxLayout(root)

        # top buttons
        top = QHBoxLayout()
        self.btn_open_root = QPushButton("Open folder…")
        self.lbl_root = QLabel(str(self.ws.root))
        self.lbl_root.setStyleSheet("color: #666;")

        self.btn_reload = QPushButton("Reload")
        self.btn_save_schema = QPushButton("Save schema.yaml (full)")
        self.btn_save_vars = QPushButton("Save variables.yaml (full)")

        top.addWidget(self.btn_open_root)
        top.addWidget(self.lbl_root, stretch=1)
        top.addWidget(self.btn_reload)
        top.addWidget(self.btn_save_vars)
        top.addWidget(self.btn_save_schema)
        root_layout.addLayout(top)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs, stretch=1)

        # --- Schema tab
        self.schema_split = QSplitter(Qt.Horizontal)
        self.schema_list = QListWidget()
        self.schema_editor = SchemaEditorPane()

        self.schema_split.addWidget(self.schema_list)
        self.schema_split.addWidget(self.schema_editor)
        self.schema_split.setStretchFactor(0, 1)
        self.schema_split.setStretchFactor(1, 3)

        schema_tab = QWidget()
        schema_layout = QVBoxLayout(schema_tab)
        schema_layout.addWidget(self.schema_split)

        schema_btns = QHBoxLayout()
        self.btn_apply_var = QPushButton("Apply (store full)")
        self.btn_add_key = QPushButton("Add key…")
        self.btn_remove_key = QPushButton("Remove key")
        schema_btns.addWidget(self.btn_apply_var)
        schema_btns.addStretch(1)
        schema_btns.addWidget(self.btn_add_key)
        schema_btns.addWidget(self.btn_remove_key)
        schema_layout.addLayout(schema_btns)

        self.tabs.addTab(schema_tab, "Schema")

        # --- Config tab
        self.config_split = QSplitter(Qt.Horizontal)
        self.config_list = QListWidget()
        self.config_editor = ConfigEditorPane()

        self.config_split.addWidget(self.config_list)
        self.config_split.addWidget(self.config_editor)
        self.config_split.setStretchFactor(0, 1)
        self.config_split.setStretchFactor(1, 3)

        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)
        config_layout.addWidget(self.config_split)

        config_btns = QHBoxLayout()
        self.btn_gen_defaults = QPushButton("Generate config (fill defaults)")
        self.btn_gen_empty = QPushButton("Generate config (empty)")
        self.btn_load_config = QPushButton("Load config.yaml")
        self.btn_save_config = QPushButton("Save config.yaml")
        self.btn_apply_value = QPushButton("Apply value")
        config_btns.addWidget(self.btn_gen_defaults)
        config_btns.addWidget(self.btn_gen_empty)
        config_btns.addStretch(1)
        config_btns.addWidget(self.btn_load_config)
        config_btns.addWidget(self.btn_save_config)
        config_btns.addWidget(self.btn_apply_value)
        config_layout.addLayout(config_btns)

        self.tabs.addTab(config_tab, "Config")

        self.setCentralWidget(root)

        # state
        self._current_key: str | None = None
        self._config: dict[str, Any] = {}

        # wire
        self.btn_reload.clicked.connect(self.reload_all)
        self.btn_save_schema.clicked.connect(self.save_schema_full)
        self.btn_save_vars.clicked.connect(self.save_vars_full)
        self.btn_apply_var.clicked.connect(self.apply_schema_editor_store_full)
        self.btn_add_key.clicked.connect(self.add_key)
        self.btn_remove_key.clicked.connect(self.remove_key)

        self.schema_list.currentItemChanged.connect(self.on_schema_select)

        self.btn_gen_defaults.clicked.connect(lambda: self.generate_config("defaults"))
        self.btn_gen_empty.clicked.connect(lambda: self.generate_config("empty"))
        self.btn_load_config.clicked.connect(self.load_config)
        self.btn_save_config.clicked.connect(self.save_config)
        self.btn_apply_value.clicked.connect(self.apply_config_value)
        self.config_list.currentItemChanged.connect(self.on_config_select)

        self.btn_open_root.clicked.connect(self.open_folder)

        self.populate_lists()
        self.load_config()  # try load existing config.yaml

    def open_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select workspace folder", str(self.ws.root))
        if not d:
            return
        self.ws.root = Path(d)
        self.ws.variables_path = self.ws.root / "variables.yaml"
        self.ws.schema_path = self.ws.root / "schema.yaml"
        self.ws.config_path = self.ws.root / "config.yaml"
        self.lbl_root.setText(str(self.ws.root))
        self.reload_all()

    def reload_all(self) -> None:
        self.ws.load()
        self.populate_lists()
        self.load_config()

    def populate_lists(self) -> None:
        self.schema_list.clear()
        self.config_list.clear()

        for k in self.ws.inventory:
            it = QListWidgetItem(k)
            it.setData(Qt.UserRole, k)
            self.schema_list.addItem(it)

            it2 = QListWidgetItem(k)
            it2.setData(Qt.UserRole, k)
            self.config_list.addItem(it2)

        if self.ws.inventory:
            self.schema_list.setCurrentRow(0)
            self.config_list.setCurrentRow(0)

    def _item_key(self, item: QListWidgetItem | None) -> str | None:
        if item is None:
            return None
        k = item.data(Qt.UserRole)
        return str(k) if k else None

    # --- schema tab actions

    def on_schema_select(self, cur: QListWidgetItem | None, _prev: QListWidgetItem | None) -> None:
        k = self._item_key(cur)
        if not k:
            return
        self._current_key = k
        sv = self.ws.resolved_var(k)
        self.schema_editor.set_var(k, sv)

    def apply_schema_editor_store_full(self) -> None:
        old_key = self._current_key
        if not old_key:
            return

        new_key = self.schema_editor.get_key()
        if not new_key:
            QMessageBox.warning(self, "Invalid", "Key must not be empty.")
            return

        var = self.schema_editor.get_var()

        # consistency checks
        if var.stype == "enum" and (not var.options):
            QMessageBox.warning(self, "Invalid", "stype=enum requires options.")
            return
        if var.stype == "enum" and var.dtype != "str":
            QMessageBox.warning(self, "Invalid", "Enum should use dtype=str.")
            return
        if var.stype == "vector" and (var.n is None or var.n <= 0):
            QMessageBox.warning(self, "Invalid", "stype=vector requires n > 0.")
            return
        if var.dtype in ("int", "float"):
            if var.vmin is not None and var.vmax is not None and var.vmin > var.vmax:
                QMessageBox.warning(self, "Invalid", "vmin must be <= vmax.")
                return

        # rename if needed (also migrates config key)
        try:
            if old_key != new_key:
                self.ws.rename_key(old=old_key, new=new_key, config=self._config)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid", str(e))
            return

        self.ws.set_var(new_key, var)
        self._current_key = new_key

        self.populate_lists()
        self._select_key_in_list(self.schema_list, new_key)
        self._select_key_in_list(self.config_list, new_key)

    def add_key(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        k, ok = QInputDialog.getText(self, "Add key", "Variable key:")
        if not ok:
            return
        key = k.strip()
        if not key:
            return
        if key not in self.ws.vars:
            self.ws.vars[key] = DEFAULT_SCHEMA_VAR
        self.populate_lists()
        self._select_key_in_list(self.schema_list, key)

    def remove_key(self) -> None:
        k = self._current_key
        if not k:
            return
        self.ws.remove_key(k)
        self._config.pop(k, None)
        self.populate_lists()

    def save_schema_full(self) -> None:
        self.ws.save_schema_full()
        QMessageBox.information(self, "Saved", f"Saved: {self.ws.schema_path}")

    def save_vars_full(self) -> None:
        self.ws.save_variables_full()
        QMessageBox.information(self, "Saved", f"Saved: {self.ws.variables_path}")

    def _select_key_in_list(self, lw: QListWidget, key: str) -> None:
        for i in range(lw.count()):
            it = lw.item(i)
            if self._item_key(it) == key:
                lw.setCurrentRow(i)
                break

    # --- config tab actions

    def load_config(self) -> None:
        self._config = self.ws.load_config()
        if self.ws.inventory:
            self._select_key_in_list(self.config_list, self.ws.inventory[0])

    def save_config(self) -> None:
        # save with defaults filled (so "unset" means default in file)
        full = self.ws.generate_config(existing=self._config, mode="defaults")
        self.ws.save_config(full)
        QMessageBox.information(self, "Saved", f"Saved: {self.ws.config_path}")

    def generate_config(self, mode: str) -> None:
        self._config = self.ws.generate_config(existing=self._config, mode=mode)
        QMessageBox.information(self, "Generated", f"Generated config ({mode}).")
        cur = self.config_list.currentItem()
        self.on_config_select(cur, None)

    def on_config_select(self, cur: QListWidgetItem | None, _prev: QListWidgetItem | None) -> None:
        k = self._item_key(cur)
        if not k:
            return
        sv = self.ws.resolved_var(k)
        val = self._config.get(k, None)
        self.config_editor.set_entry(k, sv, val)

    def apply_config_value(self) -> None:
        cur = self.config_list.currentItem()
        k = self._item_key(cur)
        if not k:
            return
        sv = self.ws.resolved_var(k)
        v = self.config_editor.get_value(sv)

        # coercion/validation
        if sv.dtype == "int" and v is not None and not isinstance(v, int):
            QMessageBox.warning(self, "Invalid", "Expected int.")
            return
        if sv.dtype == "float" and v is not None and not isinstance(v, (int, float)):
            QMessageBox.warning(self, "Invalid", "Expected float.")
            return
        if sv.stype == "enum" and sv.options and v is not None and str(v) not in set(map(str, sv.options)):
            QMessageBox.warning(self, "Invalid", "Value not in enum options.")
            return
        if sv.dtype in ("int", "float") and v is not None:
            f = float(v)
            if sv.vmin is not None and f < float(sv.vmin):
                QMessageBox.warning(self, "Invalid", f"value < vmin ({sv.vmin})")
                return
            if sv.vmax is not None and f > float(sv.vmax):
                QMessageBox.warning(self, "Invalid", f"value > vmax ({sv.vmax})")
                return

        # store "unset" as None in UI state; file save fills defaults anyway
        self._config[k] = v


def main() -> None:
    import sys

    root = Path.cwd()
    ws = SchemaWorkspace(root=root)

    app = QApplication(sys.argv)
    win = MainWindow(ws)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
