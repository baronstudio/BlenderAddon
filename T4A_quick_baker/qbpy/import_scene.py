import bpy


class Import:
    @staticmethod
    def import_fbx(filepath: str, properties: bpy.types.Property = None, **kwargs):
        """Import an FBX file.

        Args:
            filepath (str): Import file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for import parameters.
        """
        default_params = {
            "files": [],  # list of dictionaries, where each dictionary represents a file with a name key.
            # include
            "use_custom_normals": True,
            "use_subsurf": False,
            "use_custom_props": True,
            "use_custom_props_enum_as_string": True,
            "use_image_search": True,
            # transform
            "global_scale": 1,
            "decal_offset": 0,
            "bake_space_transform": False,
            "use_prepost_rot": True,
            # manual_orientation
            "use_manual_orientation": False,
            "axis_forward": "-Z",
            "axis_up": "Y",
            # animation
            "use_anim": True,
            "anim_offset": 1,
            # armature
            "ignore_leaf_bones": False,
            "force_connect_children": False,
            "automatic_bone_orientation": False,
            "primary_bone_axis": "Y",
            "secondary_bone_axis": "X",
        }

        # Update default parameters with any provided in kwargs
        import_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    import_params[key] = getattr(properties, key)

        import_params["filepath"] = filepath

        if bpy.app.version >= (3, 6, 0):
            import_params["colors_type"] = kwargs.get("colors_type", default_params.get("colors_type", "SRGB"))

        bpy.ops.import_scene.fbx(**import_params)

    @staticmethod
    def import_obj(filepath: str, properties: bpy.types.Property = None, **kwargs):
        """Import an OBJ file.

        Args:
            filepath (str): Import file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for import parameters.
        """
        default_params_3_6 = {
            "directory": "",
            "files": [],
            "check_existing": False,
            "global_scale": 1,
            "clamp_size": 0,
            "forward_axis": "NEGATIVE_Z",
            "up_axis": "Y",
            "use_split_objects": True,
            "use_split_groups": False,
            "import_vertex_groups": False,
            "validate_meshes": False,
        }

        default_params_3_3 = {
            "use_image_search": True,
            "use_smooth_groups": True,
            "use_edges": True,
            "global_clamp_size": 0.0,
            "axis_forward": "-Z",
            "axis_up": "Y",
            "split_mode": "ON",
            "use_split_objects": True,
            "use_split_groups": False,
            "use_groups_as_vgroups": False,
        }

        if bpy.app.version >= (3, 6, 0):
            default_params = default_params_3_6
        else:
            default_params = default_params_3_3

        # Update default parameters with any provided in kwargs
        import_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    import_params[key] = getattr(properties, key)

        import_params["filepath"] = filepath

        if bpy.app.version >= (3, 6, 0):
            bpy.ops.wm.obj_import(**import_params)
        else:
            bpy.ops.import_scene.obj(**import_params)

    @staticmethod
    def import_alembic(filepath: str, properties: bpy.types.Property = None, **kwargs):
        """Import an Alembic file.
        Args:
            filepath (str): Import file path.
            properties (bpy.types.Property, optional): Properties from property group. Defaults to None.
            **kwargs: Additional keyword arguments for import parameters.
        """

        default_params = {
            "directory": "",
            "files": [],
            "scale": 1,
            "relative_path": True,
            "set_frame_range": True,
            "is_sequence": False,
            "validate_meshes": False,
            "always_add_cache_reader": False,
        }

        # Update default parameters with any provided in kwargs
        import_params = {**default_params, **kwargs}

        # Override with properties if provided
        if properties:
            for key in default_params:
                if hasattr(properties, key):
                    import_params[key] = getattr(properties, key)

        import_params["filepath"] = filepath

        bpy.ops.wm.alembic_import(**import_params)
