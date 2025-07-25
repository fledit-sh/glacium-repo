from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence
import pandas as pd

from glacium.core.base import PythonJobBase
from glacium.engines.py_engine import PyEngine
from glacium.post import analysis as post_analysis


class AnalyzeMultishotJob(PythonJobBase):
    """Analyse MULTISHOT solver exports."""

    name = "ANALYZE_MULTISHOT"
    deps = ("POSTPROCESS_MULTISHOT",)

    def args(self) -> Sequence[str | Path]:  # unused
        return []

    def execute(self) -> None:  # noqa: D401
        project_root = self.project.root
        run_dir = project_root / "run_MULTISHOT"
        out_dir = project_root / "analysis" / "MULTISHOT"
        out_dir.mkdir(parents=True, exist_ok=True)

        cfg = self.project.config
        p_inf = float(cfg.get("FSP_FREESTREAM_PRESSURE", 101325.0))
        t_inf = float(cfg.get("FSP_FREESTREAM_TEMPERATURE", 288.0))
        u_inf = float(cfg.get("FSP_FREESTREAM_VELOCITY", 0.0))
        chord = float(cfg.get("FSP_CHARAC_LENGTH", 1.0))
        rho_inf = p_inf / (287.05 * t_inf)

        wall_tol = float(cfg.get("CP_WALL_TOL", 1e-4))
        rel_pct = float(cfg.get("CP_REL_PCT", 2.0))

        cp_results: list[tuple[str, pd.DataFrame]] = []
        for dat in sorted(run_dir.glob("soln.fensap.??????.dat")):
            df = post_analysis.read_tec_ascii(dat)
            cp = post_analysis.compute_cp(
                df,
                p_inf,
                rho_inf,
                u_inf,
                chord,
                wall_tol,
                rel_pct,
            )
            cp_results.append((dat.stem, cp))
            img = out_dir / f"{dat.stem}_cp.png"
            post_analysis.plot_cp_directional(
                dat,
                p_inf,
                rho_inf,
                u_inf,
                chord,
                img,
            )

        if cp_results:
            post_analysis.plot_cp_overlay(cp_results, out_dir / "all_cp.png")

        for dat in sorted(run_dir.glob("swimsol.ice.??????.dat")):
            df = post_analysis.read_wall_zone(dat)
            proc, unit = post_analysis.process_wall_zone(df, chord=chord, unit="mm")
            img = out_dir / f"{dat.stem}_ice.png"
            post_analysis.plot_ice_thickness(proc, unit, img)

        cwd = os.getcwd()
        os.chdir(run_dir)
        try:
            segments = post_analysis.load_contours("*.stl")
        finally:
            os.chdir(cwd)
        post_analysis.animate_growth(segments, out_dir / "ice_growth.gif")
