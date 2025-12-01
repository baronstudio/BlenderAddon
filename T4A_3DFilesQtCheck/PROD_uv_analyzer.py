"""Module d'analyse des UV mappings pour les modèles 3D importés.

Fonctionnalités :
- Analyse des overlaps UV avec seuil configurable
- Détection des UVs hors limites (0-1)
- Analyse des proportions et distorsions
- Détection UDIM automatique
- Support multi-channels/couches UV
- Intégration avec le système d'import existant
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector
from typing import List, Dict, Tuple, Optional, Set
import time


class _SimpleLogger:
    def debug(self, msg, *args):
        try:
            from . import PROD_Parameters
            if PROD_Parameters.is_debug_mode():
                print(f"[T4A] [DEBUG] [UV] " + (msg % args if args else msg))
        except Exception:
            pass

    def info(self, msg, *args):
        print(f"[T4A] [INFO] [UV] " + (msg % args if args else msg))

    def error(self, msg, *args):
        print(f"[T4A] [ERROR] [UV] " + (msg % args if args else msg))


logger = _SimpleLogger()


def get_uv_preferences():
    """Récupère les préférences UV ou utilise les valeurs par défaut."""
    try:
        from . import PROD_Parameters
        addon_name = PROD_Parameters.__package__
        prefs = bpy.context.preferences.addons[addon_name].preferences
        return {
            'overlap_threshold': getattr(prefs, 'uv_overlap_threshold', 1.0) / 100.0,  # Convertir % en décimal
            'grid_resolution': getattr(prefs, 'uv_grid_resolution', 256),
            'square_tolerance': getattr(prefs, 'uv_square_tolerance', 0.1)
        }
    except Exception:
        return {
            'overlap_threshold': 0.01,  # 1%
            'grid_resolution': 256,
            'square_tolerance': 0.1
        }


def get_mesh_uv_data(mesh_obj):
    """Extrait toutes les données UV d'un mesh object."""
    if not mesh_obj or mesh_obj.type != 'MESH':
        return None
    
    mesh = mesh_obj.data
    if not mesh.uv_layers:
        return None
    
    uv_data = {
        'object_name': mesh_obj.name,
        'total_faces': len(mesh.polygons),
        'total_vertices': len(mesh.vertices),
        'uv_layers': {}
    }
    
    # Analyser chaque couche UV
    for layer_index, uv_layer in enumerate(mesh.uv_layers):
        layer_data = {
            'name': uv_layer.name,
            'is_active': uv_layer == mesh.uv_layers.active,
            'coordinates': [],
            'faces': [],
            'bounds': {'min_u': float('inf'), 'max_u': float('-inf'), 
                      'min_v': float('inf'), 'max_v': float('-inf')}
        }
        
        # Collecter les coordonnées UV pour chaque face
        for poly in mesh.polygons:
            face_uvs = []
            for loop_index in poly.loop_indices:
                uv_coord = uv_layer.data[loop_index].uv
                face_uvs.append((uv_coord.x, uv_coord.y))
                
                # Mettre à jour les bounds
                layer_data['bounds']['min_u'] = min(layer_data['bounds']['min_u'], uv_coord.x)
                layer_data['bounds']['max_u'] = max(layer_data['bounds']['max_u'], uv_coord.x)
                layer_data['bounds']['min_v'] = min(layer_data['bounds']['min_v'], uv_coord.y)
                layer_data['bounds']['max_v'] = max(layer_data['bounds']['max_v'], uv_coord.y)
            
            layer_data['faces'].append({
                'index': poly.index,
                'uvs': face_uvs,
                'area_3d': poly.area
            })
        
        uv_data['uv_layers'][layer_index] = layer_data
    
    return uv_data


