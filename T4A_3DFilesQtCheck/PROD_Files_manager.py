import os
import bpy
import threading
import time
import json
import math
import mathutils
import bmesh

from typing import List
from . import PROD_texture_manager
from . import PROD_uv_analyzer
from . import PROD_topology_analyzer


def _t4a_print(level: str, msg: str, *args):
    try:
        if args:
            print(f"[T4A] [{level}] " + (msg % args))
        else:
            print(f"[T4A] [{level}] {msg}")
    except Exception:
        if args:
            parts = ' '.join(str(a) for a in args)
            print(f"[T4A] [{level}] {msg} {parts}")
        else:
            print(f"[T4A] [{level}] {msg}")


class _SimpleLogger:
    def debug(self, msg, *args):
        # Only print debug messages if debug mode is enabled
        try:
            from . import PROD_Parameters
            if PROD_Parameters.is_debug_mode():
                _t4a_print('DEBUG', msg, *args)
        except Exception:
            pass

    def info(self, msg, *args):
        _t4a_print('INFO', msg, *args)

    def error(self, msg, *args):
        _t4a_print('ERROR', msg, *args)


logger = _SimpleLogger()


def _gather_files(path: str, exts: List[str]) -> List[str]:
    found = []
    if not path:
        return found
    for root, dirs, files in os.walk(path):
        for f in files:
            fn = f.lower()
            for e in exts:
                if fn.endswith(e):
                    found.append(os.path.join(root, f))
                    break
    return found


def _import_file(filepath: str) -> bool:
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == '.fbx':
            bpy.ops.import_scene.fbx(filepath=filepath)
        elif ext in ('.glb', '.gltf'):
            bpy.ops.import_scene.gltf(filepath=filepath)
        elif ext == '.obj':
            bpy.ops.import_scene.obj(filepath=filepath)
        elif ext == '.stl':
            bpy.ops.import_mesh.stl(filepath=filepath)
        elif ext == '.abc':
            bpy.ops.wm.alembic_import(filepath=filepath)
        elif ext == '.usd':
            try:
                bpy.ops.wm.usd_import(filepath=filepath)
            except Exception:
                # try generic import if different operator
                bpy.ops.import_scene.usd(filepath=filepath)
        elif ext == '.blend':
            # Append all objects from the .blend file (non-destructive)
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)
        else:
            # unknown extension
            return False
        return True
    except Exception as e:
        logger.error("[T4A] Erreur d'import pour %s: %s", filepath, e)
        return False


class T4A_OT_ScanAndImport(bpy.types.Operator):
    bl_idname = "t4a.scan_directory"
    bl_label = "Scan et importer"
    bl_description = "Scanner le répertoire défini et proposer l'import des fichiers 3D trouvés"

    files_count: bpy.props.IntProperty(name="Files Count", default=0)

    def invoke(self, context, event):
        addon_name = __package__ or "T4A_3DFilesQtCheck"
        prefs = None
        try:
            prefs = context.preferences.addons[addon_name].preferences
        except Exception:
            prefs = None

        path = getattr(prefs, 'scan_path', '') if prefs is not None else ''
        exts = ['.fbx', '.glb', '.gltf', '.obj', '.blend', '.abc', '.usd', '.stl']
        files = _gather_files(path, exts)
        self.files_count = len(files)
        self._files_list = files

        if self.files_count == 0:
            self.report({'INFO'}, "Aucun fichier trouvé dans le chemin configuré.")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Nombre de fichiers trouvés: {self.files_count}")
        layout.label(text="Souhaitez-vous importer tous ces fichiers dans la scène actuelle ?")

    def execute(self, context):
        # Run scene setup before importing files
        try:
            result = bpy.ops.t4a.setup_scene(targetVolumCube=1.0)
            # operator returns a set-like value; check for FINISHED
            if result != {'FINISHED'}:
                self.report({'WARNING'}, "SetupScene cancelled or failed — import aborted.")
                return {'CANCELLED'}
        except Exception:
            self.report({'WARNING'}, "SetupScene call failed — import aborted.")
            return {'CANCELLED'}

        imported = 0
        failed = 0
        for f in getattr(self, '_files_list', []):
            # Use the operator that imports the file and places contents into a collection
            try:
                res = bpy.ops.t4a.import_file_to_collection(filepath=f)
                ok = (res == {'FINISHED'})
            except Exception:
                ok = False
            if ok:
                imported += 1
            else:
                failed += 1

        # store results into scene props for UI reporting
        try:
            scene = context.scene
            scene.t4a_last_imported_count = imported
            scene.t4a_last_import_failed = failed
        except Exception:
            pass

        self.report({'INFO'}, f"Importés: {imported}, Échecs: {failed}")
        return {'FINISHED'}


classes = (
    T4A_OT_ScanAndImport,
)


def _find_layer_collection(layer_coll, coll_name):
    """Recursively find LayerCollection matching coll_name."""
    if layer_coll.collection.name == coll_name:
        return layer_coll
    for child in layer_coll.children:
        found = _find_layer_collection(child, coll_name)
        if found:
            return found
    return None


class T4A_OT_SetupScene(bpy.types.Operator):
    bl_idname = "t4a.setup_scene"
    bl_label = "Setup Scene"
    bl_description = "Nettoie la scène active et crée un volume de référence"

    targetVolumCube: bpy.props.FloatProperty(
        name="Target Volume Cube",
        description="Taille du cube de référence en mètres",
        default=1.0,
        min=0.001,
        unit='LENGTH'
    )

    def execute(self, context):
        try:
            # 1) Delete all objects
            for obj in list(bpy.data.objects):
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass

            # 2) Unlink and remove collections under the scene collection
            scene = context.scene
            root_coll = scene.collection
            # unlink child collections
            for child in list(root_coll.children):
                try:
                    root_coll.children.unlink(child)
                except Exception:
                    pass
                try:
                    bpy.data.collections.remove(child)
                except Exception:
                    pass

            # 3) Purge orphan data (best effort)
            try:
                bpy.ops.outliner.orphans_purge(do_recursive=True)
            except Exception:
                # fallback: try without args
                try:
                    bpy.ops.outliner.orphans_purge()
                except Exception:
                    pass

            # 4) Create support collection
            coll_name = "Check_Support_Helpers"
            coll = bpy.data.collections.get(coll_name)
            if coll is None:
                coll = bpy.data.collections.new(coll_name)
            # link to scene collection if not already
            if coll.name not in [c.name for c in root_coll.children]:
                try:
                    root_coll.children.link(coll)
                except Exception:
                    pass

            # 5) Create cube of given size and place at ground so base at Z=0
            size = float(self.targetVolumCube)
            zloc = size / 4.0
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, zloc))
            obj = context.active_object
            if obj is None:
                # try last created
                obj = bpy.context.object
            if obj is not None:
                # scale to target size
                obj.scale = (size / 2.0, size / 2.0, size / 2.0)
                obj.name = "VolumeRef"
                try:
                    obj.display_type = 'WIRE'
                except Exception:
                    try:
                        obj.show_wire = True
                    except Exception:
                        pass

                # unlink from other collections and link to support collection
                for c in list(obj.users_collection):
                    try:
                        c.objects.unlink(obj)
                    except Exception:
                        pass
                try:
                    coll.objects.link(obj)
                except Exception:
                    pass

            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"SetupScene failed: {e}")
            return {'CANCELLED'}


