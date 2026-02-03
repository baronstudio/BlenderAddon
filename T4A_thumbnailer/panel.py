# -----------------------------------------------------------------------------
# T4A Thumbnailer
# Copyright (c) 2026 Tech4Art COnseil
# Author: Tech4Art COnseil
# Licensed under the GNU General Public License v3.0 (GPL-3.0-or-later)
# See LICENSE file for details.
# -----------------------------------------------------------------------------
import bpy

class T4A_PT_thumbnail_panel(bpy.types.Panel):
    bl_label = "T4A Thumbnailer"
    bl_idname = "T4A_PT_thumbnail_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A Thumbnailer'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.t4a_thumbnailer

        col = layout.column()
        col.prop(props, "output_folder")
        row = col.row(align=True)
        row.prop(props, "resolution_x")
        row.prop(props, "resolution_y")
        col.prop(props, "jpeg_quality")
        col.prop(props, "filename_suffix")
        col.prop(props, "use_batch")

        col.separator()
        col.operator("t4a.thumbnail_render_active", text="Rendre vignette active")
        col.operator("t4a.thumbnail_batch", text="Batch materials")
