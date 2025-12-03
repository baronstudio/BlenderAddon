"""
Module d'analyse et comparaison des dimensions 3D
Analyse les dimensions réelles des modèles dans la scène et compare avec les données IA
"""

import bpy
import bmesh
from mathutils import Vector
import re
from typing import Tuple, Optional, Dict, Any


def calculate_collection_dimensions(collection_name: str) -> Tuple[float, float, float]:
    """
    Calcule les dimensions réelles d'une collection dans la scène 3D.
    
    Args:
        collection_name: Nom de la collection à analyser
        
    Returns:
        Tuple (largeur, hauteur, profondeur) en unités Blender
    """
    try:
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            return (0.0, 0.0, 0.0)
        
        # Récupérer tous les mesh objects de la collection
        mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH' and obj.data]
        
        if not mesh_objects:
            return (0.0, 0.0, 0.0)
        
        # Calculer la bounding box globale de tous les objets
        min_coords = Vector((float('inf'), float('inf'), float('inf')))
        max_coords = Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for obj in mesh_objects:
            # Obtenir la bounding box de l'objet dans l'espace monde
            bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            
            # Mettre à jour les coordonnées min/max
            for corner in bbox_corners:
                for i in range(3):
                    min_coords[i] = min(min_coords[i], corner[i])
                    max_coords[i] = max(max_coords[i], corner[i])
        
        # Calculer les dimensions
        dimensions = max_coords - min_coords
        
        # Appliquer l'échelle de la scène si nécessaire
        scene = bpy.context.scene
        scale_factor = getattr(scene, 't4a_scale_length', 1.0)
        if isinstance(scale_factor, (int, float)) and scale_factor != 1.0:
            dimensions *= scale_factor
        
        return (dimensions.x, dimensions.y, dimensions.z)
        
    except Exception as e:
        print(f"Erreur lors du calcul des dimensions pour {collection_name}: {e}")
        return (0.0, 0.0, 0.0)


def format_dimensions(width: float, height: float, depth: float, unit: str = "cm") -> str:
    """
    Formate les dimensions en string lisible.
    
    Args:
        width, height, depth: Dimensions en unités Blender
        unit: Unité d'affichage
        
    Returns:
        String formaté (ex: "L:10.5 H:20.0 P:5.2 cm")
    """
    try:
        return f"L:{width:.2f} H:{height:.2f} P:{depth:.2f} {unit}"
    except:
        return f"L:{width} H:{height} P:{depth} {unit}"


def parse_ai_dimensions(ai_text: str) -> Optional[Tuple[float, float, float]]:
    """
    Parse le texte des dimensions IA pour extraire des valeurs numériques.
    
    Args:
        ai_text: Texte contenant les dimensions de l'IA
        
    Returns:
        Tuple (largeur, hauteur, profondeur) ou None si impossible à parser
    """
    if not ai_text or not ai_text.strip():
        return None
    
    try:
        # Patterns de recherche pour différents formats
        patterns = [
            # Format: "L:10.5 H:20.0 P:5.2"
            r'L\s*:\s*([\d.]+).*?H\s*:\s*([\d.]+).*?P\s*:\s*([\d.]+)',
            # Format: "10.5 x 20.0 x 5.2"
            r'([\d.]+)\s*x\s*([\d.]+)\s*x\s*([\d.]+)',
            # Format: "largeur: 10.5, hauteur: 20.0, profondeur: 5.2"
            r'largeur\s*:\s*([\d.]+).*?hauteur\s*:\s*([\d.]+).*?profondeur\s*:\s*([\d.]+)',
            # Format: "Width: 10.5, Height: 20.0, Depth: 5.2"
            r'width\s*:\s*([\d.]+).*?height\s*:\s*([\d.]+).*?depth\s*:\s*([\d.]+)',
            # Format: "10.5cm x 20.0cm x 5.2cm"
            r'([\d.]+)\s*cm\s*x\s*([\d.]+)\s*cm\s*x\s*([\d.]+)\s*cm',
        ]
        
        ai_text_clean = ai_text.lower().strip()
        
        for pattern in patterns:
            match = re.search(pattern, ai_text_clean, re.IGNORECASE)
            if match:
                try:
                    w, h, d = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    return (w, h, d)
                except (ValueError, IndexError):
                    continue
        
        return None
        
    except Exception as e:
        print(f"Erreur lors du parsing des dimensions IA: {e}")
        return None


def calculate_dimension_difference(ai_dims: Tuple[float, float, float], 
                                scene_dims: Tuple[float, float, float]) -> float:
    """
    Calcule le pourcentage de différence maximum entre dimensions IA et scène.
    
    Args:
        ai_dims: Dimensions IA (largeur, hauteur, profondeur)
        scene_dims: Dimensions scène (largeur, hauteur, profondeur)
        
    Returns:
        Pourcentage de différence maximum (0-100)
    """
    try:
        max_diff = 0.0
        
        for i in range(3):
            ai_val = ai_dims[i]
            scene_val = scene_dims[i]
            
            if ai_val > 0 and scene_val > 0:
                diff = abs(ai_val - scene_val) / ai_val * 100
                max_diff = max(max_diff, diff)
        
        return min(max_diff, 100.0)  # Limiter à 100%
        
    except Exception as e:
        print(f"Erreur lors du calcul de différence: {e}")
        return 100.0