class T4A_OT_ImportFileToCollection(bpy.types.Operator):
    bl_idname = "t4a.import_file_to_collection"
    bl_label = "Import File To Collection"
    bl_description = "Importe un fichier et place ses objets dans une collection nommée selon le fichier"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        before_ids = {id(o) for o in bpy.data.objects}
        ok = _import_file(filepath)
        if not ok:
            return {'CANCELLED'}

        # find newly created objects
        new_objs = [o for o in bpy.data.objects if id(o) not in before_ids]

        # build collection name: EXT_filename (ext uppercased)
        base = os.path.basename(filepath)
        ext = os.path.splitext(base)[1].lstrip('.').upper() or 'FILE'
        coll_name = f"{ext}_{base}"

        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            coll = bpy.data.collections.new(coll_name)
        # link to scene collection root
        try:
            root_coll = context.scene.collection
            if coll.name not in [c.name for c in root_coll.children]:
                root_coll.children.link(coll)
        except Exception:
            pass

        # move new objects into the collection
        for obj in new_objs:
            try:
                # unlink from other collections
                for uc in list(obj.users_collection):
                    try:
                        uc.objects.unlink(obj)
                    except Exception:
                        pass
                coll.objects.link(obj)
            except Exception:
                pass

        # Normaliser les objets importés
        try:
            bpy.ops.t4a.normalize_imported_objects(
                target_collection=coll_name,
                auto_center=True,
                place_on_ground=True,
                auto_orient_front=False, ##Systhém not working well
                apply_transforms=True,
                create_bounding_box=True
            )
            logger.info("[T4A] Normalisation effectuée pour: %s", coll_name)
        except Exception as e:
            logger.error("[T4A] Erreur normalisation: %s", e)

        # Analyser et consolider les textures
        try:
            texture_result = PROD_texture_manager.analyze_and_consolidate_textures(coll, filepath)
            
            # Stocker les résultats dans les propriétés de scène
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                # Chercher ou créer l'entrée pour ce fichier
                dim_item = None
                for item in dims:
                    if item.name == base:
                        dim_item = item
                        break
                
                if dim_item is None:
                    dim_item = dims.add()
                    dim_item.name = base
                
                # S'assurer que texture_result est initialisé (créé automatiquement par Blender)
                # Il devrait être disponible via la propriété PointerProperty
                tex_res = dim_item.texture_result
                if texture_result['success']:
                    stats = texture_result['statistics']
                    tex_res.analysis_success = True
                    tex_res.texture_count = stats['count']
                    tex_res.total_size_kb = stats['total_size_kb']
                    tex_res.max_resolution = stats['max_resolution']
                    tex_res.min_resolution = stats['min_resolution']
                    tex_res.texture_directory = texture_result['texture_directory']
                    tex_res.extracted_count = texture_result['extracted_count']
                    tex_res.consolidated_count = texture_result['consolidated_count']
                    tex_res.analysis_error = ""
                    
                    logger.info("[T4A] Analyse textures réussie: %d textures traitées", stats['count'])
                else:
                    tex_res.analysis_success = False
                    tex_res.analysis_error = texture_result.get('error', 'Erreur inconnue')
                    logger.error("[T4A] Erreur analyse textures: %s", tex_res.analysis_error)
            
        except Exception as e:
            logger.error("[T4A] Erreur analyse textures: %s", e)

        # Analyser les UVs
        try:
            uv_result = PROD_uv_analyzer.analyze_collection_uvs(coll)
            
            # Stocker les résultats UV dans les propriétés de scène
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                # Chercher l'entrée pour ce fichier (déjà créée précédemment)
                dim_item = None
                for item in dims:
                    if item.name == base:
                        dim_item = item
                        break
                
                if dim_item and hasattr(dim_item, 'uv_result') and dim_item.uv_result:
                    uv_res = dim_item.uv_result
                    if uv_result['summary']['analysis_success']:
                        summary = uv_result['summary']
                        uv_res.analysis_success = True
                        uv_res.total_faces = summary['total_faces']
                        uv_res.uv_layers_count = summary['total_uv_layers']
                        uv_res.has_overlaps = summary['has_overlaps']
                        uv_res.has_outside_uvs = summary['has_outside_uvs']
                        uv_res.uses_udim = summary['uses_udim']
                        uv_res.aspect_ratio = summary['average_aspect_ratio']
                        uv_res.is_square = abs(summary['average_aspect_ratio'] - 1.0) <= 0.1
                        uv_res.analysis_error = ""
                        
                        # Calculer des statistiques agrégées depuis les objets individuels
                        overlap_percentages = []
                        outside_percentages = []
                        udim_tiles_set = set()
                        
                        for obj_result in uv_result['objects_results'].values():
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
                        
                        logger.info("[T4A] Analyse UV réussie: %d objets, %d couches UV", 
                                   uv_result['analyzed_objects'], summary['total_uv_layers'])
                        
                        # Analyser le Texel Density si l'analyse UV a réussi
                        try:
                            from . import PROD_texel_density
                            logger.info("[T4A] Début analyse texel density pour: %s", base)
                            
                            texel_result = PROD_texel_density.analyze_collection_texel_density(coll, context)
                            
                            if texel_result['summary']['analysis_success']:
                                # Stocker les résultats dans uv_result
                                uv_res.has_texel_analysis = True
                                uv_res.average_texel_density = texel_result['summary']['average_density']
                                uv_res.min_texel_density = texel_result['summary']['min_density']
                                uv_res.max_texel_density = texel_result['summary']['max_density']
                                uv_res.texel_density_variance = texel_result['summary']['global_variance']
                                uv_res.texel_density_status = texel_result['summary']['density_status']
                                
                                logger.info("[T4A] Analyse texel density réussie: %.1f px/cm (variance: %.1f%%)",
                                           uv_res.average_texel_density, uv_res.texel_density_variance)
                            else:
                                logger.error("[T4A] Erreur analyse texel density: %s", 
                                           texel_result['summary']['analysis_error'])
                        
                        except Exception as e:
                            logger.error("[T4A] Erreur analyse texel density: %s", e)
                    else:
                        uv_res.analysis_success = False
                        uv_res.analysis_error = summary.get('analysis_error', 'Erreur inconnue')
                        logger.error("[T4A] Erreur analyse UV: %s", uv_res.analysis_error)
            
        except Exception as e:
            logger.error("[T4A] Erreur analyse UV: %s", e)

        # Analyser la topologie
        try:
            topology_result = PROD_topology_analyzer.analyze_collection_topology(coll, context)
            logger.info("[T4A] Analyse topologie terminée pour: %s", base)
            
            # Stocker les résultats topologie dans les propriétés de scène
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                logger.info("[T4A] Recherche de l'entrée '%s' dans %d items dims", base, len(dims))
                # Chercher ou créer l'entrée pour ce fichier
                dim_item = None
                for item in dims:
                    if item.name == base:
                        dim_item = item
                        logger.info("[T4A] Trouvé l'entrée correspondante: %s", item.name)
                        break
                
                if dim_item is None:
                    dim_item = dims.add()
                    dim_item.name = base
                    logger.info("[T4A] Créé nouvelle entrée dims: %s", base)
                
                if dim_item and hasattr(dim_item, 'topology_result'):
                    topo_res = dim_item.topology_result
                    if topology_result['summary']['analysis_success']:
                        summary = topology_result['summary']
                        topo_res.analysis_success = True
                        
                        # Statistiques générales
                        total_vertices = sum(obj.get('total_vertices', 0) for obj in topology_result['objects_results'].values())
                        total_polygons = sum(obj.get('total_polygons', 0) for obj in topology_result['objects_results'].values())
                        topo_res.total_vertices = total_vertices
                        topo_res.total_polygons = total_polygons
                        
                        # Problèmes manifold
                        topo_res.has_manifold_issues = summary['total_manifold_issues'] > 0
                        topo_res.manifold_error_count = summary['total_manifold_issues']
                        
                        # Normales
                        topo_res.inverted_faces_count = summary['total_inverted_faces']
                        topo_res.has_normal_issues = summary['total_inverted_faces'] > 0
                        
                        # Calculer la cohérence moyenne des normales
                        normal_consistencies = []
                        for obj_result in topology_result['objects_results'].values():
                            if obj_result.get('normal_consistency', 0) > 0:
                                normal_consistencies.append(obj_result['normal_consistency'])
                        
                        if normal_consistencies:
                            topo_res.normal_consistency = sum(normal_consistencies) / len(normal_consistencies)
                        else:
                            topo_res.normal_consistency = 100.0
                        
                        # Vertices
                        topo_res.isolated_vertices_count = summary['total_isolated_vertices']
                        topo_res.has_isolated_vertices = summary['total_isolated_vertices'] > 0
                        topo_res.duplicate_vertices_count = summary['total_duplicate_vertices']
                        topo_res.has_duplicate_vertices = summary['total_duplicate_vertices'] > 0
                        
                        # Vertex colors
                        topo_res.objects_with_vertex_colors = summary['objects_with_vertex_colors']
                        topo_res.has_vertex_colors = summary['objects_with_vertex_colors'] > 0
                        
                        # Calculer les couches de vertex colors totales
                        total_color_layers = sum(obj.get('vertex_color_layers_count', 0) for obj in topology_result['objects_results'].values())
                        topo_res.vertex_color_layers_count = total_color_layers
                        
                        # Distribution polygones
                        topo_res.average_quad_percentage = summary['average_quad_percentage']
                        
                        # Calculer totaux des types de polygones
                        total_triangles = sum(obj.get('triangles_count', 0) for obj in topology_result['objects_results'].values())
                        total_quads = sum(obj.get('quads_count', 0) for obj in topology_result['objects_results'].values())
                        total_ngons = sum(obj.get('ngons_count', 0) for obj in topology_result['objects_results'].values())
                        
                        topo_res.triangles_count = total_triangles
                        topo_res.quads_count = total_quads
                        topo_res.ngons_count = total_ngons
                        
                        # Calculer pourcentages globaux
                        total_polys = total_triangles + total_quads + total_ngons
                        if total_polys > 0:
                            topo_res.triangles_percentage = (total_triangles / total_polys) * 100
                            topo_res.quads_percentage = (total_quads / total_polys) * 100
                            topo_res.ngons_percentage = (total_ngons / total_polys) * 100
                        
                        topo_res.analysis_error = ""
                        
                        logger.info("[T4A] Analyse topologie réussie: %d objets, %d erreurs manifold, %d faces inversées", 
                                   topology_result['analyzed_objects'], summary['total_manifold_issues'], summary['total_inverted_faces'])
                        logger.info("[T4A] Données topologie stockées pour '%s': vertices=%d, polygones=%d", 
                                   base, total_vertices, total_polygons)
                    else:
                        topo_res.analysis_success = False
                        topo_res.analysis_error = summary.get('analysis_error', 'Erreur inconnue')
                        logger.error("[T4A] Erreur analyse topologie: %s", topo_res.analysis_error)
                
                # Forcer le rafraîchissement de l'interface après stockage des données
                try:
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            area.tag_redraw()
                    logger.info("[T4A] Interface rafraîchie après analyse topologie")
                except Exception:
                    pass
            
        except Exception as e:
            logger.error("[T4A] Erreur analyse topologie: %s", e)
            import traceback
            traceback.print_exc()
            
            # Stocker l'erreur dans l'UI même en cas d'exception
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None:
                # Chercher ou créer l'entrée pour ce fichier
                dim_item = None
                for item in dims:
                    if item.name == base:
                        dim_item = item
                        break
                
                if dim_item is None:
                    dim_item = dims.add()
                    dim_item.name = base
                
                if dim_item and hasattr(dim_item, 'topology_result'):
                    topo_res = dim_item.topology_result
                    topo_res.analysis_success = False
                    topo_res.analysis_error = f"Exception: {str(e)}"
                    logger.error("[T4A] Erreur stockée dans l'UI pour '%s'", base)
                    
                    # Forcer le rafraîchissement de l'interface même en cas d'erreur
                    try:
                        for area in context.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
                    except Exception:
                        pass

        # Assign a color tag based on hash of name (cycle through available tags)
        try:
            tags = ['COLOR_01','COLOR_02','COLOR_03','COLOR_04','COLOR_05','COLOR_06','COLOR_07','COLOR_08','COLOR_09','COLOR_10','COLOR_11','COLOR_12']
            idx = abs(hash(coll_name)) % len(tags)
            if hasattr(coll, 'color_tag'):
                try:
                    coll.color_tag = tags[idx]
                except Exception:
                    pass
        except Exception:
            pass

        # After import, try to find a matching JPG/PNG/TXT/PDF with the same base name
        # in the configured scan path and request analysis if present.
        # Priority: Images (JPG/PNG) first, then TXT/PDF files
        try:
            from . import PROD_Parameters
            addon_name = PROD_Parameters.__package__
            try:
                prefs = context.preferences.addons[addon_name].preferences
                base_path = prefs.scan_path
            except Exception:
                base_path = os.environ.get('SCAN_PATH', '')

            if base_path:
                stem = os.path.splitext(base)[0]
                
                # Search for files in order of priority: JPG/PNG (images) first, then TXT/PDF
                found = None
                found_type = None
                
                # Priority 1: Images (JPG/PNG)
                for ext in ('.jpg', '.jpeg', '.png'):
                    candidate = os.path.join(base_path, stem + ext)
                    if os.path.exists(candidate):
                        found = candidate
                        found_type = 'image'
                        logger.debug("[T4A] Image trouvée: %s", candidate)
                        break
                
                # Priority 2: Text/PDF files (only if no image found)
                if not found:
                    for ext in ('.txt', '.pdf'):
                        candidate = os.path.join(base_path, stem + ext)
                        if os.path.exists(candidate):
                            found = candidate
                            found_type = 'text'
                            logger.debug("[T4A] Fichier texte trouvé: %s", candidate)
                            break
                
                if found:
                    # call appropriate analyze operator based on file type
                    try:
                        if found_type == 'image':
                            # Utiliser le prompt d'analyse de texte pour extraire les dimensions des images
                            bpy.ops.t4a.analyze_image_file_for_dimensions(filepath=found)
                            logger.info("[T4A] Analyse d'image (dimensions) lancée pour: %s", found)
                        else:  # text/pdf
                            bpy.ops.t4a.analyze_text_file(filepath=found)
                            logger.info("[T4A] Analyse de texte lancée pour: %s", found)
                    except Exception as e:
                        logger.error("[T4A] Échec analyse pour %s: %s", found, e)
                else:
                    logger.debug("[T4A] Aucun fichier correspondant trouvé pour: %s", stem)
        except Exception as e:
            logger.error("[T4A] Recherche/analyse post-import échouée: %s", e)

        # Schedule dimension verification after import and potential analysis
        try:
            bpy.ops.t4a.verify_dimensions_on_import(collection_name=coll_name)
            logger.debug("[T4A] Vérification des dimensions programmée pour: %s", coll_name)
        except Exception as e:
            logger.error("[T4A] Erreur lors de la programmation de vérification: %s", e)

        return {'FINISHED'}


