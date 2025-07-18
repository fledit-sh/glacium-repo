from pathlib import Path

from glacium.api import Run


def main():
    # create projects below ./runs in the current directory
    run = (
        Run("runs")
        .name("demo_case")
        # global parameters
        .set("MULTISHOT_COUNT", 3)
        .set("N_CPU", 4)
        # case specific parameters
        .set("CASE_VELOCITY", 50)
        .set("CASE_AOA", 4)
        .add_job("POINTWISE_MESH2")
        .add_job("XFOIL_POLAR")
    )

    project = run.create()
    print("Created project", project.uid)

    # demonstrate mesh helpers
    mesh_src = Path("demo.mesh")
    mesh_src.write_text("mesh data")
    run.set_mesh(mesh_src, project)
    mesh_path = run.get_mesh(project)
    print("Mesh path in project:", mesh_path)


if __name__ == "__main__":
    main()
