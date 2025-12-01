"""
Module d'analyse de topologie 3D pour T4A_3DFilesQtCheck.
Analyse la qualité géométrique et topologique des mesh 3D.

Fonctionnalités:
- Détection manifold/non-manifold
- Analyse des normales
- Détection vertices isolés
- Détection vertices dupliqués
- Analyse vertex colors
- Distribution des types de polygones
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector
from collections import defaultdict

# Import du logger personnalisé
try:
    from . import PROD_autoload
    logger = PROD_autoload._SimpleLogger("TOPOLOGY", debug_mode=True)
except ImportError:
    # Fallback logger basique
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("T4A_TOPOLOGY")


def create_progress_bar(progress, width=20):
    """Crée une barre de progression ASCII."""
    filled = int(progress * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}]"


def update_topology_progress(context, current, total, mesh_name):
    """Met à jour la progression pour l'analyse topologique."""
    if total == 0:
        return
    
    progress = current / total
    percentage = int(progress * 100)
    
    # Mise à jour de la barre de statut Blender
    if context and hasattr(context, 'window_manager'):
        try:
            context.window_manager.progress_update(progress)
        except:
            pass
    
    # Affichage console avec barre de progression
    bar = create_progress_bar(progress, width=20)
    logger.info("%s %d%% - Mesh %d/%d: %s", 
                bar, percentage, current, total, mesh_name[:40])


def get_topology_preferences():
    """Récupère les préférences de topologie de l'addon."""
    try:
        preferences = bpy.context.preferences.addons['T4A_3DFilesQtCheck'].preferences
        return {
            'duplicate_tolerance': getattr(preferences, 'topology_duplicate_tolerance', 0.0001),
            'normal_threshold': getattr(preferences, 'topology_normal_threshold', 0.5),
            'analyze_vertex_colors': getattr(preferences, 'topology_analyze_vertex_colors', True)
        }
    except Exception:
        return {
            'duplicate_tolerance': 0.0001,  # 0.1mm
            'normal_threshold': 0.5,       # 50% cohérence minimum
            'analyze_vertex_colors': True
        }


def get_mesh_topology_data(mesh_obj):
    """Extrait les données de base pour l'analyse topologique."""
    if not mesh_obj or mesh_obj.type != 'MESH':
        return None
    
    mesh = mesh_obj.data
    if not mesh.vertices or not mesh.polygons:
        return None
    
    topology_data = {
        'object_name': mesh_obj.name,
        'total_vertices': len(mesh.vertices),
        'total_edges': len(mesh.edges),
        'total_polygons': len(mesh.polygons),
        'has_vertex_colors': len(mesh.vertex_colors) > 0,
        'vertex_color_layers': len(mesh.vertex_colors)
    }
    
    return topology_data


def detect_manifold_issues(mesh_obj):
    """Détecte les problèmes de manifold dans le mesh."""
    logger.debug("Analyse manifold pour objet: %s", mesh_obj.name)
    
    # Créer une copie bmesh pour l'analyse
    bm = bmesh.new()
    bm.from_mesh(mesh_obj.data)
    
    # Assurer les indices des faces
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    
    non_manifold_edges = []
    non_manifold_verts = []
    
    # Détecter les edges non-manifold
    for edge in bm.edges:
        if not edge.is_manifold:
            non_manifold_edges.append({
                'index': edge.index,
                'face_count': len(edge.link_faces),
                'vertices': [v.index for v in edge.verts]
            })
    
    # Détecter les vertices non-manifold
    for vert in bm.verts:
        if not vert.is_manifold:
            non_manifold_verts.append({
                'index': vert.index,
                'edge_count': len(vert.link_edges),
                'face_count': len(vert.link_faces),
                'coordinate': tuple(vert.co)
            })
    
    bm.free()
    
    result = {
        'has_manifold_issues': len(non_manifold_edges) > 0 or len(non_manifold_verts) > 0,
        'manifold_error_count': len(non_manifold_edges) + len(non_manifold_verts),
        'non_manifold_edges': non_manifold_edges,
        'non_manifold_vertices': non_manifold_verts,
        'edge_issues_count': len(non_manifold_edges),
        'vertex_issues_count': len(non_manifold_verts)
    }
    
    logger.debug("Manifold: %d erreurs détectées", result['manifold_error_count'])
    return result


