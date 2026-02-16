from line import Line

class LineBlank(Line):
    pattern = r"^\s*$"

    def assemble(self):
        self.check()
        self.ctx = tuple()

    def disassemble(self):
        self.raw = ""
