import logging
from domain import VarPool, ControlledVar
from application import Case

logging.basicConfig(level=logging.INFO)

pool = VarPool(name="Main Pool")
pool.attach(ControlledVar(key="alpha_deg", _value=3, min=-10, max=20))
pool.attach(ControlledVar(key="cfl", _value=5.0, min=0.1, max=50.0))

case = Case(id="case_001", name="GridStudy A", vars=pool)

case.init()
case.apply()
case.check()
case.render()

logging.getLogger("sim").info(case.summary())
