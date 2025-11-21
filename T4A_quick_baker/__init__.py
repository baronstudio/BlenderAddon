bl_info = {
    "name": "T4AQuick_Baker",
    "author": "Tech4artconseil@gmail.com (Karan @b3dhub)",
    "description": "PBR Texture Baker custom for Tech4Art assets.",
    "blender": (3, 3, 0),
    "version": (3, 0, 0),
    "category": "Bake",
    "location": "3D Viewport | Shader Editor > Sidebar(N-Panel) > T4A_Q-Baker",
    "support": "COMMUNITY",
    "warning": "",
    "doc_url": "https://github.com/baronstudio/BlenderAddon/tree/master/T4A_quick_baker",
    "tracker_url": "",
}


import bpy

from . import source


def register():
    source.register()


def unregister():
    source.unregister()
