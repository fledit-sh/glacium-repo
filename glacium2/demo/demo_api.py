from glacium2.fensap import Project

cs = Case("a new case") #
cs.save("filename")
cs.load("filename")



prj = Project(".", recipe="single")
prj[""]
prj.consume()
prj.consume("config.drop.000001")