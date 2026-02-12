from .converter import Converter
from ..lineparser import LineCategory, LineComment, LineKeyValue
from typing import Any

class ConfigDropConverter(Converter):
    def feed_line(self, line: str) -> Any:

        s = line.strip()
        if not s:
            return None

        s2 = line.lstrip()
        if s2.startswith("# Category:"):
            return LineCategory(line).raw

        if s2.startswith("#"):
            return LineComment(line).raw

        return LineKeyValue(line).raw