bl_info = {
    "name": "T4A Thumbnailer",
    "author": "baronstudio",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Sidebar > T4A Thumbnailer",
    "description": "Génère des thumbnails JPEG à partir de la caméra active et applique les différents matériaux en batch",
    "category": "Object",
}

import bpy

from .props import T4A_Props
from .operators import T4A_OT_thumbnail_batch, T4A_OT_thumbnail_render_active
from .panel import T4A_PT_thumbnail_panel

classes = (
    T4A_Props,
    T4A_OT_thumbnail_batch,
    T4A_OT_thumbnail_render_active,
    T4A_PT_thumbnail_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.t4a_thumbnailer = bpy.props.PointerProperty(type=T4A_Props)


def unregister():
    del bpy.types.Scene.t4a_thumbnailer
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
