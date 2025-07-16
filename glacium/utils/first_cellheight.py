"""First cell height calculations."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Any

import math
import yaml

__all__ = ["from_case"]


def _ambient_pressure(altitude: float) -> float:
    """Return ambient pressure at ``altitude`` in metres (Pa)."""

    return 101325.0 * (1.0 - 2.25577e-5 * altitude) ** 5.2559




def from_case(case: Path | Mapping[str, Any]) -> float:
    """Compute the first cell height from ``case.yaml`` data."""

    if not isinstance(case, Mapping):
        data = yaml.safe_load(Path(case).read_text())
    else:
        data = case

    chord = float(data.get("CASE_CHARACTERISTIC_LENGTH", 1.0))
    velocity = float(data.get("CASE_VELOCITY", 0.0))
    altitude = float(data.get("CASE_ALTITUDE", 0.0))
    temperature = float(data.get("CASE_TEMPERATURE", 288.0))
    yplus = float(data.get("CASE_YPLUS", 1.0))

    pressure = _ambient_pressure(altitude)
    density = pressure / (287.05 * temperature)
    nu = interpolate_kinematic_viscosity(temperature)
    mu = density * nu

    reynolds = density * velocity * chord / mu if mu else 0.0

    Cf = 0.026 / reynolds**(1/7)
    tau_w = Cf * velocity**2 / 2
    u_tau = sqrt(tau_w)
    s = yplus * nu / u_tau

    return s


# ---------------------------------------------------------------------------
# Legacy interactive interface retained for backwards compatibility
from math import sqrt


def interpolate_kinematic_viscosity(T_K: float) -> float:
    """Linear interpolation of air kinematic viscosity [m²/s] vs. temperature [K]."""

    table = [
        (175, 0.586e-5),
        (200, 0.753e-5),
        (225, 0.935e-5),
        (250, 1.132e-5),
        (275, 1.343e-5),
        (300, 1.568e-5),
        (325, 1.807e-5),
        (350, 2.056e-5),
        (375, 2.317e-5),
        (400, 2.591e-5),
        (450, 3.168e-5),
        (500, 3.782e-5),
        (550, 4.439e-5),
        (600, 5.128e-5),
    ]
    for (T1, nu1), (T2, nu2) in zip(table, table[1:]):
        if T1 < T_K < T2:
            return nu1 + (nu2 - nu1) * (T_K - T1) / (T2 - T1)
    raise ValueError("Temperature out of supported range 175–600 K")

def main() -> None:
    L = float(input("Reference length [m]? "))
    mode = int(input("Reynolds number [1] or velocity [2]? "))

    if mode == 1:
        Re = float(input("Reynolds number? "))
        T_C = float(input("Temperature [°C]? "))
        nu = interpolate_kinematic_viscosity(T_C + 273.15)
        V = Re * nu / L
        print(f"Airspeed v = {V:.3f} m/s")
    elif mode == 2:
        V = float(input("Velocity [m/s]? "))
        T_C = float(input("Temperature [°C]? "))
        nu = interpolate_kinematic_viscosity(T_C + 273.15)
        Re = V * L / nu
        print(f"Reynolds number Re = {int(round(Re))}")
    else:
        raise ValueError("Choose 1 or 2.")

    y_plus = float(input("Desired y+? "))

    Cf = 0.026 / Re**(1/7)
    tau_w = Cf * V**2 / 2
    u_tau = sqrt(tau_w)
    s = y_plus * nu / u_tau

    print(f"\nWall spacing s = {s:.6e} m")

if __name__ == "__main__":
    main()
