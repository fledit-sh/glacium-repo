"""Jobs manipulating project configuration."""

from __future__ import annotations

from glacium.models.job import Job
from glacium.managers.ConfigManager import ConfigManager


def _reynolds_number(rho: float, velocity: float, chord: float, mu: float) -> float:
    """Return the Reynolds number ``Re = rho * V * c / mu``."""
    return rho * velocity * chord / mu

__all__ = ["ReynoldsConfigJob"]


class ReynoldsConfigJob(Job):
    """Compute and propagate the Reynolds number."""

    name = "CONFIG_REYNOLDS"
    deps: tuple[str, ...] = ()

    def execute(self) -> None:  # noqa: D401
        cfg_mgr = ConfigManager(self.project.paths)
        cfg = cfg_mgr.load_global()

        re = cfg.get("REYNOLDS_NUMBER")
        if re is None:
            rho = cfg.get("AIR_DENSITY", 1.225)
            velocity = cfg.get(
                "FSP_FREESTREAM_VELOCITY", cfg.get("ICE_REF_VELOCITY", 0)
            )
            chord = cfg.get("PWS_CHORD_LENGTH", 1.0)
            mu = cfg.get("AIR_VISCOSITY", 1.789e-5)
            re = _reynolds_number(rho, velocity, chord, mu)
            cfg["REYNOLDS_NUMBER"] = re

        cfg["PWS_POL_REYNOLDS"] = re
        cfg["PWS_PSI_REYNOLDS"] = re
        cfg["FSP_REYNOLDS_NUMBER"] = re
        cfg["ICE_REYNOLDS_NUMBER"] = re

        cfg_mgr.dump_global()
