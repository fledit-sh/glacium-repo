from line import Line

class LineUnknown(Line):

    pattern = r"^.*$"

    def assemble(self):
        self.ctx = (self.raw,)

    def disassemble(self):
        self.raw = self.ctx[0]
