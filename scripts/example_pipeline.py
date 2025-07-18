

from pathlib import Path
from itertools import product
import yaml
from glacium.api.run import Run


# ----- build a single project ------------------------------------------- #
def main():
    run = Run("")
    run.select_airfoil("NACA0008.dat")
    run.set("CASE_ROUGHNESS", 50)
    run.set("CASE_CHARACTERISTIC_LENGTH", 0.431)
    run.set("CASE_VELOCITY", 50)
    run.set("CASE_ALTITUDE", 100)
    run.set("CASE_TEMPERATURE", -2)
    run.set("CASE_AOA", 0)
    run.set("CASE_MVD", 20)
    run.set("CASE_YPLUS", 0.3)
    run.set("PWS_REFINEMENT", 8)
    run.create()


if __name__ == "__main__":
    main()
