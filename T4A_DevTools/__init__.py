# Year: 2026
# Author : Tech4Art Conseil

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
T4A Dev Tools
Small helper panel for add-on developers: hot-reload an add-on, reload scripts,
open add-on folders, toggle the system console and developer options.
"""

bl_info = {
    "name": "T4A Dev Tools",
    "author": "Jean-Baptiste BARON / Tech 4 Art Conseil",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar (N) > T4A Dev",
    "description": "Developer helpers: hot-reload add-ons, reload scripts, console and dev options",
    "category": "Development",
    "doc_url": "https://github.com/baronstudio/BlenderAddon/tree/master/T4A_DevTools",
    "tracker_url": "https://github.com/baronstudio/BlenderAddon/issues",
}

import os
import sys

import addon_utils
import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences, Operator, Panel

ADDON_ID = __package__ or __name__


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_prefs(context):
    return context.preferences.addons[ADDON_ID].preferences


def find_addon_module(module_name):
    """Return the Python module object of an installed add-on, or None."""
    for mod in addon_utils.modules(refresh=False):
        if mod.__name__ == module_name:
            return mod
    return sys.modules.get(module_name)


def addon_label(module_name):
    mod = find_addon_module(module_name)
    if mod is not None:
        info = addon_utils.module_bl_info(mod)
        name = info.get("name")
        if name:
            return name
    return module_name


def reload_addon(module_name):
    """Disable an add-on, purge it (and its sub-modules) from sys.modules, re-enable it.

    Purging sys.modules forces a fresh import of every sub-module, which a plain
    disable/enable does not do.
    """
    addon_utils.disable(module_name, default_set=False)
    prefix = module_name + "."
    for name in [n for n in sys.modules if n == module_name or n.startswith(prefix)]:
        del sys.modules[name]
    return addon_utils.enable(module_name, default_set=True, persistent=True)


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class T4A_DEV_Preferences(AddonPreferences):
    bl_idname = ADDON_ID

    target_addon: StringProperty(
        name="Add-on",
        description="Add-on module to hot-reload (must be enabled)",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "target_addon", context.preferences, "addons", icon="PLUGIN")


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class T4A_DEV_OT_reload_addon(Operator):
    """Disable, purge from memory and re-enable the selected add-on"""
    bl_idname = "t4a_dev.reload_addon"
    bl_label = "Reload Add-on"
    bl_options = {"REGISTER"}

    module: StringProperty(default="", options={"SKIP_SAVE"})

    def execute(self, context):
        module_name = self.module or get_prefs(context).target_addon
        if not module_name:
            self.report({"WARNING"}, "No add-on selected")
            return {"CANCELLED"}
        if module_name == ADDON_ID:
            self.report({"WARNING"}, "T4A Dev Tools cannot reload itself, use 'Reload Scripts'")
            return {"CANCELLED"}
        if module_name not in context.preferences.addons:
            self.report({"WARNING"}, f"'{module_name}' is not enabled")
            return {"CANCELLED"}

        try:
            mod = reload_addon(module_name)
        except Exception as exc:  # keep Blender alive whatever the add-on does
            self.report({"ERROR"}, f"Reload failed: {exc}")
            return {"CANCELLED"}

        if mod is None:
            self.report({"ERROR"}, f"Failed to re-enable '{module_name}', see the system console")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Reloaded: {addon_label(module_name)}")
        return {"FINISHED"}


class T4A_DEV_OT_open_addon_folder(Operator):
    """Open the folder of the selected add-on in the file browser"""
    bl_idname = "t4a_dev.open_addon_folder"
    bl_label = "Open Add-on Folder"

    def execute(self, context):
        module_name = get_prefs(context).target_addon
        mod = find_addon_module(module_name) if module_name else None
        path = getattr(mod, "__file__", None)
        if not path:
            self.report({"WARNING"}, "Add-on folder not found")
            return {"CANCELLED"}
        bpy.ops.wm.path_open(filepath=os.path.dirname(path))
        return {"FINISHED"}


class T4A_DEV_OT_open_user_addons(Operator):
    """Open the user add-ons / extensions folder"""
    bl_idname = "t4a_dev.open_user_addons"
    bl_label = "Open User Add-ons Folder"

    def execute(self, context):
        path = bpy.utils.user_resource("EXTENSIONS", path="user_default") \
            if bpy.app.version >= (4, 2, 0) else bpy.utils.user_resource("SCRIPTS", path="addons")
        if not path or not os.path.isdir(path):
            path = bpy.utils.user_resource("SCRIPTS", path="addons")
        os.makedirs(path, exist_ok=True)
        bpy.ops.wm.path_open(filepath=path)
        return {"FINISHED"}


class T4A_DEV_OT_clear_console(Operator):
    """Clear the system console (terminal) output"""
    bl_idname = "t4a_dev.clear_console"
    bl_label = "Clear System Console"

    def execute(self, context):
        os.system("cls" if os.name == "nt" else "clear")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class T4A_DEV_PT_main(Panel):
    bl_label = "T4A Dev Tools"
    bl_idname = "T4A_DEV_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "T4A Dev"

    def draw(self, context):
        layout = self.layout
        prefs = get_prefs(context)

        # --- Add-on hot reload
        box = layout.box()
        box.label(text="Add-on Reload", icon="FILE_REFRESH")
        box.prop_search(prefs, "target_addon", context.preferences, "addons", text="", icon="PLUGIN")
        row = box.row(align=True)
        row.scale_y = 1.4
        row.enabled = bool(prefs.target_addon)
        row.operator(T4A_DEV_OT_reload_addon.bl_idname, text="Reload Add-on", icon="FILE_REFRESH")
        row.operator(T4A_DEV_OT_open_addon_folder.bl_idname, text="", icon="FILE_FOLDER")
        box.operator("script.reload", text="Reload All Scripts", icon="SCRIPT")

        # --- Console
        box = layout.box()
        box.label(text="Console", icon="CONSOLE")
        row = box.row(align=True)
        if sys.platform == "win32":
            row.operator("wm.console_toggle", text="Toggle", icon="WINDOW")
        row.operator(T4A_DEV_OT_clear_console.bl_idname, text="Clear", icon="TRASH")

        # --- Developer options (stored in Blender preferences)
        view = context.preferences.view
        box = layout.box()
        box.label(text="Interface", icon="PREFERENCES")
        col = box.column(align=True)
        col.prop(view, "show_developer_ui", text="Developer Extras")
        col.prop(view, "show_tooltips_python", text="Python Tooltips")
        box.operator(T4A_DEV_OT_open_user_addons.bl_idname, text="User Add-ons Folder", icon="FILE_FOLDER")

        # --- Info
        col = layout.column(align=True)
        col.enabled = False
        col.label(text=f"Blender {bpy.app.version_string}", icon="BLENDER")
        col.label(text=f"Python {sys.version.split()[0]}")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    T4A_DEV_Preferences,
    T4A_DEV_OT_reload_addon,
    T4A_DEV_OT_open_addon_folder,
    T4A_DEV_OT_open_user_addons,
    T4A_DEV_OT_clear_console,
    T4A_DEV_PT_main,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
