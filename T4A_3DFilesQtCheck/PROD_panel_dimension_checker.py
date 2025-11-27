"""
Panel pour les fonctions de vérification et comparaison des dimensions.

Ajoute des boutons pour :
- Comparer les dimensions d'une collection spécifique
- Créer des BoundingBoxes pour tous les modèles
- Nettoyer les helpers
- Contrôler la création forcée des BoundingBoxes
"""
import os
import bpy


class T4A_PT_DimensionChecker(bpy.types.Panel):
    bl_label = "Dimension Checker"
    bl_idname = "T4A_PT_dimension_checker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.label(text="Vérification des Dimensions")
        layout.separator()

        # Global operations box
        box = layout.box()
        box.label(text="Opérations Globales")
        
        # Create bounding boxes for all models
        row = box.row()
        row.operator("t4a.create_bounding_boxes", text="Créer toutes les BoundingBoxes", icon='MESH_CUBE')
        
        # Clear helpers
        row = box.row()
        row.operator("t4a.clear_helpers", text="Nettoyer les Helpers", icon='TRASH')
        
        # Force creation control
        try:
            from . import PROD_Utilitaire
            force_creation = getattr(PROD_Utilitaire, 'forceHelperBoxCreation', False)
            
            row = box.row()
            # Create a dummy property to display the checkbox
            row.prop(context.scene, 't4a_force_helper_creation', 
                     text="Forcer création BoundingBox")
            
            # Update the module variable if the property changed
            scene_force = getattr(scene, 't4a_force_helper_creation', force_creation)
            if scene_force != force_creation:
                PROD_Utilitaire.forceHelperBoxCreation = scene_force
        except Exception:
            box.label(text="Contrôle force création indisponible")

        layout.separator()

        # Individual collection operations
        box = layout.box()
        box.label(text="Collections Importées")
        
        # List imported collections with dimension check buttons
        root_coll = scene.collection
        found_collections = False
        
        for coll in root_coll.children:
            # Skip helper collections
            if coll.name.startswith('T4A_') or coll.name in ['Check_Support_Helpers', 'T4A_Helpers']:
                continue
                
            # Check if collection has 3D objects
            has_objects = any(obj.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'} 
                            for obj in coll.all_objects)
            if not has_objects:
                continue
                
            found_collections = True
            
            # Check if AI dimensions are available for this collection
            has_ai_dims = False
            try:
                # Extract base name from collection name (remove EXT_ prefix)
                parts = coll.name.split('_', 1)
                if len(parts) == 2:
                    base_name = parts[1]
                    stem = os.path.splitext(base_name)[0]
                    
                    # Check if there's a matching dimension analysis
                    dims_collection = getattr(scene, 't4a_dimensions', None)
                    if dims_collection:
                        for item in dims_collection:
                            item_name = item.name
                            if (stem in item_name or 
                                item_name.startswith(f"IMG_{stem}") or
                                item_name == base_name or
                                os.path.splitext(item_name)[0] == stem):
                                # Check if the dimensions contain actual values
                                dim_text = getattr(item, 'dimensions', '') or ''
                                if dim_text.strip() and 'NOT_FOUND' not in dim_text.upper():
                                    has_ai_dims = True
                                break
            except Exception:
                pass
            
            # Collection row with name and check button
            row = box.row()
            split = row.split(factor=0.6)
            
            # Collection name with warning icon if no AI dimensions
            name_row = split.row()
            if not has_ai_dims:
                name_row.alert = True
                name_row.label(text="⚠", icon='ERROR')
            
            # Collection name (truncate if too long)
            coll_display = coll.name
            if len(coll_display) > 15:
                coll_display = coll_display[:12] + "..."
            name_row.label(text=coll_display)
            
            # Check dimensions button
            button_split = split.split(factor=0.7)
            if has_ai_dims:
                op = button_split.operator("t4a.compare_dimensions", text="Vérifier", icon='CHECKMARK')
            else:
                op = button_split.operator("t4a.compare_dimensions", text="Vérifier", icon='QUESTION')
            op.collection_name = coll.name
            
            # Status indicator
            if not has_ai_dims:
                button_split.label(text="Pas d'IA", icon='X')
        
        if not found_collections:
            box.label(text="Aucune collection trouvée")
            box.label(text="Importez des modèles 3D d'abord")

        layout.separator()

        # Statistics box
        stats_box = layout.box()
        stats_box.label(text="Statistiques")
        
        # Count helper objects
        helper_count = 0
        try:
            for obj in bpy.data.objects:
                if obj.name.startswith('T4A_HELPER_'):
                    helper_count += 1
        except Exception:
            pass
            
        stats_box.label(text=f"Helpers créés: {helper_count}")
        
        # Count dimension results
        dim_count = 0
        ai_available_count = 0
        try:
            dims = getattr(scene, 't4a_dimensions', None)
            if dims:
                dim_count = len(dims)
                for item in dims:
                    dim_text = getattr(item, 'dimensions', '') or ''
                    if dim_text.strip() and 'NOT_FOUND' not in dim_text.upper():
                        ai_available_count += 1
        except Exception:
            pass
            
        stats_box.label(text=f"Analyses IA: {dim_count}")
        if dim_count > 0:
            if ai_available_count == dim_count:
                stats_box.label(text=f"✓ Toutes les analyses OK ({ai_available_count})", icon='CHECKMARK')
            elif ai_available_count > 0:
                stats_box.label(text=f"⚠ {ai_available_count}/{dim_count} analyses utilisables", icon='ERROR')
            else:
                stats_box.label(text="✗ Aucune analyse utilisable", icon='CANCEL')


def register_panel_props():
    """Register properties needed by the panel."""
    try:
        # Property to control force creation from UI
        bpy.types.Scene.t4a_force_helper_creation = bpy.props.BoolProperty(
            name="Force Helper Creation",
            description="Force la création de BoundingBox même si les dimensions correspondent",
            default=True,
            update=update_force_creation
        )
    except Exception:
        pass


def update_force_creation(self, context):
    """Update the module variable when UI property changes."""
    try:
        from . import PROD_Utilitaire
        PROD_Utilitaire.forceHelperBoxCreation = context.scene.t4a_force_helper_creation
    except Exception:
        pass


def unregister_panel_props():
    """Unregister panel properties."""
    try:
        del bpy.types.Scene.t4a_force_helper_creation
    except Exception:
        pass


def register():
    register_panel_props()
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    unregister_panel_props()


classes = (
    T4A_PT_DimensionChecker,
)

__all__ = ('T4A_PT_DimensionChecker',)