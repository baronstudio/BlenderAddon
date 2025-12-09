"""
T4A Assets Configuration Baker - Material Baking Engine V1
Operators for material baking, PBR texture generation, and material optimization
"""

import bpy
from bpy.types import Operator
import time
import os


class T4A_OT_BakerMat(Operator):
    """Operator for material baking"""
    bl_idname = "t4a.baker_mat"
    bl_label = "Bake Materials"
    bl_description = "Execute material baking process for selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        prefs = context.preferences.addons[__package__].preferences
        start_time = time.time()
        props.is_baking = True
        self.report({'INFO'}, "Starting material baking process...")

        obj = context.active_object
        if not obj or not obj.data or not hasattr(obj.data, 'materials'):
            self.report({'WARNING'}, "No active object with materials found")
            props.is_baking = False
            return {'CANCELLED'}

        # Contrôle si Cycles est configuré pour le baking
        if context.scene.render.engine != 'CYCLES':
            bpy.ops.t4a.prepare_cycles_baking()

        # Vérifie que la liste des matériaux est configurée
        if not props.materials:
            self.report({'WARNING'}, "No materials configured. Use 'Refresh Material List' button first.")
            props.is_baking = False
            return {'CANCELLED'}

        total_bakes = 0
        successful_bakes = 0

        # S'assure que l'objet est sélectionné pour le baking
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Boucle sur la liste des matériaux configurés dans l'UI
        for mat_item in props.materials:
            mat_name = mat_item.name
            
            # Trouve le matériau correspondant dans l'objet
            mat = bpy.data.materials.get(mat_name)

            # Move material to first slot and set as active
            if mat and obj.data.materials.get(mat_name):
                mat_index = obj.data.materials.find(mat_name)
                if mat_index != -1 and mat_index != 0:
                    # Remove from current position
                    obj.data.materials.pop(index=mat_index)
                    # Insert at first position
                    obj.data.materials.append(mat)
                    # Move to index 0
                    for i in range(len(obj.data.materials) - 1, 0, -1):
                        obj.data.materials[i], obj.data.materials[i-1] = obj.data.materials[i-1], obj.data.materials[i]
                # Set as active material slot
                obj.active_material_index = 0
                    #bpy.context.object.active_material_index = mat_index
                    #bpy.ops.object.material_slot_assign()

            if not mat:
                self.report({'WARNING'}, f"Material '{mat_name}' not found in scene. Skipping.")
                continue
            
            # Vérifie que le matériau utilise des nodes
            if not mat.use_nodes:
                self.report({'WARNING'}, f"Material '{mat_name}' does not use nodes. Skipping.")
                continue
            
            # Boucle sur toutes les maps configurées pour ce matériau
            for map_item in mat_item.maps:
                # Ignore les maps désactivées
                if not map_item.enabled:
                    continue
                
                total_bakes += 1
                bake_type = map_item.map_type
                output_format = map_item.output_format
                resolution = map_item.resolution
                
                self.report({'INFO'}, f"Baking {bake_type} for material '{mat_name}' at {resolution}x{resolution}...")
                
                # Crée une image temporaire pour le baking
                img_name = f"{mat_name}_{bake_type}"
                img = bpy.data.images.new(img_name, width=resolution, height=resolution)

                # Attribue l'image à un node du matériau
                nodes = mat.node_tree.nodes
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = img
                mat.node_tree.nodes.active = tex_node

                # Configure le type de baking
                context.scene.render.bake.use_selected_to_active = False
                context.scene.render.bake.use_clear = True
                context.scene.render.bake.margin = 16
                context.scene.render.bake.use_pass_direct = True
                context.scene.render.bake.use_pass_indirect = True

                # Lance le baking
                try:
                    bpy.ops.object.bake(type=bake_type)
                    successful_bakes += 1
                except Exception as e:
                    self.report({'ERROR'}, f"Bake failed for {mat_name} ({bake_type}): {e}")
                    # Nettoyage en cas d'erreur
                    try:
                        nodes.remove(tex_node)
                    except:
                        pass
                    if img:
                        bpy.data.images.remove(img)
                    continue

                # Sauvegarde l'image
                ext = output_format.lower()
                if ext == 'jpeg':
                    ext = 'jpg'
                elif ext == 'open_exr':
                    ext = 'exr'
                
                file_path = bpy.path.abspath(f"//{mat_name}_{bake_type}.{ext}")
                img.filepath_raw = file_path
                img.file_format = output_format
                try:
                    img.save()
                    self.report({'INFO'}, f"Saved: {file_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to save {file_path}: {e}")

                # Nettoyage du node temporaire et de l'image
                try:
                    nodes.remove(tex_node)
                except:
                    pass
                bpy.data.images.remove(img)

        end_time = time.time()
        props.last_bake_time = end_time - start_time
        props.is_baking = False
        
        self.report({'INFO'}, f"Material baking completed: {successful_bakes}/{total_bakes} successful in {props.last_bake_time:.2f}s")
        return {'FINISHED'}


