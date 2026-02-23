
from pprint import pprint
from glacium2.documents import DocumentLoader
import yaml
import os
from jinja2 import Environment, FileSystemLoader




loader = DocumentLoader()
doc = loader.load("config.drop.000001")

config = doc.gen_config()
schema = doc.gen_schema()
# pprint(cfg)
pprint(schema)

schema["FILES"]["FSP_FILE_CRYSTAL_SOLUTION_MULTI"]["quoted"] = True
schema["GRID_GUI_METADATA"]["FSP_GUI_ITYP_BC_COLORS_B"]["quoted"] = True

with open("config.yaml", "w") as f:
    yaml.safe_dump(config, f, sort_keys=False, indent=2)

with open("schema.yaml", "w") as f:
    yaml.safe_dump(schema, f, sort_keys=False, indent=2)


import yaml
from jinja2 import Environment, FileSystemLoader

with open("config.yaml") as f:
    config = yaml.safe_load(f) or {}

with open("schema.yaml") as f:
    schema = yaml.safe_load(f) or {}

env = Environment(loader=FileSystemLoader("."))
tpl = env.get_template("templates/config.drop.j2")

rendered = tpl.render(cfg=config, schema=schema)

# print(rendered[:500])  # debug: erste Zeichen
with open("config.drop.rendered", "w") as f:
    f.write(rendered)


