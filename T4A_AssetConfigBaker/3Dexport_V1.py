"""
T4A Assets Configuration Baker - 3D Export Module V1
GLB export operators for collections
"""

import bpy
from bpy.types import Operator
import os


class T4A_OT_ExportCollectionGLB(Operator):
    """Export a single collection as GLB file"""
    bl_idname = "t4a.export_collection_glb"
    bl_label = "Export Collection as GLB"
    bl_description = "Export the specified collection as a GLB file"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Property to pass the collection name
    collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="Name of the collection to export",
        default=""
    )
    
    def execute(self, context):
        """Execute GLB export for a single collection"""
        scene = context.scene
        props = scene.t4a_baker_props
        prefs = context.preferences.addons[__package__].preferences
        
        # Get the collection
        collection = bpy.data.collections.get(self.collection_name)
        if not collection:
            self.report({'WARNING'}, f"Collection '{self.collection_name}' not found")
            return {'CANCELLED'}
        
        # Find collection item in export list to get settings
        coll_item = None
        for item in props.export_collections:
            if item.name == self.collection_name:
                coll_item = item
                break
        
        if not coll_item:
            self.report({'WARNING'}, f"Collection '{self.collection_name}' not in export list")
            return {'CANCELLED'}
        
        # Get export path
        export_path = prefs.default_export_path
        if not export_path or not os.path.exists(export_path):
            self.report({'WARNING'}, "Export path not configured or invalid. Check preferences.")
            return {'CANCELLED'}
        
        # Build output filepath
        output_file = os.path.join(export_path, f"{collection.name}.glb")
        
        self.report({'INFO'}, f"Preparing to export: {collection.name}")
        
        # Implement actual GLB export
        self._export_collection_to_glb(context, collection, coll_item, output_file)
        
        self.report({'INFO'}, f"Exported: {output_file}")
        return {'FINISHED'}
    
    def _export_collection_to_glb(self, context, collection, coll_item, filepath):
        """
        Export collection to GLB file
        
        Args:
            context: Blender context
            collection: Collection to export
            coll_item: T4A_CollectionExportItem with export settings
            filepath: Output GLB filepath
        """
        print(f"[T4A Export] Exporting collection '{collection.name}' to '{filepath}'")
        
        # Save current selection
        original_selection = context.selected_objects.copy()
        original_active = context.view_layer.objects.active
        
        try:
            # Select all objects in collection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in collection.all_objects:
                obj.select_set(True)
            
            if not context.selected_objects:
                print(f"[T4A Export] Warning: No objects in collection '{collection.name}'")
                return
            
            # Determine file format
            if coll_item.export_format == 'GLB':
                export_format = 'GLB'
            elif coll_item.export_format == 'GLTF_SEPARATE':
                export_format = 'GLTF_SEPARATE'
            else:  # 'GLTF_EMBEDDED'
                export_format = 'GLTF_EMBEDDED'
            
            # Export using glTF exporter
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format=export_format,
                use_selection=True,
                export_apply=coll_item.export_apply_modifiers,
                export_materials=coll_item.export_materials,
                export_colors=coll_item.export_colors,
                export_cameras=coll_item.export_cameras,
                export_lights=coll_item.export_lights,
                export_yup=coll_item.export_yup
            )
            
        finally:
            # Restore original selection
            bpy.ops.object.select_all(action='DESELECT')
            for obj in original_selection:
                if obj:
                    obj.select_set(True)
            context.view_layer.objects.active = original_active


class T4A_OT_ExportAllCollections(Operator):
    """Export all enabled collections as GLB files"""
    bl_idname = "t4a.export_all_collections"
    bl_label = "Export All Collections"
    bl_description = "Export all enabled collections from the export list as GLB files"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Execute batch GLB export for all collections"""
        scene = context.scene
        props = scene.t4a_baker_props
        
        # Check if there are collections to export
        if not props.export_collections:
            self.report({'WARNING'}, "No collections configured for export")
            return {'CANCELLED'}
        
        # Count enabled collections
        enabled_collections = [coll for coll in props.export_collections if coll.enabled]
        if not enabled_collections:
            self.report({'WARNING'}, "No enabled collections to export")
            return {'CANCELLED'}
        
        self.report({'INFO'}, f"Starting export of {len(enabled_collections)} collection(s)")
        
        # Export each enabled collection
        exported_count = 0
        failed_count = 0
        
        for coll_item in enabled_collections:
            collection = bpy.data.collections.get(coll_item.name)
            if not collection:
                self.report({'WARNING'}, f"Collection '{coll_item.name}' not found, skipping")
                failed_count += 1
                continue
            
            # Call single export operator
            result = bpy.ops.t4a.export_collection_glb(collection_name=coll_item.name)
            
            if 'FINISHED' in result:
                exported_count += 1
            else:
                failed_count += 1
        
        # Report summary
        self.report({'INFO'}, f"Export complete: {exported_count} successful, {failed_count} failed")
        return {'FINISHED'}


# Registration
classes = (
    T4A_OT_ExportCollectionGLB,
    T4A_OT_ExportAllCollections,
)


def register():
    pass


def unregister():
    pass