def detect_uv_overlaps(uv_layer_data, grid_resolution=256, threshold=0.01):
    """Détecte les overlaps UV en utilisant une grille de rasterisation."""
    logger.debug("Détection overlaps avec grille %dx%d, seuil %.1f%%", 
                grid_resolution, grid_resolution, threshold * 100)
    
    # Créer une grille pour tracker la couverture
    grid = {}
    face_coverage = {}
    
    for face_data in uv_layer_data['faces']:
        face_index = face_data['index']
        uvs = face_data['uvs']
        
        # Calculer la bounding box de la face en coordonnées grille
        min_u = min(uv[0] for uv in uvs)
        max_u = max(uv[0] for uv in uvs)
        min_v = min(uv[1] for uv in uvs)
        max_v = max(uv[1] for uv in uvs)
        
        # Convertir en coordonnées de grille
        grid_min_u = int(min_u * grid_resolution)
        grid_max_u = int(max_u * grid_resolution) + 1
        grid_min_v = int(min_v * grid_resolution)
        grid_max_v = int(max_v * grid_resolution) + 1
        
        # Marquer les cellules de grille occupées par cette face
        occupied_cells = []
        for gu in range(max(0, grid_min_u), min(grid_resolution, grid_max_u)):
            for gv in range(max(0, grid_min_v), min(grid_resolution, grid_max_v)):
                # Test point-in-polygon simpliste pour la cellule de grille
                cell_center_u = (gu + 0.5) / grid_resolution
                cell_center_v = (gv + 0.5) / grid_resolution
                
                if _point_in_polygon((cell_center_u, cell_center_v), uvs):
                    cell_key = (gu, gv)
                    occupied_cells.append(cell_key)
                    
                    if cell_key not in grid:
                        grid[cell_key] = []
                    grid[cell_key].append(face_index)
        
        face_coverage[face_index] = occupied_cells
    
    # Identifier les overlaps
    overlapping_faces = set()
    overlap_count = 0
    
    for cell_key, face_list in grid.items():
        if len(face_list) > 1:
            overlap_count += 1
            overlapping_faces.update(face_list)
    
    # Calculer le pourcentage d'overlap
    total_cells = sum(len(cells) for cells in face_coverage.values())
    overlap_percentage = (overlap_count / max(1, total_cells)) * 100
    
    return {
        'has_overlaps': overlap_percentage > (threshold * 100),
        'overlap_percentage': overlap_percentage,
        'overlap_count': overlap_count,
        'overlapping_faces': list(overlapping_faces),
        'total_overlapping_faces': len(overlapping_faces)
    }


def _point_in_polygon(point, polygon):
    """Test simple point-in-polygon (ray casting algorithm)."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def detect_uvs_outside_bounds(uv_layer_data):
    """Détecte les UVs en dehors de l'espace 0-1."""
    outside_faces = []
    total_faces = len(uv_layer_data['faces'])
    
    for face_data in uv_layer_data['faces']:
        face_index = face_data['index']
        uvs = face_data['uvs']
        
        has_outside = False
        for u, v in uvs:
            if u < 0 or u > 1 or v < 0 or v > 1:
                has_outside = True
                break
        
        if has_outside:
            outside_faces.append({
                'index': face_index,
                'uvs': uvs,
                'extent': {
                    'min_u': min(uv[0] for uv in uvs),
                    'max_u': max(uv[0] for uv in uvs),
                    'min_v': min(uv[1] for uv in uvs),
                    'max_v': max(uv[1] for uv in uvs)
                }
            })
    
    outside_percentage = (len(outside_faces) / max(1, total_faces)) * 100
    
    return {
        'has_outside_uvs': len(outside_faces) > 0,
        'outside_percentage': outside_percentage,
        'outside_count': len(outside_faces),
        'outside_faces': outside_faces
    }


def analyze_uv_proportions(uv_layer_data, square_tolerance=0.1):
    """Analyse les proportions et distorsions UV."""
    bounds = uv_layer_data['bounds']
    
    # Calculer le ratio d'aspect du layout UV global
    width = bounds['max_u'] - bounds['min_u']
    height = bounds['max_v'] - bounds['min_v']
    
    if height > 0:
        aspect_ratio = width / height
        is_square = abs(aspect_ratio - 1.0) <= square_tolerance
    else:
        aspect_ratio = float('inf')
        is_square = False
    
    # Calculer la distorsion moyenne (aire UV vs aire 3D)
    total_uv_area = 0
    total_3d_area = 0
    distortions = []
    
    for face_data in uv_layer_data['faces']:
        uvs = face_data['uvs']
        area_3d = face_data['area_3d']
        
        # Calculer l'aire UV de la face (approximation triangulation)
        if len(uvs) >= 3:
            uv_area = _calculate_polygon_area_2d(uvs)
            total_uv_area += uv_area
            total_3d_area += area_3d
            
            if area_3d > 0:
                distortion = uv_area / area_3d
                distortions.append(distortion)
    
    average_distortion = sum(distortions) / len(distortions) if distortions else 0
    
    return {
        'is_square': is_square,
        'aspect_ratio': aspect_ratio,
        'layout_width': width,
        'layout_height': height,
        'total_uv_area': total_uv_area,
        'total_3d_area': total_3d_area,
        'average_distortion': average_distortion,
        'distortion_range': (min(distortions), max(distortions)) if distortions else (0, 0)
    }


def _calculate_polygon_area_2d(points):
    """Calcule l'aire d'un polygone 2D en utilisant la formule shoelace."""
    if len(points) < 3:
        return 0
    
    area = 0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2


