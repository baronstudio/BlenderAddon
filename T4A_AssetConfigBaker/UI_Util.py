"""
T4A Assets Configuration Baker - Material UI Operators
Operators for managing material list and bake maps in the UI
"""

import bpy
from bpy.types import Operator


# PBR Preset configurations
PBR_PRESETS = {
    'STANDARD': [
        ('ALBEDO', '_albedo'),
        ('NORMAL_GL', '_normal_gl'),
        ('METALLIC', '_metallic'),
        ('ROUGHNESS', '_roughness'),
        ('OCCLUSION', '_occlusion'),
    ],
    'GAME': [
        ('ALBEDO', '_albedo'),
        ('NORMAL_GL', '_normal'),
        ('OCCLUSION', '_occlusion'),
        ('ROUGHNESS', '_roughness'),
        ('METALLIC', '_metallic'),
    ],
    'FULL': [
        ('ALBEDO', '_albedo'),
        ('NORMAL_GL', '_normal_gl'),
        ('METALLIC', '_metallic'),
        ('ROUGHNESS', '_roughness'),
        ('OCCLUSION', '_occlusion'),
        ('ALPHA', '_alpha'),
        ('EMISSION', '_emission'),
        ('HEIGHT', '_height'),
    ],
    'GLTF': [
        ('ALBEDO', '_basecolor'),
        ('NORMAL_GL', '_normal'),
        ('OCCLUSION', '_occlusion'),
        ('ROUGHNESS', '_roughness'),
        ('METALLIC', '_metallic'),
    ],
}


class T4A_OT_RefreshMaterialList(Operator):
    """Refresh the material list from active object"""
    bl_idname = "t4a.refresh_material_list"
    bl_label = "Refresh Material List"
    bl_description = "Refresh the list of materials from the active object"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        obj = context.active_object
        
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "No active mesh object")
            return {'CANCELLED'}
        
        # Clear existing list
        props.materials.clear()
        
        # Get preset configuration (unified property)
        preset = props.preset_selection if not props.preset_selection.startswith('CUSTOM_') else 'STANDARD'
        preset_maps = PBR_PRESETS.get(preset, PBR_PRESETS['STANDARD'])
        
        # Add all materials from active object
        if hasattr(obj.data, 'materials'):
            for mat in obj.data.materials:
                if mat:
                    mat_item = props.materials.add()
                    mat_item.name = mat.name
                    
                    # Add maps based on preset
                    for map_type, suffix in preset_maps:
                        map_item = mat_item.maps.add()
                        map_item.map_type = map_type
                        map_item.file_suffix = suffix
                        map_item.enabled = True
                        map_item.output_format = 'PNG'
                        map_item.resolution = 1024
        
        self.report({'INFO'}, f"Loaded {len(props.materials)} material(s) with {preset} preset")
        return {'FINISHED'}


class T4A_OT_AddBakeMap(Operator):
    """Add a new bake map to the selected material"""
    bl_idname = "t4a.add_bake_map"
    bl_label = "Add Bake Map"
    bl_description = "Add a new bake map configuration"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.materials or props.active_material_index >= len(props.materials):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        mat_item = props.materials[props.active_material_index]
        
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
        
        if not props.materials or props.active_material_index >= len(props.materials):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        mat_item = props.materials[props.active_material_index]
        
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


class T4A_OT_ApplyPBRPreset(Operator):
    """Apply PBR preset to selected material"""
    bl_idname = "t4a.apply_pbr_preset"
    bl_label = "Apply PBR Preset"
    bl_description = "Apply the selected PBR preset to the active material"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not props.materials or props.active_material_index >= len(props.materials):
            self.report({'WARNING'}, "No material selected")
            return {'CANCELLED'}
        
        mat_item = props.materials[props.active_material_index]
        
        # Get preset from unified preset_selection property
        preset = props.preset_selection
        
        # Skip custom presets (they are loaded via file)
        if preset.startswith('CUSTOM_'):
            self.report({'INFO'}, "Custom preset already loaded from file")
            return {'FINISHED'}
        
        if preset == 'CUSTOM':
            self.report({'INFO'}, "Custom preset - manually configure maps")
            return {'FINISHED'}
        
        preset_maps = PBR_PRESETS.get(preset, PBR_PRESETS['STANDARD'])
        
        # Clear existing maps
        mat_item.maps.clear()
        
        # Add preset maps
        for map_type, suffix in preset_maps:
            map_item = mat_item.maps.add()
            map_item.map_type = map_type
            map_item.file_suffix = suffix
            map_item.enabled = True
            map_item.output_format = 'PNG'
            map_item.resolution = 1024
        
        self.report({'INFO'}, f"Applied {preset} preset to {mat_item.name}")
        return {'FINISHED'}


# Registration
classes = (
    T4A_OT_RefreshMaterialList,
    T4A_OT_ApplyPBRPreset,
    T4A_OT_AddBakeMap,
    T4A_OT_RemoveBakeMap,
)


def register():
    pass


def unregister():
    pass
