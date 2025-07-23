import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from glacium.utils.convergence.io import parse_headers, read_history_with_labels


def test_parse_headers_and_read_history(tmp_path):
    content = "\n".join([
        "# 1 residual   ",
        "#2 lift   ",
        "1 2",
        "3 4",
    ])
    file = tmp_path / "converg"
    file.write_text(content)

    labels = parse_headers(file)
    assert labels == ["residual", "lift"]

    labels2, data = read_history_with_labels(file)
    assert labels2 == labels
    assert np.allclose(data, np.array([[1.0, 2.0], [3.0, 4.0]]))

    _, data_tail = read_history_with_labels(file, nrows=1)
    assert data_tail.shape == (1, 2)
    assert np.allclose(data_tail, np.array([[3.0, 4.0]]))
