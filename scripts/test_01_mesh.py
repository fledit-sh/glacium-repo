from glacium.api import Project


def main() -> None:
    """Run the mesh generation jobs and print the project UID."""
    proj = Project("MeshRuns").create()
    proj.add_job("XFOIL_REFINE")
    proj.add_job("XFOIL_THICKEN_TE")
    proj.add_job("XFOIL_PW_CONVERT")
    proj.add_job("POINTWISE_GCI")
    proj.add_job("FLUENT2FENSAP")
    proj.run()
    print(proj.uid)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
