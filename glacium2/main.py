
from pprint import pprint
from glacium2.documents import DocConfig






doc = DocConfig()
doc.open("config.drop.000001")
cfg = doc.gen_config()
pprint(doc.keys())