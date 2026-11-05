# -----------------------------------------------------------------------------
# T4A Thumbnailer
# Copyright (c) 2026 Tech4Art Conseil
# Author: Tech4Art Conseil
# Licensed under the GNU General Public License v3.0 (GPL-3.0-or-later)
# See LICENSE file for details.
# -----------------------------------------------------------------------------

"""
T4A Thumbnailer
Render JPEG thumbnails from the active camera, optionally one per material.

Packaged as a Blender extension (see blender_manifest.toml). ``bl_info`` is
kept only so the add-on can still be installed the legacy way; Blender 4.2+
ignores it when the manifest is present.
"""

bl_info = {
    "name": "T4A Thumbnailer",
    "author": "Jean-Baptiste BARON / Tech 4 Art Conseil",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar (N) > T4A Thumbnailer",
    "description": "Génère des thumbnails JPEG à partir de la caméra active, en batch par matériau",
    "category": "Render",
    "doc_url": "https://github.com/baronstudio/BlenderAddon/tree/master/T4A_thumbnailer",
    "tracker_url": "https://github.com/baronstudio/BlenderAddon/issues",
}

import bpy

from . import operators, panel, props

classes = (
    props.T4A_Props,
    operators.T4A_OT_thumbnail_render_active,
    operators.T4A_OT_thumbnail_batch,
    panel.T4A_PT_thumbnail_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.t4a_thumbnailer = bpy.props.PointerProperty(type=props.T4A_Props)


def unregister():
    if hasattr(bpy.types.Scene, "t4a_thumbnailer"):
        del bpy.types.Scene.t4a_thumbnailer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
