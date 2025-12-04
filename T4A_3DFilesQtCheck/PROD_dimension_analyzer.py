"""
Module d'analyse et comparaison des dimensions 3D
Analyse les dimensions réelles des modèles dans la scène et compare avec les données IA
"""

import bpy
import bmesh
from mathutils import Vector
import re
from typing import Tuple, Optional, Dict, Any
import itertools


def find_best_dimension_mapping(ai_dims: Tuple[float, float, float], 
                               model_dims: Tuple[float, float, float]) -> Dict[str, Any]:
    """
    Trouve le meilleur mapping entre dimensions IA et modèle en testant toutes les permutations.
    
    Args:
        ai_dims: Dimensions IA (largeur, hauteur, profondeur)
        model_dims: Dimensions modèle 3D (X, Y, Z)
        
    Returns:
        {
            'mapping': [(0,1), (1,2), (2,0)],  # Index mapping
            'difference_percentage': 2.3,
            'permutation_used': True,
            'method': 'best_permutation'
        }
    """
    try:
        best_diff = float('inf')
        best_mapping = None
        
        # Générer toutes les permutations possibles des indices (0,1,2)
        permutations = list(itertools.permutations([0, 1, 2]))
        
        for perm in permutations:
            # Appliquer la permutation aux dimensions modèle
            reordered_model = tuple(model_dims[i] for i in perm)
            
            # Calculer la différence avec cette permutation
            diff = calculate_dimension_difference(ai_dims, reordered_model)
            
            if diff < best_diff:
                best_diff = diff
                best_mapping = perm
        
        return {
            'mapping': best_mapping,
            'difference_percentage': best_diff,
            'permutation_used': best_mapping != (0, 1, 2),
            'method': 'best_permutation'
        }
        
    except Exception as e:
        print(f"Erreur find_best_dimension_mapping: {e}")
        return {
            'mapping': (0, 1, 2),  # Fallback identité
            'difference_percentage': 100.0,
            'permutation_used': False,
            'method': 'error_fallback'
        }


