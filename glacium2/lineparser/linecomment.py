from line import Line

class LineComment(Line):

    pattern = r"^\s*#(.*)$"

    def assemble(self):
        self.check()
        m = self.regex.match(self.raw)
        self.ctx = (m.group(1),)

    def disassemble(self):
        self.raw = f"# {self.ctx[0]}"
