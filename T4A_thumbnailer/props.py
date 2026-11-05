# -----------------------------------------------------------------------------
# T4A Thumbnailer
# Copyright (c) 2026 Tech4Art Conseil
# Author: Tech4Art Conseil
# Licensed under the GNU General Public License v3.0 (GPL-3.0-or-later)
# See LICENSE file for details.
# -----------------------------------------------------------------------------
import bpy


class T4A_Props(bpy.types.PropertyGroup):
    output_folder: bpy.props.StringProperty(
        name="Dossier d'enregistrement",
        description="Dossier où sauvegarder les thumbnails",
        default="",
        subtype='DIR_PATH'
    )
    resolution_x: bpy.props.IntProperty(
        name="Largeur",
        default=64,
        min=1,
        max=16384,
        description="Largeur du rendu en pixels"
    )
    resolution_y: bpy.props.IntProperty(
        name="Hauteur",
        default=64,
        min=1,
        max=16384,
        description="Hauteur du rendu en pixels"
    )
    jpeg_quality: bpy.props.IntProperty(
        name="Qualité JPEG",
        default=90,
        min=1,
        max=100,
        description="Qualité du JPEG de sortie (1-100)"
    )
    filename_suffix: bpy.props.StringProperty(
        name="Suffixe fichier",
        description="Suffixe ajouté au nom du fichier avant l'extension (ex: _thumb)",
        default="_thumb"
    )
