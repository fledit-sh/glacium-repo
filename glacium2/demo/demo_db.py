import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional, List, Dict, Tuple

import streamlit as st
import yaml


DB_PATH = r"C:\Users\NoelErnstingLuz\Desktop\glacium.db"
SCHEMA_SQL_PATH = r"C:\Users\NoelErnstingLuz\Desktop\asdf"  # <-- falls asdf ein Ordner ist


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def exec_script(conn: sqlite3.Connection, path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()


def scalar(q: str, params: tuple = ()) -> Any:
    with db() as conn:
        row = conn.execute(q, params).fetchone()
        return None if row is None else list(row)[0]


def rows(q: str, params: tuple = ()) -> List[sqlite3.Row]:
    with db() as conn:
        return conn.execute(q, params).fetchall()


def execute(q: str, params: tuple = ()) -> int:
    with db() as conn:
        cur = conn.execute(q, params)
        conn.commit()
        return cur.lastrowid


def ensure_schema() -> None:
    if not os.path.exists(DB_PATH):
        open(DB_PATH, "wb").close()
    with db() as conn:
        exec_script(conn, SCHEMA_SQL_PATH)


def seed_demo_data_if_empty() -> None:
    if scalar("SELECT COUNT(*) FROM variable_types") != 0:
        return

    # variable types
    vt_int   = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("INT", "scalar", "Integer"))
    vt_float = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("FLOAT", "scalar", "Float"))
    vt_str   = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("STRING", "scalar", "String"))
    vt_bool  = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("BOOL", "scalar", "Boolean"))
    vt_enum  = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("ENUM", "enum", "Enum"))
    vt_list  = execute("INSERT INTO variable_types(dogtag, base_kind, description) VALUES(?,?,?)", ("LIST", "list", "List"))

    # gui schemes
    gs_default = execute(
        "INSERT INTO gui_schemes(dogtag, enabled, hidden, quoted, readonly, widget, help_text) VALUES(?,?,?,?,?,?,?)",
        ("DEFAULT", 1, 0, 0, 0, "input", "Default widget"),
    )
    gs_slider = execute(
        "INSERT INTO gui_schemes(dogtag, enabled, hidden, quoted, readonly, widget, help_text) VALUES(?,?,?,?,?,?,?)",
        ("SLIDER", 1, 0, 0, 0, "slider", "Slider for numeric ranges"),
    )
    gs_dropdown = execute(
        "INSERT INTO gui_schemes(dogtag, enabled, hidden, quoted, readonly, widget, help_text) VALUES(?,?,?,?,?,?,?)",
        ("DROPDOWN", 1, 0, 0, 0, "dropdown", "Dropdown for enums"),
    )
    gs_hidden = execute(
        "INSERT INTO gui_schemes(dogtag, enabled, hidden, quoted, readonly, widget, help_text) VALUES(?,?,?,?,?,?,?)",
        ("HIDDEN_ADV", 1, 1, 0, 0, "input", "Hidden advanced option"),
    )

    # file schema
    file_drop = execute(
        "INSERT INTO files(dogtag, name, kind, description) VALUES(?,?,?,?)",
        ("CONFIG_DROP", "drop3d.yaml", "yaml", "Drop3D example schema"),
    )

    # enum
    enum_mode = execute(
        "INSERT INTO enums(dogtag, name, description) VALUES(?,?,?)",
        ("BC_COLOR_MODE", "Boundary color mode", "Example enum"),
    )
    ev_rgb = execute("INSERT INTO enum_values(enum_id, code, label, sort_order) VALUES(?,?,?,?)", (enum_mode, "RGB", "RGB", 1))
    ev_gray = execute("INSERT INTO enum_values(enum_id, code, label, sort_order) VALUES(?,?,?,?)", (enum_mode, "GRAY", "Grayscale", 2))

    # variables (mix types)
    v_dt = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, category, description, rule_name) VALUES(?,?,?,?,?,?,?)",
        ("CONFIG_DROP::TIME_STEP", "TIME_STEP", file_drop, vt_float, "numerics", "Time step size [s]", "positive"),
    )
    execute(
        "INSERT INTO var_constraints(variable_id, min_num, max_num, default_float) VALUES(?,?,?,?)",
        (v_dt, 1e-6, 1.0, 0.01),
    )
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_dt, gs_slider))

    v_iter = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, category, description) VALUES(?,?,?,?,?,?)",
        ("CONFIG_DROP::MAX_ITER", "MAX_ITER", file_drop, vt_int, "numerics", "Max iterations"),
    )
    execute("INSERT INTO var_constraints(variable_id, min_num, max_num, default_int) VALUES(?,?,?,?)", (v_iter, 1, 100000, 200))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_iter, gs_slider))

    v_out = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, category, description) VALUES(?,?,?,?,?,?)",
        ("CONFIG_DROP::OUTPUT_DIR", "OUTPUT_DIR", file_drop, vt_str, "io", "Output directory"),
    )
    execute("INSERT INTO var_constraints(variable_id, min_len, max_len, default_str) VALUES(?,?,?,?)", (v_out, 1, 300, "./out"))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_out, gs_default))

    v_enable = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, category, description) VALUES(?,?,?,?,?,?)",
        ("CONFIG_DROP::ENABLE_LOGGING", "ENABLE_LOGGING", file_drop, vt_bool, "io", "Enable logging"),
    )
    execute("INSERT INTO var_constraints(variable_id, default_bool) VALUES(?,?)", (v_enable, 1))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_enable, gs_default))

    v_mode = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, enum_id, category, description) VALUES(?,?,?,?,?,?,?)",
        ("CONFIG_DROP::BC_COLOR_MODE", "BC_COLOR_MODE", file_drop, vt_enum, enum_mode, "bc", "Color mode"),
    )
    execute("INSERT INTO var_constraints(variable_id, default_enum_value_id) VALUES(?,?)", (v_mode, ev_rgb))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_mode, gs_dropdown))

    # list-of-int example (like your 0..255 color array)
    v_colors = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, element_type_id, category, description) VALUES(?,?,?,?,?,?,?)",
        ("CONFIG_DROP::FSP_GUI_ITYP_BC_COLORS_R", "FSP_GUI_ITYP_BC_COLORS_R", file_drop, vt_list, vt_int, "bc", "List of 0..255 ints"),
    )
    execute("INSERT INTO var_constraints(variable_id, min_num, max_num, min_len, max_len, default_int) VALUES(?,?,?,?,?,?)",
            (v_colors, 0, 255, 1, 16, None))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_colors, gs_default))

    # hidden advanced variable
    v_adv = execute(
        "INSERT INTO variables(dogtag, name, file_id, type_id, category, description) VALUES(?,?,?,?,?,?)",
        ("CONFIG_DROP::ADV_INTERNAL", "ADV_INTERNAL", file_drop, vt_str, "advanced", "Hidden advanced option"),
    )
    execute("INSERT INTO var_constraints(variable_id, default_str) VALUES(?,?)", (v_adv, "secret"))
    execute("INSERT INTO variable_gui(variable_id, gui_scheme_id) VALUES(?,?)", (v_adv, gs_hidden))


