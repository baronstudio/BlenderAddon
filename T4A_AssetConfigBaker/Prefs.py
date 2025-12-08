"""
T4A Assets Configuration Baker - Addon Preferences
User preferences and settings for the addon
"""

import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, IntProperty, EnumProperty


class T4A_AddonPreferences(AddonPreferences):
    """Preferences for T4A Assets Configuration Baker"""
    bl_idname = __package__
    
    # Output paths
    default_export_path: StringProperty(
        name="Default Export Path",
        description="Default path for exporting baked assets",
        default="//exports/",
        subtype='DIR_PATH'
    )
    
    texture_output_path: StringProperty(
        name="Texture Output Path",
        description="Default path for baked textures",
        default="//textures/",
        subtype='DIR_PATH'
    )
    
    # Performance settings
    use_gpu_baking: BoolProperty(
        name="Use GPU for Baking",
        description="Use GPU acceleration when available for baking operations",
        default=True
    )
    
    max_bake_resolution: IntProperty(
        name="Max Bake Resolution",
        description="Maximum resolution for texture baking",
        default=4096,
        min=512,
        max=8192
    )
    
    # Workflow preferences
    auto_save_before_bake: BoolProperty(
        name="Auto-save Before Baking",
        description="Automatically save the blend file before starting baking process",
        default=True
    )
    
    show_debug_info: BoolProperty(
        name="Show Debug Info",
        description="Display debug information in the console",
        default=False
    )
    
    # Naming conventions
    texture_prefix: StringProperty(
        name="Texture Prefix",
        description="Prefix for baked texture files",
        default="T4A_"
    )
    
    # Export settings
    glb_compression: EnumProperty(
        name="GLB Compression",
        description="Compression level for GLB export",
        items=[
            ('NONE', "None", "No compression"),
            ('LOW', "Low", "Low compression"),
            ('MEDIUM', "Medium", "Medium compression (recommended)"),
            ('HIGH', "High", "High compression"),
        ],
        default='MEDIUM'
    )
    
    include_custom_props: BoolProperty(
        name="Include Custom Properties",
        description="Include custom properties in exported assets",
        default=True
    )
    
    def draw(self, context):
        layout = self.layout
        
        # Paths section
        box = layout.box()
        box.label(text="Export Paths:", icon='FILE_FOLDER')
        box.prop(self, "default_export_path")
        box.prop(self, "texture_output_path")
        
        layout.separator()
        
        # Performance section
        box = layout.box()
        box.label(text="Performance:", icon='SETTINGS')
        box.prop(self, "use_gpu_baking")
        box.prop(self, "max_bake_resolution")
        
        layout.separator()
        
        # Workflow section
        box = layout.box()
        box.label(text="Workflow:", icon='PREFERENCES')
        box.prop(self, "auto_save_before_bake")
        box.prop(self, "show_debug_info")
        box.prop(self, "texture_prefix")
        
        layout.separator()
        
        # Export settings section
        box = layout.box()
        box.label(text="Export Settings:", icon='EXPORT')
        box.prop(self, "glb_compression")
        box.prop(self, "include_custom_props")


# Registration
classes = (
    T4A_AddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