def analyze_face_normals(mesh_obj, threshold=0.5):
    """Analyse la cohérence des normales de faces."""
    logger.debug("Analyse normales pour objet: %s", mesh_obj.name)
    
    mesh = mesh_obj.data
    mesh.calc_loop_triangles()
    
    # Calculer les normales si nécessaire
    if not mesh.has_custom_normals:
        mesh.calc_normals()
    
    inconsistent_faces = []
    total_faces = len(mesh.polygons)
    
    if total_faces == 0:
        return {
            'normal_consistency': 100.0,
            'inverted_faces_count': 0,
            'has_normal_issues': False,
            'inconsistent_faces': []
        }
    
    # OPTIMISATION: Créer un dictionnaire edge -> faces pour éviter O(n²)
    logger.debug("Construction du dictionnaire d'adjacence...")
    edge_to_faces = {}
    
    for poly in mesh.polygons:
        for edge_key in poly.edge_keys:
            # Normaliser la clé d'edge (ordre des vertices)
            normalized_edge = tuple(sorted(edge_key))
            if normalized_edge not in edge_to_faces:
                edge_to_faces[normalized_edge] = []
            edge_to_faces[normalized_edge].append(poly)
    
    logger.debug("Analyse de %d faces avec dictionnaire d'adjacence", total_faces)
    
    # Analyser chaque face
    for i, poly in enumerate(mesh.polygons):
        # Log de progression tous les 1000 faces
        if i > 0 and i % 1000 == 0:
            logger.debug("Analysé %d/%d faces", i, total_faces)
            
        face_normal = poly.normal
        
        # Trouver les faces adjacentes RAPIDEMENT via le dictionnaire
        adjacent_normals = []
        for edge_key in poly.edge_keys:
            normalized_edge = tuple(sorted(edge_key))
            if normalized_edge in edge_to_faces:
                for adjacent_poly in edge_to_faces[normalized_edge]:
                    if adjacent_poly.index != poly.index:
                        adjacent_normals.append(adjacent_poly.normal)
        
        # Calculer la cohérence moyenne
        if adjacent_normals:
            consistency_scores = []
            for adj_normal in adjacent_normals:
                dot_product = face_normal.dot(adj_normal)
                consistency_scores.append(max(0, dot_product))
            
            avg_consistency = sum(consistency_scores) / len(consistency_scores)
            
            if avg_consistency < threshold:
                inconsistent_faces.append({
                    'index': poly.index,
                    'normal': tuple(face_normal),
                    'consistency': avg_consistency,
                    'center': tuple(poly.center)
                })
    
    inverted_count = len(inconsistent_faces)
    consistency = ((total_faces - inverted_count) / total_faces) * 100
    
    result = {
        'normal_consistency': consistency,
        'inverted_faces_count': inverted_count,
        'has_normal_issues': inverted_count > 0,
        'inconsistent_faces': inconsistent_faces[:10]  # Limiter à 10 pour éviter surcharge
    }
    
    logger.debug("Normales: %.1f%% cohérence, %d faces inversées", consistency, inverted_count)
    return result


def find_isolated_vertices(mesh_obj):
    """Trouve les vertices isolés (non connectés à des faces)."""
    logger.debug("Recherche vertices isolés pour objet: %s", mesh_obj.name)
    
    mesh = mesh_obj.data
    connected_vertices = set()
    
    # Collecter tous les vertices utilisés par les faces
    for poly in mesh.polygons:
        for vertex_index in poly.vertices:
            connected_vertices.add(vertex_index)
    
    # Trouver les vertices isolés
    isolated_vertices = []
    for i, vertex in enumerate(mesh.vertices):
        if i not in connected_vertices:
            isolated_vertices.append({
                'index': i,
                'coordinate': tuple(vertex.co)
            })
    
    result = {
        'isolated_vertices_count': len(isolated_vertices),
        'has_isolated_vertices': len(isolated_vertices) > 0,
        'isolated_vertices': isolated_vertices
    }
    
    logger.debug("Vertices isolés: %d détectés", len(isolated_vertices))
    return result


