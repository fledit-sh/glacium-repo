# theme_demo.py
from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStyleFactory,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class Theme:
    name: str
    qss: str


def qss_dark(accent: str = "#6aa3ff") -> str:
    # Dark, engineering-ish, low-glare; uses Qt "dynamic properties" for accents.
    return f"""
/* -------- Base -------- */
* {{
    font-family: "Segoe UI";
    font-size: 10pt;
}}

QMainWindow {{
    background: #202225;
}}

QWidget {{
    color: #e6e6e6;
    background: #202225;
}}

QLabel#Muted {{
    color: #a8abb0;
}}

QWidget#Card {{
    background: #26282c;
    border: 1px solid #35383d;
    border-radius: 10px;
}}

QGroupBox {{
    border: 1px solid #35383d;
    border-radius: 10px;
    margin-top: 10px;
    padding: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #cfd2d6;
}}

/* -------- Inputs -------- */
QLineEdit, QSpinBox, QComboBox, QTextEdit {{
    background: #17191c;
    border: 1px solid #3a3d42;
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {accent};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
}}

QPushButton {{
    background: #2d3036;
    border: 1px solid #3a3d42;
    border-radius: 8px;
    padding: 6px 10px;
}}
QPushButton:hover {{
    background: #343843;
}}
QPushButton:pressed {{
    background: #2a2d33;
}}

QPushButton#Primary {{
    background: {accent};
    color: #0b0d10;
    border: 1px solid {accent};
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: {accent};
    opacity: 0.95;
}}
QPushButton#Primary:pressed {{
    background: {accent};
    opacity: 0.9;
}}

/* -------- Slider -------- */
QSlider::groove:horizontal {{
    height: 6px;
    background: #2b2f35;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: {accent};
}}

/* -------- Tabs -------- */
QTabWidget::pane {{
    border: 1px solid #35383d;
    border-radius: 10px;
    top: -1px;
}}
QTabBar::tab {{
    background: #26282c;
    border: 1px solid #35383d;
    border-bottom: none;
    padding: 8px 12px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    background: #202225;
    border-color: {accent};
}}
QTabBar::tab:hover {{
    background: #2b2e33;
}}

/* -------- Table -------- */
QTableWidget {{
    background: #17191c;
    border: 1px solid #35383d;
    border-radius: 10px;
    gridline-color: #2b2f35;
}}
QHeaderView::section {{
    background: #26282c;
    border: none;
    padding: 6px 8px;
    color: #cfd2d6;
}}
QTableWidget::item:selected {{
    background: {accent};
    color: #0b0d10;
}}

/* -------- ToolBar -------- */
QToolBar {{
    background: #26282c;
    border: 1px solid #35383d;
    spacing: 6px;
    padding: 6px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 8px;
}}
QToolButton:hover {{
    background: #2f3238;
    border-color: #3a3d42;
}}

/* -------- Dock -------- */
QDockWidget::title {{
    background: #26282c;
    padding: 6px 10px;
    border-bottom: 1px solid #35383d;
}}

/* -------- Scrollbars -------- */
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #3a3d42;
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #4a4e55;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


def qss_light(accent: str = "#2f6df6") -> str:
    return f"""
* {{
    font-family: "Segoe UI";
    font-size: 10pt;
}}

QMainWindow {{
    background: #f6f7f9;
}}

QWidget {{
    color: #1a1c1f;
    background: #f6f7f9;
}}

QLabel#Muted {{
    color: #5f6670;
}}

QWidget#Card {{
    background: #ffffff;
    border: 1px solid #d9dde3;
    border-radius: 10px;
}}

QGroupBox {{
    border: 1px solid #d9dde3;
    border-radius: 10px;
    margin-top: 10px;
    padding: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #30343a;
}}

QLineEdit, QSpinBox, QComboBox, QTextEdit {{
    background: #ffffff;
    border: 1px solid #cfd6df;
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {{
    border: 1px solid {accent};
}}

QPushButton {{
    background: #ffffff;
    border: 1px solid #cfd6df;
    border-radius: 8px;
    padding: 6px 10px;
}}
QPushButton:hover {{
    background: #eef2f8;
}}
QPushButton:pressed {{
    background: #e6ebf4;
}}

QPushButton#Primary {{
    background: {accent};
    color: #ffffff;
    border: 1px solid {accent};
    font-weight: 600;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: #dfe4ec;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background: {accent};
}}

