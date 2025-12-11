"""
T4A Assets Configuration Baker - Properties
Scene properties for storing addon runtime variables and processing data
"""

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty
)





def convert_view_transform_to_blender(view_transform_enum):
    """Convert our enum identifier back to Blender's view transform identifier"""
    if view_transform_enum == 'FOLLOW_SCENE':
        return None  # Special case: use scene settings
    
    # Mapping dictionary for known conversions
    conversion_map = {
        'STANDARD': 'Standard',
        'ACES_1_3': 'ACES 1.3',
        'ACES_2_0': 'ACES 2.0',
        'KHRONOS_PBR_NEUTRAL': 'Khronos PBR Neutral',
        'FILMIC': 'Filmic',
        'FILMIC_LOG': 'Filmic Log',
        'RAW': 'Raw',
        'FALSE_COLOR': 'False Color',
        'AGX': 'AgX',
        'AGX_PUNCHY': 'AgX Punchy',
    }
    
    # Try direct mapping first
    if view_transform_enum in conversion_map:
        return conversion_map[view_transform_enum]
    
    # Otherwise, convert back: UPPERCASE_WITH_UNDERSCORES -> Title Case With Spaces
    return view_transform_enum.replace('_', ' ').title()




class T4A_MaterialBakeMapSettings(PropertyGroup):
    """Settings for individual bake map (diffuse, normal, etc.)"""
    map_type: EnumProperty(
        name="Map Type",
        items=[
            # PBR Core Maps
            ('ALBEDO', "Albedo (Base Color)", "Base color without lighting information"),
            ('NORMAL_GL', "Normal (OpenGL)", "Normal map in OpenGL format (+Y up)"),
            ('NORMAL_DX', "Normal (DirectX)", "Normal map in DirectX format (-Y up)"),
            ('METALLIC', "Metallic", "Metallic/Metal map for PBR"),
            ('ROUGHNESS', "Roughness", "Roughness map for PBR"),
            ('OCCLUSION', "Occlusion (AO)", "Ambient occlusion map"),
            
            # Additional PBR Maps
            ('ALPHA', "Alpha/Opacity", "Transparency/opacity map"),
            ('EMISSION', "Emission", "Emission/glow/emissive map"),
            ('HEIGHT', "Height", "Height/displacement map"),
            ('GLOSSINESS', "Glossiness", "Glossiness map (inverse of roughness)"),
            ('SPECULAR', "Specular", "Specular reflectance map"),
            
            # Legacy/Special
            ('DIFFUSE', "Diffuse (Legacy)", "Legacy diffuse baking with lighting"),
            ('COMBINED', "Combined", "Combined render output"),
        ],
        default='ALBEDO'
    )
    
    # Suffix utilisé pour le nom de fichier (ex: _albedo, _normal_gl)
    file_suffix: StringProperty(
        name="File Suffix",
        description="Suffix for the exported texture file",
        default=""
    )
    enabled: BoolProperty(
        name="Enable",
        description="Enable this map for baking",
        default=True
    )
    output_format: EnumProperty(
        name="Format",
        items=[
            ('PNG', "PNG", "PNG format"),
            ('JPEG', "JPEG", "JPEG format"),
            ('TIFF', "TIFF", "TIFF format"),
            ('OPEN_EXR', "OpenEXR", "OpenEXR format"),
        ],
        default='PNG'
    )
    
    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth for the image",
        items=[
            ('8', "8-bit", "8 bits per channel"),
            ('16', "16-bit", "16 bits per channel"),
            ('32', "32-bit", "32 bits per channel (float)"),
        ],
        default='8'
    )
    
    view_transform: EnumProperty(
        name="View Transform",
        description="Color management view transform",
        items= [
        ('FOLLOW_SCENE', "Follow Scene", "Use scene color management settings"),
        ('STANDARD', "Standard", "Standard sRGB display"),
        ('ACES_1_3', "ACES 1.3", "ACES 1.3 color management"),
        ('ACES_2_0', "ACES 2.0", "ACES 2.0 color management"),
        ('KHRONOS_PBR_NEUTRAL', "Khronos PBR Neutral", "Khronos PBR Neutral color space"),
        ('FILMIC', "Filmic", "Filmic view transform"),
        ('FILMIC_LOG', "Filmic Log", "Filmic Log encoding"),
        ('RAW', "Raw", "Raw (no color management)"),
        ('FALSE_COLOR', "False Color", "False color heat map"),
        ('AGX', "AgX", "AgX view transform"),
        ('AGX_PUNCHY', "AgX Punchy", "AgX Punchy view transform"),
    ],
        default=0
    )
    
    resolution: IntProperty(
        name="Resolution",
        description="Resolution for this map",
        default=1024,
        min=128,
        max=8192
    )


