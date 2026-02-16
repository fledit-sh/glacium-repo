from .line import Line


class LineCategory(Line):
    pattern = r"^\s*#\s*Category:\s*(.*)\s*$"

    def assemble(self):
        m = self.regex.match(self.raw)
        self.ctx = (m.group(1),)


    def disassemble(self):
        (name,) = self.ctx
        self.raw = f"# Category: {name}".rstrip()