def detect_duplicate_vertices(mesh_obj, tolerance=0.0001):
    """Détecte les vertices en superposition."""
    logger.debug("Détection doublons pour objet: %s (tolérance: %.6f)", mesh_obj.name, tolerance)
    
    mesh = mesh_obj.data
    vertices = mesh.vertices
    duplicates = []
    processed = set()
    
    # Utiliser un dictionnaire spatial pour optimiser la recherche
    spatial_hash = defaultdict(list)
    grid_size = tolerance * 10  # Grille plus large pour éviter les faux négatifs
    
    # Hash spatial des vertices
    for i, vertex in enumerate(vertices):
        grid_x = int(vertex.co.x / grid_size)
        grid_y = int(vertex.co.y / grid_size)
        grid_z = int(vertex.co.z / grid_size)
        spatial_hash[(grid_x, grid_y, grid_z)].append(i)
    
    # Chercher les doublons dans chaque cellule et voisines
    for grid_pos, vertex_indices in spatial_hash.items():
        if len(vertex_indices) < 2:
            continue
            
        # Vérifier aussi les cellules voisines
        neighbor_indices = list(vertex_indices)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    if dx == dy == dz == 0:
                        continue
                    neighbor_pos = (grid_pos[0] + dx, grid_pos[1] + dy, grid_pos[2] + dz)
                    if neighbor_pos in spatial_hash:
                        neighbor_indices.extend(spatial_hash[neighbor_pos])
        
        # Comparer les distances réelles
        for i in range(len(neighbor_indices)):
            for j in range(i + 1, len(neighbor_indices)):
                idx1, idx2 = neighbor_indices[i], neighbor_indices[j]
                
                if idx1 in processed or idx2 in processed:
                    continue
                
                if idx1 == idx2:
                    continue
                
                v1 = vertices[idx1].co
                v2 = vertices[idx2].co
                distance = (v1 - v2).length
                
                if distance <= tolerance:
                    duplicates.append({
                        'vertex1': idx1,
                        'vertex2': idx2,
                        'distance': distance,
                        'coordinate': tuple(v1)
                    })
                    processed.add(idx1)
                    processed.add(idx2)
    
    result = {
        'duplicate_vertices_count': len(duplicates),
        'has_duplicate_vertices': len(duplicates) > 0,
        'duplicate_pairs': duplicates[:20],  # Limiter à 20 paires
        'tolerance_used': tolerance
    }
    
    logger.debug("Vertices dupliqués: %d paires détectées", len(duplicates))
    return result


def check_vertex_colors(mesh_obj):
    """Analyse les vertex colors du mesh."""
    logger.debug("Analyse vertex colors pour objet: %s", mesh_obj.name)
    
    mesh = mesh_obj.data
    vertex_colors = mesh.vertex_colors
    
    color_layers_info = []
    for layer in vertex_colors:
        color_data = {
            'name': layer.name,
            'is_active': layer == vertex_colors.active,
            'data_count': len(layer.data)
        }
        color_layers_info.append(color_data)
    
    result = {
        'has_vertex_colors': len(vertex_colors) > 0,
        'vertex_color_layers_count': len(vertex_colors),
        'color_layers': color_layers_info
    }
    
    logger.debug("Vertex colors: %d couches détectées", len(vertex_colors))
    return result


def analyze_polygon_distribution(mesh_obj):
    """Analyse la distribution des types de polygones."""
    logger.debug("Analyse distribution polygones pour objet: %s", mesh_obj.name)
    
    mesh = mesh_obj.data
    polygons = mesh.polygons
    
    if not polygons:
        return {
            'total_polygons': 0,
            'triangles_count': 0,
            'quads_count': 0,
            'ngons_count': 0,
            'triangles_percentage': 0.0,
            'quads_percentage': 0.0,
            'ngons_percentage': 0.0,
            'max_polygon_sides': 0
        }
    
    triangles = 0
    quads = 0
    ngons = 0
    max_sides = 0
    
    for poly in polygons:
        sides = len(poly.vertices)
        max_sides = max(max_sides, sides)
        
        if sides == 3:
            triangles += 1
        elif sides == 4:
            quads += 1
        else:
            ngons += 1
    
    total = len(polygons)
    
    result = {
        'total_polygons': total,
        'triangles_count': triangles,
        'quads_count': quads,
        'ngons_count': ngons,
        'triangles_percentage': (triangles / total) * 100 if total > 0 else 0,
        'quads_percentage': (quads / total) * 100 if total > 0 else 0,
        'ngons_percentage': (ngons / total) * 100 if total > 0 else 0,
        'max_polygon_sides': max_sides
    }
    
    logger.debug("Distribution: %d tris, %d quads, %d ngons", triangles, quads, ngons)
    return result