QTabWidget::pane {{
    border: 1px solid #d9dde3;
    border-radius: 10px;
    top: -1px;
}}
QTabBar::tab {{
    background: #ffffff;
    border: 1px solid #d9dde3;
    border-bottom: none;
    padding: 8px 12px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 4px;
}}
QTabBar::tab:selected {{
    background: #f6f7f9;
    border-color: {accent};
}}
QTabBar::tab:hover {{
    background: #eef2f8;
}}

QTableWidget {{
    background: #ffffff;
    border: 1px solid #d9dde3;
    border-radius: 10px;
    gridline-color: #eef2f8;
}}
QHeaderView::section {{
    background: #f0f2f6;
    border: none;
    padding: 6px 8px;
    color: #30343a;
}}
QTableWidget::item:selected {{
    background: {accent};
    color: #ffffff;
}}

QToolBar {{
    background: #ffffff;
    border: 1px solid #d9dde3;
    spacing: 6px;
    padding: 6px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px 8px;
}}
QToolButton:hover {{
    background: #eef2f8;
    border-color: #d9dde3;
}}

QDockWidget::title {{
    background: #ffffff;
    padding: 6px 10px;
    border-bottom: 1px solid #d9dde3;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #cfd6df;
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #b9c2cf;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


class ThemeManager:
    def __init__(self, app: QApplication):
        self._app = app
        self._accent = "#6aa3ff"
        self._themes: dict[str, Theme] = {
            "Dark": Theme("Dark", qss_dark(self._accent)),
            "Light": Theme("Light", qss_light("#2f6df6")),
        }

    def set_accent(self, hex_color: str) -> None:
        self._accent = hex_color
        # Rebuild dark theme with new accent
        self._themes["Dark"] = Theme("Dark", qss_dark(self._accent))

    def apply(self, name: str) -> None:
        theme = self._themes[name]
        self._app.setStyleSheet(theme.qss)


class MainWindow(QMainWindow):
    def __init__(self, tm: ThemeManager):
        super().__init__()
        self.tm = tm
        self.setWindowTitle("PySide6 Theme Demonstrator")
        self.resize(1100, 720)

        self._build_toolbar()
        self._build_ui()
        self._build_docks()

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        act_new = QAction("New", self)
        act_open = QAction("Open", self)
        act_save = QAction("Save", self)
        tb.addAction(act_new)
        tb.addAction(act_open)
        tb.addAction(act_save)

        tb.addSeparator()

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentTextChanged.connect(self.tm.apply)
        tb.addWidget(QLabel("Theme: "))
        tb.addWidget(self.theme_combo)

        tb.addSeparator()

        self.accent_combo = QComboBox()
        self.accent_combo.addItems(
            [
                "Blue (#6aa3ff)",
                "Cyan (#3dd6d0)",
                "Green (#62d26f)",
                "Orange (#ffb84d)",
                "Pink (#ff6bb5)",
            ]
        )
        self.accent_combo.currentTextChanged.connect(self._on_accent)
        tb.addWidget(QLabel("Accent: "))
        tb.addWidget(self.accent_combo)

    def _on_accent(self, text: str) -> None:
        # parse "(#xxxxxx)" at end
        start = text.find("(#")
        hex_color = text[start + 1 : text.find(")", start)]
        self.tm.set_accent(hex_color)
        if self.theme_combo.currentText() == "Dark":
            self.tm.apply("Dark")

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        header = QWidget()
        header.setObjectName("Card")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 10, 12, 10)
        hl.setSpacing(12)

        title = QLabel("glacium — UI sandbox")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        subtitle = QLabel("Theme/QSS demonstrator with typical widgets")
        subtitle.setObjectName("Muted")

        hl.addWidget(title)
        hl.addStretch(1)
        hl.addWidget(subtitle)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = self._build_left_panel()
        center = self._build_center_tabs()

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(header)
        root_layout.addWidget(splitter, 1)

        self.setCentralWidget(root)

    def _build_left_panel(self) -> QWidget:
        w = QWidget()
        w.setObjectName("Card")
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(10)

        box = QGroupBox("Controls")
        fl = QFormLayout(box)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        fl.setFormAlignment(Qt.AlignmentFlag.AlignTop)

        self.case_name = QLineEdit("Case_001")
        self.re_spin = QSpinBox()
        self.re_spin.setRange(1, 10_000_000)
        self.re_spin.setValue(1_700_000)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["Air", "Droplet (Drop3D)", "Ice (Ice3D)", "Coupled"])

        self.alpha = QSlider(Qt.Orientation.Horizontal)
        self.alpha.setRange(-10, 20)
        self.alpha.setValue(4)

        fl.addRow("Case:", self.case_name)
        fl.addRow("Re:", self.re_spin)
        fl.addRow("Model:", self.model_combo)
        fl.addRow("AoA [deg]:", self.alpha)

        l.addWidget(box)

        actions = QGroupBox("Actions")
        al = QVBoxLayout(actions)

        run_btn = QPushButton("Render artefacts")
        run_btn.setObjectName("Primary")

        validate_btn = QPushButton("Validate config")
        export_btn = QPushButton("Export…")

        al.addWidget(run_btn)
        al.addWidget(validate_btn)
        al.addWidget(export_btn)
        al.addStretch(1)

        l.addWidget(actions, 1)
        return w

    def _build_center_tabs(self) -> QWidget:
        tabs = QTabWidget()

        tabs.addTab(self._tab_table(), "Variables")
        tabs.addTab(self._tab_log(), "Log")
        tabs.addTab(self._tab_editor(), "YAML")

        return tabs

    def _tab_table(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        table = QTableWidget(8, 3)
        table.setHorizontalHeaderLabels(["Key", "Value", "Source"])
        rows = [
            ("FSP_GUI_PHYSICAL_MODEL", "Air", "GUI"),
            ("FSP_CHARAC_LENGTH", "0.431", "Config"),
            ("FSP_ALPHA", "4", "GUI"),
            ("FSP_REYNOLDS", "1.7e6", "Config"),
            ("DROP_MVD", "20e-6", "Config"),
            ("DROP_LWC", "0.4", "Config"),
            ("ICE_TYPE", "rime", "Config"),
            ("MESH_ID", "12", "Project"),
        ]
        for r, (k, v, s) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(k))
            table.setItem(r, 1, QTableWidgetItem(v))
            table.setItem(r, 2, QTableWidgetItem(s))
        table.resizeColumnsToContents()

        l.addWidget(table)
        return w

    def _tab_log(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        log = QTextEdit()
        log.setReadOnly(True)
        log.setPlainText(
            "[info] Project created\n"
            "[info] Loaded grid: grid_012\n"
            "[warn] Remesh grids found: 3 (needs post-processing)\n"
            "[info] Rendering: .par .drop .ice\n"
            "[ok] Done\n"
        )
        l.addWidget(log)
        return w

    def _tab_editor(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(10, 10, 10, 10)

        editor = QTextEdit()
        editor.setPlainText(
            "project:\n"
            "  name: Case_001\n"
            "grid:\n"
            "  id: 12\n"
            "model:\n"
            "  physical: Air\n"
            "  alpha_deg: 4\n"
            "droplet:\n"
            "  mvd_m: 2.0e-5\n"
            "  lwc: 0.4\n"
        )
        l.addWidget(editor)
        return w

    def _build_docks(self) -> None:
        # Right dock: status / inspector
        dock = QDockWidget("Inspector", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)

        content = QWidget()
        content.setObjectName("Card")
        l = QVBoxLayout(content)
        l.setContentsMargins(12, 12, 12, 12)

        l.addWidget(QLabel("Selected variable:"))
        sel = QLineEdit("FSP_GUI_PHYSICAL_MODEL")
        l.addWidget(sel)

        l.addSpacing(6)
        hint = QLabel("Tip: use QSS for colors/spacing,\nPalette for global tone,\nFusion for consistent base.")
        hint.setObjectName("Muted")
        l.addWidget(hint)
        l.addStretch(1)

        dock.setWidget(content)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)


def main() -> int:
    app = QApplication(sys.argv)

    # Robust baseline style (then we override visuals via QSS)
    app.setStyle(QStyleFactory.create("Fusion"))

    tm = ThemeManager(app)
    tm.apply("Dark")

    win = MainWindow(tm)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())