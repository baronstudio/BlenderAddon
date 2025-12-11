"""
T4A Assets Configuration Baker - Export List Operators
Operators for managing export collections list
"""

import bpy
from bpy.types import Operator


class T4A_OT_RefreshExportCollectionList(Operator):
    """Refresh the export collections list from scene collections"""
    bl_idname = "t4a.refresh_export_collection_list"
    bl_label = "Refresh Export Collections List"
    bl_description = "Refresh the export collections list from scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.t4a_baker_props
        
        # Clear existing list
        props.export_collections.clear()
        
        # Add all collections from scene
        for collection in bpy.data.collections:
            item = props.export_collections.add()
            item.name = collection.name
            item.enabled = True
        
        self.report({'INFO'}, f"Refreshed export collections list: {len(props.export_collections)} collections found")
        return {'FINISHED'}


class T4A_OT_AddSelExportCollItem(Operator):
    """Add selected collection to export list"""
    bl_idname = "t4a.add_sel_export_coll_item"
    bl_label = "Add Selected Collection to Export"
    bl_description = "Add the active collection to the export list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.t4a_baker_props
        
        # Get active collection from outliner
        active_collection = context.collection
        if not active_collection:
            self.report({'WARNING'}, "No active collection selected")
            return {'CANCELLED'}
        
        # Check if already in list
        if any(item.name == active_collection.name for item in props.export_collections):
            self.report({'WARNING'}, f"Collection '{active_collection.name}' already in export list")
            return {'CANCELLED'}
        
        # Add to list
        item = props.export_collections.add()
        item.name = active_collection.name
        item.enabled = True
        
        self.report({'INFO'}, f"Added '{active_collection.name}' to export list")
        return {'FINISHED'}


class T4A_OT_DellExportCollItem(Operator):
    """Remove collection from export list"""
    bl_idname = "t4a.dell_export_coll_item"
    bl_label = "Remove Collection from Export"
    bl_description = "Remove the active collection from the export list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        props = scene.t4a_baker_props
        
        if not props.export_collections:
            self.report({'WARNING'}, "Export collections list is empty")
            return {'CANCELLED'}
        
        if props.active_export_collection_index < 0 or props.active_export_collection_index >= len(props.export_collections):
            self.report({'WARNING'}, "No valid collection selected")
            return {'CANCELLED'}
        
        # Get name before removing
        coll_name = props.export_collections[props.active_export_collection_index].name
        
        # Remove item
        props.export_collections.remove(props.active_export_collection_index)
        
        # Adjust active index
        if props.active_export_collection_index > 0:
            props.active_export_collection_index -= 1
        
        self.report({'INFO'}, f"Removed '{coll_name}' from export list")
        return {'FINISHED'}


# Registration
classes = (
    T4A_OT_RefreshExportCollectionList,
    T4A_OT_AddSelExportCollItem,
    T4A_OT_DellExportCollItem,
)


def register():
    pass


def unregister():
    pass