class T4A_OT_NormalizeImportedObjects(bpy.types.Operator):
    bl_idname = "t4a.normalize_imported_objects"
    bl_label = "Normalize Imported Objects"
    bl_description = "Normalise les objets importés : centrage, orientation, et application des transformations"

    target_collection: bpy.props.StringProperty(
        name="Target Collection",
        description="Nom de la collection à normaliser",
        default=""
    )
    
    # Paramètres des étapes A, B, C, D
    auto_center: bpy.props.BoolProperty(
        name="Auto Center", 
        description="Centrer automatiquement au (0,0)",
        default=True
    )
    
    place_on_ground: bpy.props.BoolProperty(
        name="Place on Ground",
        description="Placer le modèle au sol (Z min = 0)",
        default=True
    )
    
    auto_orient_front: bpy.props.BoolProperty(
        name="Auto Orient Front",
        description="Orienter automatiquement la face avant vers +Y",
        default=True
    )
    
    apply_transforms: bpy.props.BoolProperty(
        name="Apply Transforms",
        description="Appliquer les transformations sur tous les mesh",
        default=True
    )
    
    create_bounding_box: bpy.props.BoolProperty(
        name="Create Bounding Box",
        description="Créer une BoundingBox du modèle",
        default=True
    )

    def execute(self, context):
        coll_name = self.target_collection
        if not coll_name:
            self.report({'ERROR'}, 'Nom de collection non spécifié')
            return {'CANCELLED'}

        # Trouver la collection
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            self.report({'ERROR'}, f'Collection "{coll_name}" non trouvée')
            return {'CANCELLED'}

        logger.info("[T4A Normalize] Début normalisation pour: %s", coll_name)

        try:
            # Analyser la hiérarchie et détecter si déjà normalisé
            hierarchy_data = self._analyze_hierarchy(coll)
            
            if hierarchy_data['already_normalized']:
                logger.info("[T4A Normalize] Modèle déjà normalisé, opération ignorée")
                self.report({'INFO'}, f'Modèle "{coll_name}" déjà normalisé')
                return {'FINISHED'}
            
            mesh_objects = hierarchy_data['mesh_objects']
            root_empty = hierarchy_data['root_empty']
            
            if not mesh_objects:
                logger.warning("[T4A Normalize] Aucun objet mesh trouvé")
                self.report({'WARNING'}, 'Aucun objet mesh trouvé dans la collection')
                return {'FINISHED'}
            
            # Vérifier les échelles extrêmes
            if not self._check_extreme_scales(mesh_objects):
                return {'CANCELLED'}
            
            # Étape A: Détection et analyse (déjà fait dans _analyze_hierarchy)
            logger.info("[T4A Normalize] Étape A: Analyse terminée - %d mesh, racine: %s", 
                       len(mesh_objects), root_empty.name if root_empty else "Aucune")
            
            # Étape B: Repositionnement
            if self.auto_center or self.place_on_ground:
                self._reposition_objects(mesh_objects, root_empty)
                logger.info("[T4A Normalize] Étape B: Repositionnement terminé")
            
            # Étape C: Correction d'orientation
            if self.auto_orient_front:
                rotation_applied = self._correct_orientation(mesh_objects, root_empty)
                if rotation_applied:
                    logger.info("[T4A Normalize] Étape C: Orientation corrigée")
                else:
                    logger.info("[T4A Normalize] Étape C: Orientation correcte, aucune correction")
            
            # Étape D: Application des transformations
            if self.apply_transforms:
                applied_count = self._apply_transforms(mesh_objects)
                logger.info("[T4A Normalize] Étape D: Transformations appliquées sur %d objets", applied_count)
            
            # Créer BoundingBox si demandé
            if self.create_bounding_box:
                bbox_obj = self._create_model_bounding_box(mesh_objects, root_empty, coll_name, coll)
                if bbox_obj:
                    logger.info("[T4A Normalize] BoundingBox créée: %s", bbox_obj.name)
            
            # Marquer comme normalisé
            self._mark_as_normalized(coll)
            
            logger.info("[T4A Normalize] Normalisation terminée avec succès")
            self.report({'INFO'}, f'Normalisation terminée pour "{coll_name}"')
            return {'FINISHED'}
            
        except Exception as e:
            logger.error("[T4A Normalize] Erreur lors de la normalisation: %s", e)
            self.report({'ERROR'}, f'Erreur normalisation: {e}')
            return {'CANCELLED'}
    
    def _analyze_hierarchy(self, collection):
        """Analyse la hiérarchie des objets dans la collection."""
        
        
        mesh_objects = []
        empty_objects = []
        root_empty = None
        
        # Collecter tous les objets
        for obj in collection.all_objects:
            if obj.type == 'MESH':
                mesh_objects.append(obj)
            elif obj.type == 'EMPTY':
                empty_objects.append(obj)
        
        # Trouver l'Empty racine (celui qui n'a pas de parent dans la collection)
        if empty_objects:
            for empty in empty_objects:
                if not empty.parent or empty.parent not in collection.all_objects:
                    root_empty = empty
                    break
            
            # Si pas trouvé, prendre le premier
            if not root_empty:
                root_empty = empty_objects[0]
        
        # Vérifier si déjà normalisé (présence d'un custom property)
        already_normalized = False
        if root_empty and 't4a_normalized' in root_empty:
            already_normalized = True
        elif not root_empty and collection.all_objects:
            # Vérifier sur le premier objet s'il n'y a pas d'Empty
            first_obj = list(collection.all_objects)[0]
            if 't4a_normalized' in first_obj:
                already_normalized = True
        
        return {
            'mesh_objects': mesh_objects,
            'empty_objects': empty_objects,
            'root_empty': root_empty,
            'already_normalized': already_normalized
        }
    
    def _check_extreme_scales(self, mesh_objects):
        """Vérifie les échelles extrêmes avant Apply Transform."""
        extreme_threshold = 1000.0  # Seuil d'échelle extrême
        
        for obj in mesh_objects:
            scale_values = [abs(s) for s in obj.scale]
            max_scale = max(scale_values)
            min_scale = min(scale_values)
            
            if max_scale > extreme_threshold or min_scale < (1.0 / extreme_threshold):
                logger.warning("[T4A Normalize] Échelle extrême détectée sur %s: %s", 
                             obj.name, obj.scale)
                self.report({'WARNING'}, 
                           f'Échelle extrême sur "{obj.name}": {obj.scale}. Opération annulée.')
                return False
        
        return True
    
    def _reposition_objects(self, mesh_objects, root_empty):
        """Repositionne les objets au centre et au sol."""
        
        # Calculer la bounding box globale de tous les mesh
        bbox_min = mathutils.Vector((float('inf'), float('inf'), float('inf')))
        bbox_max = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for obj in mesh_objects:
            # Obtenir les coins de la bounding box en coordonnées mondiales
            bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
            
            for corner in bbox_corners:
                for i in range(3):
                    bbox_min[i] = min(bbox_min[i], corner[i])
                    bbox_max[i] = max(bbox_max[i], corner[i])
        
        # Calculer le déplacement nécessaire
        center = (bbox_min + bbox_max) / 2.0
        
        offset = mathutils.Vector((0, 0, 0))
        
        if self.auto_center:
            offset.x = -center.x
            offset.y = -center.y
        
        if self.place_on_ground:
            offset.z = -bbox_min.z  # Placer le point le plus bas à Z=0
        
        # Appliquer le déplacement
        if offset.length > 0.001:  # Seulement si déplacement significatif
            if root_empty:
                # Déplacer l'Empty racine
                root_empty.location += offset
            else:
                # Déplacer tous les objets mesh individuellement
                for obj in mesh_objects:
                    obj.location += offset
    
    def _correct_orientation(self, mesh_objects, root_empty):
        """Corrige l'orientation pour que la face avant soit vers +Y."""
        
        # Analyser les normales pour détecter l'orientation dominante
        total_normal = mathutils.Vector((0, 0, 0))
        face_count = 0
        
        for obj in mesh_objects:
            if obj.data and obj.data.polygons:
                # Utiliser les normales des faces existantes
                for poly in obj.data.polygons:
                    world_normal = obj.matrix_world.to_3x3() @ poly.normal
                    total_normal += world_normal
                    face_count += 1
        
        if face_count == 0:
            return False
        
        # Calculer la normale moyenne
        avg_normal = total_normal / face_count
        avg_normal.normalize()
        
        # Déterminer l'axe dominant
        abs_normal = [abs(avg_normal.x), abs(avg_normal.y), abs(avg_normal.z)]
        dominant_axis = abs_normal.index(max(abs_normal))
        
        # Vérifier si une rotation est nécessaire
        target_direction = mathutils.Vector((0, 1, 0))  # +Y
        rotation_needed = False
        rotation_angle = 0
        rotation_axis = mathutils.Vector((0, 0, 1))  # Z par défaut
        
        # Si l'axe dominant n'est pas Y, calculer la rotation
        if dominant_axis != 1:  # 1 = Y
            if dominant_axis == 0:  # X
                rotation_angle = -90 if avg_normal.x > 0 else 90
                rotation_axis = mathutils.Vector((0, 0, 1))  # Rotation autour de Z
            elif dominant_axis == 2:  # Z
                rotation_angle = 90 if avg_normal.z > 0 else -90
                rotation_axis = mathutils.Vector((1, 0, 0))  # Rotation autour de X
            rotation_needed = True
        
        # Appliquer la rotation si nécessaire
        if rotation_needed and abs(rotation_angle) > 5:  # Seuil de 5 degrés
            rotation_matrix = mathutils.Matrix.Rotation(
                math.radians(rotation_angle), 4, rotation_axis
            )
            
            if root_empty:
                # Appliquer à l'Empty racine
                root_empty.matrix_world = rotation_matrix @ root_empty.matrix_world
            else:
                # Appliquer à tous les objets mesh
                for obj in mesh_objects:
                    obj.matrix_world = rotation_matrix @ obj.matrix_world
            
            return True
        
        return False
    
    def _apply_transforms(self, mesh_objects):
        """Applique les transformations sur tous les objets mesh."""
        applied_count = 0
        
        # Sauvegarder la sélection et l'objet actif
        original_selection = list(bpy.context.selected_objects)
        original_active = bpy.context.active_object
        
        try:
            # Désélectionner tout
            bpy.ops.object.select_all(action='DESELECT')
            
            for obj in mesh_objects:
                if obj.type == 'MESH':
                    try:
                        # Sélectionner l'objet
                        obj.select_set(True)
                        bpy.context.view_layer.objects.active = obj
                        
                        # Appliquer les transformations
                        bpy.ops.object.transform_apply(
                            location=True, 
                            rotation=True, 
                            scale=True
                        )
                        
                        obj.select_set(False)
                        applied_count += 1
                        
                    except Exception as e:
                        logger.warning("[T4A Normalize] Échec Apply Transform sur %s: %s", 
                                     obj.name, e)
                        obj.select_set(False)
        
        finally:
            # Restaurer la sélection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                if obj:
                    obj.select_set(True)
            if original_active:
                bpy.context.view_layer.objects.active = original_active
        
        return applied_count
    
    def _create_model_bounding_box(self, mesh_objects, root_empty, collection_name, target_collection):
        """Crée une BoundingBox du modèle et l'ajoute comme enfant à l'Empty racine."""
        
        # Calculer la bounding box globale
        bbox_min = mathutils.Vector((float('inf'), float('inf'), float('inf')))
        bbox_max = mathutils.Vector((float('-inf'), float('-inf'), float('-inf')))
        
        for obj in mesh_objects:
            bbox_corners = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
            for corner in bbox_corners:
                for i in range(3):
                    bbox_min[i] = min(bbox_min[i], corner[i])
                    bbox_max[i] = max(bbox_max[i], corner[i])
        
        # Calculer dimensions et centre
        dimensions = bbox_max - bbox_min
        center = (bbox_min + bbox_max) / 2.0
        
        # Créer un cube pour la BoundingBox
        bbox_name = f"T4A_BBOX_{collection_name}"
        
        # Supprimer l'ancien s'il existe
        old_bbox = bpy.data.objects.get(bbox_name)
        if old_bbox:
            bpy.data.objects.remove(old_bbox, do_unlink=True)
        
        # Créer le nouveau cube
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
        bbox_obj = bpy.context.active_object
        bbox_obj.name = bbox_name
        
        # Redimensionner selon les dimensions calculées
        bbox_obj.scale = dimensions
        
        # Configurer l'affichage
        bbox_obj.display_type = 'WIRE'
        
        # Ajouter la BoundingBox à la collection du modèle
        if target_collection and bbox_obj.name not in target_collection.objects:
            target_collection.objects.link(bbox_obj)
            # Retirer de la collection principale si elle y est
            if bbox_obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(bbox_obj)
        
        # Ajouter comme enfant de l'Empty racine si disponible
        if root_empty:
            bbox_obj.parent = root_empty
            # Conversion en coordonnées locales
            bbox_obj.parent_type = 'OBJECT'
        
        # Appliquer les transformations sur la BoundingBox
        bpy.ops.object.select_all(action='DESELECT')
        bbox_obj.select_set(True)
        bpy.context.view_layer.objects.active = bbox_obj
        
        try:
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        except Exception:
            pass
        
        return bbox_obj
    
    def _mark_as_normalized(self, collection):
        """Marque la collection comme normalisée."""
        # Ajouter une propriété custom sur la collection ou le premier objet
        if collection.objects:
            first_obj = collection.objects[0]
            first_obj['t4a_normalized'] = True
            first_obj['t4a_normalize_timestamp'] = time.time()


