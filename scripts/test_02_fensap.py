"""Run a FENSAP case using a pre-generated mesh."""

from __future__ import annotations

import argparse

from glacium.api import Project


def main() -> None:
    """Execute a FENSAP run with a copied mesh and limited steps."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh-root", default="MeshRuns")
    parser.add_argument("--mesh-uid", required=True)
    parser.add_argument("--max-steps", type=int, default=700)
    parser.add_argument("--out-root", default="FensapRuns")
    args = parser.parse_args()

    mesh_proj = Project.load(args.mesh_root, args.mesh_uid)
    mesh_path = Project.get_mesh(mesh_proj)

    proj = Project(args.out_root).create()
    Project.set_mesh(mesh_path, proj)

    proj.set("FSP_MAX_TIME_STEPS_PER_CYCLE", args.max_steps)
    try:
        proj.set("FSP_GUI_FENSAP_MAX_TIME_STEPS_PER_CYCLE", args.max_steps)
    except KeyError:
        pass

    proj.add_job("FENSAP_RUN")
    proj.run()
    print(proj.uid)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()