def analyze_collection_topology(collection, context=None):
    """Analyse la topologie de tous les mesh dans une collection avec progression."""
    logger.info("Début analyse topologie pour collection: %s", collection.name)
    
    results = {
        'collection_name': collection.name,
        'total_objects': 0,
        'analyzed_objects': 0,
        'objects_results': {},
        'summary': {
            'total_manifold_issues': 0,
            'total_inverted_faces': 0,
            'total_isolated_vertices': 0,
            'total_duplicate_vertices': 0,
            'objects_with_vertex_colors': 0,
            'average_quad_percentage': 0.0,
            'analysis_success': True,
            'analysis_error': ''
        }
    }
    
    # Initialiser la barre de progression
    progress_active = False
    try:
        if context and hasattr(context, 'window_manager'):
            context.window_manager.progress_begin(0, 100)
            progress_active = True
    except:
        pass
    
    try:
        prefs = get_topology_preferences()
        # Filtrer les objets mesh en excluant les BoundingBoxes et helpers
        mesh_objects = [obj for obj in collection.all_objects 
                       if obj.type == 'MESH' 
                       and not obj.name.startswith('T4A_BBOX_')
                       and not obj.name.startswith('T4A_HELPER_')]
        
        total_meshes = len(mesh_objects)
        results['total_objects'] = total_meshes
        
        if total_meshes == 0:
            logger.info("Aucun mesh à analyser dans la collection")
            return results
        
        logger.info("Analyse de %d mesh objets...", total_meshes)
        
        total_manifold_issues = 0
        total_inverted_faces = 0
        total_isolated_vertices = 0
        total_duplicate_vertices = 0
        objects_with_colors = 0
        quad_percentages = []
        
        for i, mesh_obj in enumerate(mesh_objects):
            try:
                # Mise à jour de la progression
                current_mesh = i + 1
                update_topology_progress(context, current_mesh, total_meshes, mesh_obj.name)
                
                obj_result = analyze_mesh_topology(mesh_obj, prefs)
                if obj_result and obj_result['analysis_success']:
                    results['objects_results'][mesh_obj.name] = obj_result
                    results['analyzed_objects'] += 1
                    
                    # Accumuler les statistiques
                    total_manifold_issues += obj_result.get('manifold_error_count', 0)
                    total_inverted_faces += obj_result.get('inverted_faces_count', 0)
                    total_isolated_vertices += obj_result.get('isolated_vertices_count', 0)
                    total_duplicate_vertices += obj_result.get('duplicate_vertices_count', 0)
                    
                    if obj_result.get('has_vertex_colors', False):
                        objects_with_colors += 1
                    
                    quad_pct = obj_result.get('quads_percentage', 0)
                    if quad_pct > 0:
                        quad_percentages.append(quad_pct)
                        
            except Exception as e:
                logger.error("Erreur analyse topologie objet %s: %s", mesh_obj.name, str(e))
        
        # Affichage final de la progression
        if total_meshes > 0:
            update_topology_progress(context, total_meshes, total_meshes, "Terminé")
        
        # Calculer le résumé global
        results['summary'].update({
            'total_manifold_issues': total_manifold_issues,
            'total_inverted_faces': total_inverted_faces,
            'total_isolated_vertices': total_isolated_vertices,
            'total_duplicate_vertices': total_duplicate_vertices,
            'objects_with_vertex_colors': objects_with_colors,
            'average_quad_percentage': sum(quad_percentages) / len(quad_percentages) if quad_percentages else 0.0
        })
        
        logger.info("Analyse topologie terminée: %d/%d objets analysés", 
                   results['analyzed_objects'], results['total_objects'])
        
    except Exception as e:
        logger.error("Erreur lors de l'analyse topologie de la collection: %s", str(e))
        results['summary']['analysis_success'] = False
        results['summary']['analysis_error'] = str(e)
    
    finally:
        # Fermer la barre de progression
        if progress_active:
            try:
                context.window_manager.progress_end()
            except:
                pass
    
    return results


