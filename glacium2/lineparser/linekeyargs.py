# glacium/lines/linekeyargs.py
import shlex
from line import Line

class LineKeyArgs(Line):
    pattern = r"^\s*\S+(\s+.*)?$"

    def assemble(self):
        self.check()
        parts = shlex.split(self.raw.strip())
        if not parts:
            raise ValueError(f"{self.__class__.__name__}: empty")
        key = parts[0]
        args = tuple(parts[1:])
        self.ctx = (key, args)

    def disassemble(self):
        key, args = self.ctx
        if not args:
            self.raw = f" {key}"
            return

        def q(s: str) -> str:
            return f"\"{s}\"" if any(c.isspace() for c in s) or "\"" in s else s

        tail = " ".join(q(a) for a in args)
        self.raw = f" {key} {tail}"
