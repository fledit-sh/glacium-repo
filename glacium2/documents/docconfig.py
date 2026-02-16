from .document import Document
from ..lineparser import *

class DocConfig(Document):
    def __init__(self):
        super().__init__()

    def gen_config(self):
        cfg = dict()
        current_cat = ""
        for line in self.lines:
            if isinstance(line, LineCategory):
                current_cat = str(line.ctx[0]).upper().replace(" ","_")
                cfg[current_cat] = {}
            if isinstance(line, LineKeyArgs):
                cfg[current_cat][line.ctx[0]] = line.ctx[1]
        return cfg

    def keys(self):
        keys = []
        for line in self.lines:
            if isinstance(line, LineKeyArgs):
                keys.append(line.ctx[0])
        return keys