def analyze_mesh_topology(mesh_obj, preferences=None):
    """Analyse topologique complète d'un mesh object."""
    if not preferences:
        preferences = get_topology_preferences()
    
    logger.debug("Analyse topologie complète de l'objet: %s", mesh_obj.name)
    
    try:
        topology_data = get_mesh_topology_data(mesh_obj)
        if not topology_data:
            return {
                'object_name': mesh_obj.name,
                'analysis_success': False,
                'analysis_error': 'Aucune donnée de mesh trouvée',
                'total_vertices': 0,
                'total_polygons': 0
            }
        
        result = {
            'object_name': mesh_obj.name,
            'total_vertices': topology_data['total_vertices'],
            'total_edges': topology_data['total_edges'],
            'total_polygons': topology_data['total_polygons'],
            'analysis_success': True,
            'analysis_error': ''
        }
        
        # Analyse manifold
        logger.debug("Analyse manifold...")
        manifold_result = detect_manifold_issues(mesh_obj)
        result.update({
            'has_manifold_issues': manifold_result['has_manifold_issues'],
            'manifold_error_count': manifold_result['manifold_error_count']
        })
        
        # Analyse des normales
        logger.debug("Analyse normales...")
        normals_result = analyze_face_normals(mesh_obj, preferences['normal_threshold'])
        result.update({
            'normal_consistency': normals_result['normal_consistency'],
            'inverted_faces_count': normals_result['inverted_faces_count'],
            'has_normal_issues': normals_result['has_normal_issues']
        })
        
        # Vertices isolés
        logger.debug("Recherche vertices isolés...")
        isolated_result = find_isolated_vertices(mesh_obj)
        result.update({
            'isolated_vertices_count': isolated_result['isolated_vertices_count'],
            'has_isolated_vertices': isolated_result['has_isolated_vertices']
        })
        
        # Vertices dupliqués
        logger.debug("Détection vertices dupliqués...")
        duplicates_result = detect_duplicate_vertices(mesh_obj, preferences['duplicate_tolerance'])
        result.update({
            'duplicate_vertices_count': duplicates_result['duplicate_vertices_count'],
            'has_duplicate_vertices': duplicates_result['has_duplicate_vertices']
        })
        
        # Vertex colors
        if preferences['analyze_vertex_colors']:
            logger.debug("Analyse vertex colors...")
            colors_result = check_vertex_colors(mesh_obj)
            result.update({
                'has_vertex_colors': colors_result['has_vertex_colors'],
                'vertex_color_layers_count': colors_result['vertex_color_layers_count']
            })
        else:
            result.update({
                'has_vertex_colors': False,
                'vertex_color_layers_count': 0
            })
        
        # Distribution des polygones
        logger.debug("Analyse distribution polygones...")
        poly_result = analyze_polygon_distribution(mesh_obj)
        result.update({
            'triangles_percentage': poly_result['triangles_percentage'],
            'quads_percentage': poly_result['quads_percentage'],
            'ngons_percentage': poly_result['ngons_percentage'],
            'triangles_count': poly_result['triangles_count'],
            'quads_count': poly_result['quads_count'],
            'ngons_count': poly_result['ngons_count']
        })
        
        logger.debug("Analyse topologie complète terminée pour %s", mesh_obj.name)
        return result
        
    except Exception as e:
        logger.error("Erreur lors de l'analyse topologie de %s: %s", mesh_obj.name, str(e))
        return {
            'object_name': mesh_obj.name,
            'analysis_success': False,
            'analysis_error': str(e),
            'total_vertices': 0,
            'total_polygons': 0
        }


class T4A_OT_AnalyzeTopology(bpy.types.Operator):
    """Opérateur pour analyser la topologie d'une collection."""
    bl_idname = "t4a.analyze_topology"
    bl_label = "Analyze Topology"
    bl_description = "Analyse la topologie des mesh de la collection sélectionnée"
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
            self.report({'ERROR'}, f"Collection '{self.collection_name}' non trouvée")
            return {'CANCELLED'}
        
        try:
            # Lancer l'analyse avec progression
            logger.info("Lancement analyse topologie pour collection: %s", self.collection_name)
            results = analyze_collection_topology(collection, context)
            
            # Stocker les résultats dans les propriétés de scène
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims:
                for item in dims:
                    if self.collection_name in item.name:
                        if hasattr(item, 'topology_result') and item.topology_result:
                            topo_res = item.topology_result
                            summary = results['summary']
                            
                            # Mettre à jour les propriétés
                            topo_res.analysis_success = summary['analysis_success']
                            topo_res.analysis_error = summary.get('analysis_error', '')
                            topo_res.has_manifold_issues = summary['total_manifold_issues'] > 0
                            topo_res.manifold_error_count = summary['total_manifold_issues']
                            topo_res.inverted_faces_count = summary['total_inverted_faces']
                            topo_res.isolated_vertices_count = summary['total_isolated_vertices']
                            topo_res.duplicate_vertices_count = summary['total_duplicate_vertices']
                            topo_res.objects_with_vertex_colors = summary['objects_with_vertex_colors']
                            topo_res.average_quad_percentage = summary['average_quad_percentage']
                            
                            logger.info("Résultats topologie stockés pour %s", item.name)
                        break
            
            if results['summary']['analysis_success']:
                analyzed = results['analyzed_objects']
                total = results['total_objects']
                self.report({'INFO'}, f"Analyse topologie terminée: {analyzed}/{total} objets analysés")
            else:
                self.report({'ERROR'}, f"Erreur analyse: {results['summary']['analysis_error']}")
            
        except Exception as e:
            logger.error("Erreur opérateur analyse topologie: %s", str(e))
            self.report({'ERROR'}, f"Erreur lors de l'analyse: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


# Classes à enregistrer
classes = (
    T4A_OT_AnalyzeTopology,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()