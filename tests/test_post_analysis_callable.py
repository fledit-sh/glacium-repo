import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import glacium.post.analysis as analysis


def test_plot_ice_thickness_callable():
    assert callable(analysis.plot_ice_thickness)


def test_animate_growth_callable():
    assert callable(analysis.animate_growth)
