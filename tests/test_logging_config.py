from pathlib import Path
import logging

from glacium.utils.logging import configure, log


def test_configure_file(tmp_path):
    log_path = tmp_path / "log.txt"
    root = logging.getLogger()
    old_handlers = list(root.handlers)
    try:
        configure(level="DEBUG", file=log_path)
        log.debug("hello")
        assert log_path.exists()
        assert "hello" in log_path.read_text()
    finally:
        root.handlers = old_handlers

