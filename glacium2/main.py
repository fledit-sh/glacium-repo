from glacium2.index import Indexer
from glacium2.io import FileStreamReader
from glacium2.lineparser import *
from glacium2.index import FsIndexer
from pathlib import Path
import dearpygui.dearpygui as dpg
from pprint import pprint
LINE_TYPES = [
    LineBlank,
    LineCategory,
    LineComment,
    LineKeyArgs,
    LineUnknown,
]

def parse_line(raw: str):
    for T in LINE_TYPES:
        try:
            line = T(raw)
            return line
        except ValueError:
            pass
    return LineUnknown(raw)


class Document:
    def __init__(self):
        self.lines = []
        self._indexer = FsIndexer(".")
        self._reader = FileStreamReader()

    def open(self, fpath: str):

        with open(fpath) as f:
            for line in f:
                self.lines.append(parse_line(line))

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




doc = DocConfig()
doc.open("config.drop.000001")
cfg = doc.gen_config()
pprint(cfg["TURBULENCE"])
# for line in doc.lines:
#     if isinstance(line, LineCategory):
#         print(line)

# dpg.create_context()
# dpg.create_viewport()
# dpg.setup_dearpygui()
#
# with dpg.window(label="Example Window"):
#     dpg.add_text("Hello world")
#     dpg.add_button(label="Save", callback=print("yellow"))
#     dpg.add_input_text(label="string")
#     dpg.add_slider_float(label="float")
#
# dpg.show_viewport()
# dpg.start_dearpygui()
# dpg.destroy_context()