# classes tuple will be defined at file end to include all operators


class T4A_OT_TestGeminiConnection(bpy.types.Operator):
    bl_idname = "t4a.test_gemini_connection"
    bl_label = "Test Gemini Connection"
    bl_description = "Test connection to Google Gemini (logs result to console)"

    def execute(self, context):
        try:
            from . import PROD_Parameters
            api_key = ''
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                # fallback to environment variable
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            from . import PROD_gemini

            if model_name:
                res = PROD_gemini.test_connection(api_key, model=model_name, context=context)
            else:
                res = PROD_gemini.test_connection(api_key, context=context)
            logger.info('[T4A Gemini Test] result: %s', res)
            self.report({'INFO'}, 'Gemini test logged to console')
            return {'FINISHED'}
        except Exception as e:
            logger.error('[T4A Gemini Test] error: %s', e)
            self.report({'ERROR'}, f'Gemini test failed: {e}')
            return {'CANCELLED'}


class T4A_OT_AnalyzeTextFile(bpy.types.Operator):
    bl_idname = "t4a.analyze_text_file"
    bl_label = "Analyze Text/PDF File"
    bl_description = "Extract text from a TXT or PDF and ask Gemini to extract 3D dimensions"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}

        # extract text
        text = ''
        ext = os.path.splitext(filepath)[1].lower()
        try:
            if ext == '.txt':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    reader = PyPDF2.PdfReader(filepath)
                    pages = []
                    for p in reader.pages:
                        try:
                            pages.append(p.extract_text() or '')
                        except Exception:
                            pages.append('')
                    text = '\n'.join(pages)
                except Exception:
                    self.report({'ERROR'}, 'PyPDF2 not available or failed to read PDF')
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, 'Unsupported file type')
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f'Failed to read file: {e}')
            return {'CANCELLED'}

        # get API key
        try:
            from . import PROD_Parameters
            api_key = ''
            model_name = None
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            # Ensure model list is fresh before using model_name: if cache expired, refresh synchronously
            try:
                TTL = 3600
                now = time.time()
                ts = float(getattr(prefs, 'model_list_ts', 0) or 0)
                if now - ts >= TTL:
                    # refresh synchronously using PROD_gemini.list_models
                    try:
                        from . import PROD_gemini
                        res = PROD_gemini.list_models(api_key)
                        if res.get('success'):
                            detail = res.get('detail')
                            names = []
                            try:
                                if isinstance(detail, dict):
                                    for m in detail.get('models', []) or []:
                                        n = m.get('name') if isinstance(m, dict) else str(m)
                                        if n:
                                            short = n.split('/')[-1]
                                            names.append(short)
                                if not names and isinstance(detail, list):
                                    for x in detail:
                                        names.append(str(x))
                            except Exception:
                                names = []
                            if names:
                                try:
                                    prefs.model_list_json = json.dumps(names)
                                    prefs.model_list_ts = time.time()
                                    # if no model_name, set to first
                                    try:
                                        if not getattr(prefs, 'model_name', None):
                                            prefs.model_name = names[0]
                                    except Exception:
                                        pass
                                except Exception:
                                    pass
                    except Exception:
                        # ignore refresh errors; we'll proceed with existing model_name
                        pass
                    # re-read model_name after refresh
                    try:
                        model_name = getattr(prefs, 'model_name', None)
                    except Exception:
                        pass
            except Exception:
                # ignore any unexpected errors in the freshness/refresh block
                pass

            from . import PROD_gemini

            if model_name:
                res = PROD_gemini.analyze_text_dimensions(api_key, text, model=model_name, context=context, file_path=filepath)
            else:
                res = PROD_gemini.analyze_text_dimensions(api_key, text, context=context, file_path=filepath)
            detail = res.get('detail')
            # coerce detail to string
            if isinstance(detail, dict):
                detail_str = str(detail)
            else:
                detail_str = str(detail)

            # store into scene collection - chercher l'entrée existante ou créer
            try:
                scene = context.scene
                dims = getattr(scene, 't4a_dimensions', None)
                if dims is not None:
                    # Chercher l'entrée existante par nom de fichier
                    base_name = os.path.basename(filepath)
                    # Enlever l'extension pour correspondre au nom utilisé lors de l'import
                    file_stem = os.path.splitext(base_name)[0]
                    
                    item = None
                    for existing_item in dims:
                        # Correspondance exacte ou nom contenu dans le nom du fichier importé
                        if existing_item.name == base_name or existing_item.name == file_stem or file_stem in existing_item.name:
                            item = existing_item
                            break
                    
                    # Si aucune entrée existante trouvée, créer une nouvelle
                    if item is None:
                        item = dims.add()
                        item.name = base_name
                        item.expanded = False
                    
                    # === NOUVELLE LOGIQUE: Utiliser le système amélioré ===
                    # Mettre à jour les dimensions IA
                    item.dimensions = detail_str  # Garder pour compatibilité
                    item.ai_dimensions = detail_str
                    item.ai_analysis_success = True
                    item.ai_analysis_error = ""
                    
                    # Essayer de calculer les dimensions de la scène si une collection existe
                    try:
                        from . import PROD_dimension_analyzer
                        
                        # Chercher la collection correspondante
                        collection_name = ""
                        for coll in bpy.data.collections:
                            if file_stem in coll.name:
                                collection_name = coll.name
                                break
                        
                        if collection_name:
                            # Effectuer l'analyse complète
                            analysis_result = PROD_dimension_analyzer.analyze_collection_dimensions(
                                collection_name, detail_str
                            )
                            
                            # Mettre à jour le résultat avec toutes les nouvelles propriétés
                            PROD_dimension_analyzer.update_dimension_result(item, analysis_result)
                            
                            logger.info(f'[T4A] Analyse dimensions complète effectuée pour {collection_name}')
                        else:
                            # Pas de collection trouvée, juste marquer l'IA comme réussie
                            item.tolerance_status = 'NO_AI_DATA'
                            logger.info(f'[T4A] Aucune collection trouvée pour {file_stem}, IA seule mise à jour')
                            
                    except Exception as analysis_error:
                        # En cas d'erreur d'analyse, au moins marquer l'IA comme réussie
                        item.ai_analysis_error = f"Erreur analyse auto: {str(analysis_error)[:50]}"
                        logger.warning(f'[T4A] Erreur analyse auto dimensions: {analysis_error}')
            except Exception:
                pass

            logger.info('[T4A Analyze] result: %s', res)
            # If server returned 404, give a helpful report to the user
            status = res.get('status_code')
            if status == 404:
                self.report({'ERROR'}, "Analyse échouée (404). Vérifiez le 'Model Name' dans les préférences et que l'API Generative Language est activée pour votre projet.")
            else:
                self.report({'INFO'}, 'Analyze request sent; result logged')
            return {'FINISHED'}
        except Exception as e:
            logger.error('[T4A Analyze] error %s', e)
            self.report({'ERROR'}, f'Analyze failed: {e}')
            return {'CANCELLED'}


