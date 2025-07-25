import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "par_converter", ROOT / "glacium" / "utils" / "par_converter.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

YamlParConverter = module.YamlParConverter
JinjaParConverter = module.JinjaParConverter


def test_yaml_converter_lines():
    conv = YamlParConverter()
    assert conv.convert_line("KEY 1\n") == "KEY: 1\n"
    assert conv.convert_line("  KEY    VAL  # c\n") == "KEY: VAL  # c\n"
    assert conv.convert_line("# comment\n") == "# comment\n"
    assert conv.convert_line("\n") == "\n"
    assert conv.convert_line("KEY_ONLY\n") == "KEY_ONLY\n"


def test_jinja_converter_lines():
    conv = JinjaParConverter()
    assert conv.convert_line("  KEY    VAL  # c\n") == "  KEY {{ KEY }} # c\n"
    assert conv.convert_line("KEY\n") == "KEY {{ KEY }}\n"


def test_convert_file(tmp_path):
    src = tmp_path / "in.par"
    src.write_text("A 1\nB 2\n")
    conv = YamlParConverter()
    text = conv.convert_file(src)
    assert text == "A: 1\nB: 2\n"