def detect_udim_usage(uv_layer_data):
    """Détecte l'usage de UDIM en analysant les coordonnées UV."""
    udim_tiles = set()
    
    # Analyser toutes les coordonnées UV pour détecter les tiles UDIM
    for face_data in uv_layer_data['faces']:
        for u, v in face_data['uvs']:
            # Calculer l'index de tile UDIM
            tile_u = int(u)
            tile_v = int(v)
            
            # Format UDIM standard : 1001 + tile_u + (tile_v * 10)
            udim_id = 1001 + tile_u + (tile_v * 10)
            udim_tiles.add(udim_id)
    
    # Filtrer les tiles valides (généralement 1001-1100)
    valid_tiles = [tile for tile in udim_tiles if 1001 <= tile <= 1100]
    
    return {
        'uses_udim': len(valid_tiles) > 1,  # Plus d'une tile = UDIM
        'udim_tiles': ','.join(map(str, sorted(valid_tiles))),
        'udim_count': len(valid_tiles),
        'tile_list': sorted(valid_tiles)
    }


def analyze_collection_uvs(collection):
    """Analyse tous les UVs des mesh dans une collection."""
    logger.info("Début analyse UV pour collection: %s", collection.name)
    
    results = {
        'collection_name': collection.name,
        'total_objects': 0,
        'analyzed_objects': 0,
        'objects_results': {},
        'summary': {
            'total_faces': 0,
            'total_uv_layers': 0,
            'has_overlaps': False,
            'has_outside_uvs': False,
            'uses_udim': False,
            'average_aspect_ratio': 1.0,
            'analysis_success': True,
            'analysis_error': ''
        }
    }
    
    try:
        prefs = get_uv_preferences()
        # Filtrer les objets mesh en excluant les BoundingBoxes et autres helpers
        mesh_objects = [obj for obj in collection.all_objects 
                       if obj.type == 'MESH' 
                       and not obj.name.startswith('T4A_BBOX_')
                       and not obj.name.startswith('T4A_HELPER_')]
        results['total_objects'] = len(mesh_objects)
        
        total_faces = 0
        total_layers = 0
        global_overlaps = False
        global_outside = False
        global_udim = False
        aspect_ratios = []
        
        for mesh_obj in mesh_objects:
            try:
                obj_result = analyze_mesh_uvs(mesh_obj, prefs)
                if obj_result and obj_result['analysis_success']:
                    results['objects_results'][mesh_obj.name] = obj_result
                    results['analyzed_objects'] += 1
                    
                    # Accumuler les statistiques
                    for layer_result in obj_result['layers'].values():
                        total_faces += layer_result.get('total_faces', 0)
                        total_layers += 1
                        
                        if layer_result.get('overlaps', {}).get('has_overlaps'):
                            global_overlaps = True
                        if layer_result.get('outside', {}).get('has_outside_uvs'):
                            global_outside = True
                        if layer_result.get('udim', {}).get('uses_udim'):
                            global_udim = True
                        
                        proportions = layer_result.get('proportions', {})
                        if proportions.get('aspect_ratio', 0) > 0:
                            aspect_ratios.append(proportions['aspect_ratio'])
                            
            except Exception as e:
                logger.error("Erreur analyse UV objet %s: %s", mesh_obj.name, str(e))
        
        # Calculer le résumé global
        results['summary'].update({
            'total_faces': total_faces,
            'total_uv_layers': total_layers,
            'has_overlaps': global_overlaps,
            'has_outside_uvs': global_outside,
            'uses_udim': global_udim,
            'average_aspect_ratio': sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 1.0
        })
        
        logger.info("Analyse UV terminée: %d/%d objets analysés", 
                   results['analyzed_objects'], results['total_objects'])
        
    except Exception as e:
        logger.error("Erreur lors de l'analyse UV de la collection: %s", str(e))
        results['summary']['analysis_success'] = False
        results['summary']['analysis_error'] = str(e)
    
    return results


