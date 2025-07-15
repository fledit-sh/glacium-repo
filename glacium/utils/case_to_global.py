from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import math
import yaml

from .first_cellheight import from_case as first_cellheight, interpolate_kinematic_viscosity

"""Helper converting ``case.yaml`` files to global configuration data."""

__all__ = ["generate_global_defaults"]


def _load_yaml(file: Path) -> dict:
    return yaml.safe_load(file.read_text()) if file.exists() else {}


def _ambient_pressure(altitude: float) -> float:
    """Return ambient pressure at ``altitude`` in metres (Pa)."""
    return 101325.0 * (1.0 - 2.25577e-5 * altitude) ** 5.2559




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
    refinement = float(case.get("PWS_REFINEMENT", cfg.get("PWS_REFINEMENT", 1)))
    multishot = case.get("CASE_MULTISHOT")

    # Ambient conditions ------------------------------------------------------
    pressure = _ambient_pressure(altitude)
    density = pressure / (287.05 * temperature)
    nu = interpolate_kinematic_viscosity(temperature)
    mu = density * nu

    a = math.sqrt(1.4 * 287.05 * temperature)
    mach = velocity / a if a else 0.0
    reynolds = density * velocity * chord / mu if mu else 0.0

    # First cell height -------------------------------------------------------
    first_height = first_cellheight(case)

    # Velocity vector ---------------------------------------------------------
    alpha = math.radians(aoa)
    vx = velocity * math.cos(alpha)
    vy = velocity * math.sin(alpha)
    vz = 0.0

    # Populate configuration --------------------------------------------------
    cfg.update({
        "PWS_CHORD_LENGTH": chord,
        "PWS_TE_GAP": 0.001/chord,
        "PWS_TREX_FIRST_HEIGHT": first_height,
        "PWS_POL_REYNOLDS": reynolds,
        "PWS_PSI_REYNOLDS": reynolds,
        "PWS_POL_MACH": mach,
        "PWS_PSI_MACH": mach,
        "PWS_EXTRUSION_Z_DISTANCE": chord * 0.1,
        "MSH_Z_SPAN": chord * 0.1,
        "MSH_MPX": chord * 1.4,
        "MSH_MPY": 0.0,
        "MSH_MPZ": chord * 0.1 * 0.5,
        "MSH_FIRSTCELLHEIGHT": 0.0000045,
        "FSP_CHARAC_LENGTH": chord,
        "FSP_REF_AREA": 0.1*chord**2,
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
        "FSP_TS": f"3 {temperature} 0 0",
        "FSP_TS_EQUATION": f'3 "{temperature}" "0" "0"',
        "FSP_PS": f"3 {pressure} 0 0",
        "FSP_PS_EQUATION": f'3 "{pressure}" "0" "0"',
        "FSP_MOMENTS_REFERENCE_POINT_COMPONENT_X": chord/4,
        "FSP_MOMENTS_REFERENCE_POINT_COMPONENT_Z": chord*0.1*0.5,
        "ICE_MACH_NUMBER": mach,
        "ICE_REYNOLDS_NUMBER": reynolds,
        "ICE_REF_AIR_PRESSURE": pressure / 1000.0,
        "ICE_REF_TEMPERATURE": temperature - 273.15,
        "ICE_REF_VELOCITY": velocity,
        "ICE_CHARAC_LENGTH": chord,
        "ICE_TEMPERATURE": temperature - 273.15,
        "DRP_GUI_BC_DIAM": f'3 "{mvd}" "" ""',
        "DRP_GUI_BC_LWC": f'3 "{lwc}" "" ""',
        "DRP_GUI_BC_TEMP": f'3 "{temperature}" "" ""',
        "DRP_GUI_BC_VX": f'3 "{vx}" "" ""',
        "DRP_GUI_BC_VY": f'3 "{vy}" "" ""',
        "FSP_DROPLET_INITIAL_VEL": f'3 {vx} {vy} 0',
        "DRP_GUI_ANGLE_OF_ATTACK_ALPHA": aoa,
        "FSP_ANGLE_OF_ATTACK_ALPHA": aoa,
        "FSP_GUI_DROPLET_INITIAL_VEL_COMP_X": vx,
        "FSP_GUI_DROPLET_INITIAL_VEL_COMP_Y": vy,
        "PWS_REFINEMENT": refinement,

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
    if multishot is not None:
        cfg["CASE_MULTISHOT"] = list(multishot)

    return cfg
