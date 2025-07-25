"""Physics helper functions."""

from __future__ import annotations


def ambient_pressure(altitude: float) -> float:
    """Return ambient pressure at ``altitude`` in metres (Pa)."""

    return 101325.0 * (1.0 - 2.25577e-5 * altitude) ** 5.2559


def interpolate_kinematic_viscosity(T_K: float) -> float:
    """Interpolate air kinematic viscosity [m²/s] for temperature ``T_K`` in K."""

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


__all__ = ["ambient_pressure", "interpolate_kinematic_viscosity"]
