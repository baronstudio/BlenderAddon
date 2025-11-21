import os
import time
from functools import wraps
from typing import Any, Callable

import bpy

from ... import __package__ as package
from ... import bl_info

# Try to import tomllib (Python 3.11+) or fallback to external 'toml' if available.
try:
    import tomllib as _toml
    _TOML_BINARY = True
except Exception:
    try:
        import toml as _toml
        _TOML_BINARY = False
    except Exception:
        _toml = None
        _TOML_BINARY = False


def addon_path() -> str:
    """Get the path of the addon directory.

    Returns:
        str: Returns the path of the addon directory.
    """
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def icon_value(icon_name: str) -> int:
    """Get the integer value of a Blender icon by its name.

    Args:
        icon_name: Name of the Blender icon.

    Returns:
        Integer value representing the icon.
    """
    return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items[icon_name].value


def preferences() -> dict:
    """Get the preferences of the addon.

    Returns:
        dict: Returns the preferences of the addon.
    """
    return bpy.context.preferences.addons[package].preferences


def tag_redraw(area_type: str = "VIEW_3D", region_type: str = "UI"):
    for window in (w for wm in bpy.data.window_managers for w in wm.windows):
        for region in (
            r for area in window.screen.areas if area.type == area_type for r in area.regions if r.type == region_type
        ):
            region.tag_redraw()


def ui_update_timer() -> float | None:
    """Update the UI in the bpy.app.timers.

    Returns:
        float | None: Returns the input time if the update (redraw) is successful; returns None if a ReferenceError occurs.
    """
    try:
        tag_redraw()
    except ReferenceError:
        return None

    return 0.1


def timer(func: Callable) -> Callable:
    """Decorator to measure the time taken by a function to execute.

    Args:
        func: Function to be measured.

    Returns:
        Function: Returns the decorated function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start: float = time.perf_counter()
        result: Any = func(*args, **kwargs)
        end: float = time.perf_counter()
        print(f"{func.__name__} took {end - start:.2f} seconds to execute.")

        return result

    return wrapper


def _get_manifest_version():
    """Try to read `blender_manifest.toml` and return its `version` value.

    Returns:
        The parsed version (str or sequence) or None if not available/parsable.
    """
    if _toml is None:
        return None

    manifest_path = os.path.join(addon_path(), "blender_manifest.toml")
    if not os.path.exists(manifest_path):
        return None

    try:
        if _TOML_BINARY:
            with open(manifest_path, "rb") as f:
                data = _toml.load(f)
        else:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = _toml.load(f)
        return data.get("version")
    except Exception:
        return None


# Prefer the manifest version when available, otherwise fall back to bl_info
_manifest_version = _get_manifest_version()
if _manifest_version:
    # If manifest gives a sequence like [2,9,5]
    if isinstance(_manifest_version, (list, tuple)):
        try:
            version = tuple(int(x) for x in _manifest_version)
            version_str = ".".join(map(str, version))
        except Exception:
            # keep raw values as string fallback
            version = bl_info.get("version", (0, 0, 0))
            version_str = ".".join(map(str, version))
    else:
        # manifest version is likely a string like "2.9.5"
        version_str = str(_manifest_version)
        try:
            version = tuple(int(x) for x in version_str.split("."))
        except Exception:
            version = bl_info.get("version", (0, 0, 0))
else:
    version = bl_info["version"]
    version_str = ".".join(map(str, bl_info["version"]))
