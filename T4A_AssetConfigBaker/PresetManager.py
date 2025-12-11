"""
T4A Assets Configuration Baker - Preset Manager
System for saving and loading custom baking configurations
"""

import bpy
from bpy.types import Operator
import json
import os
from pathlib import Path


def get_presets_directory():
    """Get or create the presets directory in Blender's user config"""
    config_path = Path(bpy.utils.user_resource('CONFIG'))
    presets_dir = config_path / "t4a_baker_presets"
    presets_dir.mkdir(parents=True, exist_ok=True)
    return presets_dir


def get_preset_filepath(preset_name):
    """Get the full path for a preset file"""
    presets_dir = get_presets_directory()
    # Sanitize filename
    safe_name = "".join(c for c in preset_name if c.isalnum() or c in (' ', '-', '_')).strip()
    return presets_dir / f"{safe_name}.json"


def serialize_material_config(mat_item):
    """Convert a material configuration to JSON-serializable dict"""
    config = {
        'name': mat_item.name,
        'enabled': mat_item.enabled,
        'maps': []
    }
    
    for map_item in mat_item.maps:
        map_config = {
            'map_type': map_item.map_type,
            'file_suffix': map_item.file_suffix,
            'enabled': map_item.enabled,
            'output_format': map_item.output_format,
            'resolution': map_item.resolution,
        }
        config['maps'].append(map_config)
    
    return config


def deserialize_material_config(config, target_mat_item):
    """Apply a configuration dict to a material item"""
    target_mat_item.name = config.get('name', '')
    target_mat_item.enabled = config.get('enabled', True)
    
    # Clear existing maps
    target_mat_item.maps.clear()
    
    # Add maps from config
    for map_config in config.get('maps', []):
        new_map = target_mat_item.maps.add()
        new_map.map_type = map_config.get('map_type', 'ALBEDO')
        new_map.file_suffix = map_config.get('file_suffix', '')
        new_map.enabled = map_config.get('enabled', True)
        new_map.output_format = map_config.get('output_format', 'PNG')
        new_map.resolution = map_config.get('resolution', 1024)


class T4A_OT_SaveBakingPreset(Operator):
    """Save current baking configuration as a preset"""
    bl_idname = "t4a.save_baking_preset"
    bl_label = "Save Baking Preset"
    bl_description = "Save the current material baking configuration as a reusable preset"
    bl_options = {'REGISTER'}
    
    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name for this preset",
        default="My Preset"
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        if not self.preset_name.strip():
            self.report({'ERROR'}, "Preset name cannot be empty")
            return {'CANCELLED'}
        
        # Find the current object item in the hierarchy
        if not props.collections or props.active_collection_index >= len(props.collections):
            self.report({'WARNING'}, "No collection selected")
            return {'CANCELLED'}
        
        coll_item = props.collections[props.active_collection_index]
        
        if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        obj_item = coll_item.objects[coll_item.active_object_index]
        
        if not obj_item.materials:
            self.report({'WARNING'}, "No materials to save. Configure materials first.")
            return {'CANCELLED'}
        
        # Use PresetLoader to save the preset
        from . import PresetLoader
        
        try:
            # Extract materials data (first material as template)
            materials_data = []
            if obj_item.materials:
                materials_data.append(obj_item.materials[0])
            
            # Save using PresetLoader
            preset_id = PresetLoader.save_custom_preset(self.preset_name, materials_data)
            
            self.report({'INFO'}, f"Preset saved: {self.preset_name} ({preset_id})")
            
            # Update the selected preset to the newly created one
            props.preset_selection = preset_id
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save preset: {e}")
            return {'CANCELLED'}


