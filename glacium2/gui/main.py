# app.py
import dearpygui.dearpygui as dpg

def build_ui():
    dpg.create_context()

    with dpg.viewport_menu_bar():
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="New Project")
            dpg.add_menu_item(label="Open...")
            dpg.add_menu_item(label="Save")
        with dpg.menu(label="View"):
            dpg.add_menu_item(label="Reset Layout")
        with dpg.menu(label="Help"):
            dpg.add_menu_item(label="About")

    with dpg.window(label="FENSAP GUI (Mock)", tag="MAIN", width=1400, height=900):
        # Optional: Dockspace
        dpg.add_text("Mock UI - no functionality")

    # Panels as separate windows (dockable)
    with dpg.window(label="Project", tag="PANEL_PROJECT", width=300, height=600):
        dpg.add_input_text(label="Project root", width=-1)
        dpg.add_button(label="Scan")
        dpg.add_separator()
        dpg.add_text("Cases")
        with dpg.child_window(height=-1):
            dpg.add_selectable(label="Case 001")
            dpg.add_selectable(label="Case 002")

    with dpg.window(label="Workspace", tag="PANEL_WORKSPACE", width=800, height=600):
        with dpg.tab_bar():
            with dpg.tab(label="Geometry"):
                dpg.add_text("Geometry tab")
            with dpg.tab(label="Mesh"):
                dpg.add_text("Mesh tab")
            with dpg.tab(label="Flow"):
                dpg.add_text("Flow tab")
            with dpg.tab(label="Droplets"):
                dpg.add_text("Droplets tab")
            with dpg.tab(label="Ice"):
                dpg.add_text("Ice tab")
            with dpg.tab(label="Results"):
                dpg.add_text("Results tab")

    with dpg.window(label="Properties", tag="PANEL_PROPS", width=350, height=600):
        dpg.add_text("Config / Schema")
        dpg.add_separator()
        dpg.add_input_text(label="Parameter A", width=-1)
        dpg.add_input_text(label="Parameter B", width=-1)
        dpg.add_input_float(label="Angle of attack", width=-1)

    with dpg.window(label="Log", tag="PANEL_LOG", width=1400, height=200):
        with dpg.child_window(height=-1):
            dpg.add_text("[INFO] Ready")

    dpg.create_viewport(title="FENSAP Mock", width=1400, height=900)
    dpg.setup_dearpygui()

    # Enable docking
    dpg.configure_app(docking=True, docking_space=True)

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    build_ui()