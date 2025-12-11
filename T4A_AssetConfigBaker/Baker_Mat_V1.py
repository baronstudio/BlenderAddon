"""
T4A Assets Configuration Baker - Material Baking Engine V1
Operators for material baking, PBR texture generation, and material optimization
"""

import bpy
from bpy.types import Operator
import time
import os
from . import BakeTypeMapper


class T4A_OT_BakerMat(Operator):
    """Operator for material baking"""
    bl_idname = "t4a.baker_mat"
    bl_label = "Bake Materials"
    bl_description = "Execute material baking process for selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Property to pass the object name to bake
    target_object: bpy.props.StringProperty(
        name="Target Object",
        description="Name of the object to bake (if empty, uses active object)",
        default=""
    )
    
    def execute(self, context):
        props = context.scene.t4a_baker_props
        prefs = context.preferences.addons[__package__].preferences
        start_time = time.time()
        props.is_baking = True
        self.report({'INFO'}, "Starting material baking process...")

        # Use target_object if specified, otherwise use active object
        if self.target_object:
            obj = bpy.data.objects.get(self.target_object)
            if not obj:
                self.report({'WARNING'}, f"Object '{self.target_object}' not found")
                props.is_baking = False
                return {'CANCELLED'}
            else:
                obj = bpy.data.objects.get(self.target_object)
        else:
            obj = context.active_object

        #force use of target_object
        #obj = bpy.data.objects.get(self.target_object)
        props.is_baking = False
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

        #a ce stade l'object a baker est selectioner dans la boucle supperieur de Baker_General.py 

        # Mémorise l'ordre original des matériaux pour restauration ultérieure
        original_materials_order = [mat for mat in obj.data.materials if mat]
        original_active_index = obj.active_material_index

        # Boucle sur la liste des matériaux configurés dans l'UI
        for mat_item in props.materials:
            # Ignore les matériaux désactivés
            if not mat_item.enabled:
                continue
            
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
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

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
                
                # Check if we need to extract a specific socket (e.g., Metallic, Alpha)
                socket_to_extract = BakeTypeMapper.requires_socket_extraction(bake_type)
                if socket_to_extract:
                    # Create emission setup to capture the socket value
                    success = self._setup_socket_extraction(mat, socket_to_extract, img)
                    if not success:
                        self.report({'WARNING'}, f"Could not extract socket '{socket_to_extract}' for {mat_name}. Skipping.")
                        bpy.data.images.remove(img)
                        continue
                else:
                    # Standard baking setup
                    tex_node = nodes.new('ShaderNodeTexImage')
                    tex_node.image = img
                    mat.node_tree.nodes.active = tex_node

                # Configure le type de baking avec le mapping
                cycles_bake_type = BakeTypeMapper.setup_bake_settings(context, bake_type)
                
                context.scene.render.bake.use_selected_to_active = False
                context.scene.render.bake.use_clear = True
                context.scene.render.bake.margin = 16
                
                # Lance le baking avec le type Cycles approprié
                try:
                    bpy.ops.object.bake(type=cycles_bake_type)
                    
                    # Post-processing si nécessaire
                    post_process = BakeTypeMapper.requires_post_processing(bake_type)
                    if post_process:
                        self._apply_post_processing(img, post_process)
                    
                    successful_bakes += 1
                except Exception as e:
                    self.report({'ERROR'}, f"Bake failed for {mat_name} ({bake_type} -> {cycles_bake_type}): {e}")
                    # Nettoyage en cas d'erreur
                    if socket_to_extract:
                        self._cleanup_socket_extraction(mat)
                    else:
                        try:
                            nodes.remove(tex_node)
                        except:
                            pass
                    if img:
                        bpy.data.images.remove(img)
                    continue

                # Sauvegarde l'image avec le suffix configuré
                ext = output_format.lower()
                if ext == 'jpeg':
                    ext = 'jpg'
                elif ext == 'open_exr':
                    ext = 'exr'
                
                # Utilise le suffix personnalisé ou génère un par défaut
                suffix = map_item.file_suffix if map_item.file_suffix else f"_{bake_type.lower()}"
                
                # Construit le chemin hiérarchique : base_path/collection/object/
                base_path = bpy.path.abspath(prefs.default_export_path)
                
                # Détermine la collection de l'objet
                collection_name = "Uncategorized"
                for coll in bpy.data.collections:
                    if obj.name in coll.objects:
                        collection_name = coll.name
                        break
                
                # Crée la structure de dossiers
                output_dir = os.path.join(base_path, collection_name, obj.name)
                os.makedirs(output_dir, exist_ok=True)
                
                # Chemin complet du fichier
                file_path = os.path.join(output_dir, f"{mat_name}{suffix}.{ext}")
                img.filepath_raw = file_path
                img.file_format = output_format
                try:
                    img.save()
                    self.report({'INFO'}, f"Saved: {file_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to save {file_path}: {e}")

                # Nettoyage du node temporaire et de l'image
                if socket_to_extract:
                    self._cleanup_socket_extraction(mat)
                else:
                    try:
                        nodes.remove(tex_node)
                    except:
                        pass
                bpy.data.images.remove(img)

        # Restaure l'ordre original des matériaux
        if original_materials_order:
            # Vide la liste actuelle
            while len(obj.data.materials) > 0:
                obj.data.materials.pop(index=0)
            
            # Réinsère les matériaux dans l'ordre original
            for mat in original_materials_order:
                obj.data.materials.append(mat)
            
            # Restaure l'index actif
            if 0 <= original_active_index < len(obj.data.materials):
                obj.active_material_index = original_active_index

        end_time = time.time()
        props.last_bake_time = end_time - start_time
        props.is_baking = False
        
        self.report({'INFO'}, f"Material baking completed: {successful_bakes}/{total_bakes} successful in {props.last_bake_time:.2f}s")
        return {'FINISHED'}
    
    def _setup_socket_extraction(self, material, socket_name, target_image):
        """
        Setup material to extract a specific socket value via emission
        Stores original output node for restoration
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Find Principled BSDF
        principled = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if not principled:
            return False
        
        # Check if socket exists and is connected
        if socket_name not in principled.inputs:
            return False
        
        socket = principled.inputs[socket_name]
        
        # Store original material output for restoration
        material_output = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                material_output = node
                break
        
        # Store original connection
        if material_output and material_output.inputs['Surface'].is_linked:
            original_link = material_output.inputs['Surface'].links[0]
            material['_t4a_original_surface'] = original_link.from_socket.name
            material['_t4a_original_node'] = original_link.from_node.name
        
        # Create emission setup
        emission = nodes.new('ShaderNodeEmission')
        emission.name = '_T4A_TempEmission'
        
        # Create image texture node for baking
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.name = '_T4A_TempBakeTarget'
        tex_node.image = target_image
        nodes.active = tex_node
        
        # Connect socket to emission
        if socket.is_linked:
            # Socket has connection, use it
            from_socket = socket.links[0].from_socket
            links.new(from_socket, emission.inputs['Color'])
        else:
            # Socket has default value, use it
            if hasattr(socket, 'default_value'):
                emission.inputs['Color'].default_value = (socket.default_value,) * 3 + (1,)
        
        # Connect to output
        if material_output:
            links.new(emission.outputs['Emission'], material_output.inputs['Surface'])
        
        return True
    
    def _cleanup_socket_extraction(self, material):
        """
        Restore material to original state after socket extraction
        """
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Remove temporary nodes
        for node in list(nodes):
            if node.name in ['_T4A_TempEmission', '_T4A_TempBakeTarget']:
                nodes.remove(node)
        
        # Restore original connection
        if '_t4a_original_surface' in material and '_t4a_original_node' in material:
            material_output = None
            for node in nodes:
                if node.type == 'OUTPUT_MATERIAL':
                    material_output = node
                    break
            
            original_node = nodes.get(material['_t4a_original_node'])
            if material_output and original_node:
                socket_name = material['_t4a_original_surface']
                if socket_name in original_node.outputs:
                    links.new(original_node.outputs[socket_name], material_output.inputs['Surface'])
            
            # Cleanup stored data
            del material['_t4a_original_surface']
            del material['_t4a_original_node']
    
    def _apply_post_processing(self, image, post_process_settings):
        """
        Apply post-processing to baked image
        """
        import numpy as np
        
        # Get pixel data
        pixels = np.array(image.pixels[:])
        width = image.size[0]
        height = image.size[1]
        channels = image.channels
        
        # Reshape to (height, width, channels)
        pixels = pixels.reshape((height, width, channels))
        
        # Apply transformations
        if post_process_settings.get('flip_y'):
            # Flip Y channel (for DirectX normal maps)
            if channels >= 2:
                pixels[:, :, 1] = 1.0 - pixels[:, :, 1]
        
        if post_process_settings.get('invert'):
            # Invert all color channels (for glossiness)
            for c in range(min(3, channels)):
                pixels[:, :, c] = 1.0 - pixels[:, :, c]
        
        # Write back to image
        image.pixels = pixels.flatten().tolist()


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