def determine_tolerance_status(difference_percentage: float, 
                             tolerance_warning: float = 10.0,
                             tolerance_error: float = 25.0) -> str:
    """
    Détermine le statut de tolérance basé sur le pourcentage de différence.
    
    Args:
        difference_percentage: Pourcentage de différence calculé
        tolerance_warning: Seuil d'avertissement (défaut: 10%)
        tolerance_error: Seuil d'erreur (défaut: 25%)
        
    Returns:
        Statut: 'OK', 'WARNING', 'ERROR'
    """
    if difference_percentage <= tolerance_warning:
        return 'OK'
    elif difference_percentage <= tolerance_error:
        return 'WARNING'
    else:
        return 'ERROR'


def analyze_collection_dimensions(collection_name: str, ai_dimensions_text: str = "") -> Dict[str, Any]:
    """
    Analyse complète des dimensions d'une collection avec comparaison IA.
    
    Args:
        collection_name: Nom de la collection à analyser
        ai_dimensions_text: Texte des dimensions trouvées par l'IA
        
    Returns:
        Dictionnaire avec tous les résultats d'analyse
    """
    result = {
        'collection_name': collection_name,
        'ai_analysis_success': False,
        'ai_dimensions': ai_dimensions_text,
        'ai_error': '',
        'scene_dimensions': '',
        'scene_width': 0.0,
        'scene_height': 0.0,
        'scene_depth': 0.0,
        'tolerance_status': 'NO_AI_DATA',
        'difference_percentage': 0.0
    }
    
    try:
        # 1. Calculer les dimensions de la scène
        scene_w, scene_h, scene_d = calculate_collection_dimensions(collection_name)
        result['scene_width'] = scene_w
        result['scene_height'] = scene_h
        result['scene_depth'] = scene_d
        result['scene_dimensions'] = format_dimensions(scene_w, scene_h, scene_d)
        
        # 2. Parser les dimensions IA si disponibles
        if ai_dimensions_text and ai_dimensions_text.strip():
            ai_dims = parse_ai_dimensions(ai_dimensions_text)
            
            if ai_dims:
                result['ai_analysis_success'] = True
                
                # 3. Calculer la différence si les deux sont disponibles
                if scene_w > 0 or scene_h > 0 or scene_d > 0:
                    scene_dims = (scene_w, scene_h, scene_d)
                    diff_percent = calculate_dimension_difference(ai_dims, scene_dims)
                    result['difference_percentage'] = diff_percent
                    result['tolerance_status'] = determine_tolerance_status(diff_percent)
                else:
                    result['tolerance_status'] = 'NO_AI_DATA'
            else:
                result['ai_error'] = "Format de dimensions IA non reconnu"
                result['tolerance_status'] = 'AI_ERROR'
        else:
            result['tolerance_status'] = 'NO_AI_DATA'
            
    except Exception as e:
        result['ai_error'] = f"Erreur d'analyse: {str(e)[:50]}"
        result['tolerance_status'] = 'AI_ERROR'
    
    return result


def update_dimension_result(dim_result, analysis_result: Dict[str, Any]):
    """
    Met à jour un objet T4A_DimResult avec les résultats d'analyse.
    
    Args:
        dim_result: Instance de T4A_DimResult à mettre à jour
        analysis_result: Dictionnaire de résultats d'analyse
    """
    try:
        # Mettre à jour toutes les propriétés
        for key, value in analysis_result.items():
            if hasattr(dim_result, key):
                setattr(dim_result, key, value)
                
    except Exception as e:
        print(f"Erreur lors de la mise à jour du résultat: {e}")


# === OPÉRATEUR BLENDER POUR RECALCULER LES DIMENSIONS ===

class T4A_OT_RecalculateDimensions(bpy.types.Operator):
    """Recalcule les dimensions d'une collection et compare avec l'IA"""
    bl_idname = "t4a.recalculate_dimensions"
    bl_label = "Recalculer Dimensions"
    bl_description = "Recalcule les dimensions de la collection et compare avec les données IA"
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
        
        try:
            # Trouver le résultat de dimension correspondant
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            
            if not dims:
                self.report({'ERROR'}, "Aucune donnée de dimension trouvée")
                return {'CANCELLED'}
            
            # Chercher l'item correspondant
            target_item = None
            for item in dims:
                if self.collection_name in item.name:
                    target_item = item
                    break
            
            if not target_item:
                self.report({'ERROR'}, f"Collection {self.collection_name} non trouvée")
                return {'CANCELLED'}
            
            # Effectuer l'analyse
            ai_text = getattr(target_item, 'ai_dimensions', '') or getattr(target_item, 'dimensions', '')
            analysis_result = analyze_collection_dimensions(self.collection_name, ai_text)
            
            # Mettre à jour le résultat
            update_dimension_result(target_item, analysis_result)
            
            # Forcer le rafraîchissement de l'UI
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            self.report({'INFO'}, f"Dimensions recalculées pour {self.collection_name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Erreur: {str(e)}")
            return {'CANCELLED'}


def register():
    """Enregistrement des classes Blender"""
    bpy.utils.register_class(T4A_OT_RecalculateDimensions)


def unregister():
    """Désenregistrement des classes Blender"""
    bpy.utils.unregister_class(T4A_OT_RecalculateDimensions)


if __name__ == "__main__":
    register()