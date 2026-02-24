# fensap_mock_model_tab.py
import dearpygui.dearpygui as dpg


# ---------- "Groupbox" helper (looks close to a framed section) ----------
from contextlib import contextmanager

@contextmanager
def groupbox(label: str, width: int = -1):
    with dpg.group(horizontal=False):
        dpg.add_text(label)
        with dpg.child_window(
            border=True,
            width=width,
            height=0,
            autosize_y=True,
            menubar=False,
        ):
            yield


# ---------- UI builder ----------
def build_model_tab():
    # Overall vertical layout
    with dpg.group(horizontal=False):

        # --- Physical model section ---
        with groupbox("Physical model"):
            # Two-column grid: label | control
            with dpg.table(header_row=False, borders_innerV=False, borders_innerH=False, resizable=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=160)
                dpg.add_table_column(width_fixed=False, init_width_or_weight=1)

                # Physical model
                with dpg.table_row():
                    dpg.add_text("Physical model")
                    dpg.add_combo(
                        items=["Air", "Droplets", "Air + Droplets"],
                        default_value="Air",
                        width=260,
                        tag="model.physical_model",
                    )

                # Momentum equations
                with dpg.table_row():
                    dpg.add_text("Momentum equations")
                    dpg.add_combo(
                        items=["Euler", "Navier-Stokes"],
                        default_value="Navier-Stokes",
                        width=260,
                        tag="model.momentum_equations",
                    )

                # Energy equation
                with dpg.table_row():
                    dpg.add_text("Energy equation")
                    dpg.add_combo(
                        items=["Full PDE", "Constant enthalpy", "Energy-only"],
                        default_value="Full PDE",
                        width=260,
                        tag="model.energy_equation",
                    )


        # --- Turbulence model section ---
        with groupbox("Turbulence model"):
            with dpg.table(header_row=False, borders_innerV=False, borders_innerH=False, resizable=False):
                dpg.add_table_column(width_fixed=True, init_width_or_weight=200)
                dpg.add_table_column(width_fixed=False, init_width_or_weight=1)

                with dpg.table_row():
                    dpg.add_text("Turbulence model")
                    dpg.add_combo(
                        items=["Spalart-Allmaras"],
                        default_value="Spalart-Allmaras",
                        width=260,
                        tag="model.turbulence_model",
                    )

                with dpg.table_row():
                    dpg.add_text("Eddy/Laminar viscosity ratio")
                    dpg.add_input_float(
                        default_value=1e-5,
                        format="%.5e",
                        width=120,
                        tag="model.eddy_laminar_ratio",
                    )

                with dpg.table_row():
                    dpg.add_text("Relaxation factor")
                    dpg.add_input_float(
                        default_value=1.0,
                        format="%.6g",
                        width=120,
                        tag="model.relaxation_factor",
                    )

                with dpg.table_row():
                    dpg.add_text("Number of iterations")
                    dpg.add_input_int(
                        default_value=1,
                        step=1,
                        step_fast=10,
                        width=120,
                        tag="model.num_iterations",
                    )

        dpg.add_spacer(height=8)

        # --- Surface roughness / Transition / Body forces (each like a thin group row) ---
        with groupbox("Surface roughness"):
            dpg.add_combo(
                items=["No roughness"],
                default_value="No roughness",
                width=260,
                tag="model.surface_roughness",
            )

        dpg.add_spacer(height=6)

        with groupbox("Transition"):
            dpg.add_combo(
                items=["No transition"],
                default_value="No transition",
                width=260,
                tag="model.transition",
            )

        dpg.add_spacer(height=6)

        with groupbox("Body forces"):
            dpg.add_combo(
                items=["None"],
                default_value="None",
                width=260,
                tag="model.body_forces",
            )


def main():
    dpg.create_context()

    dpg.create_viewport(title="FENSAP Mock", width=1000, height=700)
    dpg.setup_dearpygui()
    dpg.configure_app(docking=True, docking_space=True)

    with dpg.window(tag="Main", label="FENSAP", width=980, height=660):
        # Top tabs like screenshot
        with dpg.tab_bar(tag="top.tabs"):
            with dpg.tab(label="Model"):
                build_model_tab()
            with dpg.tab(label="Conditions"):
                dpg.add_text("Conditions (mock)")
            with dpg.tab(label="Boundaries"):
                dpg.add_text("Boundaries (mock)")
            with dpg.tab(label="Solver"):
                dpg.add_text("Solver (mock)")
            with dpg.tab(label="Out"):
                dpg.add_text("Out (mock)")

        # Bottom buttons (Run disabled style-ish)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=740)
            dpg.add_button(label="Run", enabled=False, width=90, height=28)
            dpg.add_button(label="Close", width=90, height=28)

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    main()