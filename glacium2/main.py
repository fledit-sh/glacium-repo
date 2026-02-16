
from pprint import pprint
from glacium2.documents import DocConfig






doc = DocConfig()
doc.open("config.drop.000001")
for m in doc.lines:
    pprint(str(m))
cfg = doc.gen_config()

