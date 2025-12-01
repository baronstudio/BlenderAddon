"""Module de gestion des textures pour les modèles 3D importés.

Fonctionnalités :
- Analyse des textures packées et externes
- Extraction et consolidation des textures
- Génération de statistiques détaillées
- Intégration avec le système d'import existant
"""

import os
import shutil
import bpy
import bmesh
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class _SimpleLogger:
    def debug(self, msg, *args):
        try:
            from . import PROD_Parameters
            if PROD_Parameters.is_debug_mode():
                print(f"[T4A] [DEBUG] [Textures] " + (msg % args if args else msg))
        except Exception:
            pass

    def info(self, msg, *args):
        print(f"[T4A] [INFO] [Textures] " + (msg % args if args else msg))

    def error(self, msg, *args):
        print(f"[T4A] [ERROR] [Textures] " + (msg % args if args else msg))


logger = _SimpleLogger()

# Extensions de textures supportées
SUPPORTED_TEXTURE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.tga', '.hdr', '.exr', 
    '.webp', '.gif', '.bmp', '.ai', '.svg', '.dds', '.ktx', '.basis'
}

# Types de textures communs pour la détection de doublons intelligents
TEXTURE_TYPES = [
    'albedo', 'diffuse', 'base_color', 'basecolor',
    'normal', 'normalmap', 'normal_map',
    'roughness', 'rough', 'metallic', 'metalness',
    'specular', 'spec', 'glossiness', 'gloss',
    'displacement', 'displace', 'height', 'bump',
    'ambient_occlusion', 'ao', 'occlusion',
    'emission', 'emissive', 'glow',
    'opacity', 'alpha', 'transparency',
    'subsurface', 'sss', 'transmission'
]


def get_texture_type_from_name(filename: str) -> str:
    """Détecte le type de texture à partir du nom de fichier."""
    name_lower = filename.lower()
    for tex_type in TEXTURE_TYPES:
        if tex_type in name_lower:
            return tex_type
    return 'unknown'


def get_image_info(image: bpy.types.Image) -> Dict:
    """Récupère les informations détaillées d'une image Blender."""
    info = {
        'name': image.name,
        'filepath': getattr(image, 'filepath', ''),
        'resolution': f"{image.size[0]}x{image.size[1]}" if len(image.size) >= 2 else "unknown",
        'width': image.size[0] if len(image.size) >= 2 else 0,
        'height': image.size[1] if len(image.size) >= 2 else 0,
        'format': getattr(image, 'file_format', 'unknown'),
        'colorspace': getattr(image.colorspace_settings, 'name', 'unknown'),
        'is_packed': hasattr(image, 'packed_file') and image.packed_file is not None,
        'source': getattr(image, 'source', 'unknown'),
        'size_kb': 0,
        'texture_type': get_texture_type_from_name(image.name),
        'exists': False
    }
    
    # Calculer la taille si le fichier existe
    if info['filepath'] and os.path.exists(info['filepath']):
        try:
            info['size_kb'] = os.path.getsize(info['filepath']) / 1024.0
            info['exists'] = True
        except Exception:
            pass
    elif info['is_packed'] and image.packed_file:
        info['size_kb'] = len(image.packed_file.data) / 1024.0
        info['exists'] = True
    
    return info


def find_missing_textures(base_path: str, missing_names: List[str]) -> Dict[str, str]:
    """Recherche les textures manquantes dans le dossier et ses sous-dossiers."""
    found_textures = {}
    base_path = Path(base_path)
    
    if not base_path.exists():
        return found_textures
    
    # Construire une liste de tous les fichiers de texture
    all_texture_files = []
    for ext in SUPPORTED_TEXTURE_EXTENSIONS:
        all_texture_files.extend(base_path.rglob(f"*{ext}"))
    
    logger.debug("Recherche de textures dans: %s", base_path)
    logger.debug("Fichiers de texture trouvés: %d", len(all_texture_files))
    
    # Pour chaque texture manquante, chercher des correspondances
    for missing_name in missing_names:
        missing_stem = Path(missing_name).stem.lower()
        best_match = None
        best_score = 0
        
        for texture_file in all_texture_files:
            file_stem = texture_file.stem.lower()
            
            # Score de correspondance basé sur la similarité des noms
            score = 0
            if file_stem == missing_stem:
                score = 100  # Correspondance exacte
            elif missing_stem in file_stem or file_stem in missing_stem:
                score = 80   # Correspondance partielle
            elif any(word in file_stem for word in missing_stem.split('_')):
                score = 50   # Correspondance de mots
            
            if score > best_score:
                best_score = score
                best_match = str(texture_file)
        
        if best_match and best_score >= 50:  # Seuil de correspondance
            found_textures[missing_name] = best_match
            logger.debug("Correspondance trouvée: %s -> %s (score: %d)", missing_name, best_match, best_score)
    
    return found_textures


