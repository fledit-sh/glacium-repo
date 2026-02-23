from glacium2.fensap import Project
from glacium2 import Case

cs = Case("a new case") #
cs.save("filename")
cs.load("filename")



prj = Project(".", recipe="single")
prj[""]
prj.consume()
prj.consume("config.drop.000001")
prj.


class Recipe:
    def __init__(self,