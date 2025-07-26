#!/usr/bin/env python3
# plot_airfoil_veusz.py

import sys
import numpy as np
import veusz.embed as vz


def main(filename: str) -> None:
    # 1. Daten laden ---------------------------------------------------------
    x, y = np.loadtxt(filename, skiprows=1, unpack=True)

    # 2. Veusz-Fenster -------------------------------------------------------
    v = vz.Embedded(f"Airfoil – {filename}")
    v.EnableToolbar()

    # 3. Seiten‑ & Graph‑Gerüst ---------------------------------------------
    v.To(v.Add("page", name="page1"))
    v.To(v.Add("graph", name="graph1", autoadd=False))
    v.Add("axis", name="x")
    v.Add("axis", name="y", direction="vertical")

    # 4. Datensätze übergeben -----------------------------------------------
    v.SetData("xdata", x)
    v.SetData("ydata", y)

    v.Add(
        "xy",
        xData="xdata",
        yData="ydata",
        PlotLine__color="black",
        PlotLine__width="1pt",
        MarkerFill__hide=True,
        MarkerLine__hide=True,
    )

    # 5. Ansicht & Update ----------------------------------------------------
    v.Zoom("page")
    v.ForceUpdate()

    input("⏎ schließt das Fenster …")
    v.Close()


if __name__ == "__main__":

    main("AH63K127.dat")
