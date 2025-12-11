
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
        
        # UIList pour les collections à baker
        row = box.row()
        row.template_list(
            "T4A_UL_CollectionBakeList", "",
            props, "collections",
            props, "active_collection_index",
            rows=3
        )
        
        # Boutons pour gérer la liste des collections
        col = row.column(align=True)
        col.operator("t4a.refresh_collection_list", icon='FILE_REFRESH', text="")
        col.operator("t4a.add_sel_coll_item", icon='ADD', text="")
        col.operator("t4a.dell_coll_item", icon='REMOVE', text="")
        
        # UIList pour les objets de la collection sélectionnée
        if props.collections and props.active_collection_index < len(props.collections):
            coll_item = props.collections[props.active_collection_index]
            
            box.separator()
            box.label(text=f"Objects in: {coll_item.name}", icon='OBJECT_DATA')
            
            row = box.row()
            # Disable if collection is not enabled
            row.enabled = coll_item.enabled
            row.template_list(
                "T4A_UL_ObjectBakeList", "",
                coll_item, "objects",
                coll_item, "active_object_index",
                rows=3
            )
            
            # Boutons pour gérer la liste des objets
            col = row.column(align=True)
            col.operator("t4a.refresh_object_list", icon='FILE_REFRESH', text="")
            col.operator("t4a.add_sel_object_item", icon='ADD', text="")
            col.operator("t4a.dell_object_item", icon='REMOVE', text="")
        
        box.separator()
        col = box.column(align=True)
        
        # Placeholder for Baker_V1 operators
        ###col.operator("t4a.baker_example", text="Run 3D Baker", icon='RENDER_STILL')
        
        # Material Baking section
        box = layout.box()
        box.label(text="Material Baking:", icon='MATERIAL')
        
       
        
        
        
        box.separator()
        
        # UIList pour les matériaux - Accès via la hiérarchie collections → objects
        if props.collections and props.active_collection_index < len(props.collections):
            coll_item = props.collections[props.active_collection_index]
            
            # Disable entire material section if collection is disabled
            material_section_enabled = coll_item.enabled

           
            
            if coll_item.objects and coll_item.active_object_index < len(coll_item.objects):
                obj_item = coll_item.objects[coll_item.active_object_index]
                
                # Also check if object is enabled
                material_section_enabled = material_section_enabled and obj_item.enabled
                
                # UIList des matériaux de l'objet sélectionné
                row = box.row()
                row.enabled = material_section_enabled
                row.template_list(
                    "T4A_UL_MaterialBakeList", "",
                    obj_item, "materials",
                    obj_item, "active_material_index",
                    rows=3
                )
                
                # Boutons pour gérer la liste
                col = row.column(align=True)
                col.operator("t4a.refresh_material_list", icon='FILE_REFRESH', text="")
                


                ###### PRESETS SELECTOR ######
                # Unified Preset Management
                preset_box = box.box()
                preset_box.enabled = material_section_enabled
                preset_box.label(text="Presets:", icon='PRESET')
                
                # Dropdown with buttons (similar to Unity/Unreal)
                row = preset_box.row(align=True)
                
                # Dropdown selector (all presets from JSON)
                sub = row.row(align=True)
                sub.scale_x = 2.5
                sub.prop(props, "preset_selection", text="")
                
                # Delete button (minus icon) - only for custom presets
                from . import PresetLoader
                preset = PresetLoader.get_preset(props.preset_selection)
                if preset and preset.get('is_custom', False):
                    row.operator("t4a.delete_baking_preset", text="", icon='REMOVE')
                
                # Apply button
                row.operator("t4a.apply_preset_from_json", text="", icon='CHECKMARK')
                
                # Add button (plus icon) for creating new custom presets
                row.operator("t4a.new_preset_menu", text="", icon='ADD')

                ###### END PRESETS SELECTOR ######

                # Détails du matériau sélectionné
                if obj_item.materials and obj_item.active_material_index < len(obj_item.materials):
                    mat_item = obj_item.materials[obj_item.active_material_index]
                    
                    # Check if material is enabled too
                    maps_section_enabled = material_section_enabled and mat_item.enabled
                    
                    box.separator()
                    box.label(text=f"Maps for: {mat_item.name}", icon='NODE_MATERIAL')
                    
                    # UIList pour les maps de ce matériau
                    row = box.row()
                    row.enabled = maps_section_enabled
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
                        sub.enabled = maps_section_enabled
                        sub.prop(map_item, "enabled")
                        sub.prop(map_item, "map_type")
                        
                        # Format settings
                        row = sub.row(align=True)
                        row.prop(map_item, "output_format")
                        
                        # Show color depth based on format
                        fmt = map_item.output_format
                        if fmt in ('PNG', 'TIFF'):
                            row.prop(map_item, "color_depth", text="")
                        elif fmt == 'JPEG':
                            # JPEG only supports 8-bit
                            sub.label(text="(8-bit)", icon='INFO')
                        elif fmt == 'OPEN_EXR':
                            # EXR only supports 16/32-bit float
                            row.prop(map_item, "color_depth", text="")
                        
                        # Color Management
                        sub.prop(map_item, "view_transform")
                        
                        sub.prop(map_item, "resolution")
                else:
                    box.label(text="No materials in selected object", icon='INFO')
            else:
                box.label(text="No objects in selected collection", icon='INFO')
        else:
            box.label(text="No collections configured", icon='INFO')

        
        
        box.separator()
        
        # Progress bar
        if props.is_baking:
            col = box.column(align=True)
            col.prop(props, "bake_progress", text="Progress", slider=True)
        
        # Bake button
        col = box.column(align=True)
        #col.operator("t4a.baker_mat", text="Bake Materials (active object)", icon='NODE_MATERIAL')
        
        if props.is_baking:
            col.enabled = False  # Désactive le bouton pendant le baking
            col.operator("t4a.bake_configuration", text="Baking in progress...", icon='TIME')
        else:
            col.operator("t4a.bake_configuration", text="Bake Materials (Full Configuration)", icon='NODE_MATERIAL')


        
        # Export section
        box = layout.box()
        box.label(text="3D Export:", icon='EXPORT')
        
        # UIList for collections export
        row = box.row()
        row.template_list(
            "T4A_UL_CollectionExportList", "",
            props, "export_collections",
            props, "active_export_collection_index",
            rows=3
        )
        
        # Buttons for export list management
        col = row.column(align=True)
        col.operator("t4a.refresh_export_collection_list", icon='FILE_REFRESH', text="")
        col.operator("t4a.add_sel_export_coll_item", icon='ADD', text="")
        col.operator("t4a.dell_export_coll_item", icon='REMOVE', text="")
        
        # GLB Export options for selected collection
        if props.export_collections and props.active_export_collection_index < len(props.export_collections):
            coll_item = props.export_collections[props.active_export_collection_index]
            
            box.separator()
            export_box = box.box()
            export_box.enabled = coll_item.enabled
            export_box.label(text=f"GLB Options: {coll_item.name}", icon='SETTINGS')
            
            col = export_box.column(align=True)
            col.prop(coll_item, "export_format")
            col.separator()
            col.prop(coll_item, "export_apply_modifiers")
            col.prop(coll_item, "export_materials")
            col.separator()
            col.prop(coll_item, "export_colors")
            col.prop(coll_item, "export_cameras")
            col.prop(coll_item, "export_lights")
            col.separator()
            col.prop(coll_item, "export_yup")
        
        box.separator()
        
        # Export buttons
        col = box.column(align=True)
        col.operator("t4a.export_all_collections", text="Export All Collections", icon='EXPORT')
        
        # Single collection export (if one is selected)
        if props.export_collections and props.active_export_collection_index < len(props.export_collections):
            coll_item = props.export_collections[props.active_export_collection_index]
            op = col.operator("t4a.export_collection_glb", text=f"Export '{coll_item.name}'", icon='FILE_3D')
            op.collection_name = coll_item.name


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
        prefs = context.preferences.addons[__package__].preferences
        
        # Export Path reminder
        box = layout.box()
        box.label(text="Export Path:", icon='FILE_FOLDER')
        row = box.row()
        row.prop(prefs, "default_export_path", text="")
        row.operator("preferences.addon_show", text="", icon='PREFERENCES').module = __package__
        
        layout.separator()
        
        # Baking Settings
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
    
    @classmethod
    def poll(cls, context):
        """Control panel visibility - return False to hide the panel"""
        # Example conditions to hide panel:
        # return False  # Always hide
        # return context.scene.t4a_baker_props.some_property  # Conditional
        # prefs = context.preferences.addons[__package__].preferences
        # return prefs.show_material_panel  # From preferences
        
        return False #True  # Always show (default behavior)
    
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
#uiliste for collection baking management
class T4A_UL_CollectionBakeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')
            row.label(text=item.name, icon='OUTLINER_COLLECTION')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')

