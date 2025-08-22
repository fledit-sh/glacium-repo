import importlib


def test_run_multishot_invokes_cp_plot(tmp_path, monkeypatch):
    rm = importlib.import_module("glacium.post.multishot.run_multishot")
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()

    # create minimal shot files
    for name in [
        "soln.fensap.000001.dat",
        "droplet.drop.000001.dat",
        "swimsol.ice.000001.dat",
    ]:
        (input_dir / name).write_text("0")

    calls = []

    def fake_run_cmd(cmd, cwd=None):
        calls.append((cmd, cwd))

    monkeypatch.setattr(rm, "run_cmd", fake_run_cmd)

    rm.run_multishot(input_dir, output_dir)

    plot_calls = [c for c in calls if "glacium.post.multishot.multi_cp_plot" in c[0]]
    assert plot_calls, "multi_cp_plot not invoked"
    cmd, cwd = plot_calls[0]
    assert cmd[-1] == str(output_dir)
    assert cwd == output_dir