def list_files() -> List[sqlite3.Row]:
    return rows("SELECT * FROM files ORDER BY dogtag")


def list_configs(file_id: int) -> List[sqlite3.Row]:
    return rows("SELECT * FROM configs WHERE file_id=? ORDER BY created_at DESC", (file_id,))


def get_latest_version_id(config_id: int) -> Optional[int]:
    return scalar(
        "SELECT id FROM config_versions WHERE config_id=? ORDER BY version_no DESC LIMIT 1",
        (config_id,),
    )


def create_config(file_id: int, dogtag: str, name: str, created_by: str) -> int:
    cfg_id = execute(
        "INSERT INTO configs(file_id, dogtag, name) VALUES(?,?,?)",
        (file_id, dogtag, name),
    )
    ver_id = execute(
        "INSERT INTO config_versions(config_id, version_no, created_by, notes) VALUES(?,?,?,?)",
        (cfg_id, 1, created_by, "initial"),
    )
    return ver_id


def clone_new_version(config_id: int, created_by: str, notes: str) -> int:
    latest = rows(
        "SELECT * FROM config_versions WHERE config_id=? ORDER BY version_no DESC LIMIT 1",
        (config_id,),
    )
    if not latest:
        return execute(
            "INSERT INTO config_versions(config_id, version_no, created_by, notes) VALUES(?,?,?,?)",
            (config_id, 1, created_by, notes),
        )
    latest = latest[0]
    new_no = int(latest["version_no"]) + 1
    new_ver_id = execute(
        "INSERT INTO config_versions(config_id, version_no, created_by, notes) VALUES(?,?,?,?)",
        (config_id, new_no, created_by, notes),
    )

    # clone values + list items
    old_vals = rows("SELECT * FROM config_values WHERE config_version_id=?", (latest["id"],))
    for ov in old_vals:
        new_val_id = execute(
            """
            INSERT INTO config_values(
              config_version_id, variable_id,
              value_int, value_float, value_str, value_bool, value_enum_value_id,
              is_null
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                new_ver_id,
                ov["variable_id"],
                ov["value_int"], ov["value_float"], ov["value_str"], ov["value_bool"], ov["value_enum_value_id"],
                ov["is_null"],
            ),
        )
        items = rows("SELECT * FROM config_value_list_items WHERE config_value_id=? ORDER BY idx", (ov["id"],))
        for it in items:
            execute(
                """
                INSERT INTO config_value_list_items(
                  config_value_id, idx,
                  item_int, item_float, item_str, item_bool, item_enum_value_id
                ) VALUES (?,?,?,?,?,?)
                """,
                (
                    new_val_id, it["idx"],
                    it["item_int"], it["item_float"], it["item_str"], it["item_bool"], it["item_enum_value_id"],
                ),
            )
    return new_ver_id


def schema_variables_for_file(file_id: int) -> List[sqlite3.Row]:
    return rows(
        """
        SELECT
          v.*,
          vt.dogtag AS type_dogtag, vt.base_kind AS type_base_kind,
          et.dogtag AS elem_type_dogtag,
          gs.dogtag AS gui_dogtag, gs.widget AS gui_widget,
          gs.hidden AS gui_hidden, gs.readonly AS gui_readonly, gs.help_text AS gui_help,
          c.min_num, c.max_num, c.min_len, c.max_len,
          c.default_int, c.default_float, c.default_str, c.default_bool,
          c.default_enum_value_id
        FROM variables v
        JOIN variable_types vt ON vt.id = v.type_id
        LEFT JOIN variable_types et ON et.id = v.element_type_id
        LEFT JOIN var_constraints c ON c.variable_id = v.id
        LEFT JOIN variable_gui vg ON vg.variable_id = v.id
        LEFT JOIN gui_schemes gs ON gs.id = vg.gui_scheme_id
        WHERE v.file_id=?
        ORDER BY COALESCE(v.category,''), v.name
        """,
        (file_id,),
    )


def enum_options(enum_id: int) -> List[sqlite3.Row]:
    return rows(
        "SELECT * FROM enum_values WHERE enum_id=? AND is_deprecated=0 ORDER BY COALESCE(sort_order, 999999), code",
        (enum_id,),
    )


def ensure_value_row(config_version_id: int, variable_id: int) -> int:
    existing = scalar(
        "SELECT id FROM config_values WHERE config_version_id=? AND variable_id=?",
        (config_version_id, variable_id),
    )
    if existing is not None:
        return int(existing)
    return execute(
        "INSERT INTO config_values(config_version_id, variable_id, is_null) VALUES(?,?,1)",
        (config_version_id, variable_id),
    )


def get_value_row(config_version_id: int, variable_id: int) -> sqlite3.Row:
    rid = ensure_value_row(config_version_id, variable_id)
    return rows("SELECT * FROM config_values WHERE id=?", (rid,))[0]


def set_scalar_value(value_id: int, kind: str, val: Any, is_null: bool = False) -> None:
    cols = {
        "INT": ("value_int", int(val) if val is not None else None),
        "FLOAT": ("value_float", float(val) if val is not None else None),
        "STRING": ("value_str", str(val) if val is not None else None),
        "BOOL": ("value_bool", 1 if bool(val) else 0),
        "ENUM": ("value_enum_value_id", int(val) if val is not None else None),
    }
    col, v = cols[kind]
    execute(
        f"""
        UPDATE config_values
        SET {col}=?, is_null=?
        WHERE id=?
        """,
        (v, 1 if is_null else 0, value_id),
    )


def replace_list_items(value_id: int, elem_kind: str, items: List[Any]) -> None:
    execute("DELETE FROM config_value_list_items WHERE config_value_id=?", (value_id,))
    for i, x in enumerate(items):
        if elem_kind == "INT":
            execute("INSERT INTO config_value_list_items(config_value_id, idx, item_int) VALUES(?,?,?)", (value_id, i, int(x)))
        elif elem_kind == "FLOAT":
            execute("INSERT INTO config_value_list_items(config_value_id, idx, item_float) VALUES(?,?,?)", (value_id, i, float(x)))
        elif elem_kind == "STRING":
            execute("INSERT INTO config_value_list_items(config_value_id, idx, item_str) VALUES(?,?,?)", (value_id, i, str(x)))
        elif elem_kind == "BOOL":
            execute("INSERT INTO config_value_list_items(config_value_id, idx, item_bool) VALUES(?,?,?)", (value_id, i, 1 if bool(x) else 0))
        elif elem_kind == "ENUM":
            execute("INSERT INTO config_value_list_items(config_value_id, idx, item_enum_value_id) VALUES(?,?,?)", (value_id, i, int(x)))
        else:
            raise ValueError(f"Unsupported elem kind: {elem_kind}")


def read_list_items(value_id: int, elem_kind: str) -> List[Any]:
    its = rows("SELECT * FROM config_value_list_items WHERE config_value_id=? ORDER BY idx", (value_id,))
    out: List[Any] = []
    for it in its:
        if elem_kind == "INT":
            out.append(it["item_int"])
        elif elem_kind == "FLOAT":
            out.append(it["item_float"])
        elif elem_kind == "STRING":
            out.append(it["item_str"])
        elif elem_kind == "BOOL":
            out.append(bool(it["item_bool"]))
        elif elem_kind == "ENUM":
            out.append(it["item_enum_value_id"])
    return out


def build_export_dict(file_id: int, config_version_id: int) -> Dict[str, Any]:
    vrows = schema_variables_for_file(file_id)
    out: Dict[str, Any] = {}
    for v in vrows:
        val = get_value_row(config_version_id, v["id"])
        t = v["type_dogtag"]
        base = v["type_base_kind"]

        if int(val["is_null"]) == 1:
            continue  # omit unset
        if base == "scalar":
            if t == "INT":
                out[v["name"]] = val["value_int"]
            elif t == "FLOAT":
                out[v["name"]] = val["value_float"]
            elif t == "STRING":
                out[v["name"]] = val["value_str"]
            elif t == "BOOL":
                out[v["name"]] = bool(val["value_bool"])
        elif base == "enum":
            ev_id = val["value_enum_value_id"]
            if ev_id is None:
                continue
            ev = rows("SELECT code FROM enum_values WHERE id=?", (ev_id,))[0]
            out[v["name"]] = ev["code"]
        elif base == "list":
            elem = v["elem_type_dogtag"] or "STRING"
            items = read_list_items(val["id"], "ENUM" if elem == "ENUM" else elem)
            if elem == "ENUM":
                # map enum_value_id -> code
                mapped = []
                for ev_id in items:
                    ev = rows("SELECT code FROM enum_values WHERE id=?", (ev_id,))[0]
                    mapped.append(ev["code"])
                out[v["name"]] = mapped
            else:
                out[v["name"]] = items
    return out


# ---------------- UI helpers ----------------

def widget_scalar(v: sqlite3.Row, current: sqlite3.Row) -> Tuple[Any, bool]:
    t = v["type_dogtag"]
    ro = int(v["gui_readonly"] or 0) == 1
    help_text = v["gui_help"] or v["description"] or ""
    k = f"var::{v['id']}"

    if t == "INT":
        mn = v["min_num"]
        mx = v["max_num"]
        default = v["default_int"]
        value = current["value_int"]
        if value is None and default is not None:
            value = int(default)
        if v["gui_widget"] == "slider" and mn is not None and mx is not None:
            return st.slider(v["name"], int(mn), int(mx), int(value or int(mn)), disabled=ro, help=help_text, key=k), False
        return st.number_input(v["name"], value=int(value or 0), step=1, disabled=ro, help=help_text, key=k), False

    if t == "FLOAT":
        mn = v["min_num"]
        mx = v["max_num"]
        default = v["default_float"]
        value = current["value_float"]
        if value is None and default is not None:
            value = float(default)
        if v["gui_widget"] == "slider" and mn is not None and mx is not None:
            return st.slider(v["name"], float(mn), float(mx), float(value or float(mn)), disabled=ro, help=help_text, key=k), False
        return st.number_input(v["name"], value=float(value or 0.0), disabled=ro, help=help_text, key=k), False

    if t == "STRING":
        default = v["default_str"]
        value = current["value_str"]
        if (value is None or value == "") and default is not None:
            value = str(default)
        return st.text_input(v["name"], value=value or "", disabled=ro, help=help_text, key=k), False

    if t == "BOOL":
        default = v["default_bool"]
        value = current["value_bool"]
        if value is None and default is not None:
            value = int(default)
        return st.checkbox(v["name"], value=bool(value or 0), disabled=ro, help=help_text, key=k), False

    raise ValueError(f"Unsupported scalar type: {t}")


def widget_enum(v: sqlite3.Row, current: sqlite3.Row) -> Tuple[Any, bool]:
    ro = int(v["gui_readonly"] or 0) == 1
    help_text = v["gui_help"] or v["description"] or ""
    opts = enum_options(v["enum_id"])
    id_by_label = {}
    labels = []
    for o in opts:
        label = f"{o['code']}" if not o["label"] else f"{o['code']} — {o['label']}"
        labels.append(label)
        id_by_label[label] = o["id"]

    chosen_id = current["value_enum_value_id"]
    if chosen_id is None and v["default_enum_value_id"] is not None:
        chosen_id = int(v["default_enum_value_id"])

    default_idx = 0
    if chosen_id is not None:
        for i, o in enumerate(opts):
            if int(o["id"]) == int(chosen_id):
                default_idx = i
                break

    k = f"var::{v['id']}"
    label = st.selectbox(v["name"], labels, index=default_idx, disabled=ro, help=help_text, key=k)
    return id_by_label[label], False


def widget_list(v: sqlite3.Row, current: sqlite3.Row) -> Tuple[Any, bool]:
    ro = int(v["gui_readonly"] or 0) == 1
    help_text = v["gui_help"] or v["description"] or ""
    elem = v["elem_type_dogtag"] or "STRING"
    k = f"var::{v['id']}"

    items = read_list_items(current["id"], "ENUM" if elem == "ENUM" else elem)

    # simple editor: comma-separated
    if elem in ("INT", "FLOAT", "STRING"):
        if elem == "INT":
            s = ",".join("" if x is None else str(int(x)) for x in items)
        elif elem == "FLOAT":
            s = ",".join("" if x is None else str(float(x)) for x in items)
        else:
            s = ",".join("" if x is None else str(x) for x in items)

        s2 = st.text_input(f"{v['name']} (comma-separated)", value=s, disabled=ro, help=help_text, key=k)
        parts = [p.strip() for p in s2.split(",") if p.strip() != ""]
        try:
            if elem == "INT":
                parsed = [int(p) for p in parts]
            elif elem == "FLOAT":
                parsed = [float(p) for p in parts]
            else:
                parsed = parts
        except ValueError:
            st.warning(f"Invalid list values for {v['name']}")
            parsed = items

        # optional numeric min/max clamp check
        mn = v["min_num"]
        mx = v["max_num"]
        if elem in ("INT", "FLOAT") and (mn is not None or mx is not None):
            bad = [x for x in parsed if (mn is not None and x < mn) or (mx is not None and x > mx)]
            if bad:
                st.warning(f"{v['name']}: values out of range [{mn},{mx}]: {bad}")

        return (elem, parsed), False

    if elem == "ENUM":
        opts = enum_options(v["enum_id"])
        codes = [o["code"] for o in opts]
        ev_id_by_code = {o["code"]: o["id"] for o in opts}
        # map item enum_value_ids -> codes
        chosen_codes = []
        for ev_id in items:
            r = rows("SELECT code FROM enum_values WHERE id=?", (ev_id,))
            if r:
                chosen_codes.append(r[0]["code"])

        chosen_codes = st.multiselect(v["name"], codes, default=chosen_codes, disabled=ro, help=help_text, key=k)
        parsed_ids = [int(ev_id_by_code[c]) for c in chosen_codes]
        return ("ENUM", parsed_ids), False

    raise ValueError(f"Unsupported list element type: {elem}")


def main() -> None:
    st.set_page_config(page_title="Config DB Demo", layout="wide")
    st.title("Config / Variable Schema → Streamlit UI Demo")

    ensure_schema()
    seed_demo_data_if_empty()

    files = list_files()
    if not files:
        st.info("No files schema found.")
        return

    file_map = {f"{r['dogtag']} — {r['name']}": r for r in files}
    file_key = st.sidebar.selectbox("File schema", list(file_map.keys()))
    file_row = file_map[file_key]
    file_id = int(file_row["id"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("Config instances")

    configs = list_configs(file_id)
    cfg_labels = ["(create new)"] + [f"{c['dogtag']} — {c['name'] or ''}".strip() for c in configs]
    cfg_choice = st.sidebar.selectbox("Select config", cfg_labels, index=0)

    if cfg_choice == "(create new)":
        st.subheader("Create new config")
        dogtag = st.text_input("Config dogtag", value=f"DROP_RUN_{scalar('SELECT COUNT(*) FROM configs')+1:05d}")
        name = st.text_input("Name", value="Demo run")
        created_by = st.text_input("Created by", value="Noel")
        if st.button("Create"):
            ver_id = create_config(file_id, dogtag, name, created_by)
            st.success(f"Created config version id={ver_id}")
            st.rerun()
        st.stop()

    cfg_row = configs[cfg_labels.index(cfg_choice) - 1]
    cfg_id = int(cfg_row["id"])

    latest_ver_id = get_latest_version_id(cfg_id)
    if latest_ver_id is None:
        st.warning("No versions for this config.")
        st.stop()

    # Version controls
    st.subheader(f"Editing: {cfg_row['dogtag']} — {cfg_row['name'] or ''}")
    cols = st.columns([1, 1, 2])
    with cols[0]:
        new_by = st.text_input("New version created by", value="Noel")
    with cols[1]:
        new_notes = st.text_input("Notes", value="tweak parameters")
    with cols[2]:
        if st.button("Clone → New Version"):
            new_ver_id = clone_new_version(cfg_id, new_by, new_notes)
            st.success(f"Created version id={new_ver_id}")
            latest_ver_id = new_ver_id

    # Load schema variables
    vrows = schema_variables_for_file(file_id)

    # UI: group by category
    categories: Dict[str, List[sqlite3.Row]] = {}
    for v in vrows:
        cat = v["category"] or "uncategorized"
        categories.setdefault(cat, []).append(v)

    show_hidden = st.sidebar.checkbox("Show hidden (advanced)", value=False)

    changed_any = False

    for cat, vs in categories.items():
        st.markdown(f"### {cat}")
        for v in vs:
            if int(v["gui_hidden"] or 0) == 1 and not show_hidden:
                continue

            current = get_value_row(latest_ver_id, int(v["id"]))

            # "unset" toggle
            left, right = st.columns([1, 6])
            with left:
                unset_key = f"unset::{latest_ver_id}::{v['id']}"
                unset = st.checkbox("unset", value=bool(current["is_null"]), key=unset_key)
            with right:
                base = v["type_base_kind"]
                t = v["type_dogtag"]

                if unset:
                    if int(current["is_null"]) == 0:
                        execute("UPDATE config_values SET is_null=1 WHERE id=?", (current["id"],))
                        changed_any = True
                    st.caption(v["description"] or "")
                    continue

                if int(current["is_null"]) == 1:
                    execute("UPDATE config_values SET is_null=0 WHERE id=?", (current["id"],))
                    current = get_value_row(latest_ver_id, int(v["id"]))
                    changed_any = True

                if base == "scalar":
                    new_val, _ = widget_scalar(v, current)
                    set_scalar_value(current["id"], t, new_val, is_null=False)
                    changed_any = True
                elif base == "enum":
                    new_ev_id, _ = widget_enum(v, current)
                    set_scalar_value(current["id"], "ENUM", new_ev_id, is_null=False)
                    changed_any = True
                elif base == "list":
                    elem_kind, items = widget_list(v, current)
                    replace_list_items(current["id"], elem_kind, items)
                    changed_any = True
                else:
                    st.write(f"Unsupported kind: {base}")

    st.markdown("---")
    exp = build_export_dict(file_id, latest_ver_id)
    st.subheader("Export preview (YAML)")
    st.code(yaml.safe_dump(exp, sort_keys=False), language="yaml")

    st.caption(f"DB: {DB_PATH} — config_version_id={latest_ver_id}")


if __name__ == "__main__":
    main()