
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
        
        # UIList pour les matériaux de l'objet actif
        obj = context.active_object
        if obj and obj.type == 'MESH' and hasattr(obj.data, 'materials'):
            # Synchroniser la liste des matériaux avec l'objet actif
            row = box.row()
            row.template_list(
                "T4A_UL_MaterialBakeList", "",
                props, "materials",
                props, "active_material_index",
                rows=3
            )
            
            # Boutons pour gérer la liste
            col = row.column(align=True)
            col.operator("t4a.refresh_material_list", icon='FILE_REFRESH', text="")
            
            # Détails du matériau sélectionné
            if props.materials and props.active_material_index < len(props.materials):
                mat_item = props.materials[props.active_material_index]
                
                box.separator()
                box.label(text=f"Maps for: {mat_item.name}", icon='NODE_MATERIAL')
                
                # UIList pour les maps de ce matériau
                row = box.row()
                row.template_list(
                    "T4A_UL_MaterialBakeMapList", "",
                    mat_item, "maps",
                    mat_item, "active_map_index",
                    rows=2
                )
                
                # Boutons pour gérer les maps
                col = row.column(align=True)
                col.operator("t4a.add_bake_map", icon='ADD', text="")
                col.operator("t4a.remove_bake_map", icon='REMOVE', text="")
                
                # Détails de la map sélectionnée
                if mat_item.maps and mat_item.active_map_index < len(mat_item.maps):
                    map_item = mat_item.maps[mat_item.active_map_index]
                    
                    box.separator()
                    sub = box.box()
                    sub.prop(map_item, "enabled")
                    sub.prop(map_item, "map_type")
                    sub.prop(map_item, "output_format")
                    sub.prop(map_item, "resolution")
        else:
            box.label(text="No active mesh object", icon='INFO')
        
        box.separator()
        col = box.column(align=True)
        col.operator("t4a.baker_mat", text="Bake Materials", icon='NODE_MATERIAL')
        
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


# UI Lists
#uilistes for material baking management
class T4A_UL_MaterialBakeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='MATERIAL')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')

#uilistes for material bake maps management
class T4A_UL_MaterialBakeMapList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.map_type, icon='TEXTURE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='TEXTURE')


# Registration
classes = (
    T4A_PT_MainPanel,
    T4A_PT_BakerPanel,
    T4A_PT_MaterialBakerPanel,
    T4A_UL_MaterialBakeMapList,
    T4A_UL_MaterialBakeList,
    T4A_PT_InfoPanel,
)



def register():
    pass



def unregister():
    pass