#uiliste for object baking management
class T4A_UL_ObjectBakeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')
            row.label(text=item.name, icon='MESH_CUBE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MESH_CUBE')

#uilistes for material baking management
class T4A_UL_MaterialBakeList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')
            
            # Get material from Blender data to show preview icon
            mat = bpy.data.materials.get(item.name)
            if mat and mat.preview:
                # Use material preview icon (like in Blender's material list)
                row.label(text=item.name, icon_value=mat.preview.icon_id)
            else:
                # Fallback to generic material icon
                row.label(text=item.name, icon='MATERIAL')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            # In grid mode, show preview icon
            mat = bpy.data.materials.get(item.name)
            if mat and mat.preview:
                layout.label(text="", icon_value=mat.preview.icon_id)
            else:
                layout.label(text="", icon='MATERIAL')

#uilistes for material bake maps management
class T4A_UL_MaterialBakeMapList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')
            row.label(text=item.map_type, icon='TEXTURE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='TEXTURE')


# UIList for collection export management
class T4A_UL_CollectionExportList(bpy.types.UIList):
    """UIList for collections to export as GLB"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)
            row.prop(item, "enabled", text="", icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')
            row.label(text=item.name, icon='OUTLINER_COLLECTION')
            
            # Show export format icon
            if item.export_format == 'GLB':
                row.label(text="", icon='FILE_3D')
            elif item.export_format == 'GLTF_SEPARATE':
                row.label(text="", icon='FILE_FOLDER')
            elif item.export_format == 'GLTF_EMBEDDED':
                row.label(text="", icon='FILE_ARCHIVE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='OUTLINER_COLLECTION')


# Registration
classes = (
    T4A_PT_MainPanel,
    T4A_PT_BakerPanel,
    T4A_PT_MaterialBakerPanel,
    T4A_UL_CollectionBakeList,
    T4A_UL_ObjectBakeList,
    T4A_UL_MaterialBakeMapList,
    T4A_UL_MaterialBakeList,
    T4A_UL_CollectionExportList,
    T4A_PT_InfoPanel,
)



def register():
    pass



def unregister():
    pass
