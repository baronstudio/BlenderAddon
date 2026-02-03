"""Panel UI: Files Management

Interface minimale pour la gestion des fichiers d'assets.
"""

# Copyright (C) 2026 Tech4Art Conseil
# Author: Tech4Art Conseil
# License: GNU General Public License v3.0 or later
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

class T4A_PT_PROD_FilesManagement(bpy.types.Panel):
    bl_label = "Files Management"
    bl_idname = "T4A_PT_PROD_files_management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        # Try to read addon preferences (global settings)
        addon_name = __package__ or "T4A_3DFilesQtCheck"
        prefs = None
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        if prefs is not None:
            layout.label(text="Chemin à scanner :")
            layout.prop(prefs, "scan_path", text="")
            layout.separator()
            layout.operator("t4a.scan_directory", text="Scanner et importer")
        else:
            layout.label(text="Files Management — (vide pour le moment)")


classes = (
    T4A_PT_PROD_FilesManagement,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
