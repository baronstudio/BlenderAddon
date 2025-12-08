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
T4A Assets Configuration Baker
Automates and streamlines the preparation of 3D assets for web-based configurators.
Compatible with Blender 5.0+
"""

bl_info = {
    "name": "T4A Assets Configuration Baker",
    "author": "Jean-Baptiste BARON / Tech 4 Art Conseil",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "3D View > Sidebar > T4A Baker",
    "description": (
        "Automatise et optimise la préparation des assets 3D pour les configurateurs web. "
        "Analyse la scène Blender, récupère la hiérarchie, les matériaux et conventions de nommage, "
        "génère automatiquement les configurations de baking selon les paramètres utilisateur. "
        "Produit des textures optimisées, exporte en GLB avec structure propre, et organise les fichiers pour le déploiement web. "
        "Pipeline interactif pour WebGL, configurateurs produits, expériences 3D temps réel."
    ),
    "category": "Asset Management",
    "warning": "Compatible Blender 5.0+ (utilise blender_manifest.toml)",
    "doc_url": "https://github.com/baronstudio/BlenderAddon/tree/master/T4A_AssetConfigBaker",
    "tracker_url": "https://github.com/baronstudio/BlenderAddon/issues",
}

from . import auto_load

auto_load.init()

def register():
    auto_load.register()

def unregister():
    auto_load.unregister()
