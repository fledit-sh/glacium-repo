from pathlib import Path

from glacium.api import Run


def main():
    # create projects below ./runs in the current directory
    run = (
        Run("Project01")
        .name("Fine Grid")

        # Case definition
        .set("CASE_ROUGHNESS", 50)
        .set("CASE_CHARACTERISTIC_LENGTH", 0.431)
        .set("CASE_VELOCITY", 50)
        .set("CASE_ALTITUDE", 0)
        .set("CASE_TEMPERATURE", 263.15)
        .set("CASE_AOA", 0)
        .set("CASE_MVD", 20)
        .set("CASE_LWC", 0.0052)
        .set("CASE_YPLUS", 0.3)
        .set("PWS_REFINEMENT", 1)

        .add_job("XFOIL_REFINE")
        .add_job("XFOIL_THICKEN_TE")
        .add_job("XFOIL_PW_CONVERT")
        .add_job("POINTWISE_GCI")
        .add_job("FLUENT2FENSAP")
        .add_job("FENSAP_RUN")
        .add_job("FENSAP_CONVERGENCE_STATS")
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
