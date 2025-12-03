"""
Module d'analyse de Texel Density pour T4A_3DFilesQtCheck.
Évalue la densité de texel (pixels/cm) pour maintenir une cohérence visuelle.

Fonctionnalités:
- Calcul de la densité de texel par face
- Analyse de la variance entre faces
- Détection des incohérences de résolution
- Support multi-matériaux et UDIM
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector
import math
from collections import defaultdict

# Import du logger personnalisé
try:
    from . import PROD_autoload
    logger = PROD_autoload._SimpleLogger("TEXEL_DENSITY", debug_mode=True)
except ImportError:
    # Fallback logger basique
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("T4A_TEXEL_DENSITY")


def get_texture_resolution(material):
    """
    Extrait la résolution de la texture principale d'un matériau.
    
    Args:
        material: Matériau Blender
        
    Returns:
        tuple: (largeur, hauteur) ou (512, 512) par défaut
    """
    if not material or not material.use_nodes:
        return (512, 512)  # Résolution par défaut
    
    # Parcourir les nodes pour trouver Image Texture
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            image = node.image
            return (image.size[0], image.size[1])
    
    return (512, 512)  # Défaut si aucune texture trouvée


def calculate_uv_area(face, uv_layer):
    """
    Calcule l'aire d'une face dans l'espace UV (0-1).
    
    Args:
        face: Face bmesh
        uv_layer: Couche UV active
        
    Returns:
        float: Aire en unités UV²
    """
    if len(face.loops) < 3:
        return 0.0
    
    # Récupérer les coordonnées UV
    uv_coords = []
    for loop in face.loops:
        uv_coords.append(loop[uv_layer].uv)
    
    # Triangulation pour calculer l'aire
    if len(uv_coords) == 3:
        # Triangle simple
        v0, v1, v2 = uv_coords
        return 0.5 * abs((v1.x - v0.x) * (v2.y - v0.y) - (v2.x - v0.x) * (v1.y - v0.y))
    
    elif len(uv_coords) == 4:
        # Quadrilatère - diviser en deux triangles
        v0, v1, v2, v3 = uv_coords
        area1 = 0.5 * abs((v1.x - v0.x) * (v2.y - v0.y) - (v2.x - v0.x) * (v1.y - v0.y))
        area2 = 0.5 * abs((v2.x - v0.x) * (v3.y - v0.y) - (v3.x - v0.x) * (v2.y - v0.y))
        return area1 + area2
    
    else:
        # N-gon - fan triangulation depuis le premier vertex
        total_area = 0.0
        v0 = uv_coords[0]
        for i in range(1, len(uv_coords) - 1):
            v1, v2 = uv_coords[i], uv_coords[i + 1]
            area = 0.5 * abs((v1.x - v0.x) * (v2.y - v0.y) - (v2.x - v0.x) * (v1.y - v0.y))
            total_area += area
        
        return total_area


def calculate_world_area(face, world_matrix):
    """
    Calcule l'aire d'une face dans l'espace monde.
    
    Args:
        face: Face bmesh
        world_matrix: Matrice de transformation monde
        
    Returns:
        float: Aire en unités Blender²
    """
    if len(face.verts) < 3:
        return 0.0
    
    # Transformer les vertices dans l'espace monde
    world_coords = []
    for vert in face.verts:
        world_coord = world_matrix @ vert.co
        world_coords.append(world_coord)
    
    # Calculer l'aire using cross product
    if len(world_coords) == 3:
        # Triangle
        v0, v1, v2 = world_coords
        return 0.5 * (v1 - v0).cross(v2 - v0).length
    
    else:
        # Polygone - utiliser la normale de la face
        center = sum(world_coords, Vector()) / len(world_coords)
        total_area = 0.0
        
        for i in range(len(world_coords)):
            v1 = world_coords[i] - center
            v2 = world_coords[(i + 1) % len(world_coords)] - center
            total_area += 0.5 * v1.cross(v2).length
        
        return total_area


def convert_to_cm2(area_blender_units, unit_settings):
    """
    Convertit une aire en unités Blender vers cm².
    
    Args:
        area_blender_units: Aire en unités Blender
        unit_settings: Paramètres d'unité de la scène
        
    Returns:
        float: Aire en cm²
    """
    try:
        # Récupérer le facteur d'échelle
        scale_length = getattr(unit_settings, 'scale_length', 1.0)
        unit_system = getattr(unit_settings, 'system', 'METRIC')
        
        # Convertir selon le système d'unités
        if unit_system == 'METRIC':
            # 1 unité Blender = scale_length mètres
            # Convertir en cm: 1m = 100cm
            cm_per_unit = scale_length * 100.0
        elif unit_system == 'IMPERIAL':
            # 1 unité Blender = scale_length pieds
            # Convertir en cm: 1 pied = 30.48 cm
            cm_per_unit = scale_length * 30.48
        else:
            # Système 'NONE' ou autre - supposer mètres
            cm_per_unit = scale_length * 100.0
        
        # L'aire est en unités²
        area_cm2 = area_blender_units * (cm_per_unit ** 2)
        return area_cm2
        
    except Exception:
        # Fallback: supposer 1 unité = 1 mètre
        return area_blender_units * 10000.0  # 1m² = 10000cm²


def calculate_face_texel_density(face, uv_layer, material, world_matrix, scene):
    """
    Calcule la densité de texel pour une face donnée.
    
    Args:
        face: Face bmesh
        uv_layer: Couche UV active
        material: Matériau de la face
        world_matrix: Matrice transformation monde
        scene: Scène Blender pour les unités
        
    Returns:
        dict: {
            'texel_density': float,  # px/cm
            'uv_area': float,        # aire UV
            'world_area_cm2': float, # aire monde en cm²
            'texture_resolution': tuple # (w, h)
        }
    """
    result = {
        'texel_density': 0.0,
        'uv_area': 0.0,
        'world_area_cm2': 0.0,
        'texture_resolution': (512, 512),
        'error': None
    }
    
    try:
        # 1. Calcul surface UV
        uv_area = calculate_uv_area(face, uv_layer)
        if uv_area <= 0:
            result['error'] = 'UV area is zero or negative'
            return result
        
        # 2. Calcul surface monde
        world_area = calculate_world_area(face, world_matrix)
        if world_area <= 0:
            result['error'] = 'World area is zero or negative'
            return result
        
        # 3. Conversion en cm²
        world_area_cm2 = convert_to_cm2(world_area, scene.unit_settings)
        
        # 4. Résolution de texture
        texture_resolution = get_texture_resolution(material)
        
        # 5. Calcul de la densité effective
        # La surface UV occupe une fraction de la texture totale
        effective_texture_pixels = math.sqrt(texture_resolution[0] * texture_resolution[1] * uv_area)
        
        # Densité = pixels par cm
        texel_density = effective_texture_pixels / math.sqrt(world_area_cm2)
        
        result.update({
            'texel_density': texel_density,
            'uv_area': uv_area,
            'world_area_cm2': world_area_cm2,
            'texture_resolution': texture_resolution
        })
        
    except Exception as e:
        result['error'] = str(e)
        logger.error("Erreur calcul texel density face: %s", e)
    
    return result


def analyze_object_texel_density(obj, context):
    """
    Analyse la densité de texel pour un objet.
    
    Args:
        obj: Objet mesh Blender
        context: Context Blender
        
    Returns:
        dict: Résultats d'analyse par matériau
    """
    if obj.type != 'MESH':
        return {'error': 'Object is not a mesh'}
    
    # Créer bmesh depuis l'objet
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        
        # Vérifier les UVs
        if not bm.loops.layers.uv:
            return {'error': 'No UV layers found'}
        
        uv_layer = bm.loops.layers.uv.active
        if not uv_layer:
            return {'error': 'No active UV layer'}
        
        # Grouper les faces par matériau
        material_faces = defaultdict(list)
        
        for face in bm.faces:
            material_index = face.material_index
            material = obj.material_slots[material_index].material if material_index < len(obj.material_slots) else None
            material_name = material.name if material else "No Material"
            material_faces[material_name].append((face, material))
        
        # Analyser par matériau
        results = {}
        
        for material_name, face_list in material_faces.items():
            material_result = {
                'face_count': len(face_list),
                'densities': [],
                'average_density': 0.0,
                'min_density': float('inf'),
                'max_density': 0.0,
                'variance_percentage': 0.0,
                'texture_resolution': (512, 512),
                'total_uv_area': 0.0,
                'total_world_area_cm2': 0.0,
                'errors': []
            }
            
            valid_densities = []
            total_uv_area = 0.0
            total_world_area = 0.0
            
            # Analyser chaque face
            for face, material in face_list:
                face_result = calculate_face_texel_density(
                    face, uv_layer, material, obj.matrix_world, context.scene
                )
                
                if face_result['error']:
                    material_result['errors'].append(face_result['error'])
                else:
                    density = face_result['texel_density']
                    valid_densities.append(density)
                    total_uv_area += face_result['uv_area']
                    total_world_area += face_result['world_area_cm2']
                    
                    # Mise à jour min/max
                    material_result['min_density'] = min(material_result['min_density'], density)
                    material_result['max_density'] = max(material_result['max_density'], density)
                    material_result['texture_resolution'] = face_result['texture_resolution']
            
            # Calculs statistiques
            if valid_densities:
                material_result['densities'] = valid_densities
                material_result['average_density'] = sum(valid_densities) / len(valid_densities)
                material_result['total_uv_area'] = total_uv_area
                material_result['total_world_area_cm2'] = total_world_area
                
                # Calcul de la variance
                if len(valid_densities) > 1:
                    avg = material_result['average_density']
                    variance = sum((d - avg) ** 2 for d in valid_densities) / len(valid_densities)
                    material_result['variance_percentage'] = (math.sqrt(variance) / avg) * 100.0 if avg > 0 else 0.0
            else:
                material_result['min_density'] = 0.0
            
            results[material_name] = material_result
        
        return results
        
    except Exception as e:
        logger.error("Erreur analyse texel density objet %s: %s", obj.name, e)
        return {'error': str(e)}
        
    finally:
        bm.free()


def analyze_collection_texel_density(collection, context):
    """
    Analyse la densité de texel pour tous les objets mesh d'une collection.
    
    Args:
        collection: Collection Blender
        context: Context Blender
        
    Returns:
        dict: Résultats consolidés pour la collection
    """
    logger.info("Début analyse texel density collection: %s", collection.name)
    
    # Résultats globaux
    collection_results = {
        'summary': {
            'analysis_success': False,
            'analysis_error': '',
            'analyzed_objects': 0,
            'total_materials': 0,
            'average_density': 0.0,
            'min_density': float('inf'),
            'max_density': 0.0,
            'global_variance': 0.0,
            'density_status': 'GOOD'  # GOOD, WARNING, ERROR
        },
        'objects_results': {},
        'materials_summary': {}
    }
    
    try:
        # Obtenir les préférences pour les seuils
        try:
            from . import PROD_Parameters
            prefs = PROD_Parameters.get_addon_preferences()
            target_density = getattr(prefs, 'texel_density_target', 10.24)
            variance_threshold = getattr(prefs, 'texel_variance_threshold', 20.0)
        except Exception:
            target_density = 10.24
            variance_threshold = 20.0
        
        mesh_objects = [obj for obj in collection.objects if obj.type == 'MESH']
        
        if not mesh_objects:
            collection_results['summary']['analysis_error'] = 'No mesh objects found in collection'
            return collection_results
        
        all_densities = []
        materials_data = defaultdict(list)
        
        # Analyser chaque objet
        for obj in mesh_objects:
            logger.info("Analyse texel density objet: %s", obj.name)
            
            obj_result = analyze_object_texel_density(obj, context)
            
            if 'error' in obj_result:
                collection_results['objects_results'][obj.name] = {
                    'error': obj_result['error'],
                    'analysis_success': False
                }
                continue
            
            # Consolider les résultats par matériau
            obj_summary = {
                'analysis_success': True,
                'materials_count': len(obj_result),
                'materials': obj_result
            }
            
            for material_name, mat_result in obj_result.items():
                if mat_result['densities']:
                    all_densities.extend(mat_result['densities'])
                    materials_data[material_name].append(mat_result)
            
            collection_results['objects_results'][obj.name] = obj_summary
            collection_results['summary']['analyzed_objects'] += 1
        
        # Calculs globaux
        if all_densities:
            collection_results['summary']['analysis_success'] = True
            collection_results['summary']['average_density'] = sum(all_densities) / len(all_densities)
            collection_results['summary']['min_density'] = min(all_densities)
            collection_results['summary']['max_density'] = max(all_densities)
            collection_results['summary']['total_materials'] = len(materials_data)
            
            # Variance globale
            avg = collection_results['summary']['average_density']
            if len(all_densities) > 1 and avg > 0:
                variance = sum((d - avg) ** 2 for d in all_densities) / len(all_densities)
                collection_results['summary']['global_variance'] = (math.sqrt(variance) / avg) * 100.0
            
            # Évaluation du statut
            variance_pct = collection_results['summary']['global_variance']
            if variance_pct > variance_threshold:
                collection_results['summary']['density_status'] = 'ERROR'
            elif variance_pct > variance_threshold / 2:
                collection_results['summary']['density_status'] = 'WARNING'
            else:
                collection_results['summary']['density_status'] = 'GOOD'
        
        # Résumé par matériau
        for material_name, mat_data_list in materials_data.items():
            all_mat_densities = []
            for mat_data in mat_data_list:
                all_mat_densities.extend(mat_data['densities'])
            
            if all_mat_densities:
                collection_results['materials_summary'][material_name] = {
                    'average_density': sum(all_mat_densities) / len(all_mat_densities),
                    'min_density': min(all_mat_densities),
                    'max_density': max(all_mat_densities),
                    'face_count': sum(len(md['densities']) for md in mat_data_list)
                }
        
        logger.info("Analyse texel density terminée: %d objets analysés", 
                   collection_results['summary']['analyzed_objects'])
        
    except Exception as e:
        collection_results['summary']['analysis_error'] = str(e)
        logger.error("Erreur analyse texel density collection: %s", e)
    
    return collection_results


# Operator pour lancer l'analyse depuis l'UI
class T4A_OT_AnalyzeTexelDensity(bpy.types.Operator):
    """Analyse la densité de texel d'une collection"""
    bl_idname = "t4a.analyze_texel_density"
    bl_label = "Analyser Texel Density"
    bl_description = "Analyse la densité de texel (pixels/cm) de la collection"
    
    collection_name: bpy.props.StringProperty(name="Collection Name")
    
    def execute(self, context):
        if not self.collection_name:
            self.report({'ERROR'}, "Nom de collection manquant")
            return {'CANCELLED'}
        
        collection = bpy.data.collections.get(self.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' introuvable")
            return {'CANCELLED'}
        
        # Lancer l'analyse
        result = analyze_collection_texel_density(collection, context)
        
        if result['summary']['analysis_success']:
            avg_density = result['summary']['average_density']
            variance = result['summary']['global_variance']
            self.report({'INFO'}, f"Analyse terminée: {avg_density:.1f} px/cm (variance: {variance:.1f}%)")
        else:
            error = result['summary']['analysis_error']
            self.report({'ERROR'}, f"Erreur analyse: {error}")
        
        return {'FINISHED'}


def register():
    bpy.utils.register_class(T4A_OT_AnalyzeTexelDensity)


def unregister():
    bpy.utils.unregister_class(T4A_OT_AnalyzeTexelDensity)


if __name__ == "__main__":
    register()