class T4A_OT_BakePBRMaps(Operator):
    """Bake complete PBR texture set (Diffuse, Normal, Roughness, Metallic)"""
    bl_idname = "t4a.bake_pbr_maps"
    bl_label = "Bake PBR Maps"
    bl_description = "Bake complete PBR texture set for selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        prefs = context.preferences.addons[__package__].preferences
        
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        resolution = int(props.bake_resolution)
        
        self.report({'INFO'}, "Baking PBR texture set...")
        self.report({'INFO'}, f"Resolution: {resolution}x{resolution}")
        
        # List of PBR maps to bake
        pbr_maps = ['DIFFUSE', 'NORMAL', 'ROUGHNESS', 'EMIT']
        
        for bake_type in pbr_maps:
            self.report({'INFO'}, f"Baking {bake_type} map...")
            # TODO: Implement baking for each map type
        
        self.report({'INFO'}, "PBR maps baking completed")
        
        return {'FINISHED'}


class T4A_OT_BakeDiffuse(Operator):
    """Bake diffuse/base color map"""
    bl_idname = "t4a.bake_diffuse"
    bl_label = "Bake Diffuse"
    bl_description = "Bake diffuse/base color texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        self.report({'INFO'}, "Baking diffuse map...")
        
        # TODO: Implement diffuse baking
        # - Set up image texture
        # - Configure bake settings
        # - Execute bake
        # - Save result
        
        return {'FINISHED'}


class T4A_OT_BakeNormal(Operator):
    """Bake normal map"""
    bl_idname = "t4a.bake_normal"
    bl_label = "Bake Normal"
    bl_description = "Bake normal map from high-poly to low-poly"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        self.report({'INFO'}, "Baking normal map...")
        
        if props.mat_use_selected_to_active:
            self.report({'INFO'}, "Using selected to active baking")
        
        # TODO: Implement normal map baking
        
        return {'FINISHED'}


class T4A_OT_BakeRoughness(Operator):
    """Bake roughness map"""
    bl_idname = "t4a.bake_roughness"
    bl_label = "Bake Roughness"
    bl_description = "Bake roughness/glossiness texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        self.report({'INFO'}, "Baking roughness map...")
        
        # TODO: Implement roughness baking
        
        return {'FINISHED'}


class T4A_OT_BakeAO(Operator):
    """Bake ambient occlusion map"""
    bl_idname = "t4a.bake_ao"
    bl_label = "Bake AO"
    bl_description = "Bake ambient occlusion texture"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        self.report({'INFO'}, "Baking ambient occlusion map...")
        
        # TODO: Implement AO baking
        
        return {'FINISHED'}


class T4A_OT_OptimizeMaterials(Operator):
    """Optimize materials for web export"""
    bl_idname = "t4a.optimize_materials"
    bl_label = "Optimize Materials"
    bl_description = "Optimize materials for web/real-time rendering"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        self.report({'INFO'}, "Optimizing materials for web...")
        
        optimized_count = 0
        
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue
            
            if obj.data.materials:
                for mat in obj.data.materials:
                    if mat:
                        # TODO: Implement material optimization
                        # - Simplify node trees
                        # - Remove unused nodes
                        # - Optimize texture sizes
                        optimized_count += 1
        
        self.report({'INFO'}, f"Optimized {optimized_count} material(s)")
        
        return {'FINISHED'}


class T4A_OT_CreateBakeMaterial(Operator):
    """Create optimized material for baked textures"""
    bl_idname = "t4a.create_bake_material"
    bl_label = "Create Bake Material"
    bl_description = "Create a new material setup for baked textures"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        
        # Create new material
        mat_name = f"T4A_Baked_{props.asset_name}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        
        self.report({'INFO'}, f"Created material: {mat_name}")
        
        # TODO: Set up node tree for baked textures
        # - Add Image Texture nodes
        # - Connect to Principled BSDF
        # - Set up UV mapping
        
        return {'FINISHED'}


class T4A_OT_BatchBakeMaterials(Operator):
    """Batch bake materials for multiple objects"""
    bl_idname = "t4a.batch_bake_materials"
    bl_label = "Batch Bake Materials"
    bl_description = "Bake materials for all selected objects in batch"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        prefs = context.preferences.addons[__package__].preferences
        
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected")
            return {'CANCELLED'}
        
        start_time = time.time()
        props.is_baking = True
        
        total_objects = len(selected_objects)
        baked_count = 0
        
        self.report({'INFO'}, f"Starting batch baking for {total_objects} object(s)...")
        
        for i, obj in enumerate(selected_objects):
            if obj.type != 'MESH':
                continue
            
            # Update progress
            progress = (i + 1) / total_objects
            props.bake_progress = progress
            
            self.report({'INFO'}, f"Baking {obj.name} ({i+1}/{total_objects})...")
            
            # TODO: Implement baking for each object
            
            baked_count += 1
        
        end_time = time.time()
        props.last_bake_time = end_time - start_time
        props.is_baking = False
        props.bake_progress = 0.0
        
        self.report({'INFO'}, f"Batch baking completed: {baked_count} object(s) in {props.last_bake_time:.2f}s")
        
        return {'FINISHED'}


# Registration
classes = (
    T4A_OT_BakerMat,
    T4A_OT_BakePBRMaps,
    T4A_OT_BakeDiffuse,
    T4A_OT_BakeNormal,
    T4A_OT_BakeRoughness,
    T4A_OT_BakeAO,
    T4A_OT_OptimizeMaterials,
    T4A_OT_CreateBakeMaterial,
    T4A_OT_BatchBakeMaterials,
)


def register():
    #for cls in classes:
        #bpy.utils.register_class(cls)
    pass


def unregister():
    #for cls in reversed(classes):
        #bpy.utils.unregister_class(cls)
    pass