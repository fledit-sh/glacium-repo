import sys
from pathlib import Path
from jinja2 import Environment

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glacium.templating import register_filters
from glacium.templates import filters


def test_register_filters():
    env = Environment()
    register_filters(env)
    for name in filters.__all__:
        assert name in env.filters
