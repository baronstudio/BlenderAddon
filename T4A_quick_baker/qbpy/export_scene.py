import bpy


class Export:
    @staticmethod
    def export_fbx(filepath: str, properties: bpy.types.Property = None, **kwargs) -> str:
        """Export the scene to an FBX file.

        Args:
            filepath (str): Export file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for export parameters.

        Returns:
            str: Filepath of the exported file.
        """
        default_params = {
            "path_mode": "COPY",
            "embed_textures": True,
            "batch_mode": "OFF",
            "use_batch_own_dir": True,
            # Include
            "use_selection": True,
            "use_visible": False,
            "use_active_collection": False,
            "object_types": {"EMPTY", "CAMERA", "LIGHT", "ARMATURE", "MESH", "OTHER"},
            "use_custom_props": True,
            # Transform
            "global_scale": 1,
            "apply_scale_options": "FBX_SCALE_NONE",
            "axis_forward": "-Z",
            "axis_up": "Y",
            "apply_unit_scale": True,
            "use_space_transform": True,
            "bake_space_transform": False,
            # Geometry
            "mesh_smooth_type": "FACE",
            "use_subsurf": False,
            "use_mesh_modifiers": True,
            "use_mesh_edges": False,
            "use_triangles": False,
            "use_tspace": False,
            "colors_type": "SRGB",
            "prioritize_active_color": False,
            # Armature
            "primary_bone_axis": "Y",
            "secondary_bone_axis": "X",
            "armature_nodetype": "NULL",
            "use_armature_deform_only": True,
            "add_leaf_bones": False,
            # Animation
            "bake_anim": True,
            "bake_anim_use_all_bones": True,
            "bake_anim_use_nla_strips": True,
            "bake_anim_use_all_actions": False,
            "bake_anim_force_startend_keying": True,
            "bake_anim_step": 1,
            "bake_anim_simplify_factor": 1,
        }

        # Update default parameters with any provided in kwargs
        export_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    export_params[key] = getattr(properties, key)

        export_params["filepath"] = filepath

        if bpy.app.version >= (3, 6, 0):
            export_params["colors_type"] = kwargs.get("colors_type", default_params["colors_type"])
            export_params["prioritize_active_color"] = kwargs.get(
                "prioritize_active_color", default_params["prioritize_active_color"]
            )

        bpy.ops.export_scene.fbx(**export_params)
        return filepath

    @staticmethod
    def export_obj(filepath: str, properties: bpy.types.Property = None, **kwargs) -> str:
        """Export the object to an OBJ file.

        Args:
            filepath (str): Export file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for export parameters.

        Returns:
            str: Filepath of the exported file.
        """
        default_params_3_6 = {
            "export_selected_objects": True,
            "global_scale": 1,
            "forward_axis": "NEGATIVE_Z",
            "up_axis": "Y",
            "apply_modifiers": True,
            "export_eval_mode": "DAG_EVAL_VIEWPORT",
            "export_uv": True,
            "export_normals": True,
            "export_colors": False,
            "export_triangulated_mesh": False,
            "export_curves_as_nurbs": False,
            "export_materials": True,
            "export_pbr_extensions": False,
            "path_mode": "COPY",
            "export_object_groups": False,
            "export_material_groups": False,
            "export_vertex_groups": False,
            "export_smooth_groups": False,
            "smooth_group_bitflags": False,
            "export_animation": True,
            "start_frame": 1,
            "end_frame": 250,
        }

        default_params_3_3 = {
            "use_selection": True,
            "use_blen_objects": True,
            "group_by_object": False,
            "group_by_material": False,
            "use_animation": True,
            "axis_forward": "-Z",
            "axis_up": "Y",
            "use_mesh_modifiers": True,
            "use_smooth_groups": False,
            "use_smooth_groups_bitflags": False,
            "use_normals": True,
            "use_uvs": True,
            "use_materials": True,
            "use_triangles": True,
            "use_nurbs": False,
            "use_vertex_groups": False,
            "keep_vertex_order": False,
        }

        if bpy.app.version >= (3, 6, 0):
            default_params = default_params_3_6
        else:
            default_params = default_params_3_3

        # Update default parameters with any provided in kwargs
        export_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    export_params[key] = getattr(properties, key)

        export_params["filepath"] = filepath

        if bpy.app.version >= (3, 6, 0):
            bpy.ops.wm.obj_export(**export_params)
        else:
            bpy.ops.export_scene.obj(**export_params)

        return filepath

    @staticmethod
    def export_off(filepath: str, mesh: bpy.types.Mesh):
        """Export triangulated mesh to Object File Format.

        mesh (bpy.types.Mesh): The mesh to export.
        filepath (str): Filepath to save the file to.
        """
        with open(filepath, "wb") as off:
            off.write(b"OFF\n")
            off.write(str.encode(f"{len(mesh.vertices)} {len(mesh.polygons)} 0\n"))
            for vert in mesh.vertices:
                off.write(str.encode("{:g} {:g} {:g}\n".format(*vert.co)))
            for face in mesh.polygons:
                off.write(str.encode("3 {} {} {}\n".format(*face.vertices)))

    @staticmethod
    def export_gltf(filepath: str, properties: bpy.types.Property = None, **kwargs) -> str:
        """Export the scene to a GLTF file.

        Args:
            filepath (str): Export file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for export parameters.

        Returns:
            str: Filepath of the exported file.
        """
        common_params = {
            "export_format": "GLB",
            "export_keep_originals": False,
            "export_texture_dir": "",
            "export_copyright": "",
            "will_save_settings": False,
            # Include
            "use_selection": False,
            "use_visible": False,
            "use_renderable": False,
            "use_active_collection": False,
            "use_active_scene": False,
            "export_extras": False,
            "export_cameras": False,
            "export_lights": False,
            # Transform
            "export_yup": True,
            # Geometry
            ## Mesh
            "export_apply": False,
            "export_texcoords": True,
            "export_normals": True,
            "export_tangents": False,
            "use_mesh_edges": False,
            "use_mesh_vertices": False,
            # Material
            "export_materials": "EXPORT",
            "export_image_format": "AUTO",
            ## PBR Extensions
            "export_original_specular": False,
            # Compression
            "export_draco_mesh_compression_enable": False,
            "export_draco_mesh_compression_level": 6,
            "export_draco_position_quantization": 14,
            "export_draco_normal_quantization": 10,
            "export_draco_texcoord_quantization": 12,
            "export_draco_color_quantization": 10,
            "export_draco_generic_quantization": 12,
            # Animation
            "export_current_frame": False,
            ## Animation
            "export_animations": True,
            "export_frame_range": False,
            "export_frame_step": 1,
            "export_force_sampling": True,
            "export_nla_strips": True,
            "export_optimize_animation_size": False,
            "export_anim_single_armature": True,
            ## Shape Keys
            "export_morph": True,
            "export_morph_normal": True,
            "export_morph_tangent": False,
            ## Skinning
            "export_skins": True,
            "export_all_influences": False,
            "export_def_bones": False,
        }

        default_params_3_3 = {
            **common_params,
            "export_colors": True,
            "use_active_collection_with_nested": False,
        }

        default_params_3_6 = {
            **default_params_3_3,
            "export_attributes": False,
            "export_jpeg_quality": 75,
            # Armature
            "export_rest_position_armature": True,
            "export_hierarchy_flatten_bones": False,
            # Lighting
            "export_import_convert_lighting_mode": "SPEC",
            # Animation
            "export_animation_mode": "ACTIONS",
            "export_nla_strips_merged_animation_name": "Animation",
            "export_bake_animation": False,
            "export_anim_scene_split_object": True,
            "export_anim_slide_to_zero": False,
            "export_negative_frame": "SLIDE",
            "export_reset_pose_bones": True,
            "export_morph_reset_sk_data": True,
            "export_optimize_animation_size": True,
            "export_optimize_animation_keep_anim_armature": True,
            "export_optimize_animation_keep_anim_object": False,
        }

        default_params_4_2 = {
            **common_params,
            # Data
            ## Scene Graph
            "export_gn_mesh": False,
            "export_gpu_instances": False,
            "export_hierarchy_flatten_objs": False,
            "export_hierarchy_full_collections": False,
            ## Mesh
            "export_attributes": False,
            "export_shared_accessors": False,
            ### Vertex Colors
            "export_vertex_color": "MATERIAL",
            "export_all_vertex_colors": True,
            "export_active_vertex_color_when_no_material": True,
            # Material
            "export_image_quality": 75,
            "export_image_add_webp": False,
            "export_image_webp_fallback": False,
            ## Unused Textures and Images
            "export_unused_images": False,
            "export_unused_textures": False,
            ## Optimize Shape Keys
            "export_try_sparse_sk": True,
            "export_try_omit_sparse_sk": False,
            # Armature
            "export_armature_object_remove": False,
            "export_influence_nb": 4,
            # Animation
            "export_animation_mode": "ACTIONS",
            "export_anim_scene_split_object": True,
            "export_anim_slide_to_zero": False,
            "export_negative_frame": "SLIDE",
            "export_reset_pose_bones": True,
            "export_morph_reset_sk_data": True,
            "export_pointer_animation": False,
            "export_convert_animation_pointer": False,
            "export_optimize_animation_size": True,
            "export_optimize_animation_keep_anim_armature": True,
            "export_optimize_animation_keep_anim_object": False,
            "export_optimize_disable_viewport": False,
            "export_extra_animations": False,
            "export_action_filter": False,
            "export_nla_strips_merged_animation_name": "Animation",
        }

        default_params_4_4 = {
            **default_params_4_2,
            "export_leaf_bone": False,
            "export_merge_animation": "ACTION",
        }

        if bpy.app.version >= (4, 4, 0):
            default_params = default_params_4_4
        elif bpy.app.version >= (4, 2, 0):
            default_params = default_params_4_2
        elif bpy.app.version >= (3, 6, 0):
            default_params = default_params_3_6
        else:
            default_params = default_params_3_3

        # Update default parameters with any provided in kwargs
        export_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    export_params[key] = getattr(properties, key)

        export_params["filepath"] = filepath

        bpy.ops.export_scene.gltf(**export_params)
        return filepath