def create_texture_directory(model_filepath: str) -> str:
    """Crée le dossier de destination pour les textures."""
    model_path = Path(model_filepath)
    model_dir = model_path.parent
    model_name = model_path.stem
    
    texture_dir = model_dir / f"textures_{model_name}"
    texture_dir.mkdir(exist_ok=True)
    
    return str(texture_dir)


def generate_unique_filename(target_dir: str, original_name: str, texture_type: str = None) -> str:
    """Génère un nom de fichier unique en évitant les doublons."""
    target_path = Path(target_dir)
    original_path = Path(original_name)
    base_name = original_path.stem
    extension = original_path.suffix
    
    # Si on connaît le type de texture, l'intégrer dans le nom
    if texture_type and texture_type != 'unknown':
        if texture_type not in base_name.lower():
            base_name = f"{base_name}_{texture_type}"
    
    # Chercher un nom de fichier disponible
    counter = 0
    while True:
        if counter == 0:
            new_name = f"{base_name}{extension}"
        else:
            new_name = f"{base_name}_{counter:02d}{extension}"
        
        new_path = target_path / new_name
        if not new_path.exists():
            return new_name
        counter += 1


def extract_packed_textures(collection: bpy.types.Collection, texture_dir: str) -> List[Dict]:
    """Extrait les textures packées du modèle vers le dossier de destination."""
    extracted_textures = []
    
    # Parcourir tous les matériaux de la collection
    materials = set()
    for obj in collection.all_objects:
        if hasattr(obj, 'material_slots'):
            for slot in obj.material_slots:
                if slot.material:
                    materials.add(slot.material)
    
    # Extraire les images packées
    images_to_extract = set()
    for material in materials:
        if material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    if hasattr(node.image, 'packed_file') and node.image.packed_file:
                        images_to_extract.add(node.image)
    
    logger.info("Images packées trouvées: %d", len(images_to_extract))
    
    for image in images_to_extract:
        try:
            # Générer un nom de fichier unique
            texture_type = get_texture_type_from_name(image.name)
            unique_name = generate_unique_filename(texture_dir, image.name, texture_type)
            target_path = os.path.join(texture_dir, unique_name)
            
            # Extraire l'image
            image.filepath_raw = target_path
            image.save()
            
            # Mettre à jour les informations de l'image
            info = get_image_info(image)
            info['extracted_to'] = target_path
            extracted_textures.append(info)
            
            logger.debug("Texture extraite: %s -> %s", image.name, target_path)
            
        except Exception as e:
            logger.error("Erreur lors de l'extraction de %s: %s", image.name, str(e))
    
    return extracted_textures


