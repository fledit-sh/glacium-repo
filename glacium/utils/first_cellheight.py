"""First cell height calculations."""

from __future__ import annotations

from math import sqrt
from pathlib import Path
from typing import Any, Mapping

import yaml

from glacium.physics import ambient_pressure, interpolate_kinematic_viscosity

__all__ = ["from_case"]


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

    pressure = ambient_pressure(altitude)
    density = pressure / (287.05 * temperature)
    nu = interpolate_kinematic_viscosity(temperature)
    mu = density * nu

    reynolds = density * velocity * chord / mu if mu else 0.0

    Cf = 0.026 / reynolds ** (1 / 7)
    tau_w = Cf * velocity**2 / 2
    u_tau = sqrt(tau_w)
    s = yplus * nu / u_tau

    return s


# ---------------------------------------------------------------------------
# Legacy interactive interface retained for backwards compatibility


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

    Cf = 0.026 / Re ** (1 / 7)
    tau_w = Cf * V**2 / 2
    u_tau = sqrt(tau_w)
    s = y_plus * nu / u_tau

    print(f"\nWall spacing s = {s:.6e} m")


if __name__ == "__main__":
    main()
