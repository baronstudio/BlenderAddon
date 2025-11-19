bl_info = {
    "name": "Quick Baker",
    "author": "Karan @b3dhub",
    "description": "PBR Texture Baker",
    "blender": (3, 3, 0),
    "version": (2, 9, 5),
    "category": "Bake",
    "location": "3D Viewport | Shader Editor > Sidebar(N-Panel) > Q-Baker",
    "support": "COMMUNITY",
    "warning": "",
    "doc_url": "https://b3dhub.github.io/quick-baker-docs",
    "tracker_url": "https://discord.gg/sdnHHZpWbT",
}


import bpy

from . import source


def register():
    source.register()


def unregister():
    source.unregister()
