from glacium.fensap import Project
from glacium import Case

cs = Case("a new case") #
cs.save("filename")
cs.load("filename")



prj = Project(".")
prj.consume()
prj.consume("config.drop.000001")
prj.