def smart_dimension_analysis(ai_text: str, ai_dims: Tuple[float, float, float],
                           model_dims: Tuple[float, float, float], 
                           auto_threshold: float = 0.01) -> Dict[str, Any]:
    """
    Analyse intelligente avec permutation automatique si écart trop important.
    
    Args:
        ai_text: Texte IA original
        ai_dims: Dimensions parsed de l'IA
        model_dims: Dimensions du modèle 3D
        auto_threshold: Seuil d'écart (en fraction) déclenchant la permutation auto
        
    Returns:
        {
            'original_difference': 25.4,
            'best_difference': 2.1,
            'mapping_used': [(0,2), (1,1), (2,0)],
            'permutation_applied': True,
            'confidence': 'HIGH',
            'method': 'auto_permutation'
        }
    """
    try:
        # 1. Calcul de l'écart original (mapping direct)
        original_diff = calculate_dimension_difference(ai_dims, model_dims)
        
        # 2. Vérifier si permutation nécessaire
        if original_diff <= auto_threshold * 100:  # Convertir en pourcentage
            # Écart acceptable, pas de permutation
            return {
                'original_difference': original_diff,
                'best_difference': original_diff,
                'mapping_used': (0, 1, 2),
                'permutation_applied': False,
                'confidence': 'HIGH',
                'method': 'direct_mapping'
            }
        
        # 3. Chercher le meilleur mapping par permutation
        mapping_result = find_best_dimension_mapping(ai_dims, model_dims)
        
        # 4. Déterminer le niveau de confiance
        best_diff = mapping_result['difference_percentage']
        if best_diff <= 5.0:
            confidence = 'HIGH'
        elif best_diff <= 15.0:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'original_difference': original_diff,
            'best_difference': best_diff,
            'mapping_used': mapping_result['mapping'],
            'permutation_applied': mapping_result['permutation_used'],
            'confidence': confidence,
            'method': 'auto_permutation' if mapping_result['permutation_used'] else 'direct_mapping'
        }
        
    except Exception as e:
        print(f"Erreur smart_dimension_analysis: {e}")
        return {
            'original_difference': 100.0,
            'best_difference': 100.0, 
            'mapping_used': (0, 1, 2),
            'permutation_applied': False,
            'confidence': 'LOW',
            'method': 'error_fallback'
        }


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
    Analyse intelligente des dimensions d'une collection avec auto-permutation.
    
    Args:
        collection_name: Nom de la collection à analyser
        ai_dimensions_text: Texte des dimensions trouvées par l'IA
        
    Returns:
        Dictionnaire avec tous les résultats d'analyse étendus:
        - Données classiques + permutation_applied, original_difference, mapping_method, etc.
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
        'difference_percentage': 0.0,
        # Nouvelles propriétés pour l'auto-permutation
        'permutation_applied': False,
        'original_difference': 0.0,
        'mapping_method': 'no_analysis',
        'mapping_used': (0, 1, 2),  # Mapping identité par défaut
        'confidence_level': 'LOW'
    }
    
    try:
        # 1. Calculer les dimensions de la scène
        scene_w, scene_h, scene_d = calculate_collection_dimensions(collection_name)
        original_scene_dims = (scene_w, scene_h, scene_d)
        
        result['scene_width'] = scene_w
        result['scene_height'] = scene_h
        result['scene_depth'] = scene_d
        result['scene_dimensions'] = format_dimensions(scene_w, scene_h, scene_d)
        
        # 2. Parser les dimensions IA si disponibles
        if ai_dimensions_text and ai_dimensions_text.strip():
            ai_dims = parse_ai_dimensions(ai_dimensions_text)
            
            if ai_dims:
                result['ai_analysis_success'] = True
                
                # 3. Analyse intelligente avec auto-permutation
                if scene_w > 0 or scene_h > 0 or scene_d > 0:
                    # Récupérer le seuil de permutation auto des préférences
                    try:
                        prefs = bpy.context.preferences.addons["T4A_3DFilesQtCheck"].preferences
                        auto_threshold = prefs.dimension_permutation_threshold
                    except:
                        auto_threshold = 0.01  # Fallback 1%
                    
                    # Analyse intelligente avec auto-permutation
                    smart_result = smart_dimension_analysis(ai_dimensions_text, ai_dims, original_scene_dims, auto_threshold)
                    
                    # Appliquer la meilleure permutation trouvée
                    best_mapping = smart_result['mapping_used']
                    final_scene_dims = tuple(original_scene_dims[i] for i in best_mapping)
                    
                    # Mettre à jour les dimensions de scène avec la permutation
                    result['scene_width'] = final_scene_dims[0]
                    result['scene_height'] = final_scene_dims[1] 
                    result['scene_depth'] = final_scene_dims[2]
                    result['scene_dimensions'] = format_dimensions(final_scene_dims[0], final_scene_dims[1], final_scene_dims[2])
                    
                    # Remplir les nouvelles informations de mapping
                    result['difference_percentage'] = smart_result['best_difference']
                    result['tolerance_status'] = determine_tolerance_status(smart_result['best_difference'])
                    result['permutation_applied'] = smart_result['permutation_applied']
                    result['original_difference'] = smart_result['original_difference']
                    result['mapping_method'] = smart_result['method']
                    result['mapping_used'] = best_mapping
                    result['confidence_level'] = smart_result['confidence']
                    
                    # Log si permutation appliquée
                    if smart_result['permutation_applied']:
                        mapping_str = " -> ".join([f"{['W','H','D'][i]}→{['X','Y','Z'][best_mapping[i]]}" for i in range(3)])
                        print(f"[DIMENSION_MAPPING] Collection '{collection_name}': Permutation appliquée ({mapping_str})")
                        print(f"[DIMENSION_MAPPING] Écart réduit de {smart_result['original_difference']:.1f}% à {smart_result['best_difference']:.1f}%")
                        
                else:
                    result['tolerance_status'] = 'NO_SCENE_DATA'
            else:
                result['ai_error'] = "Format de dimensions IA non reconnu"
                result['tolerance_status'] = 'AI_ERROR'
        else:
            result['tolerance_status'] = 'NO_AI_DATA'
            
    except Exception as e:
        result['ai_error'] = f"Erreur d'analyse: {str(e)[:50]}"
        result['tolerance_status'] = 'AI_ERROR'
        print(f"Erreur dans analyze_collection_dimensions: {e}")
    
    return result


def update_dimension_result(dim_result, analysis_result: Dict[str, Any]):
    """
    Met à jour un objet T4A_DimResult avec les résultats d'analyse étendue.
    
    Args:
        dim_result: Instance de T4A_DimResult à mettre à jour
        analysis_result: Dictionnaire de résultats d'analyse avec nouvelles propriétés
    """
    try:
        # Mapping des propriétés principales
        property_mapping = {
            'ai_analysis_success': 'ai_analysis_success',
            'ai_dimensions': 'ai_dimensions', 
            'ai_error': 'ai_analysis_error',  # Nom différent dans T4A_DimResult
            'scene_dimensions': 'scene_dimensions',
            'scene_width': 'scene_width',
            'scene_height': 'scene_height', 
            'scene_depth': 'scene_depth',
            'difference_percentage': 'difference_percentage',
            'tolerance_status': 'tolerance_status'
        }
        
        # Mettre à jour les propriétés classiques
        for result_key, dim_result_attr in property_mapping.items():
            if result_key in analysis_result and hasattr(dim_result, dim_result_attr):
                setattr(dim_result, dim_result_attr, analysis_result[result_key])
        
        # Mettre à jour les nouvelles propriétés de permutation
        new_properties = {
            'permutation_applied': 'permutation_applied',
            'original_difference': 'original_difference',
            'mapping_method': 'mapping_method',
            'confidence_level': 'confidence_level'
        }
        
        for result_key, dim_result_attr in new_properties.items():
            if result_key in analysis_result and hasattr(dim_result, dim_result_attr):
                setattr(dim_result, dim_result_attr, analysis_result[result_key])
        
        # Gestion spéciale pour le mapping utilisé (tuple vers propriétés séparées)
        if 'mapping_used' in analysis_result and hasattr(dim_result, 'mapping_used_x'):
            mapping = analysis_result['mapping_used']
            if isinstance(mapping, (tuple, list)) and len(mapping) >= 3:
                dim_result.mapping_used_x = mapping[0]
                dim_result.mapping_used_y = mapping[1] 
                dim_result.mapping_used_z = mapping[2]
        
        # Log des mises à jour importantes
        if analysis_result.get('permutation_applied', False):
            original = analysis_result.get('original_difference', 0.0)
            final = analysis_result.get('difference_percentage', 0.0)
            method = analysis_result.get('mapping_method', 'unknown')
            print(f"[UPDATE_DIM_RESULT] Permutation mise à jour: {original:.1f}% → {final:.1f}% ({method})")
                
    except Exception as e:
        print(f"Erreur lors de la mise à jour du résultat: {e}")


