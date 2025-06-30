from glacium.config import compose_config


def test_compose_config_override():
    cfg = compose_config(["XFOIL_POLAR_OUT=test.dat"])
    assert cfg["XFOIL_POLAR_OUT"] == "test.dat"
