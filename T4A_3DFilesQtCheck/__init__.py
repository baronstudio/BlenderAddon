bl_info = {
    "name": "T4A_3DFilesQtCheck",
    "author": "Tech4Art Conseil <tech4artconseil@gmail.com>",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > T4A",
    "description": "Outils de contrôle de fichiers 3D — vérification qualité de maillage, textures, UV, matériaux et échelles.",
    "warning": "Work in progress",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View",
}

# Package-level loader: délègue l'enregistrement aux modules PROD_*
from . import PROD_autoload


def register():
    PROD_autoload.register()


def unregister():
    PROD_autoload.unregister()


if __name__ == "__main__":
    register()
