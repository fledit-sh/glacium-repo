from __future__ import annotations

"""Utilities for converting FENSAP ``.par`` files."""

from pathlib import Path

__all__ = ["ParConverter", "YamlParConverter", "JinjaParConverter"]


class ParConverter:
    """Base class for ``.par`` file converters."""

    def convert_line(self, line: str) -> str:  # pragma: no cover - overridden
        """Convert a single line of text.

        Subclasses override :meth:`format_line` to control the output format.
        """
        newline = "\n" if line.endswith("\n") else ""
        raw = line[:-1] if newline else line

        stripped = raw.lstrip()
        if not stripped or stripped.startswith("#"):
            return raw + newline

        prefix_len = len(raw) - len(stripped)
        prefix = raw[:prefix_len]

        parts = stripped.split(None, 1)
        key = parts[0]
        rest = parts[1] if len(parts) == 2 else ""

        if rest == "":
            return self.on_missing_value(prefix, key) + newline

        return self.format_line(prefix, key, rest) + newline

    def on_missing_value(self, prefix: str, key: str) -> str:
        """Handle lines that contain only a key without a value."""
        return self.format_line(prefix, key, "")

    def format_line(self, prefix: str, key: str, rest: str) -> str:
        """Return the formatted output for ``key`` and ``rest``."""
        raise NotImplementedError

    def convert_file(self, file: Path | str) -> str:
        """Return the converted content of *file*."""
        path = Path(file)
        text = path.read_text(encoding="utf-8", errors="ignore")
        return "".join(self.convert_line(l) for l in text.splitlines(keepends=True))


class YamlParConverter(ParConverter):
    """Converter emitting YAML key/value pairs."""

    def format_line(self, prefix: str, key: str, rest: str) -> str:  # noqa: ARG002
        value = rest.lstrip()
        return f"{key}: {value}"

    def on_missing_value(self, prefix: str, key: str) -> str:  # noqa: ARG002
        return key


class JinjaParConverter(ParConverter):
    """Converter emitting Jinja2 placeholders."""

    def format_line(self, prefix: str, key: str, rest: str) -> str:
        part = rest.lstrip()
        inline_comment = ""
        if "#" in part:
            inline_comment = " #" + part.split("#", 1)[1]
        return f"{prefix}{key} {{{{ {key} }}}}{inline_comment}"