class T4A_MaterialBakeItem(PropertyGroup):
    """Represents a material with its bake maps configuration"""
    name: StringProperty(
        name="Material Name",
        description="Name of the material"
    )
    enabled: BoolProperty(
        name="Enable",
        description="Enable this material for baking",
        default=True
    )
    maps: CollectionProperty(
        type=T4A_MaterialBakeMapSettings,
        name="Bake Maps"
    )
    active_map_index: IntProperty(
        name="Active Map Index",
        description="Index of the active map in the list",
        default=0
    )


class T4A_ObjectBakeItem(PropertyGroup):
    """Represents an object to bake"""
    name: StringProperty(
        name="Object Name",
        description="Name of the object"
    )
    enabled: BoolProperty(
        name="Enable",
        description="Enable this object for baking",
        default=True
    )
    materials: CollectionProperty(
        type=T4A_MaterialBakeItem,
        name="Materials",
        description="List of materials for this object"
    )
    active_material_index: IntProperty(
        name="Active Material Index",
        description="Index of the active material in the list",
        default=0
    )


class T4A_CollectionBakeItem(PropertyGroup):
    """Represents a collection to bake"""
    name: StringProperty(
        name="Collection Name",
        description="Name of the collection"
    )
    enabled: BoolProperty(
        name="Enable",
        description="Enable this collection for baking",
        default=True
    )
    objects: CollectionProperty(
        type=T4A_ObjectBakeItem,
        name="Objects",
        description="List of objects in this collection"
    )
    active_object_index: IntProperty(
        name="Active Object Index",
        description="Index of the active object in the list",
        default=0,
        update=lambda self, context: self.on_active_object_changed(context)
    )
    
    def on_active_object_changed(self, context):
        """Callback when active object index changes - select and make active in 3D view"""
        if self.objects and 0 <= self.active_object_index < len(self.objects):
            obj_item = self.objects[self.active_object_index]
            obj = bpy.data.objects.get(obj_item.name)
            
            if obj:
                # Deselect all objects
                bpy.ops.object.select_all(action='DESELECT')
                
                # Select and make active
                obj.select_set(True)
                context.view_layer.objects.active = obj
                
                # Refresh material list for this object (stored in obj_item now)
                obj_item.materials.clear()
                
                # Get preset configuration
                props = context.scene.t4a_baker_props
                preset_id = props.preset_selection if props.preset_selection and props.preset_selection != 'NONE' else 'standard'
                
                # Import here to avoid circular dependency
                from . import PresetLoader
                
                # Add all materials from the newly active object
                if hasattr(obj.data, 'materials'):
                    for mat in obj.data.materials:
                        if mat:
                            mat_item = obj_item.materials.add()
                            mat_item.name = mat.name
                            mat_item.enabled = True
                            
                            # Apply preset from JSON
                            PresetLoader.apply_preset_to_material(preset_id, mat_item)


