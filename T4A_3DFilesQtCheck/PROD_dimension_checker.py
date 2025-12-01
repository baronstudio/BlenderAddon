"""
Module pour la comparaison des dimensions et création de BoundingBox.

Contient :
- opérateur pour comparer les dimensions IA vs modèle 3D
- opérateur pour créer des BoundingBox pour chaque collection
- logique de comparaison et création automatique de helpers
"""
import os
import bpy
import mathutils
from typing import Optional, Dict, Any


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


def get_dimension_status(collection_name: str) -> dict:
    """Obtient le statut des dimensions pour une collection donnée.
    
    Args:
        collection_name: Nom de la collection
        
    Returns:
        dict: {
            'status': 'OK'|'WARNING'|'ERROR'|'NO_AI_DATA',
            'difference': float (pourcentage),
            'has_ai_dims': bool
        }
    """
    try:
        scene = bpy.context.scene
        
        # Extraire le nom de base de la collection (enlever préfixe EXT_)
        parts = collection_name.split('_', 1)
        if len(parts) == 2:
            base_name = parts[1]
            stem = os.path.splitext(base_name)[0]
        else:
            base_name = collection_name
            stem = os.path.splitext(collection_name)[0]
        
        # Chercher les données d'analyse correspondantes
        dims_collection = getattr(scene, 't4a_dimensions', None)
        if not dims_collection:
            return {'status': 'NO_AI_DATA', 'difference': 0.0, 'has_ai_dims': False}
        
        # Trouver l'entrée correspondante
        matching_item = None
        for item in dims_collection:
            item_name = item.name
            if (stem in item_name or 
                item_name.startswith(f"IMG_{stem}") or
                item_name == base_name or
                os.path.splitext(item_name)[0] == stem):
                matching_item = item
                break
        
        if not matching_item:
            return {'status': 'NO_AI_DATA', 'difference': 0.0, 'has_ai_dims': False}
        
        # Vérifier si on a des données IA valides
        dim_text = getattr(matching_item, 'dimensions', '') or ''
        if not dim_text.strip() or 'NOT_FOUND' in dim_text.upper():
            return {'status': 'NO_AI_DATA', 'difference': 0.0, 'has_ai_dims': False}
        
        # Retourner le statut stocké
        status = getattr(matching_item, 'tolerance_status', 'NO_AI_DATA')
        difference = getattr(matching_item, 'difference_percentage', 0.0)
        
        return {
            'status': status,
            'difference': difference,
            'has_ai_dims': True
        }
        
    except Exception as e:
        logger.debug(f"Erreur lors de l'obtention du statut de dimension: {e}")
        return {'status': 'NO_AI_DATA', 'difference': 0.0, 'has_ai_dims': False}


def compare_dimensions(ai_dims: Dict[str, float], bbox_dims: Dict[str, float], tolerance: float = 0.05) -> Dict[str, Any]:
    """Compare AI-analyzed dimensions with 3D model bounding box dimensions.
    
    Args:
        ai_dims: Dictionary with 'width', 'height', 'depth' keys (can be None)
        bbox_dims: Dictionary with 'width', 'height', 'depth' keys (all float)
        tolerance: Tolerance threshold (0.05 = 5%)
        
    Returns:
        Dict with 'match', 'need_helper', 'differences', 'max_difference', 'status', 'has_ai_data' keys
    """
    differences = {'width': None, 'height': None, 'depth': None}
    valid_comparisons = 0
    max_difference = 0.0
    has_ai_data = False
    
    # Compare each dimension
    for dim in ['width', 'height', 'depth']:
        ai_val = ai_dims.get(dim)
        bbox_val = bbox_dims.get(dim, 0.0)
        
        if ai_val is not None and ai_val > 0 and bbox_val > 0:
            has_ai_data = True
            valid_comparisons += 1
            diff = abs(ai_val - bbox_val) / ai_val
            differences[dim] = {
                'ai': ai_val,
                'model': bbox_val,
                'diff_percent': diff,
                'diff_absolute': abs(ai_val - bbox_val)
            }
            max_difference = max(max_difference, diff)
    
    # Determine overall match and status
    if not has_ai_data:
        return {
            'match': True,  # No comparison possible
            'need_helper': False,
            'differences': differences,
            'max_difference': 0.0,
            'status': 'NO_AI_DATA',
            'has_ai_data': False
        }
    
    # Determine status based on max difference
    is_within_tolerance = max_difference <= tolerance
    
    if is_within_tolerance:
        status = 'OK'
    elif max_difference <= tolerance * 2:  # Warning zone: 1x to 2x tolerance
        status = 'WARNING'
    else:  # Error zone: > 2x tolerance
        status = 'ERROR'
    
    # Determine if helper box is needed
    from . import PROD_Utilitaire
    force_creation = getattr(PROD_Utilitaire, 'forceHelperBoxCreation', False)
    
    return {
        'match': is_within_tolerance,
        'need_helper': force_creation or not is_within_tolerance,  # Create helper if outside tolerance
        'differences': differences,
        'max_difference': max_difference,
        'status': status,
        'has_ai_data': has_ai_data
    }


