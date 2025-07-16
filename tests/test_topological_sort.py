import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium import Run, Pipeline


def test_topological_sort_fifo_order():
    root = Run()
    a = Run().depends_on(root)
    b = Run().depends_on(root)
    c = Run().depends_on(root)

    pipe = Pipeline([root, b, a, c])
    order = [r.id for r in pipe._topological_sort()]
    assert order == [root.id, b.id, a.id, c.id]