def consolidate_external_textures(collection: bpy.types.Collection, model_filepath: str, texture_dir: str) -> List[Dict]:
    """Consolide les textures externes dans le dossier de destination."""
    consolidated_textures = []
    
    # Identifier les textures manquantes ou externes
    materials = set()
    for obj in collection.all_objects:
        if hasattr(obj, 'material_slots'):
            for slot in obj.material_slots:
                if slot.material:
                    materials.add(slot.material)
    
    missing_textures = []
    existing_textures = []
    
    for material in materials:
        if material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == 'TEX_IMAGE' and node.image:
                    image = node.image
                    if not (hasattr(image, 'packed_file') and image.packed_file):
                        # Texture externe
                        if image.filepath and os.path.exists(image.filepath):
                            existing_textures.append(image)
                        else:
                            missing_textures.append(image.name)
    
    logger.info("Textures externes existantes: %d", len(existing_textures))
    logger.info("Textures manquantes: %d", len(missing_textures))
    
    # Chercher les textures manquantes
    model_dir = os.path.dirname(model_filepath)
    found_textures = find_missing_textures(model_dir, missing_textures)
    
    # Copier les textures existantes
    for image in existing_textures:
        try:
            texture_type = get_texture_type_from_name(image.name)
            unique_name = generate_unique_filename(texture_dir, os.path.basename(image.filepath), texture_type)
            target_path = os.path.join(texture_dir, unique_name)
            
            shutil.copy2(image.filepath, target_path)
            
            # Mettre à jour le chemin de l'image
            image.filepath = target_path
            
            info = get_image_info(image)
            info['consolidated_to'] = target_path
            consolidated_textures.append(info)
            
            logger.debug("Texture copiée: %s -> %s", image.filepath, target_path)
            
        except Exception as e:
            logger.error("Erreur lors de la copie de %s: %s", image.name, str(e))
    
    # Copier les textures trouvées pour les manquantes
    for missing_name, found_path in found_textures.items():
        try:
            texture_type = get_texture_type_from_name(missing_name)
            unique_name = generate_unique_filename(texture_dir, missing_name, texture_type)
            target_path = os.path.join(texture_dir, unique_name)
            
            shutil.copy2(found_path, target_path)
            
            # Créer une info factice pour cette texture
            info = {
                'name': missing_name,
                'filepath': target_path,
                'resolution': 'unknown',
                'width': 0,
                'height': 0,
                'format': Path(found_path).suffix[1:].upper(),
                'colorspace': 'unknown',
                'is_packed': False,
                'source': 'FILE',
                'size_kb': os.path.getsize(found_path) / 1024.0,
                'texture_type': texture_type,
                'exists': True,
                'recovered_from': found_path
            }
            consolidated_textures.append(info)
            
            logger.debug("Texture récupérée: %s -> %s", found_path, target_path)
            
        except Exception as e:
            logger.error("Erreur lors de la récupération de %s: %s", missing_name, str(e))
    
    return consolidated_textures


def calculate_texture_statistics(texture_list: List[Dict]) -> Dict:
    """Calcule les statistiques des textures."""
    if not texture_list:
        return {
            'count': 0,
            'total_size_kb': 0.0,
            'max_resolution': 'N/A',
            'min_resolution': 'N/A',
            'formats': {},
            'types': {},
            'avg_size_kb': 0.0
        }
    
    total_size = sum(tex.get('size_kb', 0) for tex in texture_list)
    resolutions = []
    formats = {}
    types = {}
    
    for tex in texture_list:
        # Résolutions
        if tex.get('width', 0) > 0 and tex.get('height', 0) > 0:
            resolutions.append((tex['width'], tex['height']))
        
        # Formats
        fmt = tex.get('format', 'unknown')
        formats[fmt] = formats.get(fmt, 0) + 1
        
        # Types
        tex_type = tex.get('texture_type', 'unknown')
        types[tex_type] = types.get(tex_type, 0) + 1
    
    # Résolutions min/max
    max_res = min_res = 'N/A'
    if resolutions:
        max_w, max_h = max(resolutions, key=lambda x: x[0] * x[1])
        min_w, min_h = min(resolutions, key=lambda x: x[0] * x[1])
        max_res = f"{max_w}x{max_h}"
        min_res = f"{min_w}x{min_h}"
    
    return {
        'count': len(texture_list),
        'total_size_kb': round(total_size, 2),
        'max_resolution': max_res,
        'min_resolution': min_res,
        'formats': formats,
        'types': types,
        'avg_size_kb': round(total_size / len(texture_list), 2) if texture_list else 0.0
    }


def analyze_and_consolidate_textures(collection: bpy.types.Collection, model_filepath: str) -> Dict:
    """Fonction principale : analyse et consolide les textures d'un modèle."""
    logger.info("Début analyse textures pour: %s", collection.name)
    
    try:
        # Créer le dossier de destination
        texture_dir = create_texture_directory(model_filepath)
        logger.info("Dossier textures: %s", texture_dir)
        
        # Extraire les textures packées
        extracted_textures = extract_packed_textures(collection, texture_dir)
        
        # Consolider les textures externes
        consolidated_textures = consolidate_external_textures(collection, model_filepath, texture_dir)
        
        # Combiner toutes les textures
        all_textures = extracted_textures + consolidated_textures
        
        # Calculer les statistiques
        stats = calculate_texture_statistics(all_textures)
        
        result = {
            'success': True,
            'texture_directory': texture_dir,
            'extracted_count': len(extracted_textures),
            'consolidated_count': len(consolidated_textures),
            'total_textures': len(all_textures),
            'statistics': stats,
            'texture_list': all_textures
        }
        
        logger.info("Analyse terminée: %d textures extraites, %d consolidées", 
                   len(extracted_textures), len(consolidated_textures))
        
        return result
        
    except Exception as e:
        logger.error("Erreur lors de l'analyse des textures: %s", str(e))
        return {
            'success': False,
            'error': str(e),
            'texture_directory': '',
            'extracted_count': 0,
            'consolidated_count': 0,
            'total_textures': 0,
            'statistics': calculate_texture_statistics([]),
            'texture_list': []
        }


