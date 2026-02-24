from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from glacium2.gui.tecplot.tecplotviewer import TecplotViewer, main
else:
    from .tecplot.tecplotviewer import TecplotViewer, main

__all__ = ["TecplotViewer", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