def convert_mapping_tuple_to_properties(mapping_tuple: Tuple[int, int, int]) -> Dict[str, int]:
    """
    Convertit un tuple de mapping en dictionnaire de propriétés séparées.
    
    Args:
        mapping_tuple: Tuple (x_index, y_index, z_index)
        
    Returns:
        Dict avec mapping_used_x, mapping_used_y, mapping_used_z
    """
    try:
        if not isinstance(mapping_tuple, (tuple, list)) or len(mapping_tuple) != 3:
            return {'mapping_used_x': 0, 'mapping_used_y': 1, 'mapping_used_z': 2}
            
        return {
            'mapping_used_x': mapping_tuple[0],
            'mapping_used_y': mapping_tuple[1],
            'mapping_used_z': mapping_tuple[2]
        }
    except:
        return {'mapping_used_x': 0, 'mapping_used_y': 1, 'mapping_used_z': 2}


# === OPÉRATEUR BLENDER POUR RECALCULER LES DIMENSIONS ===

class T4A_OT_RecalculateDimensions(bpy.types.Operator):
    """Recalcule les dimensions avec recherche automatique de permutation optimale"""
    bl_idname = "t4a.recalculate_dimensions"
    bl_label = "Recalculer Dimensions"
    bl_description = "Recalcule les dimensions avec recherche automatique de la meilleure permutation"
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
            collection = bpy.data.collections.get(self.collection_name)
            if not collection:
                self.report({'ERROR'}, f"Collection '{self.collection_name}' introuvable")
                return {'CANCELLED'}

            # Récupérer l'analyse IA depuis les custom properties
            ai_text = collection.get("ia_analysis_dimensions", "")
            if not ai_text:
                self.report({'WARNING'}, "Aucune analyse IA trouvée pour cette collection")
                return {'CANCELLED'}

            # Effectuer l'analyse complète avec permutation intelligente
            print(f"[DIMENSION_RECALC] Recalcul avec auto-permutation pour '{self.collection_name}'")
            analysis_result = analyze_collection_dimensions(self.collection_name, ai_text)

            if analysis_result['ai_analysis_success']:
                # Mettre à jour les données dans la scène si nécessaire
                scene = context.scene
                dims = getattr(scene, 't4a_dimensions', None)
                
                if dims:
                    # Chercher l'item correspondant pour mise à jour
                    target_item = None
                    for item in dims:
                        if item.collection_name == self.collection_name:
                            target_item = item
                            break
                    
                    if target_item:
                        # Mettre à jour les nouvelles propriétés
                        update_dimension_result(target_item, analysis_result)
                
                # Messages informatifs
                if analysis_result.get('permutation_applied', False):
                    mapping = analysis_result.get('mapping_used', (0,1,2))
                    mapping_str = " -> ".join([f"{['W','H','D'][i]}→{['X','Y','Z'][mapping[i]]}" for i in range(3)])
                    original_diff = analysis_result.get('original_difference', 0.0)
                    new_diff = analysis_result.get('difference_percentage', 0.0)
                    
                    status_msg = f"Permutation appliquée ({mapping_str}): {original_diff:.1f}% → {new_diff:.1f}%"
                    self.report({'INFO'}, f"Dimensions optimisées ! {status_msg}")
                else:
                    diff = analysis_result.get('difference_percentage', 0.0)
                    status_msg = f"Mapping direct conservé - Écart: {diff:.1f}%"
                    self.report({'INFO'}, f"Dimensions recalculées. {status_msg}")
                    
                print(f"[DIMENSION_RECALC] Résultat: {status_msg}")
            else:
                error_msg = analysis_result.get('ai_error', 'Erreur inconnue lors du recalcul')
                self.report({'ERROR'}, f"Échec du recalcul: {error_msg}")
                return {'CANCELLED'}

            # Forcer le rafraîchissement de l'UI
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Erreur lors du recalcul: {str(e)}")
            print(f"[DIMENSION_RECALC] Erreur: {e}")
            return {'CANCELLED'}
    
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