class T4A_OT_ListGeminiModels(bpy.types.Operator):
    bl_idname = "t4a.list_gemini_models"
    bl_label = "Lister les modèles Gemini"
    bl_description = "Interroge l'API Generative Language pour lister les modèles disponibles (logs)"

    def execute(self, context):
        try:
            from . import PROD_Parameters, PROD_gemini
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                api_key = prefs.google_api_key
            except Exception:
                api_key = os.environ.get('GOOGLE_API_KEY', '')

            if not api_key:
                self.report({'ERROR'}, 'No API key provided')
                return {'CANCELLED'}

            # Use the centralized list_models function
            result = PROD_gemini.list_models(api_key)
            
            if result.get('success'):
                models_data = result.get('detail', [])
                compatible_count = sum(1 for m in models_data if isinstance(m, dict) and m.get('compatible', True))
                total_count = len(models_data)
                
                self.report({'INFO'}, f'Liste récupérée: {total_count} modèles ({compatible_count} compatibles generateContent)')
                
                # Log details to console
                print(f"[T4A] [INFO] --- MODÈLES DISPONIBLES POUR VOTRE CLÉ ---")
                for model_info in models_data:
                    if isinstance(model_info, dict):
                        name = model_info.get('name', 'Unknown')
                        compatible = model_info.get('compatible', True)
                        status = "✓" if compatible else "✗"
                        print(f"[T4A] [INFO] {status} {name} {'(compatible generateContent)' if compatible else '(incompatible)'}")
                    else:
                        print(f"[T4A] [INFO] ✓ {model_info}")
                print(f"[T4A] [INFO] ------------------------------------------")
                
                return {'FINISHED'}
            else:
                detail = result.get('detail', 'Unknown error')
                status_code = result.get('status_code')
                if status_code:
                    self.report({'ERROR'}, f"HTTP Error {status_code}")
                else:
                    self.report({'ERROR'}, f"Listing failed: {detail}")
                return {'CANCELLED'}
        except Exception as e:
            logger.error('[T4A List Models] error: %s', e)
            self.report({'ERROR'}, f'Listing failed: {e}')
            return {'CANCELLED'}