class T4A_OT_CompareDimensions(bpy.types.Operator):
    bl_idname = "t4a.compare_dimensions"
    bl_label = "Comparer Dimensions"
    bl_description = "Compare les dimensions IA avec les dimensions du modèle 3D et crée une BoundingBox si nécessaire"

    collection_name: bpy.props.StringProperty(name="Collection Name", default="")

    def execute(self, context):
        try:
            coll_name = self.collection_name
            if not coll_name:
                self.report({'ERROR'}, 'Nom de collection non spécifié')
                return {'CANCELLED'}

            # Find the collection
            coll = bpy.data.collections.get(coll_name)
            if not coll:
                self.report({'ERROR'}, f'Collection "{coll_name}" non trouvée')
                return {'CANCELLED'}

            # Measure 3D model bbox
            from . import PROD_Utilitaire
            bbox_data = PROD_Utilitaire.measure_collection_bbox(coll)
            if not bbox_data:
                self.report({'ERROR'}, 'Impossible de mesurer la bounding box du modèle 3D')
                return {'CANCELLED'}

            bbox_dims = {
                'width': bbox_data['width'],
                'height': bbox_data['height'], 
                'depth': bbox_data['depth']
            }

            # Find matching AI dimensions
            scene = context.scene
            ai_dims = None
            ai_text = ""
            
            # Look for matching dimension analysis in scene
            try:
                dims_collection = getattr(scene, 't4a_dimensions', None)
                if dims_collection:
                    # Extract base name from collection name (remove EXT_ prefix)
                    parts = coll_name.split('_', 1)
                    if len(parts) == 2:
                        base_name = parts[1]
                        stem = os.path.splitext(base_name)[0]
                        
                        # Look for matching dimension result
                        for item in dims_collection:
                            item_name = item.name
                            # Check if this dimension result matches our model
                            if (stem in item_name or 
                                item_name.startswith(f"IMG_{stem}") or
                                item_name == base_name or
                                os.path.splitext(item_name)[0] == stem):
                                ai_text = item.dimensions
                                break
            except Exception as e:
                logger.debug("Error finding AI dimensions: %s", e)

            if ai_text:
                # Parse AI dimensions
                ai_dims = PROD_Utilitaire.parse_dimensions_string(ai_text)
                logger.info("Dimensions IA trouvées: %s", ai_dims)
            else:
                logger.info("Aucune dimension IA trouvée pour %s", coll_name)
                ai_dims = {'width': None, 'height': None, 'depth': None}

            # Compare dimensions with tolerance from preferences
            tolerance = 0.05  # default
            try:
                from . import PROD_Parameters
                prefs = PROD_Parameters.get_addon_preferences()
                if prefs:
                    tolerance = getattr(prefs, 'dimension_tolerance', 0.05)
            except Exception:
                pass
                
            comparison = compare_dimensions(ai_dims, bbox_dims, tolerance=tolerance)
            
            # Stocker le statut dans l'item de dimension correspondant
            try:
                dims_collection = getattr(scene, 't4a_dimensions', None)
                if dims_collection:
                    # Extraire le nom de base de la collection
                    parts = coll_name.split('_', 1)
                    if len(parts) == 2:
                        base_name = parts[1]
                        stem = os.path.splitext(base_name)[0]
                        
                        # Trouver et mettre à jour l'entrée correspondante
                        for item in dims_collection:
                            item_name = item.name
                            if (stem in item_name or 
                                item_name.startswith(f"IMG_{stem}") or
                                item_name == base_name or
                                os.path.splitext(item_name)[0] == stem):
                                item.tolerance_status = comparison['status']
                                item.difference_percentage = comparison['max_difference'] * 100
                                break
            except Exception as e:
                logger.debug(f"Erreur lors de la mise à jour du statut: {e}")
            
            logger.info("Comparaison pour %s:", coll_name)
            
            # Get scene unit scale for logging
            try:
                from . import PROD_Utilitaire
                unit_scale = PROD_Utilitaire.get_scene_unit_scale()
                logger.info("  Échelle de la scène: %.3f", unit_scale)
            except Exception:
                unit_scale = 1.0
                
            logger.info("  Modèle 3D (avec échelle): W=%.3f H=%.3f D=%.3f", 
                       bbox_dims['width'], bbox_dims['height'], bbox_dims['depth'])
            if any(v is not None for v in ai_dims.values()):
                logger.info("  IA: W=%s H=%s D=%s", 
                           ai_dims['width'] or 'N/A', 
                           ai_dims['height'] or 'N/A', 
                           ai_dims['depth'] or 'N/A')
                logger.info("  Correspondance: %s (diff max: %.1f%%)", 
                           "OUI" if comparison['match'] else "NON",
                           comparison['max_difference'] * 100)
            else:
                logger.info("  Aucune dimension IA disponible")

            # Check if AI dimensions are available for comparison
            has_ai_dims = any(v is not None and v > 0 for v in ai_dims.values())
            
            # Create helper box only if we have AI dimensions to compare or if forced
            from . import PROD_Utilitaire
            force_creation = getattr(PROD_Utilitaire, 'forceHelperBoxCreation', False)
            
            if has_ai_dims and comparison['need_helper']:
                # Use AI dimensions if available, otherwise use model dimensions
                helper_dims = {}
                for key in ['width', 'height', 'depth']:
                    ai_val = ai_dims.get(key)
                    if ai_val is not None and ai_val > 0:
                        helper_dims[key] = ai_val
                    else:
                        helper_dims[key] = bbox_dims[key]

                helper_obj = PROD_Utilitaire.create_or_update_helper_box(
                    coll_name, helper_dims, bbox_data['center']
                )
                if helper_obj:
                    try:
                        unit_scale = PROD_Utilitaire.get_scene_unit_scale()
                        scale_info = f" (échelle scène: {unit_scale:.2f})" if unit_scale != 1.0 else ""
                    except Exception:
                        scale_info = ""
                        
                    if comparison['match']:
                        self.report({'INFO'}, f'BoundingBox de référence créée pour "{coll_name}" (création forcée){scale_info}')
                    else:
                        self.report({'WARNING'}, 
                                   f'Différence détectée pour "{coll_name}" - BoundingBox créée (diff max: {comparison["max_difference"]*100:.1f}%){scale_info}')
                else:
                    self.report({'ERROR'}, f'Erreur lors de la création de la BoundingBox pour "{coll_name}"')
                    
            elif force_creation and not has_ai_dims:
                # Force creation even without AI dims - use model dimensions
                helper_obj = PROD_Utilitaire.create_or_update_helper_box(
                    coll_name, bbox_dims, bbox_data['center']
                )
                if helper_obj:
                    try:
                        unit_scale = PROD_Utilitaire.get_scene_unit_scale()
                        scale_info = f" (échelle scène: {unit_scale:.2f})" if unit_scale != 1.0 else ""
                    except Exception:
                        scale_info = ""
                    self.report({'WARNING'}, f'⚠ BoundingBox créée pour "{coll_name}" sans dimensions IA (création forcée){scale_info}')
                else:
                    self.report({'ERROR'}, f'Erreur lors de la création forcée de la BoundingBox pour "{coll_name}"')
                    
            elif not has_ai_dims:
                # No AI dimensions available and no forced creation
                self.report({'WARNING'}, f'⚠ Impossible de comparer "{coll_name}" - Aucune dimension IA disponible')
                
            else:
                # AI dimensions available but no helper needed
                self.report({'INFO'}, f'Dimensions OK pour "{coll_name}" - Aucune BoundingBox nécessaire')

            return {'FINISHED'}

        except Exception as e:
            logger.error("Erreur lors de la comparaison: %s", e)
            self.report({'ERROR'}, f'Erreur: {e}')
            return {'CANCELLED'}


