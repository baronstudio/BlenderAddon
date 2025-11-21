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
        description="Qualité du JPEG de sortie (0-100)"
    )
    use_batch: bpy.props.BoolProperty(
        name="Batch tous les matériaux",
        default=True,
        description="Si vrai, appliquera tous les matériaux assignés à l'objet sélectionné"
    )
    filename_suffix: bpy.props.StringProperty(
        name="Suffixe fichier",
        description="Suffixe ajouté au nom du fichier avant l'extension (ex: _thumb)",
        default="_thumb"
    )