class T4A_OT_AnalyzeImageFileForDimensions(bpy.types.Operator):
    bl_idname = "t4a.analyze_image_file_for_dimensions"
    bl_label = "Analyze Image File for Dimensions"
    bl_description = "Analyze a JPG/PNG image using text analysis prompt to extract dimensions"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, "Image file not found")
            return {'CANCELLED'}

        # Check if file is supported image format
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png'):
            self.report({'ERROR'}, 'Unsupported image format. Only JPG and PNG are supported.')
            return {'CANCELLED'}

        # Get API key and model
        try:
            from . import PROD_Parameters
            api_key = ''
            model_name = None
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            if not api_key:
                self.report({'ERROR'}, 'No API key configured')
                return {'CANCELLED'}

            from . import PROD_gemini

            # Call the image analysis function with text prompt
            if model_name:
                res = PROD_gemini.analyze_image_with_ocr(
                    api_key, filepath, 
                    model=model_name, 
                    context=context, 
                    use_text_prompt=True  # Utiliser le prompt text pour extraire les dimensions
                )
            else:
                res = PROD_gemini.analyze_image_with_ocr(
                    api_key, filepath, 
                    context=context, 
                    use_text_prompt=True  # Utiliser le prompt text pour extraire les dimensions
                )
                
            detail = res.get('detail')
            # coerce detail to string
            if isinstance(detail, dict):
                detail_str = str(detail)
            else:
                detail_str = str(detail)

            # store into scene collection - chercher l'entrée existante ou créer
            try:
                scene = context.scene
                dims = getattr(scene, 't4a_dimensions', None)
                if dims is not None:
                    # Chercher l'entrée existante par nom de fichier
                    base_name = os.path.basename(filepath)
                    # Enlever l'extension pour correspondre au nom utilisé lors de l'import
                    file_stem = os.path.splitext(base_name)[0]
                    
                    item = None
                    for existing_item in dims:
                        # Correspondance exacte ou nom contenu dans le nom du fichier importé
                        if existing_item.name == base_name or existing_item.name == file_stem or file_stem in existing_item.name:
                            item = existing_item
                            break
                    
                    # Si aucune entrée existante trouvée, créer une nouvelle avec préfixe IMG_
                    if item is None:
                        item = dims.add()
                        item.name = f"IMG_{base_name}"
                        item.expanded = False
                    
                    # === NOUVELLE LOGIQUE: Utiliser le système amélioré ===
                    # Mettre à jour les dimensions IA (analyse d'image)
                    item.dimensions = detail_str  # Garder pour compatibilité
                    item.ai_dimensions = detail_str
                    item.ai_analysis_success = True
                    item.ai_analysis_error = ""
                    
                    # Pour les images, pas de collection 3D associée généralement
                    # Marquer comme données IA uniquement
                    item.tolerance_status = 'NO_AI_DATA'  # Pas de comparaison possible
                    item.scene_dimensions = "Image - pas de modèle 3D"
                
                self.report({'INFO'}, f'Image analyzed for dimensions: {os.path.basename(filepath)}')
                
                # log debug if debug_mode is enabled
                try:
                    from . import PROD_Parameters
                    prefs = PROD_Parameters.get_addon_preferences()
                    if getattr(prefs, 'debug_mode', False):
                        print(f"[DEBUG] Image dimensions analysis result: {detail_str}")
                except Exception:
                    pass
                    
            except Exception as e:
                self.report({'ERROR'}, f'Failed to store analysis result: {e}')
                return {'CANCELLED'}

        except Exception as e:
            self.report({'ERROR'}, f'Image analysis failed: {e}')
            return {'CANCELLED'}

        return {'FINISHED'}