class T4A_BakerProperties(PropertyGroup):
    """Main property group for T4A Baker addon"""
    
    # ===== 3D BAKING PROPERTIES =====
    
    bake_resolution: EnumProperty(
        name="Bake Resolution",
        description="Resolution for baked textures",
        items=[
            ('512', "512", "512x512 pixels"),
            ('1024', "1024", "1024x1024 pixels"),
            ('2048', "2048", "2048x2048 pixels (recommended)"),
            ('4096', "4096", "4096x4096 pixels"),
            ('8192', "8192", "8192x8192 pixels"),
        ],
        default='2048'
    )
    
    bake_samples: IntProperty(
        name="Bake Samples",
        description="Number of samples for baking",
        default=128,
        min=1,
        max=4096
    )
    
    use_adaptive_sampling: BoolProperty(
        name="Adaptive Sampling",
        description="Use adaptive sampling for baking",
        default=True
    )
    
    bake_margin: IntProperty(
        name="Bake Margin",
        description="Margin in pixels for baked textures",
        default=16,
        min=0,
        max=64
    )
    
    # ===== MATERIAL BAKING PROPERTIES =====
    
    mat_bake_type: EnumProperty(
        name="Bake Type",
        description="Type of baking to perform",
        items=[
            ('COMBINED', "Combined", "Bake combined diffuse and specular"),
            ('DIFFUSE', "Diffuse", "Bake diffuse color only"),
            ('GLOSSY', "Glossy", "Bake glossy/specular"),
            ('NORMAL', "Normal", "Bake normal map"),
            ('ROUGHNESS', "Roughness", "Bake roughness map"),
            ('EMIT', "Emission", "Bake emission"),
            ('AO', "Ambient Occlusion", "Bake ambient occlusion"),
        ],
        default='COMBINED'
    )
    
    mat_output_format: EnumProperty(
        name="Output Format",
        description="Image format for baked textures",
        items=[
            ('PNG', "PNG", "PNG format (lossless)"),
            ('JPEG', "JPEG", "JPEG format (lossy)"),
            ('TIFF', "TIFF", "TIFF format (lossless, large file)"),
            ('OPEN_EXR', "OpenEXR", "OpenEXR format (HDR)"),
        ],
        default='PNG'
    )
    
    mat_use_selected_to_active: BoolProperty(
        name="Selected to Active",
        description="Bake from selected objects to the active object",
        default=False
    )
    
    mat_use_clear: BoolProperty(
        name="Clear Image",
        description="Clear image before baking",
        default=True
    )
    
    # ===== PROCESSING STATE =====
    
    is_baking: BoolProperty(
        name="Is Baking",
        description="Indicates if a baking operation is in progress",
        default=False
    )
    
    bake_progress: FloatProperty(
        name="Bake Progress",
        description="Current baking progress (0 to 100%)",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    )
    
    last_bake_time: FloatProperty(
        name="Last Bake Time",
        description="Time taken for the last baking operation (seconds)",
        default=0.0,
        min=0.0
    )
    
    # ===== EXPORT SETTINGS =====
    
    export_glb: BoolProperty(
        name="Export GLB",
        description="Export the baked asset as GLB format",
        default=True
    )
    
    export_path: StringProperty(
        name="Export Path",
        description="Path where the asset will be exported",
        default="",
        subtype='DIR_PATH'
    )
    
    asset_name: StringProperty(
        name="Asset Name",
        description="Name of the asset for export",
        default="Asset"
    )
    
    # ===== ASSET HIERARCHY =====
    
    analyze_hierarchy: BoolProperty(
        name="Analyze Hierarchy",
        description="Analyze and preserve object hierarchy during export",
        default=True
    )
    
    preserve_naming: BoolProperty(
        name="Preserve Naming",
        description="Preserve original object and material names",
        default=True
    )
    
    # ===== WEB CONFIGURATOR SETTINGS =====
    
    generate_metadata: BoolProperty(
        name="Generate Metadata",
        description="Generate metadata file for web configurator",
        default=True
    )
    
    optimize_for_web: BoolProperty(
        name="Optimize for Web",
        description="Apply web optimization settings (reduced poly count, texture compression)",
        default=True
    )
    
    target_polycount: IntProperty(
        name="Target Polycount",
        description="Target polygon count for web optimization",
        default=50000,
        min=1000,
        max=500000
    )
    
    # ===== 3D BAKING UI DATA =====
    
    collections: CollectionProperty(
        type=T4A_CollectionBakeItem,
        name="Collections",
        description="List of collections to bake"
    )
    
    active_collection_index: IntProperty(
        name="Active Collection Index",
        description="Index of the active collection in the list",
        default=0
    )
    
    # ===== MATERIAL BAKING UI DATA =====
    
    preset_selection: EnumProperty(
        name="Preset",
        description="Baking preset (PBR built-in or custom)",
        items=lambda self, context: self.get_all_preset_items(context),
        update=lambda self, context: self.on_preset_changed(context)
    )
    
    def get_all_preset_items(self, context):
        """Dynamic enum items from JSON presets"""
        from . import PresetLoader
        
        # Get all presets from JSON files
        items = PresetLoader.get_all_preset_items()
        
        return items
    
    def on_preset_changed(self, context):
        """Auto-apply preset when selection changes"""
        # All presets are now loaded from JSON files
        # The preset_selection directly contains the preset ID
        if self.preset_selection and self.preset_selection != 'NONE':
            bpy.ops.t4a.apply_preset_from_json(preset_id=self.preset_selection)


# Registration
classes = (
    T4A_MaterialBakeMapSettings,
    T4A_MaterialBakeItem,
    T4A_ObjectBakeItem,
    T4A_CollectionBakeItem,
    T4A_BakerProperties,
)


def register():
    # Les classes sont déjà enregistrées par auto_load avant l'appel à register()
    # On attache simplement le PointerProperty à la Scene
    bpy.types.Scene.t4a_baker_props = bpy.props.PointerProperty(type=T4A_BakerProperties)

def unregister():
    # Unregister properties from scene
    if hasattr(bpy.types.Scene, 't4a_baker_props'):
        del bpy.types.Scene.t4a_baker_props