class T4A_OT_ConsolidateTextures(bpy.types.Operator):
    """Opérateur pour consolider manuellement les textures d'une collection."""
    bl_idname = "t4a.consolidate_textures"
    bl_label = "Consolidate Textures"
    bl_description = "Analyse et consolide les textures de la collection sélectionnée"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="Nom de la collection à analyser",
        default=""
    )
    
    def execute(self, context):
        if not self.collection_name:
            self.report({'ERROR'}, "Nom de collection requis")
            return {'CANCELLED'}
        
        # Trouver la collection
        collection = bpy.data.collections.get(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' introuvable")
            return {'CANCELLED'}
        
        # Essayer de deviner le chemin du fichier original
        # Format attendu: "EXT_filename.ext"
        try:
            parts = self.collection_name.split('_', 1)
            if len(parts) >= 2:
                filename = parts[1]
                # Essayer de trouver le fichier dans le contexte des préférences
                from . import PROD_Parameters
                addon_name = PROD_Parameters.__package__
                try:
                    prefs = context.preferences.addons[addon_name].preferences
                    base_path = prefs.scan_path
                    if base_path:
                        model_path = os.path.join(base_path, filename)
                        if os.path.exists(model_path):
                            result = analyze_and_consolidate_textures(collection, model_path)
                        else:
                            # Utiliser un chemin factice basé sur le nom de la collection
                            fake_path = os.path.join(base_path, filename)
                            result = analyze_and_consolidate_textures(collection, fake_path)
                    else:
                        self.report({'ERROR'}, "Chemin de scan non configuré dans les préférences")
                        return {'CANCELLED'}
                except Exception:
                    # Fallback avec chemin factice
                    fake_path = f"/tmp/{filename}"
                    result = analyze_and_consolidate_textures(collection, fake_path)
            else:
                self.report({'ERROR'}, "Format de nom de collection non reconnu")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Erreur lors de l'analyse: {str(e)}")
            return {'CANCELLED'}
        
        # Mettre à jour les résultats dans les propriétés de scène
        try:
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                # Chercher l'entrée correspondante
                filename = parts[1] if len(parts) >= 2 else self.collection_name
                dim_item = None
                for item in dims:
                    if item.name == filename:
                        dim_item = item
                        break
                
                if dim_item and hasattr(dim_item, 'texture_result') and dim_item.texture_result:
                    tex_res = dim_item.texture_result
                    if result['success']:
                        stats = result['statistics']
                        tex_res.analysis_success = True
                        tex_res.texture_count = stats['count']
                        tex_res.total_size_kb = stats['total_size_kb']
                        tex_res.max_resolution = stats['max_resolution']
                        tex_res.min_resolution = stats['min_resolution']
                        tex_res.texture_directory = result['texture_directory']
                        tex_res.extracted_count = result['extracted_count']
                        tex_res.consolidated_count = result['consolidated_count']
                        tex_res.analysis_error = ""
                    else:
                        tex_res.analysis_success = False
                        tex_res.analysis_error = result.get('error', 'Erreur inconnue')
        except Exception as e:
            logger.error("Erreur mise à jour propriétés: %s", str(e))
        
        if result['success']:
            stats = result['statistics']
            self.report({'INFO'}, 
                       f"Consolidation réussie: {stats['count']} textures, "
                       f"{stats['total_size_kb']:.1f} KB, "
                       f"Dossier: {os.path.basename(result['texture_directory'])}")
        else:
            self.report({'ERROR'}, f"Consolidation échouée: {result.get('error', 'Erreur inconnue')}")
        
        return {'FINISHED'}


# Classes à enregistrer
classes = (
    T4A_OT_ConsolidateTextures,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)