class T4A_OT_AnalyzeImageFile(bpy.types.Operator):
    bl_idname = "t4a.analyze_image_file"
    bl_label = "Analyze Image File"
    bl_description = "Analyze a JPG/PNG image with Gemini Vision for OCR and technical content extraction"

    filepath: bpy.props.StringProperty(name="Filepath", subtype='FILE_PATH')

    def execute(self, context):
        filepath = self.filepath
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, "Image file not found")
            return {'CANCELLED'}

        # Check if file is supported image format
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png'):
            self.report({'ERROR'}, 'Unsupported image format. Only JPG and PNG are supported.')
            return {'CANCELLED'}

        # Get API key and model
        try:
            from . import PROD_Parameters
            api_key = ''
            model_name = None
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                api_key = prefs.google_api_key
                model_name = getattr(prefs, 'model_name', None)
            except Exception:
                api_key = os.environ.get('GOOGLE_API_KEY', '')
                model_name = os.environ.get('MODEL_NAME', None)

            if not api_key:
                self.report({'ERROR'}, 'No API key configured')
                return {'CANCELLED'}

            # Ensure model list is fresh before using model_name
            try:
                TTL = 3600
                now = time.time()
                ts = float(getattr(prefs, 'model_list_ts', 0) or 0)
                if now - ts >= TTL:
                    # refresh synchronously using PROD_gemini.list_models
                    try:
                        from . import PROD_gemini
                        res = PROD_gemini.list_models(api_key)
                        if res.get('success'):
                            detail = res.get('detail')
                            if detail and isinstance(detail, list):
                                try:
                                    # Store the complete list with compatibility info
                                    prefs.model_list_json = json.dumps(detail)
                                    prefs.model_list_ts = time.time()
                                    # if no model_name, set to first compatible model
                                    if not getattr(prefs, 'model_name', None):
                                        try:
                                            # Find first compatible model, fallback to first model
                                            first_compatible = None
                                            first_model = None
                                            for model_info in detail:
                                                if isinstance(model_info, dict):
                                                    name = model_info.get('name', '')
                                                    if name:
                                                        if first_model is None:
                                                            first_model = name
                                                        if model_info.get('compatible', False) and first_compatible is None:
                                                            first_compatible = name
                                            
                                            prefs.model_name = first_compatible or first_model or 'models/gemini-2.5-flash-lite'
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    # re-read model_name after refresh
                    try:
                        model_name = getattr(prefs, 'model_name', None)
                    except Exception:
                        pass
            except Exception:
                pass

            from . import PROD_gemini

            # Call the image analysis function
            if model_name:
                res = PROD_gemini.analyze_image_with_ocr(api_key, filepath, model=model_name, context=context)
            else:
                res = PROD_gemini.analyze_image_with_ocr(api_key, filepath, context=context)
                
            detail = res.get('detail')
            # coerce detail to string
            if isinstance(detail, dict):
                detail_str = str(detail)
            else:
                detail_str = str(detail)

            # store into scene collection - chercher l'entrée existante ou créer
            try:
                scene = context.scene
                dims = getattr(scene, 't4a_dimensions', None)
                if dims is not None:
                    # Chercher l'entrée existante par nom de fichier
                    base_name = os.path.basename(filepath)
                    # Enlever l'extension pour correspondre au nom utilisé lors de l'import
                    file_stem = os.path.splitext(base_name)[0]
                    
                    item = None
                    for existing_item in dims:
                        # Correspondance exacte ou nom contenu dans le nom du fichier importé
                        if existing_item.name == base_name or existing_item.name == file_stem or file_stem in existing_item.name:
                            item = existing_item
                            break
                    
                    # Si aucune entrée existante trouvée, créer une nouvelle avec préfixe IMG_
                    if item is None:
                        item = dims.add()
                        item.name = f"IMG_{base_name}"
                        item.expanded = False
                    
                    # Mettre à jour les dimensions
                    item.dimensions = detail_str
            except Exception:
                pass

            logger.info('[T4A Analyze Image] result: %s', res)
            
            # If server returned error, give helpful report
            status = res.get('status_code')
            if status == 404:
                self.report({'ERROR'}, "Analyse d'image échouée (404). Vérifiez le 'Model Name' dans les préférences.")
            elif not res.get('success'):
                self.report({'ERROR'}, f"Analyse d'image échouée: {detail}")
            else:
                self.report({'INFO'}, 'Image analysis completed; result stored')
            return {'FINISHED'}
        except Exception as e:
            logger.error('[T4A Analyze Image] error %s', e)
            self.report({'ERROR'}, f'Image analysis failed: {e}')
            return {'CANCELLED'}


