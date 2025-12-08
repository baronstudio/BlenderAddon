"""
T4A Assets Configuration Baker - UI Panels
All UI panels for the 3D View (N-Panel)
"""

import bpy
import tomllib
from pathlib import Path


# Utility function to read manifest data
def get_manifest_data():
    """Read and parse the blender_manifest.toml file"""
    manifest_path = Path(__file__).parent / "blender_manifest.toml"
    try:
        with open(manifest_path, 'rb') as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return {}


# Main Panel (Parent)
class T4A_PT_MainPanel(bpy.types.Panel):
    """Main panel for T4A Assets Configuration Baker"""
    bl_label = "T4A Asset Config Baker"
    bl_idname = "T4A_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A Baker'
    bl_order = 0  # First panel
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.t4a_baker_props
        
        layout.label(text="Asset Configuration Tools", icon='SCENE_DATA')
        
        # Main content section
        box = layout.box()
        box.label(text="3D Baking:", icon='SHADING_RENDERED')
        col = box.column(align=True)
        
        # Placeholder for Baker_V1 operators
        col.operator("t4a.baker_example", text="Run 3D Baker", icon='RENDER_STILL')
        
        # Material Baking section
        box = layout.box()
        box.label(text="Material Baking:", icon='MATERIAL')
        col = box.column(align=True)
        
        # Placeholder for Baker_Mat_V1 operators
        col.operator("t4a.baker_mat_example", text="Bake Materials", icon='NODE_MATERIAL')
        
        # Export section
        box = layout.box()
        box.label(text="Export:", icon='EXPORT')
        col = box.column(align=True)
        col.label(text="GLB Export (Coming soon)")


# Sub-panel: 3D Baking Options
class T4A_PT_BakerPanel(bpy.types.Panel):
    """3D Baking configuration panel"""
    bl_label = "3D Baking Options"
    bl_idname = "T4A_PT_baker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A Baker'
    bl_parent_id = "T4A_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1  # Second panel
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.t4a_baker_props
        
        box = layout.box()
        col = box.column(align=True)
        
        # Properties will be defined in Properties.py
        col.label(text="Baking Settings:", icon='SETTINGS')
        col.prop(props, "bake_resolution")
        col.prop(props, "bake_samples")
        col.separator()
        col.prop(props, "use_adaptive_sampling")


# Sub-panel: Material Baking Options
class T4A_PT_MaterialBakerPanel(bpy.types.Panel):
    """Material baking configuration panel"""
    bl_label = "Material Baking Options"
    bl_idname = "T4A_PT_material_baker_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A Baker'
    bl_parent_id = "T4A_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2  # Third panel
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.t4a_baker_props
        
        box = layout.box()
        col = box.column(align=True)
        
        col.label(text="Material Settings:", icon='NODE_MATERIAL')
        col.prop(props, "mat_bake_type")
        col.prop(props, "mat_output_format")
        col.separator()
        col.prop(props, "mat_use_selected_to_active")


# Sub-panel: Info
class T4A_PT_InfoPanel(bpy.types.Panel):
    """Info panel displaying addon information from manifest"""
    bl_label = "Info"
    bl_idname = "T4A_PT_info_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A Baker'
    bl_parent_id = "T4A_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 99  # Last panel
    
    def draw(self, context):
        layout = self.layout
        manifest = get_manifest_data()
        
        if not manifest:
            layout.label(text="Manifest not found", icon='ERROR')
            return
        
        # Display manifest information
        box = layout.box()
        
        # Name and Version
        col = box.column(align=True)
        col.label(text=f"Name: {manifest.get('name', 'N/A')}")
        col.label(text=f"Version: {manifest.get('version', 'N/A')}")
        col.separator()
        
        # Maintainer
        maintainer = manifest.get('maintainer', 'N/A')
        col.label(text="Maintainer:")
        col.label(text=f"  {maintainer}", icon='USER')
        col.separator()
        
        # License
        license_info = manifest.get('license', ['N/A'])
        if isinstance(license_info, list):
            license_str = license_info[0] if license_info else 'N/A'
        else:
            license_str = str(license_info)
        col.label(text=f"License: {license_str}")
        col.separator()
        
        # Website / GitHub
        website = manifest.get('website', '')
        if website:
            col.label(text="Repository:", icon='URL')
            
            # Split long URL for display
            if len(website) > 35:
                col.label(text="  github.com/baronstudio/")
                col.label(text="  BlenderAddon/.../")
                col.label(text="  T4A_AssetConfigBaker")
            else:
                col.label(text=f"  {website}")
            
            # Operator to open URL
            col.operator("wm.url_open", text="Open GitHub", icon='URL').url = website
        
        col.separator()
        
        # Blender version requirement
        blender_min = manifest.get('blender_version_min', 'N/A')
        col.label(text=f"Requires Blender: {blender_min}+", icon='BLENDER')
        
        # Description
        box2 = layout.box()
        box2.label(text="Description:", icon='TEXT')
        tagline = manifest.get('tagline', 'N/A')
        
        # Word wrap for tagline
        words = tagline.split()
        line = ""
        for word in words:
            if len(line + word) > 30:
                box2.label(text=f"  {line}")
                line = word + " "
            else:
                line += word + " "
        if line:
            box2.label(text=f"  {line.strip()}")


# Registration
classes = (
    T4A_PT_MainPanel,
    T4A_PT_BakerPanel,
    T4A_PT_MaterialBakerPanel,
    T4A_PT_InfoPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
