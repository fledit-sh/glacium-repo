from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import math
import yaml

"""Helper converting ``case.yaml`` files to global configuration data."""

__all__ = ["generate_global_defaults"]


def _load_yaml(file: Path) -> dict:
    return yaml.safe_load(file.read_text()) if file.exists() else {}


def _ambient_pressure(altitude: float) -> float:
    """Return ambient pressure at ``altitude`` in metres (Pa)."""
    return 101325.0 * (1.0 - 2.25577e-5 * altitude) ** 5.2559


def _sutherland_mu(temp: float) -> float:
    """Dynamic viscosity of air at ``temp`` Kelvin (kg/(m*s))."""
    mu0, T0, S = 1.716e-5, 273.15, 110.4
    return mu0 * (temp / T0) ** 1.5 * (T0 + S) / (temp + S)


def generate_global_defaults(case_path: Path, template_path: Path) -> Dict[str, Any]:
    """Create a global config dictionary from ``case.yaml``.

    Parameters
    ----------
    case_path:
        Directory containing ``case.yaml`` or path to the file.
    template_path:
        ``global_default.yaml`` template used as base.
    """
    case_file = case_path / "case.yaml" if case_path.is_dir() else case_path
    case = _load_yaml(case_file)
    template = _load_yaml(template_path)

    cfg = dict(template)

    # Extract case parameters -------------------------------------------------
    roughness = float(case.get("CASE_ROUGHNESS", 0.0))
    chord = float(case.get("CASE_CHARACTERISTIC_LENGTH", 1.0))
    velocity = float(case.get("CASE_VELOCITY", 0.0))
    altitude = float(case.get("CASE_ALTITUDE", 0.0))
    temperature = float(case.get("CASE_TEMPERATURE", 288.0))
    aoa = float(case.get("CASE_AOA", 0.0))
    mvd = float(case.get("CASE_MVD", 0.0))
    lwc = float(case.get("CASE_LWC", 0.0))
    yplus = float(case.get("CASE_YPLUS", 1.0))

    # Ambient conditions ------------------------------------------------------
    pressure = _ambient_pressure(altitude)
    density = pressure / (287.05 * temperature)
    mu = _sutherland_mu(temperature)

    a = math.sqrt(1.4 * 287.05 * temperature)
    mach = velocity / a if a else 0.0
    reynolds = density * velocity * chord / mu if mu else 0.0

    # First cell height -------------------------------------------------------
    cf = 0.026 / reynolds ** 0.2 if reynolds else 0.0
    utau = math.sqrt(cf / 2.0) * velocity if velocity else 0.0
    first_height = yplus * mu / (density * utau) if utau else 0.0

    # Velocity vector ---------------------------------------------------------
    alpha = math.radians(aoa)
    vx = velocity * math.cos(alpha)
    vy = 0.0
    vz = velocity * math.sin(alpha)

    # Populate configuration --------------------------------------------------
    cfg.update({
        "PWS_CHORD_LENGTH": chord,
        "PWS_TREX_FIRST_HEIGHT": first_height,
        "PWS_POL_REYNOLDS": reynolds,
        "PWS_PSI_REYNOLDS": reynolds,
        "PWS_POL_MACH": mach,
        "PWS_PSI_MACH": mach,
        "PWS_EXTRUSION_Z_DISTANCE": chord * 0.1,
        "MSH_Z_SPAN": chord * 0.2,
        "MSH_MPX": chord * 1.02,
        "MSH_MPY": 0.0,
        "MSH_MPZ": chord * 0.1,
        "MSH_FIRSTCELLHEIGHT": first_height,
        "FSP_CHARAC_LENGTH": chord,
        "FSP_REF_AREA": chord,
        "FSP_FREESTREAM_PRESSURE": pressure,
        "FSP_FREESTREAM_TEMPERATURE": temperature,
        "FSP_FREESTREAM_VELOCITY": velocity,
        "FSP_FREESTREAM_DIAMETER": mvd,
        "FSP_FREESTREAM_LWC": lwc,
        "FSP_MACH_NUMBER": mach,
        "FSP_REYNOLDS_NUMBER": reynolds,
        "FSP_VELOCITY_X": vx,
        "FSP_VELOCITY_Y": vy,
        "FSP_VELOCITY_Z": vz,
        "FSP_VX": f"3 {vx} 0 0",
        "FSP_VY": f"3 {vy} 0 0",
        "FSP_VZ": f"3 {vz} 0 0",
        "FSP_VX_EQUATION": f'3 "{vx}" "0" "0"',
        "FSP_VY_EQUATION": f'3 "{vy}" "0" "0"',
        "FSP_VZ_EQUATION": f'3 "{vz}" "0" "0"',
        "ICE_MACH_NUMBER": mach,
        "ICE_REYNOLDS_NUMBER": reynolds,
        "ICE_REF_AIR_PRESSURE": pressure / 1000.0,
        "ICE_REF_TEMPERATURE": temperature - 273.15,
        "ICE_REF_VELOCITY": velocity,
        "ICE_TEMPERATURE": temperature - 273.15,
    })

    cfg["CASE_ROUGHNESS"] = roughness
    cfg["CASE_CHARACTERISTIC_LENGTH"] = chord
    cfg["CASE_VELOCITY"] = velocity
    cfg["CASE_ALTITUDE"] = altitude
    cfg["CASE_TEMPERATURE"] = temperature
    cfg["CASE_AOA"] = aoa
    cfg["CASE_MVD"] = mvd
    cfg["CASE_LWC"] = lwc
    cfg["CASE_YPLUS"] = yplus

    return cfg