def analyze_mesh_uvs(mesh_obj, preferences=None):
    """Analyse complète des UVs d'un mesh object."""
    if not preferences:
        preferences = get_uv_preferences()
    
    logger.debug("Analyse UV de l'objet: %s", mesh_obj.name)
    
    try:
        uv_data = get_mesh_uv_data(mesh_obj)
        if not uv_data:
            return {
                'object_name': mesh_obj.name,
                'analysis_success': False,
                'analysis_error': 'Aucune couche UV trouvée',
                'layers': {}
            }
        
        result = {
            'object_name': mesh_obj.name,
            'total_faces': uv_data['total_faces'],
            'total_vertices': uv_data['total_vertices'],
            'uv_layers_count': len(uv_data['uv_layers']),
            'analysis_success': True,
            'analysis_error': '',
            'layers': {}
        }
        
        # Analyser chaque couche UV
        for layer_index, layer_data in uv_data['uv_layers'].items():
            logger.debug("Analyse couche UV: %s", layer_data['name'])
            
            layer_result = {
                'name': layer_data['name'],
                'is_active': layer_data['is_active'],
                'total_faces': len(layer_data['faces']),
                'bounds': layer_data['bounds']
            }
            
            # Analyse des overlaps
            layer_result['overlaps'] = detect_uv_overlaps(
                layer_data, 
                preferences['grid_resolution'], 
                preferences['overlap_threshold']
            )
            
            # Analyse des UVs hors limites
            layer_result['outside'] = detect_uvs_outside_bounds(layer_data)
            
            # Analyse des proportions
            layer_result['proportions'] = analyze_uv_proportions(
                layer_data, 
                preferences['square_tolerance']
            )
            
            # Détection UDIM
            layer_result['udim'] = detect_udim_usage(layer_data)
            
            result['layers'][layer_index] = layer_result
        
        return result
        
    except Exception as e:
        logger.error("Erreur analyse UV objet %s: %s", mesh_obj.name, str(e))
        return {
            'object_name': mesh_obj.name,
            'analysis_success': False,
            'analysis_error': str(e),
            'layers': {}
        }


class T4A_OT_AnalyzeUVs(bpy.types.Operator):
    """Opérateur pour analyser les UVs d'une collection."""
    bl_idname = "t4a.analyze_uvs"
    bl_label = "Analyze UVs"
    bl_description = "Analyse les UV mappings de la collection sélectionnée"
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
        
        # Analyser les UVs
        start_time = time.time()
        result = analyze_collection_uvs(collection)
        analysis_time = time.time() - start_time
        
        # Mettre à jour les résultats dans les propriétés de scène
        try:
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                # Chercher l'entrée correspondante
                parts = self.collection_name.split('_', 1)
                filename = parts[1] if len(parts) >= 2 else self.collection_name
                
                dim_item = None
                for item in dims:
                    if item.name == filename or filename in item.name:
                        dim_item = item
                        break
                
                if dim_item and hasattr(dim_item, 'uv_result') and dim_item.uv_result:
                    uv_res = dim_item.uv_result
                    summary = result['summary']
                    
                    uv_res.analysis_success = summary['analysis_success']
                    uv_res.total_faces = summary['total_faces']
                    uv_res.uv_layers_count = summary['total_uv_layers']
                    uv_res.has_overlaps = summary['has_overlaps']
                    uv_res.has_outside_uvs = summary['has_outside_uvs']
                    uv_res.uses_udim = summary['uses_udim']
                    uv_res.aspect_ratio = summary['average_aspect_ratio']
                    uv_res.is_square = abs(summary['average_aspect_ratio'] - 1.0) <= get_uv_preferences()['square_tolerance']
                    uv_res.analysis_error = summary.get('analysis_error', '')
                    
                    # Calculer des statistiques agrégées depuis les objets individuels
                    overlap_percentages = []
                    outside_percentages = []
                    udim_tiles_set = set()
                    
                    for obj_result in result['objects_results'].values():
                        for layer_result in obj_result['layers'].values():
                            overlap_percentages.append(layer_result['overlaps']['overlap_percentage'])
                            outside_percentages.append(layer_result['outside']['outside_percentage'])
                            if layer_result['udim']['uses_udim']:
                                udim_tiles_set.update(layer_result['udim']['tile_list'])
                    
                    uv_res.overlap_percentage = max(overlap_percentages) if overlap_percentages else 0.0
                    uv_res.outside_percentage = max(outside_percentages) if outside_percentages else 0.0
                    uv_res.overlap_count = sum(1 for p in overlap_percentages if p > 0)
                    uv_res.outside_count = sum(1 for p in outside_percentages if p > 0)
                    uv_res.udim_tiles = ','.join(map(str, sorted(udim_tiles_set)))
                    uv_res.udim_count = len(udim_tiles_set)
                    
        except Exception as e:
            logger.error("Erreur mise à jour propriétés UV: %s", str(e))
        
        # Rapport de succès
        if result['summary']['analysis_success']:
            self.report({'INFO'}, 
                       f"Analyse UV réussie: {result['analyzed_objects']} objets analysés en {analysis_time:.2f}s")
        else:
            self.report({'ERROR'}, 
                       f"Analyse UV échouée: {result['summary']['analysis_error']}")
        
        return {'FINISHED'}


# Classes à enregistrer
classes = (
    T4A_OT_AnalyzeUVs,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)