class T4A_OT_CreateBoundingBoxes(bpy.types.Operator):
    bl_idname = "t4a.create_bounding_boxes"
    bl_label = "Créer BoundingBoxes"
    bl_description = "Crée des BoundingBox pour tous les modèles 3D importés selon leurs dimensions IA"

    def execute(self, context):
        scene = context.scene
        root_coll = scene.collection
        processed = 0
        created = 0

        try:
            # Process all imported model collections
            for coll in list(root_coll.children):
                # Skip helper collections
                if coll.name.startswith('T4A_') or coll.name in ['Check_Support_Helpers', 'T4A_Helpers']:
                    continue
                    
                # Check if collection has 3D objects
                has_objects = any(obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'} 
                                for obj in coll.all_objects)
                if not has_objects:
                    continue

                processed += 1
                
                try:
                    # Call compare_dimensions operator for this collection
                    result = bpy.ops.t4a.compare_dimensions(collection_name=coll.name)
                    if result == {'FINISHED'}:
                        created += 1
                        logger.debug("BoundingBox créée pour: %s", coll.name)
                    else:
                        logger.error("Erreur lors de la création pour: %s", coll.name)
                except Exception as e:
                    logger.error("Erreur pour collection %s: %s", coll.name, e)

            if processed > 0:
                self.report({'INFO'}, f'Traité {processed} collections, {created} BoundingBoxes créées')
            else:
                self.report({'INFO'}, 'Aucune collection de modèles 3D trouvée')

            return {'FINISHED'}

        except Exception as e:
            logger.error("Erreur lors de la création des BoundingBoxes: %s", e)
            self.report({'ERROR'}, f'Erreur: {e}')
            return {'CANCELLED'}


