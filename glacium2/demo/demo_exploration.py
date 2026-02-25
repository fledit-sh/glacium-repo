
from pprint import pprint
from glacium2.documents import DocumentLoader
import yaml
import os
from jinja2 import Environment, FileSystemLoader
import logging

logging.basicConfig(level=logging.DEBUG)

loader = DocumentLoader()
doc = loader.load("../data/config.drop.000001")
# doc = loader.load("config.drop.rendered")

config = doc.gen_config()
schema = doc.gen_schema()

schema["FILES"]["FSP_FILE_CRYSTAL_SOLUTION_MULTI"]["quoted"] = True
schema["GRID_GUI_METADATA"]["FSP_GUI_ITYP_BC_COLORS_B"]["quoted"] = True

# pprint(config)

with open("../config/fsp_drp_config.yaml") as f:
    yaml.safe_dump(config, f, sort_keys=False, indent=2)

with open("../config/fsp_drp_schema.yaml") as f:
    yaml.safe_dump(schema, f, sort_keys=False, indent=2)


import yaml
from jinja2 import Environment, FileSystemLoader

with open("../config/fsp_drp_config.yaml") as f:
    config = yaml.safe_load(f) or {}

with open("../config/fsp_drp_schema.yaml") as f:
    schema = yaml.safe_load(f) or {}

env = Environment(loader=FileSystemLoader(".."))
tpl = env.get_template("templates/config.drop.j2")

rendered = tpl.render(cfg=config, schema=schema)

with open("../data/config.drop.rendered2", "w") as f:
    f.write(rendered)

with open("../data/config.drop.rendered", "w") as f:
    f.write(rendered)




