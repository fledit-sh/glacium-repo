from line import Line


class LineCategory(Line):
    pattern = r"^\s*#\s*Category:\s*(.*)\s*$"

    def assemble(self):
        self.check()
        m = self.regex.match(self.raw)
        name = m.group(1)
        self.ctx = (name,)

    def disassemble(self):
        (name,) = self.ctx
        self.raw = f"# Category: {name}".rstrip()
