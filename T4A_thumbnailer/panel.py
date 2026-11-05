# -----------------------------------------------------------------------------
# T4A Thumbnailer
# Copyright (c) 2026 Tech4Art Conseil
# Author: Tech4Art Conseil
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
        layout.use_property_split = True
        layout.use_property_decorate = False
        props = context.scene.t4a_thumbnailer

        col = layout.column()
        col.prop(props, "output_folder")
        sub = col.column(align=True)
        sub.prop(props, "resolution_x")
        sub.prop(props, "resolution_y")
        col.prop(props, "jpeg_quality")
        col.prop(props, "filename_suffix")

        if context.scene.camera is None:
            layout.label(text="Aucune caméra active dans la scène", icon='ERROR')

        col = layout.column(align=True)
        col.scale_y = 1.2
        col.operator("t4a.thumbnail_render_active", text="Rendre vignette active", icon='RENDER_STILL')
        col.operator("t4a.thumbnail_batch", text="Batch matériaux", icon='MATERIAL')
