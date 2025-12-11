"""
T4A Assets Configuration Baker - Material UI Operators
Operators for managing material list and bake maps in the UI
"""

import bpy
from bpy.types import Operator
from . import PresetLoader


class T4A_OT_RefreshMaterialList(Operator):
    """Refresh the material list from active object in the hierarchy"""
    bl_idname = "t4a.refresh_material_list"
    bl_label = "Refresh Material List"
    bl_description = "Refresh the list of materials from the selected object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Find the current object item in the hierarchy
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj_item = coll_item.objects[coll_item.active_object_index]
        obj = bpy.data.objects.get(obj_item.name)
        
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Object not found or not a mesh")
            return {'CANCELLED'}
        
        # Clear existing list for this object
        obj_item.materials.clear()
        
        # Add all materials from active object
        if hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat:
                    mat_item = obj_item.materials.add()
                    mat_item.name = mat.name
                    mat_item.enabled = True
                    
                    # Apply current preset to this material
                    if props.preset_selection and props.preset_selection != 'NONE':
                        PresetLoader.apply_preset_to_material(props.preset_selection, mat_item)
        
        self.report({'INFO'}, f"Loaded {len(obj_item.materials)} material(s) with preset")
        return {'FINISHED'}


class T4A_OT_AddBakeMap(Operator):
    """Add a new bake map to the selected material"""
    bl_idname = "t4a.add_bake_map"
    bl_label = "Add Bake Map"
    bl_description = "Add a new bake map configuration"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Find the current object item in the hierarchy
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj_item = coll_item.objects[coll_item.active_object_index]
        
        if not obj_item.materials or obj_item.active_material_index >= len(obj_item.materials):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        mat_item = obj_item.materials[obj_item.active_material_index]
        
        # Add new map
        map_item = mat_item.maps.add()
        map_item.map_type = 'DIFFUSE'
        map_item.enabled = True
        map_item.output_format = 'PNG'
        map_item.resolution = 1024
        
        # Set as active
        mat_item.active_map_index = len(mat_item.maps) - 1
        
        self.report({'INFO'}, f"Added map to {mat_item.name}")
        return {'FINISHED'}


class T4A_OT_RemoveBakeMap(Operator):
    """Remove the selected bake map"""
    bl_idname = "t4a.remove_bake_map"
    bl_label = "Remove Bake Map"
    bl_description = "Remove the selected bake map"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Find the current object item in the hierarchy
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj_item = coll_item.objects[coll_item.active_object_index]
        
        if not obj_item.materials or obj_item.active_material_index >= len(obj_item.materials):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        mat_item = obj_item.materials[obj_item.active_material_index]
        
        if not mat_item.maps or mat_item.active_map_index >= len(mat_item.maps):
            self.report({'WARNING'}, "No map selected")
            return {'CANCELLED'}
        
        # Remove map
        mat_item.maps.remove(mat_item.active_map_index)
        
        # Adjust active index
        if mat_item.active_map_index > 0:
            mat_item.active_map_index -= 1
        
        self.report({'INFO'}, f"Removed map from {mat_item.name}")
        return {'FINISHED'}


class T4A_OT_ApplyPresetFromJSON(Operator):
    """Apply preset from JSON file to all materials"""
    bl_idname = "t4a.apply_preset_from_json"
    bl_label = "Apply Preset from JSON"
    bl_description = "Apply the selected preset configuration to materials"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_id: bpy.props.StringProperty(
        name="Preset ID",
        description="ID of the preset to apply",
        default=""
    )
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Use parameter or get from props
        preset_id = self.preset_id if self.preset_id else props.preset_selection
        
        if not preset_id or preset_id == 'NONE':
            self.report({'WARNING'}, "No preset selected")
            return {'CANCELLED'}
        
        # Find the current object item in the hierarchy
        if not props.collections or props.active_collection_index >= len(props.collections):
            # No hierarchy, do nothing silently
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            return {'CANCELLED'}
        
        obj_item = coll_item.objects[coll_item.active_object_index]
        
        # Apply preset to all materials of this object
        applied_count = 0
        for mat_item in obj_item.materials:
            if PresetLoader.apply_preset_to_material(preset_id, mat_item):
                applied_count += 1
        
        if applied_count > 0:
            preset = PresetLoader.get_preset(preset_id)
            preset_name = preset['name'] if preset else preset_id
            self.report({'INFO'}, f"Applied '{preset_name}' to {applied_count} material(s)")
        else:
            self.report({'WARNING'}, f"Preset '{preset_id}' not found")
        
        return {'FINISHED'}


class T4A_OT_ApplyPBRPreset(Operator):
    """Legacy operator - redirects to new JSON preset system"""
    bl_idname = "t4a.apply_pbr_preset"
    bl_label = "Apply PBR Preset"
    bl_description = "Apply the selected PBR preset to the active material"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Redirect to new system
        return bpy.ops.t4a.apply_preset_from_json()


# Registration
classes = (
    T4A_OT_RefreshMaterialList,
    T4A_OT_ApplyPresetFromJSON,
    T4A_OT_ApplyPBRPreset,
    T4A_OT_AddBakeMap,
    T4A_OT_RemoveBakeMap,
)


def register():
    pass


def unregister():
    pass
