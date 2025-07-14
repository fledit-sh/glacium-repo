import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import pytest
import csv
import os
from PyPDF2 import PdfReader

from glacium.utils.convergence import analysis_file
from glacium.utils.report_converg_fensap import build_report


def test_single_convergence_stats(tmp_path):
    conv_file = tmp_path / "converg.fensap.000000"
    out_dir = tmp_path / "out"
    os.environ["FPDF_FONT_DIR"] = "/usr/share/fonts/truetype/dejavu"
    from fpdf import fpdf
    setattr(fpdf, "FPDF_FONT_DIR", "/usr/share/fonts/truetype/dejavu")

    data = np.array([
        [1.0, 2.0],
        [3.0, 4.0],
        [5.0, 6.0],
        [7.0, 8.0],
        [9.0, 10.0],
    ])
    labels = ["foo", "bar,baz"]
    lines = [f"# 1 {labels[0]}", f"# 2 {labels[1]}"]
    lines += [" ".join(map(str, row)) for row in data]
    conv_file.write_text("\n".join(lines))

    analysis_file(tmp_path, [conv_file, out_dir])
    build_report(out_dir)

    fig_dir = out_dir / "figures"
    assert (fig_dir / "column_00.png").exists()
    assert (fig_dir / "column_01.png").exists()
    pdf_path = out_dir / "report.pdf"
    assert pdf_path.exists()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) >= 1
    stats_file = out_dir / "stats.csv"
    assert stats_file.exists()

    with stats_file.open() as fh:
        rows = list(csv.DictReader(fh))

    content = stats_file.read_text()
    assert '"bar,baz"' in content

    expected_mean = data.mean(axis=0)
    expected_var = data.var(axis=0)

    assert len(rows) == 2
    assert rows[0]["label"] == labels[0]
    assert float(rows[0]["mean"]) == pytest.approx(expected_mean[0])
    assert float(rows[0]["variance"]) == pytest.approx(expected_var[0])
    assert rows[1]["label"] == labels[1]
    assert float(rows[1]["mean"]) == pytest.approx(expected_mean[1])
    assert float(rows[1]["variance"]) == pytest.approx(expected_var[1])
