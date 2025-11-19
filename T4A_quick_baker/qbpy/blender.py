import os

import bpy
from mathutils import Vector


def preferences(package: str) -> dict:
    """Get the preferences of the package.

    Args:
        package (str): Package name.

    Returns:
        dict: Returns the preferences of the package.
    """
    return bpy.context.preferences.addons[package].preferences


def ui_scale() -> float:
    """Get the UI scale.

    Returns:
        float: UI scale.
    """
    return bpy.context.preferences.system.ui_scale


def ui_line_width() -> int:
    """Get the UI line width.

    Returns:
        int: UI line width.
    """
    return bpy.context.preferences.system.ui_line_width


def dpi() -> int:
    """Get the DPI.

    Returns:
        int: DPI.
    """
    return bpy.context.preferences.system.dpi


def scene_unit(
    value: float,
    unit_system: str = None,
    unit_category: str = "LENGTH",
    scale_length: float = 1.0,
    use_separate: bool = None,
    rotation_unit: str = None,
    length_unit: str = None,
    mass_unit: str = None,
    time_unit: str = None,
    temperature_unit: str = None,
) -> str:
    """Convert value to scene unit.

    Args:
        value (float): Value to convert.
        unit_system (enum in [NONE, METRIC, IMPERIAL], optional): Unit system to use for conversion. Defaults to None.
        unit_category (enum in [NONE, LENGTH, AREA, VOLUME, MASS, ROTATION, TIME, TIME_ABSOLUTE, VELOCITY, ACCELERATION, CAMERA, POWER, TEMPERATURE, WAVELENGTH, COLOR_TEMPERATURE, FREQUENCY], optional): Category of the unit. Defaults to "LENGTH".
        length_unit (str, optional): Unit that will be used to convert length values. Defaults to None.

    Returns:
        str: Converted value.
    """
    unit_settings = bpy.context.scene.unit_settings
    unit_scale = unit_settings.scale_length

    if unit_system is None:
        unit_system = unit_settings.system
    if use_separate is None:
        use_separate = unit_settings.use_separate
    if rotation_unit is None:
        rotation_unit = unit_settings.system_rotation
    if length_unit is None:
        length_unit = unit_settings.length_unit

    if unit_category == "LENGTH":
        if unit_system == "NONE":
            return f"{value:.6f}"
        elif unit_system == "METRIC":
            length_units = {
                "ADAPTIVE": (1, 4, "m"),
                "KILOMETERS": (1e-3, 6, "km"),
                "METERS": (1, 4, "m"),
                "CENTIMETERS": (1e2, 2, "cm"),
                "MILLIMETERS": (1e3, 1, "mm"),
                "MICROMETERS": (1e6, 0, "μm"),
            }

            if length_unit in length_units:
                factor, precision, suffix = length_units[length_unit]
                value_converted = value * factor * unit_scale

                if value_converted == int(value_converted):
                    return f"{int(value_converted)} {suffix}"

                if use_separate:
                    if length_unit == "KILOMETERS":
                        value_converted = value * unit_scale
                        return _adaptive_km_unit(value_converted)
                    elif length_unit in {"METERS"}:
                        value_converted = value * unit_scale
                        return _adaptive_m_unit(value_converted)
                    elif length_unit == "CENTIMETERS":
                        return _adaptive_cm_unit(value_converted)
                    elif length_unit in {"MILLIMETERS", "MICROMETERS"}:
                        if round(value_converted, 1) == int(value_converted):
                            return f"{int(value_converted)} {suffix}"
                        return f"{value_converted:.{precision}f} {suffix}"

                if length_unit in {"ADAPTIVE"}:
                    return bpy.utils.units.to_string(
                        unit_system, unit_category, value * unit_scale, precision=5, split_unit=use_separate
                    )

                return f"{value_converted:.{precision}f} {suffix}"

        elif unit_system == "IMPERIAL":
            length_units = {
                "ADAPTIVE": (3.28084, 5, "'"),
                "MILES": (0.000621371, 6, " mi"),
                "FEET": (3.28084, 5, "'"),
                "INCHES": (39.3701, 4, '"'),
                "THOU": (39370.1, 1, " thou"),
            }
            if length_unit in length_units:
                factor, precision, suffix = length_units[length_unit]
                value_converted = value * factor * unit_scale

                if value_converted == int(value_converted):
                    return f"{int(value_converted)} {suffix}"

                if use_separate:
                    if length_unit == "MILES":
                        value_converted = value * 3.28084 * unit_scale
                        miles = int(value_converted // 5280)
                        feet = value_converted % 5280
                        return f"{miles} mi {round(feet, 6)}'"
                    elif length_unit in {"FEET"}:
                        feet = int(value_converted)
                        inches = (value_converted - feet) * 12
                        return f"{feet}' {round(inches, 4)}\""
                    elif length_unit == "INCHES":
                        inches = int(value_converted)
                        thou = (value_converted - inches) * 1000
                        return f'{inches}" {round(thou, precision)} thou'

                if length_unit in {"ADAPTIVE"}:
                    return bpy.utils.units.to_string(
                        unit_system, unit_category, value * unit_scale, precision=6, split_unit=use_separate
                    )

                return f"{round(value_converted, precision)}{suffix}"

        return f"{round(value, 5)} m"

    elif unit_category == "ROTATION":
        rotation_units = {
            "DEGREES": (1, None, "°"),
            "RADIANS": (0.0174533, 1, " rad"),
        }

        if rotation_unit in rotation_units:
            factor, precision, suffix = rotation_units[rotation_unit]
            value_converted = value * factor

            if rotation_unit == "RADIANS":
                if round(value_converted) == int(value_converted):
                    return f"{round(value_converted)}{suffix}"
                elif value_converted < 1:
                    return f"{round(value_converted, 2)}{suffix}"
                else:
                    return f"{round(value_converted, 1)}{suffix}"
            else:
                return f"{int(value_converted)}{suffix}"


def _adaptive_km_unit(value: float) -> float:
    km = int(value // 1000)

    if value >= 1000:
        return (
            f"{km} km  {round(value % 1000, 6)} m"
            if round(value % 1000, 6) != int(value % 1000)
            else f"{km} km  {int(value % 1000)} m"
        )
    elif value >= 1 and value < 1000:
        return f"0 km {round(value, 6)} m" if round(value, 6) != int(value) else f"0 km {int(value)} m"
    elif value >= 0.01 and value < 1:
        return (
            f"0 km {round(value * 100, 6)} cm"
            if round(value * 100, 6) != int(value * 100)
            else f"0 km {int(value * 100)} cm"
        )
    elif value >= 0.001 and value < 0.01:
        return (
            f"0 km {round(value * 1000, 6)} mm"
            if round(value * 1000, 6) != int(value * 1000)
            else f"0 km {int(value * 1000)} mm"
        )
    else:
        return (
            f"0 km {round(value * 1000, 6)} μm"
            if round(value * 1000, 6) != int(value * 1000)
            else f"0 km {int(value * 1000)} μm"
        )


def _adaptive_m_unit(value: float) -> str:
    m = int(value)
    cm = (value % 1) * 100
    mm = (value % 1) * 1000

    if value == 1:
        return f"{m} m"
    if 1 <= value < 100:
        if cm < 0.99:
            return f"{m} m {round(mm, 2)} mm" if round(mm, 2) != int(mm) else f"{m} m {int(mm)} mm"
        return f"{m} m {round(cm, 3)} cm" if round(cm, 3) != int(cm) else f"{m} m {int(cm)} cm"
    if 0.01 <= value < 1:
        return (
            f"{round(value, 6)} m"
            if 0.999 <= value < 1
            else f"0 m {round(cm, 6)} cm"
            if round(cm, 6) != int(cm)
            else f"0 m {int(cm)} cm"
        )
    return f"0 m {round(mm, 6)} mm" if round(mm, 6) != int(mm) else f"0 m {int(mm)} mm"


def _adaptive_cm_unit(value: float) -> str:
    cm = int(value)
    mm = round((value - cm) * 10, 2)

    if cm < 1:
        f"{cm} cm {round(mm, 6)} mm"

    if value >= int(value) + 0.9995 or mm == 0.0:
        return f"{round(value)} cm"

    return f"{cm} cm {mm} mm" if mm != int(mm) else f"{cm} cm {round(mm)} mm"


def icons_dir(file: str) -> str:
    """Get icons directory.

    Args:
        file (str): Name of the directory.

    Returns:
        str: Icons directory.
    """
    return os.path.join(os.path.dirname(file), "../icons/")


def panel(type: str) -> tuple:
    """Panel in the region.

    Args:
        type (enum in ['WINDOW', 'HEADER', 'CHANNELS', 'TEMPORARY', 'UI', 'TOOLS', 'TOOL_PROPS', 'PREVIEW', 'HUD', 'NAVIGATION_BAR', 'EXECUTE', 'FOOTER', 'TOOL_HEADER', 'XR']): Type of the region.

    Returns:
        tuple: Dimension of the region.
    """
    for region in bpy.context.area.regions:
        if region.type == type:
            return Vector((region.width, region.height))
    return Vector((0, 0))


def collapse_panels(t_panel: bool = False, n_panel: bool = False) -> tuple[bool, bool]:
    """Collapse all panels.

    Args:
        t_panel (bool, optional): Collapse the Tool(T) panel. Defaults to False.
        n_panel (bool, optional): Collapse the Sidebar(N) panel. Defaults to False.

    Returns:
        tuple(bool): State of the panels.
    """
    original_t_panel, original_n_panel = False, False

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if hasattr(space, "show_region_toolbar") and hasattr(space, "show_region_ui"):
                        original_t_panel = space.show_region_toolbar
                        original_n_panel = space.show_region_ui

                        space.show_region_toolbar = t_panel
                        space.show_region_ui = n_panel

    return original_t_panel, original_n_panel


def set_cursor(cursor: str = "DEFAULT"):
    """Get the cursor.

    Args:
        cursor (enum in ['DEFAULT', 'NONE', 'WAIT', 'CROSSHAIR', 'MOVE_X', 'MOVE_Y', 'KNIFE', 'TEXT', 'PAINT_BRUSH', 'PAINT_CROSS', 'DOT', 'ERASER', 'HAND', 'SCROLL_X', 'SCROLL_Y', 'SCROLL_XY', 'EYEDROPPER', 'PICK_AREA', 'STOP', 'COPY', 'CROSS', 'MUTE', 'ZOOM_IN', 'ZOOM_OUT'], optional): Cursor type. Defaults to "DEFAULT".
    """
    bpy.context.window.cursor_modal_set(cursor)


def warp_cursor(event: bpy.types.Event) -> bool:
    """Warp the cursor to the edge of the screen.

    Args:
        event (bpy.types.Event): Event from the modal operator.

    Returns:
        bool: Is the cursor warped.
    """
    margin = 30
    padding = 0
    x_pos, y_pos = event.mouse_region_x, event.mouse_region_y

    if x_pos + margin > bpy.context.area.width:
        x_pos = margin + padding
    elif x_pos - margin < 0:
        x_pos = bpy.context.area.width - (margin + padding)

    if y_pos + margin > bpy.context.area.height:
        y_pos = margin + padding
    elif y_pos - margin < 0:
        y_pos = bpy.context.area.height - (margin + padding)

    if (x_pos, y_pos) != (event.mouse_region_x, event.mouse_region_y):
        bpy.context.window.cursor_warp(bpy.context.area.x + x_pos, bpy.context.area.y + y_pos)
        return True
    return False


def axis_color(axis: str = "X") -> tuple:
    """Get the color of the axis.

    Args:
        axis (enum in ['X', 'Y', 'Z'], optional): Axis. Defaults to "X".

    Returns:
        tuple: Color of the axis.
    """
    return getattr(bpy.context.preferences.themes["Default"].user_interface, f"axis_{axis.lower()}")