class T4A_OT_FindMatchingTextAndAnalyze(bpy.types.Operator):
    bl_idname = "t4a.find_and_analyze_matching"
    bl_label = "Find matching files and analyze"
    bl_description = "Look for JPG/PNG/TXT/PDF files with same base name as imported 3D files and analyze them (Images prioritized)"

    def execute(self, context):
        try:
            from . import PROD_Parameters
            try:
                prefs = PROD_Parameters.get_addon_preferences()
                base_path = prefs.scan_path
            except Exception:
                base_path = os.environ.get('SCAN_PATH', '')

            if not base_path:
                self.report({'ERROR'}, 'No scan path configured')
                return {'CANCELLED'}

            # iterate imported collections in scene root
            scene = context.scene
            root_coll = scene.collection
            processed = 0
            for coll in list(root_coll.children):
                # if collection name has an underscore, assume format EXT_basename
                parts = coll.name.split('_', 1)
                if len(parts) != 2:
                    continue
                base = parts[1]
                stem = os.path.splitext(base)[0]
                
                # Search for files in order of priority: JPG/PNG (images) first, then TXT/PDF
                found = None
                found_type = None
                
                # Priority 1: Images (JPG/PNG)
                for ext in ('.jpg', '.jpeg', '.png'):
                    candidate = os.path.join(base_path, stem + ext)
                    if os.path.exists(candidate):
                        found = candidate
                        found_type = 'image'
                        break
                
                # Priority 2: Text/PDF files (only if no image found)
                if not found:
                    for ext in ('.txt', '.pdf'):
                        candidate = os.path.join(base_path, stem + ext)
                        if os.path.exists(candidate):
                            found = candidate
                            found_type = 'text'
                            break
                
                if found:
                    # call appropriate analyze operator based on file type
                    try:
                        if found_type == 'image':
                            # Utiliser le prompt d'analyse de texte pour extraire les dimensions des images
                            bpy.ops.t4a.analyze_image_file_for_dimensions(filepath=found)
                            logger.info('[T4A] Image analysis (dimensions) launched for: %s', found)
                        else:  # text/pdf
                            bpy.ops.t4a.analyze_text_file(filepath=found)
                            logger.info('[T4A] Text analysis launched for: %s', found)
                        processed += 1
                    except Exception as e:
                        logger.error('[T4A] Analysis failed for %s: %s', found, e)

            if processed > 0:
                self.report({'INFO'}, f'Processed {processed} matching files')
            else:
                self.report({'INFO'}, 'No matching files found')
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f'Find/Analyze failed: {e}')
            return {'CANCELLED'}




def register():
    import traceback
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            logger.debug("[T4A Register] Registered %s", getattr(cls, '__name__', str(cls)))
        except ValueError as ve:
            msg = str(ve)
            if 'already registered' in msg:
                logger.debug("[T4A Register] Skipping already-registered %s", getattr(cls, '__name__', str(cls)))
            else:
                logger.debug("[T4A Register] ValueError registering %s: %s", getattr(cls, '__name__', str(cls)), msg)
                traceback.print_exc()
        except Exception:
            logger.debug("[T4A Register] Failed to register %s", getattr(cls, '__name__', str(cls)))
            traceback.print_exc()


def unregister():
    import traceback
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            logger.debug("[T4A Unregister] Unregistered %s", getattr(cls, '__name__', str(cls)))
        except ValueError as ve:
            msg = str(ve)
            if 'not registered' in msg or 'is not registered' in msg:
                logger.debug("[T4A Unregister] Skipping not-registered %s", getattr(cls, '__name__', str(cls)))
            else:
                logger.debug("[T4A Unregister] ValueError unregistering %s: %s", getattr(cls, '__name__', str(cls)), msg)
                traceback.print_exc()
        except Exception:
            logger.debug("[T4A Unregister] Failed to unregister %s", getattr(cls, '__name__', str(cls)))
            traceback.print_exc()


classes = (
    T4A_OT_ScanAndImport,
    T4A_OT_SetupScene,
    T4A_OT_ImportFileToCollection,
    T4A_OT_NormalizeImportedObjects,
    T4A_OT_TestGeminiConnection,
    T4A_OT_AnalyzeTextFile,
    T4A_OT_AnalyzeImageFile,
    T4A_OT_AnalyzeImageFileForDimensions,
    T4A_OT_ListGeminiModels,
    T4A_OT_FindMatchingTextAndAnalyze,
)
