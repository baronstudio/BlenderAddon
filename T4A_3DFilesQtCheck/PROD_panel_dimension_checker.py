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
            
            # Obtenir le statut des dimensions pour cette collection
            from . import PROD_dimension_checker
            dim_status = PROD_dimension_checker.get_dimension_status(coll.name)
            status = dim_status['status']
            has_ai_dims = dim_status['has_ai_dims']
            difference = dim_status['difference']
            
            # Collection row with name and check button
            row = box.row()
            split = row.split(factor=0.6)
            
            # Collection name avec icône de statut
            name_row = split.row()
            
            # Icône et couleur selon le statut
            if status == 'NO_AI_DATA':
                name_row.alert = True
                name_row.label(text="", icon='ERROR')  # Icône rouge pour pas de données
                tooltip = "Pas de données IA disponibles"
            elif status == 'OK':
                name_row.label(text="", icon='CHECKMARK')  # Icône verte pour OK
                tooltip = f"Dimensions conformes (diff: {difference:.1f}%)"
            elif status == 'WARNING':
                name_row.alert = True
                name_row.label(text="", icon='ERROR')  # Icône orange pour warning
                tooltip = f"Dimensions hors tolérance (diff: {difference:.1f}%)"
            else:  # ERROR
                name_row.alert = True
                name_row.label(text="", icon='CANCEL')  # Icône rouge pour erreur critique
                tooltip = f"Différence critique (diff: {difference:.1f}%)"
            
            # Collection name (tronquer si trop long)
            coll_display = coll.name
            if len(coll_display) > 15:
                coll_display = coll_display[:12] + "..."
            
            # Nom avec couleur selon le statut
            name_label = name_row.row()
            if status in ['WARNING', 'ERROR']:
                name_label.alert = True
            name_label.label(text=coll_display)
            
            # Affichage du pourcentage si hors tolérance
            if status in ['WARNING', 'ERROR'] and difference > 0:
                perc_label = name_row.row()
                perc_label.scale_x = 0.7
                perc_label.alert = True
                perc_label.label(text=f"({difference:.1f}%)")
            
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