class T4A_OT_LoadBakingPreset(Operator):
    """Load a saved baking configuration preset"""
    bl_idname = "t4a.load_baking_preset"
    bl_label = "Load Baking Preset"
    bl_description = "Load a saved baking configuration preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: bpy.props.StringProperty(
        name="Preset",
        description="Preset to load"
    )
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Use preset_name parameter, or extract from preset_selection
        if self.preset_name:
            preset_to_load = self.preset_name
        elif props.preset_selection.startswith('CUSTOM_'):
            preset_to_load = props.preset_selection[7:]  # Remove 'CUSTOM_' prefix
        else:
            self.report({'ERROR'}, "No custom preset selected")
            return {'CANCELLED'}
        
        if not preset_to_load:
            self.report({'ERROR'}, "No preset selected")
            return {'CANCELLED'}
        
        try:
            filepath = get_preset_filepath(preset_to_load)
            
            if not filepath.exists():
                self.report({'ERROR'}, f"Preset file not found: {filepath.name}")
                return {'CANCELLED'}
            
            # Load preset data
            with open(filepath, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)
            
            # Find the current object item in the hierarchy
            if not props.collections or props.active_collection_index >= len(props.collections):
                self.report({'WARNING'}, "No collection selected")
                return {'CANCELLED'}
            
            coll_item = props.collections[props.active_collection_index]
            
            if not coll_item.objects or coll_item.active_object_index >= len(coll_item.objects):
                self.report({'WARNING'}, "No object selected")
                return {'CANCELLED'}
            
            obj_item = coll_item.objects[coll_item.active_object_index]
            
            # Clear current materials for this object
            obj_item.materials.clear()
            
            # Apply preset to materials
            for mat_config in preset_data.get('materials', []):
                new_mat = obj_item.materials.add()
                deserialize_material_config(mat_config, new_mat)
            
            # Update the selected preset (with CUSTOM_ prefix)
            props.preset_selection = f"CUSTOM_{preset_to_load}"
            
            self.report({'INFO'}, f"Preset loaded: {preset_data.get('name', 'Unknown')}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {e}")
            return {'CANCELLED'}


class T4A_OT_DeleteBakingPreset(Operator):
    """Delete a saved baking preset"""
    bl_idname = "t4a.delete_baking_preset"
    bl_label = "Delete Baking Preset"
    bl_description = "Delete the selected baking preset"
    bl_options = {'REGISTER'}
    
    def invoke(self, context, event):
        props = context.scene.t4a_baker_props
        preset_id = props.preset_selection
        
        # Check if it's a custom preset (user-created, not built-in)
        from . import PresetLoader
        preset = PresetLoader.get_preset(preset_id)
        
        if not preset or not preset.get('is_custom', False):
            self.report({'ERROR'}, "Cannot delete built-in presets")
            return {'CANCELLED'}
        
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        preset_id = props.preset_selection
        
        from . import PresetLoader
        
        try:
            if PresetLoader.delete_preset(preset_id):
                self.report({'INFO'}, f"Preset deleted: {preset_id}")
                
                # Reset selection to default preset
                props.preset_selection = 'standard'
                
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to delete preset: {preset_id}")
                return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to delete preset: {e}")
            return {'CANCELLED'}


class T4A_OT_NewPresetMenu(Operator):
    """Show menu for creating a new preset"""
    bl_idname = "t4a.new_preset_menu"
    bl_label = "New Preset"
    bl_description = "Create a new baking preset"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # This will be called from the menu
        bpy.ops.t4a.save_baking_preset('INVOKE_DEFAULT')
        return {'FINISHED'}


class T4A_OT_RefreshPresetList(Operator):
    """Refresh the list of available presets"""
    bl_idname = "t4a.refresh_preset_list"
    bl_label = "Refresh Preset List"
    bl_description = "Refresh the list of available presets"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Force UI update
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


def get_available_presets():
    """Get list of available preset files"""
    presets_dir = get_presets_directory()
    presets = []
    
    if presets_dir.exists():
        for preset_file in presets_dir.glob("*.json"):
            try:
                with open(preset_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', preset_file.stem)
                    description = data.get('description', '')
                    presets.append((preset_file.stem, name, description))
            except:
                # Skip invalid preset files
                pass
    
    return presets


def get_preset_enum_items(self, context):
    """Dynamic enum items for custom presets dropdown"""
    items = []
    presets = get_available_presets()
    
    for preset_id, preset_name, preset_desc in presets:
        items.append((preset_id, preset_name, preset_desc))
    
    # Add default "New Preset" option
    if not items:
        items.append(('NONE', "No Presets", "No custom presets available"))
    
    return items


# Registration
classes = (
    T4A_OT_SaveBakingPreset,
    T4A_OT_LoadBakingPreset,
    T4A_OT_DeleteBakingPreset,
    T4A_OT_NewPresetMenu,
    T4A_OT_RefreshPresetList,
)


def register():
    pass


def unregister():
    pass
