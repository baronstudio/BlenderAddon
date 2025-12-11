"""
T4A Assets Configuration Baker - Collection Management Operators
Operators for managing collection list for 3D baking
"""

import bpy
from bpy.types import Operator


class T4A_OT_RefreshCollectionList(Operator):
    """Refresh the collection list from scene"""
    bl_idname = "t4a.refresh_collection_list"
    bl_label = "Refresh Collection List"
    bl_description = "Refresh the list of collections from the scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Clear existing list
        props.collections.clear()
        
        # Add all collections from scene
        for collection in bpy.data.collections:
            # Only add collections that have objects
            if collection.objects:
                coll_item = props.collections.add()
                coll_item.name = collection.name
                coll_item.enabled = True
        
        self.report({'INFO'}, f"Loaded {len(props.collections)} collection(s)")
        return {'FINISHED'}


class T4A_OT_AddSelectedCollection(Operator):
    """Add selected collection(s) from outliner to the bake list"""
    bl_idname = "t4a.add_sel_coll_item"
    bl_label = "Add Selected Collection"
    bl_description = "Add selected collection(s) from outliner to the bake list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Get selected collections (from view layer)
        selected_collections = []
        
        # Try to get active collection
        if context.view_layer.active_layer_collection:
            active_coll = context.view_layer.active_layer_collection.collection
            if active_coll:
                selected_collections.append(active_coll)
        
        if not selected_collections:
            self.report({'WARNING'}, "No collection selected in outliner")
            return {'CANCELLED'}
        
        added_count = 0
        for collection in selected_collections:
            # Check if collection already exists in list
            if collection.name not in [item.name for item in props.collections]:
                coll_item = props.collections.add()
                coll_item.name = collection.name
                coll_item.enabled = True
                added_count += 1
            else:
                self.report({'INFO'}, f"Collection '{collection.name}' already in list")
        
        if added_count > 0:
            self.report({'INFO'}, f"Added {added_count} collection(s)")
        
        return {'FINISHED'}


class T4A_OT_RemoveCollectionItem(Operator):
    """Remove the selected collection from the bake list"""
    bl_idname = "t4a.dell_coll_item"
    bl_label = "Remove Collection"
    bl_description = "Remove the selected collection from the bake list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_name = props.collections[props.active_collection_index].name
        props.collections.remove(props.active_collection_index)
        
        # Adjust index if needed
        if props.active_collection_index >= len(props.collections) and len(props.collections) > 0:
            props.active_collection_index = len(props.collections) - 1
        
        self.report({'INFO'}, f"Removed collection: {coll_name}")
        return {'FINISHED'}


class T4A_OT_RefreshObjectList(Operator):
    """Refresh the object list from selected collection"""
    bl_idname = "t4a.refresh_object_list"
    bl_label = "Refresh Object List"
    bl_description = "Refresh the list of objects from the selected collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        collection = bpy.data.collections.get(coll_item.name)
        
        if not collection:
            self.report({'WARNING'}, f"Collection '{coll_item.name}' not found")
            return {'CANCELLED'}
        
        # Clear existing list
        coll_item.objects.clear()
        
        # Add all MESH objects from collection
        for obj in collection.objects:
            if obj.type == 'MESH':
                obj_item = coll_item.objects.add()
                obj_item.name = obj.name
                obj_item.enabled = True
        
        self.report({'INFO'}, f"Loaded {len(coll_item.objects)} object(s) from {coll_item.name}")
        return {'FINISHED'}


class T4A_OT_AddSelectedObject(Operator):
    """Add selected object(s) to the object list"""
    bl_idname = "t4a.add_sel_object_item"
    bl_label = "Add Selected Object"
    bl_description = "Add selected object(s) to the object list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        # Get selected objects
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh object selected")
            return {'CANCELLED'}
        
        added_count = 0
        for obj in selected_objects:
            # Check if object already exists in list
            if obj.name not in [item.name for item in coll_item.objects]:
                obj_item = coll_item.objects.add()
                obj_item.name = obj.name
                obj_item.enabled = True
                added_count += 1
            else:
                self.report({'INFO'}, f"Object '{obj.name}' already in list")
        
        if added_count > 0:
            self.report({'INFO'}, f"Added {added_count} object(s)")
        
        return {'FINISHED'}


class T4A_OT_RemoveObjectItem(Operator):
    """Remove the selected object from the list"""
    bl_idname = "t4a.dell_object_item"
    bl_label = "Remove Object"
    bl_description = "Remove the selected object from the list"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj_name = coll_item.objects[coll_item.active_object_index].name
        coll_item.objects.remove(coll_item.active_object_index)
        
        # Adjust index if needed
        if coll_item.active_object_index >= len(coll_item.objects) and len(coll_item.objects) > 0:
            coll_item.active_object_index = len(coll_item.objects) - 1
        
        self.report({'INFO'}, f"Removed object: {obj_name}")
        return {'FINISHED'}


# Registration
classes = (
    T4A_OT_RefreshCollectionList,
    T4A_OT_AddSelectedCollection,
    T4A_OT_RemoveCollectionItem,
    T4A_OT_RefreshObjectList,
    T4A_OT_AddSelectedObject,
    T4A_OT_RemoveObjectItem,
)


def register():
    pass


def unregister():
    pass
