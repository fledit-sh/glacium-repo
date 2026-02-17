
from pprint import pprint
from glacium2.documents import DocConfig
import yaml

from jinja2 import Environment, FileSystemLoader




doc = DocConfig()
doc.open("config.drop.000001")


cfg = doc.gen_config()
schema = doc.gen_schema()
# pprint(cfg)
pprint(schema)

schema["FILES"]["FSP_FILE_CRYSTAL_SOLUTION_MULTI"]["quoted"] = True

with open("config.yaml", "w") as f:
    yaml.safe_dump(cfg, f, sort_keys=False, indent=2)

with open("schema.yaml", "w") as f:
    yaml.safe_dump(schema, f, sort_keys=False, indent=2)


import yaml
from jinja2 import Environment, FileSystemLoader

with open("config.yaml") as f:
    cfg = yaml.safe_load(f) or {}

with open("schema.yaml") as f:
    schema = yaml.safe_load(f) or {}

env = Environment(loader=FileSystemLoader("."))
tpl = env.get_template("templates/config.drop.j2")

rendered = tpl.render(cfg=cfg, schema=schema)

# print(rendered[:500])  # debug: erste Zeichen
with open("config.drop.rendered", "w") as f:
    f.write(rendered)