class T4A_OT_VerifyDimensionsOnImport(bpy.types.Operator):
    bl_idname = "t4a.verify_dimensions_on_import"
    bl_label = "Vérifier Dimensions à l'Import"
    bl_description = "Vérifie automatiquement les dimensions après import d'un modèle 3D"

    collection_name: bpy.props.StringProperty(name="Collection Name", default="")

    def execute(self, context):
        """Cette opération est appelée automatiquement après import pour vérifier les dimensions."""
        try:
            coll_name = self.collection_name
            if not coll_name:
                return {'CANCELLED'}

            # Delay the check slightly to ensure analysis is complete
            def delayed_check():
                try:
                    bpy.ops.t4a.compare_dimensions(collection_name=coll_name)
                except Exception as e:
                    logger.error("Erreur lors de la vérification automatique: %s", e)

            # Use a timer to delay the check
            bpy.app.timers.register(delayed_check, first_interval=2.0)
            
            return {'FINISHED'}
        except Exception as e:
            logger.error("Erreur lors de la programmation de vérification: %s", e)
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
                if hasattr(PROD_Parameters := None, 'is_debug_mode'):
                    try:
                        from . import PROD_Parameters
                        if PROD_Parameters.is_debug_mode():
                            traceback.print_exc()
                    except Exception:
                        pass
        except Exception:
            logger.error("[T4A Register] Failed to register %s", getattr(cls, '__name__', str(cls)))
            if hasattr(PROD_Parameters := None, 'is_debug_mode'):
                try:
                    from . import PROD_Parameters
                    if PROD_Parameters.is_debug_mode():
                        traceback.print_exc()
                except Exception:
                    pass


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
                if hasattr(PROD_Parameters := None, 'is_debug_mode'):
                    try:
                        from . import PROD_Parameters
                        if PROD_Parameters.is_debug_mode():
                            traceback.print_exc()
                    except Exception:
                        pass
        except Exception:
            logger.error("[T4A Unregister] Failed to unregister %s", getattr(cls, '__name__', str(cls)))
            if hasattr(PROD_Parameters := None, 'is_debug_mode'):
                try:
                    from . import PROD_Parameters
                    if PROD_Parameters.is_debug_mode():
                        traceback.print_exc()
                except Exception:
                    pass


classes = (
    T4A_OT_CompareDimensions,
    T4A_OT_CreateBoundingBoxes,
    T4A_OT_VerifyDimensionsOnImport,
)

__all__ = (
    'T4A_OT_CompareDimensions',
    'T4A_OT_CreateBoundingBoxes', 
    'T4A_OT_VerifyDimensionsOnImport',
    'compare_dimensions',
)