from math import radians
from typing import List

import bpy

from .mesh import Mesh


class Modifier:
    @staticmethod
    def _set_common_modifier_properties(
        modifier: bpy.types.Modifier,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
    ):
        """Set common properties for a modifier."""
        modifier.show_expanded = show_expanded
        modifier.show_on_cage = show_on_cage
        modifier.show_in_editmode = show_in_editmode
        modifier.show_viewport = show_viewport
        modifier.show_render = show_render
        if hasattr(modifier, "use_pin_to_last"):
            modifier.use_pin_to_last = use_pin_to_last

    # Edit
    ## Data Transfer Modifier
    @staticmethod
    def data_transfer(
        obj: bpy.types.Object,
        name: str = "DataTransfer",
        object: bpy.types.Object = None,
        use_object_transform: bool = True,
        mix_mode: str = "REPLACE",
        mix_factor: float = 1.0,
        vertex_group: str = "",
        invert_vertex_group: bool = False,
        use_vertex_data: bool = False,
        data_types_verts: set[str] = set(),
        vert_mapping: str = "NEAREST",
        layers_vgroup_select_src: str = "ALL",
        layers_vgroup_select_dst: str = "NAME",
        layers_vcol_vert_select_src: str = "ALL",
        layers_vcol_vert_select_dst: str = "NAME",
        use_edge_data: bool = False,
        data_types_edges: set[str] = set(),
        edge_mapping: str = "NEAREST",
        use_loop_data: bool = False,
        data_types_loops: set[str] = set(),
        loop_mapping: str = "NEAREST",
        layers_vcol_loop_select_src: str = "ALL",
        layers_vcol_loop_select_dst: str = "NAME",
        layers_uv_select_src: str = "ALL",
        layers_uv_select_dst: str = "NAME",
        island_precision: float = 0.0,
        use_poly_data: bool = False,
        data_types_polys: set[str] = set(),
        poly_mapping: str = "NEAREST",
        use_max_distance: bool = False,
        max_distance: float = 1.0,
        ray_radius: float = 0.0,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Data Transfer modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            object (bpy.types.Object, optional): The object to transfer data from.
            use_object_transform (bool, optional): Use object transform.
            mix_mode (str, optional): The mix mode.
            mix_factor (float, optional): The mix factor (0 to 1).
            vertex_group (str, optional): The vertex group.
            invert_vertex_group (bool, optional): Invert vertex group.
            use_vertex_data (bool, optional): Use vertex data.
            data_types_verts (set[str], optional): Data types for vertices.
            vert_mapping (str, optional): Vertex mapping.
            layers_vgroup_select_src (str, optional): Vertex group source layers.
            layers_vgroup_select_dst (str, optional): Vertex group destination layers.
            layers_vcol_vert_select_src (str, optional): Vertex color source layers.
            layers_vcol_vert_select_dst (str, optional): Vertex color destination layers.
            use_edge_data (bool, optional): Use edge data.
            data_types_edges (set[str], optional): Data types for edges.
            edge_mapping (str, optional): Edge mapping.
            use_loop_data (bool, optional): Use loop data.
            data_types_loops (set[str], optional): Data types for loops.
            loop_mapping (str, optional): Loop mapping.
            layers_vcol_loop_select_src (str, optional): Vertex color loop source layers.
            layers_vcol_loop_select_dst (str, optional): Vertex color loop destination layers.
            layers_uv_select_src (str, optional): UV source layers.
            layers_uv_select_dst (str, optional): UV destination layers.
            island_precision (float, optional): Island precision.
            use_poly_data (bool, optional): Use polygon data.
            data_types_polys (set[str], optional): Data types for polygons.
            poly_mapping (str, optional): Polygon mapping.
            use_max_distance (bool, optional): Use max distance.
            max_distance (float, optional): Max distance.
            ray_radius (float, optional): Ray radius.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Data Transfer modifier.
        """
        # Validate mix_factor
        mix_factor = max(0.0, min(mix_factor, 1.0))

        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "DATA_TRANSFER")

        modifier.object = object
        modifier.use_object_transform = use_object_transform
        modifier.mix_mode = mix_mode
        modifier.mix_factor = mix_factor
        modifier.vertex_group = vertex_group
        modifier.invert_vertex_group = invert_vertex_group
        modifier.use_vertex_data = use_vertex_data
        modifier.data_types_verts = data_types_verts
        modifier.vert_mapping = vert_mapping
        modifier.layers_vgroup_select_src = layers_vgroup_select_src
        modifier.layers_vgroup_select_dst = layers_vgroup_select_dst
        modifier.layers_vcol_vert_select_src = layers_vcol_vert_select_src
        modifier.layers_vcol_vert_select_dst = layers_vcol_vert_select_dst
        modifier.use_edge_data = use_edge_data
        modifier.data_types_edges = data_types_edges
        modifier.edge_mapping = edge_mapping
        modifier.use_loop_data = use_loop_data
        modifier.data_types_loops = data_types_loops
        modifier.loop_mapping = loop_mapping
        modifier.layers_vcol_loop_select_src = layers_vcol_loop_select_src
        modifier.layers_vcol_loop_select_dst = layers_vcol_loop_select_dst
        modifier.layers_uv_select_src = layers_uv_select_src
        modifier.layers_uv_select_dst = layers_uv_select_dst
        modifier.island_precision = island_precision
        modifier.use_poly_data = use_poly_data
        modifier.data_types_polys = data_types_polys
        modifier.poly_mapping = poly_mapping
        modifier.use_max_distance = use_max_distance
        modifier.max_distance = max_distance
        modifier.ray_radius = ray_radius

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## Mesh Cache
    @staticmethod
    def mesh_cache(
        obj: bpy.types.Object,
        name: str = "MeshCache",
        cache_format: str = "MDD",
        filepath: str = "",
        factor: float = 1.0,
        deform_mode: str = "OVERWRITE",
        interpolation: str = "LINEAR",
        vertex_group: str = "",
        time_mode: set[str] = set(),
        play_mode: str = "SCENE",
        frame_start: float = 0.0,
        frame_scale: float = 1.0,
        forward_axis: str = "POS_Y",
        up_axis: str = "POS_Z",
        flip_axis: set[str] = set(),
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Mesh Cache modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            cache_format (str, optional): Cache format to use.
            filepath (str, optional): File path to the cache.
            factor (float, optional): Factor to use.
            deform_mode (str, optional): Deform mode.
            interpolation (str, optional): Interpolation mode.
            vertex_group (str, optional): Vertex group.
            time_mode (set[str], optional): Time mode.
            play_mode (str, optional): Play mode.
            frame_start (float, optional): Start frame.
            frame_scale (float, optional): Frame scale.
            forward_axis (str, optional): Forward axis.
            up_axis (str, optional): Up axis.
            flip_axis (set[str], optional): Flip axis.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Mesh Cache modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "MESH_CACHE")

        modifier.cache_format = cache_format
        modifier.filepath = filepath
        modifier.factor = factor
        modifier.deform_mode = deform_mode
        modifier.interpolation = interpolation
        modifier.vertex_group = vertex_group
        modifier.time_mode = time_mode
        modifier.play_mode = play_mode
        modifier.frame_start = frame_start
        modifier.frame_scale = frame_scale
        modifier.forward_axis = forward_axis
        modifier.up_axis = up_axis
        modifier.flip_axis = flip_axis

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## Mesh Sequence Cache
    @staticmethod
    def mesh_sequence_cache(
        obj: bpy.types.Object,
        name: str = "MeshSequenceCache",
        cache_file: bpy.types.CacheFile = None,
        object_path: str = "",
        read_data: set[str] = {"VERT", "POLY", "UV", "COLOR"},
        use_vertex_interpolation: bool = True,
        velocity_scale: float = 1.0,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Mesh Sequence Cache modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            cache_file (bpy.types.CacheFile, optional): The cache file to use.
            object_path (str, optional): The object path.
            read_data (set[str], optional): The data to read.
            use_vertex_interpolation (bool, optional): Use vertex interpolation.
            velocity_scale (float, optional): The velocity scale.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Mesh Sequence Cache modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "MESH_SEQUENCE_CACHE")

        modifier.cache_file = cache_file
        modifier.object_path = object_path
        modifier.read_data = read_data
        modifier.use_vertex_interpolation = use_vertex_interpolation
        modifier.velocity_scale = velocity_scale

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## UV Project Modifier
    @staticmethod
    def uv_project(
        obj: bpy.types.Object,
        name: str = "UVProject",
        uv_layer: str = "",
        aspect_x: float = 1.0,
        aspect_y: float = 1.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        projector_count: int = 1,
        projectors: list[bpy.types.Object] = None,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = True,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add an UV project modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            uv_layer (str, optional): UV layer to use.
            aspect_x (float, optional): Aspect ratio x.
            aspect_y (float, optional): Aspect ratio y.
            scale_x (float, optional): Scale x.
            scale_y (float, optional): Scale y.
            projector_count (int, optional): Number of projectors.
            projectors (list[bpy.types.Object], optional, max 10): Projector objects.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: UV Project modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "UV_PROJECT")

        modifier.uv_layer = uv_layer
        modifier.aspect_x = aspect_x
        modifier.aspect_y = aspect_y
        modifier.scale_x = scale_x
        modifier.scale_y = scale_y

        if projectors:
            modifier.projector_count = len(projectors)
            for projector, obj in zip(modifier.projectors, projectors):
                projector.object = obj

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## UV Warp Modifier
    @staticmethod
    def uv_warp(
        obj: bpy.types.Object,
        name: str = "UVWarp",
        uv_layer: str = "",
        center: tuple[float, float] = (0.5, 0.5),
        axis_u: str = "X",
        axis_v: str = "Y",
        object_from: bpy.types.Object = None,
        object_to: bpy.types.Object = None,
        vertex_group: str = "",
        invert_vertex_group: bool = False,
        offset: tuple[float, float] = (0.0, 0.0),
        scale: tuple[float, float] = (1.0, 1.0),
        rotation: float = 0.0,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = True,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add an UV warp modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            uv_layer (str, optional): UV layer to use.
            center (tuple[float, float], optional): Center of the warp.
            axis_u (str, optional): U axis.
            axis_v (str, optional): V axis.
            object_from (bpy.types.Object, optional): Object to warp from.
            object_to (bpy.types.Object, optional): Object to warp to.
            vertex_group (str, optional): Vertex group.
            invert_vertex_group (bool, optional): Invert the vertex group.
            offset (tuple[float, float], optional): Offset.
            scale (tuple[float, float], optional): Scale.
            rotation (float, optional): Rotation in degrees.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: UV Warp modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "UV_WARP")

        modifier.uv_layer = uv_layer
        modifier.center = center
        modifier.axis_u = axis_u
        modifier.axis_v = axis_v
        modifier.object_from = object_from
        modifier.object_to = object_to
        modifier.vertex_group = vertex_group
        modifier.invert_vertex_group = invert_vertex_group
        modifier.offset = offset
        modifier.scale = scale
        modifier.rotation = radians(rotation)

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## Vertex Weight Edit Modifier
    @staticmethod
    def vertex_weight_edit(
        obj: bpy.types.Object,
        name: str = "VertexWeightEdit",
        vertex_group: str = "",
        default_weight: float = 0.0,
        use_add: bool = False,
        add_threshold: float = 0.01,
        use_remove: bool = False,
        remove_threshold: float = 0.01,
        normalize: bool = False,
        falloff_type: str = "LINEAR",
        invert_falloff: bool = False,
        mask_constant: float = 1.0,
        mask_vertex_group: str = "",
        invert_mask_vertex_group: bool = False,
        mask_texture: bpy.types.Texture = None,
        mask_tex_use_channel: str = "INT",
        mask_tex_mapping: str = "LOCAL",
        mask_tex_map_object: bpy.types.Object = None,
        mask_tex_map_bone: bpy.types.Bone = None,
        mask_tex_uv_layer: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Vertex Weight Edit modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            vertex_group (str, optional): The vertex group.
            default_weight (float, optional): The default weight.
            use_add (bool, optional): Use add.
            add_threshold (float, optional): The add threshold.
            use_remove (bool, optional): Use remove.
            remove_threshold (float, optional): The remove threshold.
            normalize (bool, optional): Normalize.
            falloff_type (str, optional): The falloff type.
            invert_falloff (bool, optional): Invert falloff.
            mask_constant (float, optional): The mask constant.
            mask_vertex_group (str, optional): The mask vertex group.
            invert_mask_vertex_group (bool, optional): Invert mask vertex group.
            mask_texture (bpy.types.Texture, optional): The mask texture.
            mask_tex_use_channel (str, optional): The mask texture use channel.
            mask_tex_mapping (str, optional): The mask texture mapping.
            mask_tex_map_object (bpy.types.Object, optional): The mask texture map object.
            mask_tex_map_bone (bpy.types.Bone, optional): The mask texture map bone.
            mask_tex_uv_layer (str, optional): The mask texture UV layer.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Vertex Weight Edit modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "VERTEX_WEIGHT_EDIT")

        modifier.vertex_group = vertex_group
        modifier.default_weight = default_weight
        modifier.use_add = use_add
        modifier.add_threshold = add_threshold
        modifier.use_remove = use_remove
        modifier.remove_threshold = remove_threshold
        modifier.normalize = normalize
        modifier.falloff_type = falloff_type
        modifier.invert_falloff = invert_falloff
        modifier.mask_constant = mask_constant
        modifier.mask_vertex_group = mask_vertex_group
        modifier.invert_mask_vertex_group = invert_mask_vertex_group
        modifier.mask_texture = mask_texture
        modifier.mask_tex_use_channel = mask_tex_use_channel
        modifier.mask_tex_mapping = mask_tex_mapping
        modifier.mask_tex_map_object = mask_tex_map_object
        modifier.mask_tex_map_bone = mask_tex_map_bone
        modifier.mask_tex_uv_layer = mask_tex_uv_layer

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## Vertex Weight Mix Modifier
    @staticmethod
    def vertex_weight_mix(
        obj: bpy.types.Object,
        name: str = "VertexWeightEdit",
        vertex_group_a: str = "",
        vertex_group_b: str = "",
        default_weight_a: float = 0.0,
        default_weight_b: float = 0.0,
        mix_set: str = "AND",
        mix_mode: str = "REPLACE",
        normalize: bool = False,
        mask_constant: float = 1.0,
        mask_vertex_group: str = "",
        invert_mask_vertex_group: bool = False,
        mask_texture: bpy.types.Texture = None,
        mask_tex_use_channel: str = "INT",
        mask_tex_mapping: str = "LOCAL",
        mask_tex_map_object: bpy.types.Object = None,
        mask_tex_map_bone: bpy.types.Bone = None,
        mask_tex_uv_layer: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Vertex Weight Mix modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            vertex_group_a (str, optional): The vertex group A.
            vertex_group_b (str, optional): The vertex group B.
            default_weight_a (float, optional): The default weight A.
            default_weight_b (float, optional): The default weight B.
            mix_set (str, optional): The mix set.
            mix_mode (str, optional): The mix mode.
            normalize (bool, optional): Normalize.
            mask_constant (float, optional): The mask constant.
            mask_vertex_group (str, optional): The mask vertex group.
            invert_mask_vertex_group (bool, optional): Invert mask vertex group.
            mask_texture (bpy.types.Texture, optional): The mask texture.
            mask_tex_use_channel (str, optional): The mask texture use channel.
            mask_tex_mapping (str, optional): The mask texture mapping.
            mask_tex_map_object (bpy.types.Object, optional): The mask texture map object.
            mask_tex_map_bone (bpy.types.Bone, optional): The mask texture map bone.
            mask_tex_uv_layer (str, optional): The mask texture UV layer.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Vertex Weight Mix modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "VERTEX_WEIGHT_MIX")

        modifier.vertex_group_a = vertex_group_a
        modifier.vertex_group_b = vertex_group_b
        modifier.default_weight_a = default_weight_a
        modifier.default_weight_b = default_weight_b
        modifier.mix_set = mix_set
        modifier.mix_mode = mix_mode
        modifier.normalize = normalize
        modifier.mask_constant = mask_constant
        modifier.mask_vertex_group = mask_vertex_group
        modifier.invert_mask_vertex_group = invert_mask_vertex_group
        modifier.mask_texture = mask_texture
        modifier.mask_tex_use_channel = mask_tex_use_channel
        modifier.mask_tex_mapping = mask_tex_mapping
        modifier.mask_tex_map_object = mask_tex_map_object
        modifier.mask_tex_map_bone = mask_tex_map_bone
        modifier.mask_tex_uv_layer = mask_tex_uv_layer

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    ## Vertex Weight Proximity Modifier
    @staticmethod
    def vertex_weight_proximity(
        obj: bpy.types.Object,
        name: str = "VertexWeightEdit",
        vertex_group: str = "",
        target: bpy.types.Object = None,
        proximty_mode: str = "OBJECT",
        proximty_geometry: set[str] = {"VERTEX"},
        min_dist: float = 0.0,
        max_dist: float = 1.0,
        normalize: bool = False,
        falloff_type: str = "LINEAR",
        invert_falloff: bool = False,
        mask_constant: float = 1.0,
        mask_vertex_group: str = "",
        invert_mask_vertex_group: bool = False,
        mask_texture: bpy.types.Texture = None,
        mask_tex_use_channel: str = "INT",
        mask_tex_mapping: str = "LOCAL",
        mask_tex_map_object: bpy.types.Object = None,
        mask_tex_map_bone: bpy.types.Bone = None,
        mask_tex_uv_layer: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Vertex Weight Proximity modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            vertex_group (str, optional): The vertex group.
            target (bpy.types.Object, optional): The target object.
            proximty_mode (str, optional): The proximity mode.
            proximty_geometry (set[str], optional): The proximity geometry.
            min_dist (float, optional): The minimum distance.
            max_dist (float, optional): The maximum distance.
            normalize (bool, optional): Normalize.
            falloff_type (str, optional): The falloff type.
            invert_falloff (bool, optional): Invert falloff.
            mask_constant (float, optional): The mask constant.
            mask_vertex_group (str, optional): The mask vertex group.
            invert_mask_vertex_group (bool, optional): Invert mask vertex group.
            mask_texture (bpy.types.Texture, optional): The mask texture.
            mask_tex_use_channel (str, optional): The mask texture use channel.
            mask_tex_mapping (str, optional): The mask texture mapping.
            mask_tex_map_object (bpy.types.Object, optional): The mask texture map object.
            mask_tex_map_bone (bpy.types.Bone, optional): The mask texture map bone.
            mask_tex_uv_layer (str, optional): The mask texture UV layer.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Vertex Weight Proximity modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "VERTEX_WEIGHT_PROXIMITY")

        modifier.vertex_group = vertex_group
        modifier.target = target
        modifier.proximty_mode = proximty_mode
        modifier.proximty_geometry = proximty_geometry
        modifier.min_dist = min_dist
        modifier.max_dist = max_dist
        modifier.normalize = normalize
        modifier.falloff_type = falloff_type
        modifier.invert_falloff = invert_falloff
        modifier.mask_constant = mask_constant
        modifier.mask_vertex_group = mask_vertex_group
        modifier.invert_mask_vertex_group = invert_mask_vertex_group
        modifier.mask_texture = mask_texture
        modifier.mask_tex_use_channel = mask_tex_use_channel
        modifier.mask_tex_mapping = mask_tex_mapping
        modifier.mask_tex_map_object = mask_tex_map_object
        modifier.mask_tex_map_bone = mask_tex_map_bone
        modifier.mask_tex_uv_layer = mask_tex_uv_layer

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Generate
    ## Array Modifier
    @staticmethod
    def array(
        obj: bpy.types.Object,
        name: str = "Array",
        fit_type: str = "FIXED_COUNT",
        count: int = 2,
        use_relative_offset: bool = True,
        relative_offset_displace: tuple[float, float, float] = (1.0, 0.0, 0.0),
        use_constant_offset: bool = False,
        constant_offset_displace: tuple[float, float, float] = (1.0, 0.0, 0.0),
        use_object_offset: bool = False,
        offset_object: bpy.types.Object = None,
        use_merge_vertices: bool = False,
        merge_threshold: float = 0.01,
        use_merge_vertices_cap: bool = False,
        offset_u: float = 0.0,
        offset_v: float = 0.0,
        start_cap: bpy.types.Object = None,
        end_cap: bpy.types.Object = None,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = True,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add an Array modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            fit_type (str, optional): Fit type.
            count (int, optional): Number of copies.
            use_relative_offset (bool, optional): Use relative offset.
            relative_offset_displace (tuple[float, float, float], optional): Relative offset.
            use_constant_offset (bool, optional): Use constant offset.
            constant_offset_displace (tuple[float, float, float], optional): Constant offset.
            use_object_offset (bool, optional): Use object offset.
            offset_object (bpy.types.Object, optional): Offset object.
            use_merge_vertices (bool, optional): Use merge vertices.
            merge_threshold (float, optional): Merge threshold.
            use_merge_vertices_cap (bool, optional): Use merge vertices cap.
            offset_u (float, optional): Offset U.
            offset_v (float, optional): Offset V.
            start_cap (bpy.types.Object, optional): Start cap object.
            end_cap (bpy.types.Object, optional): End cap object.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Array modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "ARRAY")

        modifier.fit_type = fit_type
        modifier.count = count
        modifier.use_relative_offset = use_relative_offset
        modifier.relative_offset_displace = relative_offset_displace
        modifier.use_constant_offset = use_constant_offset
        modifier.constant_offset_displace = constant_offset_displace
        modifier.use_object_offset = use_object_offset
        modifier.offset_object = offset_object
        modifier.use_merge_vertices = use_merge_vertices
        modifier.merge_threshold = merge_threshold
        modifier.use_merge_vertices_cap = use_merge_vertices_cap
        modifier.offset_u = offset_u
        modifier.offset_v = offset_v
        modifier.start_cap = start_cap
        modifier.end_cap = end_cap

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Bevel Modifier
    @staticmethod
    def bevel(
        obj: bpy.types.Object,
        name: str = "Bevel",
        affect: str = "EDGES",
        offset_type: str = "OFFSET",
        width: float = 0.1,
        segments: int = 1,
        limit_method: str = "ANGLE",
        angle_limit: float = 30,
        vertex_group: str = "",
        profile_type: str = "SUPERELLIPSE",
        profile: float = 0.5,
        miter_outer: str = "MITER_SHARP",
        miter_inner: str = "MITER_SHARP",
        vmesh_method: str = "ADJ",
        use_clamp_overlap: bool = True,
        loop_slide: bool = True,
        harden_normals: bool = False,
        mark_seam: bool = False,
        mark_sharp: bool = False,
        material: int = -1,
        face_strength_mode: str = "NONE",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Bevel modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            affect (str, optional): The affect type.
            offset_type (str, optional): The offset type.
            width (float, optional): The width of the bevel.
            segments (int, optional): The number of segments.
            limit_method (str, optional): The limit method.
            angle_limit (float, optional): The angle limit for the bevel.
            vertex_group (str, optional): The vertex group.
            profile_type (str, optional): The profile type.
            profile (float, optional): The profile shape.
            miter_outer (str, optional): The outer miter type.
            miter_inner (str, optional): The inner miter type.
            vmesh_method (str, optional): The vertex mesh method.
            use_clamp_overlap (bool, optional): Use clamp overlap.
            loop_slide (bool, optional): Use loop slide.
            harden_normals (bool, optional): Harden normals.
            mark_seam (bool, optional): Mark seam.
            mark_sharp (bool, optional): Mark sharp.
            material (int, optional): The material index.
            face_strength_mode (str, optional): The face strength mode.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Bevel modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "BEVEL")

        modifier.affect = affect
        modifier.offset_type = offset_type
        modifier.width = width
        modifier.segments = segments
        modifier.limit_method = limit_method
        modifier.angle_limit = radians(angle_limit)
        modifier.vertex_group = vertex_group
        modifier.profile_type = profile_type
        modifier.profile = profile
        modifier.miter_outer = miter_outer
        modifier.miter_inner = miter_inner
        modifier.vmesh_method = vmesh_method
        modifier.use_clamp_overlap = use_clamp_overlap
        modifier.loop_slide = loop_slide
        modifier.harden_normals = harden_normals
        modifier.mark_seam = mark_seam
        modifier.mark_sharp = mark_sharp
        modifier.material = material
        modifier.face_strength_mode = face_strength_mode

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Boolean Modifier
    @staticmethod
    def boolean(
        obj: bpy.types.Object,
        object: bpy.types.Object,
        operation: str = "DIFFERENCE",
        solver: str = "EXACT",
        use_self: bool = False,
        use_hole_tolerant: bool = False,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Boolean modifier.

        Args:
            obj (bpy.types.Object): The object to add the modifier to.
            object (bpy.types.Object): The object to use for the boolean operation.
            operation (str, optional): The operation to perform on the object.
                Options are 'DIFFERENCE', 'UNION', 'INTERSECT'. Default is 'DIFFERENCE'.
            solver (str, optional): The solver for the boolean operation.
                Options are 'EXACT', 'FAST'. Default is 'EXACT'.
            use_self (bool, optional): Self Intersection. Default is False.
            use_hole_tolerant (bool, optional): Hole Tolerant. Default is False.
            show_expanded (bool, optional): Show expanded. Default is False.
            show_on_cage (bool, optional): Show on cage. Default is False.
            show_in_editmode (bool, optional): Show in edit mode. Default is False.
            show_viewport (bool, optional): Show in viewport. Default is True.
            show_render (bool, optional): Show in render. Default is True.
            use_pin_to_last (bool, optional): Use pin to last. Default is False.
            check (bool, optional): Check if the modifier exists. Default is True.

        Returns:
            bpy.types.Modifier: Boolean modifier.
        """
        modifier = obj.modifiers.get("Boolean") if check else None
        if not modifier:
            modifier = obj.modifiers.new("Boolean", "BOOLEAN")

        modifier.operation = operation
        modifier.object = object
        modifier.solver = solver
        modifier.use_self = use_self
        modifier.use_hole_tolerant = use_hole_tolerant

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Decimate Modifier
    @staticmethod
    def decimate(
        obj: bpy.types.Object,
        name: str = "Decimate",
        decimate_type: str = "COLLAPSE",
        angle_limit: float = 0.0872665,
        delimit: set[str] = None,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Decimate modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            decimate_type (str, optional): Type of decimation.
            angle_limit (float, optional): Angle limit for decimation.
            delimit (set[str], optional): Delimit set of strings.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Decimate modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "DECIMATE")

        modifier.decimate_type = decimate_type
        modifier.angle_limit = radians(angle_limit)

        if delimit:
            modifier.delimit = delimit

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Geometry Node Modifier
    @staticmethod
    def geometry_node(
        obj: bpy.types.Object,
        name: str = "GeometryNodes",
        node_group: bpy.types.NodeGroup = None,
        bake_target: str = "PACKED",
        bake_directory: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = True,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Geometry Node modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            node_group (bpy.types.NodeGroup, optional): The node group to use.
            bake_target (str, optional): Where to store the baked data.
            bake_directory (str, optional): Location on disk where the bake data is stored.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Geometry Node modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "NODES")

        if node_group:
            modifier.node_group = node_group

        modifier.bake_target = bake_target
        modifier.bake_directory = bake_directory

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Edge Split Modifier
    @staticmethod
    def edge_split(
        obj: bpy.types.Object,
        name: str = "EdgeSplit",
        use_edge_angle: bool = True,
        split_angle: float = 30,
        use_edge_sharp: bool = True,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add an Edge Split modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            use_edge_angle (bool, optional): Split edges with high angle between faces.
            split_angle (float, optional): Angle above which to split edges.
            use_edge_sharp (bool, optional): Split edges that are marked as sharp.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Edge Split modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "EDGE_SPLIT")

        modifier.use_edge_angle = use_edge_angle
        modifier.split_angle = radians(split_angle)
        modifier.use_edge_sharp = use_edge_sharp

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Mirror Modifier
    @staticmethod
    def mirror(
        obj: bpy.types.Object,
        name: str = "Mirror",
        use_axis: tuple[bool, bool, bool] = (True, False, False),
        use_bisect_axis: tuple[bool, bool, bool] = (False, False, False),
        use_bisect_flip_axis: tuple[bool, bool, bool] = (False, False, False),
        mirror_object: bpy.types.Object = None,
        use_clip: bool = False,
        use_mirror_merge: bool = True,
        merge_threshold: float = 0.001,
        bisect_threshold: float = 0.001,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Mirror modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            use_axis (tuple[bool, bool, bool], optional): Axes to mirror.
            use_bisect_axis (tuple[bool, bool, bool], optional): Axes to bisect.
            use_bisect_flip_axis (tuple[bool, bool, bool], optional): Axes to flip bisect.
            mirror_object (bpy.types.Object, optional): Object to use as mirror.
            use_clip (bool, optional): Prevent vertices from going through the mirror during transform.
            use_mirror_merge (bool, optional): Merge vertices in the middle.
            merge_threshold (float, optional): Distance from axis within which vertices are merged.
            bisect_threshold (float, optional): Distance from axis within which vertices are bisected.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Mirror modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "MIRROR")

        modifier.use_axis = use_axis
        modifier.use_bisect_axis = use_bisect_axis
        modifier.use_bisect_flip_axis = use_bisect_flip_axis
        modifier.mirror_object = mirror_object
        modifier.use_clip = use_clip
        modifier.use_mirror_merge = use_mirror_merge
        modifier.merge_threshold = merge_threshold
        modifier.bisect_threshold = bisect_threshold

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Remesh Modifier
    @staticmethod
    def remesh(
        obj: bpy.types.Object,
        name: str = "Remesh",
        mode: str = "VOXEL",
        octree_depth: int = 4,
        scale: float = 0.9,
        sharpness: float = 1.0,
        use_remove_disconnected: bool = True,
        threshold: float = 1.0,
        voxel_size: float = 0.1,
        adaptivity: float = 0.0,
        use_smooth_shading=True,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Remesh modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            mode (str, optional): Mode to use.
            octree_depth (int, optional): Octree depth.
            scale (float, optional): Scale.
            sharpness (float, optional): Sharpness.
            use_remove_disconnected (bool, optional): Remove disconnected.
            threshold (float, optional): Threshold.
            voxel_size (float, optional): Voxel size.
            adaptivity (float, optional): Adaptivity.
            use_smooth_shading (bool, optional): Smooth shading.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Remesh modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "REMESH")

        modifier.mode = mode
        modifier.octree_depth = octree_depth
        modifier.scale = scale
        modifier.sharpness = sharpness
        modifier.use_remove_disconnected = use_remove_disconnected
        modifier.threshold = threshold
        modifier.voxel_size = voxel_size
        modifier.adaptivity = adaptivity
        modifier.use_smooth_shade = use_smooth_shading

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Screw Modifier
    @staticmethod
    def screw(
        obj: bpy.types.Object,
        name: str = "Screw",
        angle: float = 360,
        screw_offset: float = 0.0,
        iterations: int = 1,
        axis: str = "Z",
        object: bpy.types.Object = None,
        use_object_screw_offset: bool = False,
        steps: int = 16,
        render_steps: int = 16,
        use_merge_vertices: bool = False,
        merge_threshold: float = 0.01,
        use_stretch_u: bool = False,
        use_stretch_v: bool = False,
        use_smooth_shade: bool = True,
        use_normal_calculate: bool = False,
        use_normal_flip: bool = False,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = True,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Screw modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            angle (float, optional): The angle to screw.
            screw_offset (float, optional): The screw offset.
            iterations (int, optional): The number of iterations.
            axis (str, optional): The axis to screw.
            object (bpy.types.Object, optional): The object to use for the screw.
            use_object_screw_offset (bool, optional): Use object screw offset.
            steps (int, optional): The number of steps.
            render_steps (int, optional): The number of render steps.
            use_merge_vertices (bool, optional): Merge vertices.
            merge_threshold (float, optional): The merge threshold.
            use_stretch_u (bool, optional): Stretch U.
            use_stretch_v (bool, optional): Stretch V.
            use_smooth_shade (bool, optional): Smooth shade.
            use_normal_calculate (bool, optional): Calculate normals.
            use_normal_flip (bool, optional): Flip normals.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Screw modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SCREW")

        modifier.angle = radians(angle)
        modifier.screw_offset = screw_offset
        modifier.iterations = iterations
        modifier.axis = axis
        modifier.object = object
        modifier.use_object_screw_offset = use_object_screw_offset
        modifier.steps = steps
        modifier.render_steps = render_steps
        modifier.use_merge_vertices = use_merge_vertices
        modifier.merge_threshold = merge_threshold
        modifier.use_stretch_u = use_stretch_u
        modifier.use_stretch_v = use_stretch_v
        modifier.use_smooth_shade = use_smooth_shade
        modifier.use_normal_calculate = use_normal_calculate
        modifier.use_normal_flip = use_normal_flip

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Skin Modifier
    @staticmethod
    def skin(
        obj: bpy.types.Object,
        name: str = "Skin",
        branch_smoothing: float = 0.0,
        use_x_symmetry: bool = True,
        use_y_symmetry: bool = False,
        use_z_symmetry: bool = False,
        use_smooth_shade: bool = False,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Skin modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            branch_smoothing (float, optional): Branch smoothing.
            use_x_symmetry (bool, optional): Use X symmetry.
            use_y_symmetry (bool, optional): Use Y symmetry.
            use_z_symmetry (bool, optional): Use Z symmetry.
            use_smooth_shade (bool, optional): Use smooth shading.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Skin modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SKIN")

        modifier.branch_smoothing = branch_smoothing
        modifier.use_x_symmetry = use_x_symmetry
        modifier.use_y_symmetry = use_y_symmetry
        modifier.use_z_symmetry = use_z_symmetry
        modifier.use_smooth_shade = use_smooth_shade

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Solidify Modifier
    @staticmethod
    def solidify(
        obj: bpy.types.Object,
        name: str = "Solidify",
        solidify_mode: str = "EXTRUDE",
        nonmanifold_thickness_mode: str = "CONSTRAINTS",
        nonmanifold_boundary_mode: str = "NONE",
        thickness: float = 0.01,
        offset: float = -1.0,
        nonmanifold_merge_threshold: float = 0.0001,
        use_even_offset: bool = False,
        use_rim: bool = True,
        use_rim_only: bool = False,
        vertex_group: str = "",
        invert_vertex_group: bool = False,
        thickness_vertex_group: float = 0.0,
        use_flat_faces: bool = False,
        use_flip_normals: bool = False,
        use_quality_normals: bool = False,
        material_offset: int = 0,
        material_offset_rim: int = 0,
        edge_crease_inner: float = 0.0,
        edge_crease_outer: float = 0.0,
        edge_crease_rim: float = 0.0,
        bevel_convex: float = 0.0,
        thickness_clamp: float = 0.0,
        use_thickness_angle_clamp: bool = False,
        shell_vertex_group: str = "",
        rim_vertex_group: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Solidify modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            solidify_mode (str, optional): The solidify mode.
            nonmanifold_thickness_mode (str, optional): The nonmanifold thickness mode.
            nonmanifold_boundary_mode (str, optional): The nonmanifold boundary mode.
            thickness (float, optional): The thickness of the solidify.
            offset (float, optional): The offset of the solidify.
            nonmanifold_merge_threshold (float, optional): The nonmanifold merge threshold.
            use_even_offset (bool, optional): Use even offset.
            use_rim (bool, optional): Use rim.
            use_rim_only (bool, optional): Use rim only.
            vertex_group (str, optional): The vertex group.
            invert_vertex_group (bool, optional): Invert vertex group.
            thickness_vertex_group (float, optional): The thickness vertex group.
            use_flat_faces (bool, optional): Use flat faces.
            use_flip_normals (bool, optional): Flip normals.
            use_quality_normals (bool, optional): Use quality normals.
            material_offset (int, optional): The material offset.
            material_offset_rim (int, optional): The material offset rim.
            edge_crease_inner (float, optional): The edge crease inner.
            edge_crease_outer (float, optional): The edge crease outer.
            edge_crease_rim (float, optional): The edge crease rim.
            bevel_convex (float, optional): The bevel convex.
            thickness_clamp (float, optional): The thickness clamp.
            use_thickness_angle_clamp (bool, optional): Use thickness angle clamp.
            shell_vertex_group (str, optional): The shell vertex group.
            rim_vertex_group (str, optional): The rim vertex group.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Solidify modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SOLIDIFY")

        modifier.solidify_mode = solidify_mode
        modifier.nonmanifold_thickness_mode = nonmanifold_thickness_mode
        modifier.nonmanifold_boundary_mode = nonmanifold_boundary_mode
        modifier.thickness = thickness
        modifier.offset = offset
        modifier.nonmanifold_merge_threshold = nonmanifold_merge_threshold
        modifier.use_even_offset = use_even_offset
        modifier.use_rim = use_rim
        modifier.use_rim_only = use_rim_only
        modifier.vertex_group = vertex_group
        modifier.invert_vertex_group = invert_vertex_group
        modifier.thickness_vertex_group = thickness_vertex_group
        modifier.use_flat_faces = use_flat_faces
        modifier.use_flip_normals = use_flip_normals
        modifier.use_quality_normals = use_quality_normals
        modifier.material_offset = material_offset
        modifier.material_offset_rim = material_offset_rim
        modifier.edge_crease_inner = edge_crease_inner
        modifier.edge_crease_outer = edge_crease_outer
        modifier.edge_crease_rim = edge_crease_rim
        modifier.bevel_convex = bevel_convex
        modifier.thickness_clamp = thickness_clamp
        modifier.use_thickness_angle_clamp = use_thickness_angle_clamp
        modifier.shell_vertex_group = shell_vertex_group
        modifier.rim_vertex_group = rim_vertex_group

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Subsurf Modifier
    @staticmethod
    def subsurf(
        obj: bpy.types.Object,
        name: str = "Subdivision",
        subdivision_type: str = "CATMULL_CLARK",
        levels: int = 1,
        render_levels: int = 2,
        show_only_control_edges: bool = True,
        use_limit_surface: bool = True,
        quality: int = 3,
        uv_smooth: str = "PRESERVE_BOUNDARY",
        boundary_smooth: str = "ALL",
        use_crease: bool = True,
        use_custom_normals: bool = False,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Subsurf modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            subdivision_type (str, optional): Subdivision type to use for the modifier.
            levels (int, optional): Levels of subdivision.
            render_levels (int, optional): Levels of subdivision for rendering.
            show_only_control_edges (bool, optional): Show only control edges.
            use_limit_surface (bool, optional): Use limit surface.
            quality (int, optional): Quality of the subdivision.
            uv_smooth (str, optional): UV smoothing method.
            boundary_smooth (str, optional): Boundary smoothing method.
            use_crease (bool, optional): Use crease.
            use_custom_normals (bool, optional): Use custom normals.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Subsurf modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SUBSURF")

        modifier.subdivision_type = subdivision_type
        modifier.levels = levels
        modifier.render_levels = render_levels
        modifier.show_only_control_edges = show_only_control_edges
        modifier.use_limit_surface = use_limit_surface
        modifier.quality = quality
        modifier.uv_smooth = uv_smooth
        modifier.boundary_smooth = boundary_smooth
        modifier.use_crease = use_crease
        modifier.use_custom_normals = use_custom_normals

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Triangulate Modifier
    @staticmethod
    def triangulate(
        obj: bpy.types.Object,
        name: str = "Triangulate",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Triangulate modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Triangulate modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "TRIANGULATE")

        modifier.min_vertices = 5

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Weld Modifier
    @staticmethod
    def weld(
        obj: bpy.types.Object,
        name: str = "Weld",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Weld modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Weld modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "WELD")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Wireframe Modifier
    @staticmethod
    def wireframe(
        obj: bpy.types.Object,
        name: str = "Wireframe",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Wireframe modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Wireframe modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "WIREFRAME")
            modifier.use_boundary = True

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Weighted Normal Modifier
    @staticmethod
    def weighted_normal(
        obj: bpy.types.Object,
        name: str = "WeightedNormal",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Weighted Normal modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Weighted Normal modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "WEIGHTED_NORMAL")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Armature Modifier
    @staticmethod
    def armature(
        obj: bpy.types.Object,
        name: str = "Armature",
        object: bpy.types.Object = None,
        vertex_group: str = "",
        invert_vertex_group: bool = False,
        use_deform_preserve_volume: bool = False,
        use_multi_modifier: bool = False,
        use_vertex_groups: bool = True,
        use_bone_envelopes: bool = False,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add an Armature modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            object (bpy.types.Object, optional): Armature object to use.
            vertex_group (str, optional): Vertex group to use.
            invert_vertex_group (bool, optional): Invert vertex group.
            use_deform_preserve_volume (bool, optional): Preserve volume during deformation.
            use_multi_modifier (bool, optional): Use multiple modifiers.
            use_vertex_groups (bool, optional): Use vertex groups.
            use_bone_envelopes (bool, optional): Use bone envelopes.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Armature modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "ARMATURE")

        modifier.object = object
        modifier.vertex_group = vertex_group
        modifier.invert_vertex_group = invert_vertex_group
        modifier.use_deform_preserve_volume = use_deform_preserve_volume
        modifier.use_multi_modifier = use_multi_modifier
        modifier.use_vertex_groups = use_vertex_groups
        modifier.use_bone_envelopes = use_bone_envelopes

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Cast Modifier
    @staticmethod
    def cast(
        obj: bpy.types.Object,
        name: str = "Cast",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Cast modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Cast modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "CAST")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Curve Modifier
    @staticmethod
    def curve(
        obj: bpy.types.Object,
        name: str = "Curve",
        object: bpy.types.Curve = None,
        deform_axis: str = "POS_X",
        vertex_group: str = "",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Curve modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            object (bpy.types.Curve, optional): Curve object to deform with.
            deform_axis (str, optional): The axis that the curve deforms along.
            vertex_group (str, optional): Name of Vertex Group which determines influence of modifier per point.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Curve modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "CURVE")

        modifier.object = object
        modifier.deform_axis = deform_axis
        modifier.vertex_group = vertex_group

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Displace Modifier
    @staticmethod
    def displace(
        obj: bpy.types.Object,
        name: str = "Displace",
        strength=1.0,
        mid_level=0.5,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Displace modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            strength (float, optional): Strength of the modifier.
            mid_level (float, optional): Mid-level of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Displace modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "DISPLACE")

        modifier.strength = strength
        modifier.mid_level = mid_level

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Lattice Modifier
    @staticmethod
    def lattice(
        obj: bpy.types.Object,
        name: str = "Lattice",
        object: bpy.types.Object = None,
        vertex_group: str = "",
        invert_vertex_group: bool = False,
        strength: float = 1.0,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Lattice modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            object (bpy.types.Object, optional): Lattice object to deform with.
            vertex_group (str, optional): Name of Vertex Group which determines influence of modifier per point.
            invert_vertex_group (bool, optional): Invert the vertex group.
            strength (float, optional): The strength of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Lattice modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "LATTICE")

        modifier.object = object
        modifier.vertex_group = vertex_group
        modifier.invert_vertex_group = invert_vertex_group
        modifier.strength = strength

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Shrinkwrap Modifier
    @staticmethod
    def shrinkwrap(
        obj: bpy.types.Object,
        name: str = "Shrinkwrap",
        target: bpy.types.Object = None,
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Shrinkwrap modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            target (bpy.types.Object, optional): The object to use as the target.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Shrinkwrap modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SHRINKWRAP")

        modifier.wrap_method = "PROJECT"
        modifier.use_negative_direction = True
        modifier.use_invert_cull = True
        modifier.target = target

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Simple Deform Modifier
    @staticmethod
    def deform(
        obj: bpy.types.Object,
        name: str = "SimpleDeform",
        deform_method="TWIST",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Simple Deform modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            deform_method (str, optional): The deform method to use.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Simple Deform modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SIMPLE_DEFORM")
            modifier.deform_method = deform_method
            modifier.angle = radians(45)
            modifier.deform_axis = "X"

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Smooth Modifier
    @staticmethod
    def smooth(
        obj: bpy.types.Object,
        name: str = "Smooth",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Smooth modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Smooth modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "SMOOTH")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Smooth Corrective Modifier
    @staticmethod
    def smooth_corrective(
        obj: bpy.types.Object,
        name: str = "CorrectiveSmooth",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Smooth Corrective modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Smooth Corrective modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "CORRECTIVE_SMOOTH")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Smooth Laplacian Modifier
    @staticmethod
    def smooth_laplacian(
        obj: bpy.types.Object,
        name: str = "LaplacianSmooth",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Smooth Laplacian modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Smooth Laplacian modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "LAPLACIANSMOOTH")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Wave Modifier
    @staticmethod
    def wave(
        obj: bpy.types.Object,
        name: str = "Wave",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Wave modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Wave modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "WAVE")

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    # Cloth Modifier
    @staticmethod
    def cloth(
        obj: bpy.types.Object,
        name: str = "Cloth",
        show_expanded: bool = True,
        show_on_cage: bool = False,
        show_in_editmode: bool = False,
        show_viewport: bool = True,
        show_render: bool = True,
        use_pin_to_last: bool = False,
        check: bool = True,
    ) -> bpy.types.Modifier:
        """Add a Cloth modifier.

        Args:
            obj (bpy.types.Object): Object to add the modifier to.
            name (str, optional): Name of the modifier.
            show_expanded (bool, optional): Show expanded.
            show_on_cage (bool, optional): Show on cage.
            show_in_editmode (bool, optional): Show in edit mode.
            show_viewport (bool, optional): Show in viewport.
            show_render (bool, optional): Show in render.
            use_pin_to_last (bool, optional): Use pin to last.
            check (bool, optional): Check if the modifier exists.

        Returns:
            bpy.types.Modifier: Cloth modifier.
        """
        modifier = obj.modifiers.get(name) if check else None
        if not modifier:
            modifier = obj.modifiers.new(name, "CLOTH")
            modifier.settings.use_pressure = True
            modifier.settings.quality = 5
            modifier.settings.time_scale = 0.5
            modifier.settings.uniform_pressure_force = 15
            modifier.settings.shrink_min = -0.3
            Mesh.create_vgroup(obj, modifier)

        Modifier._set_common_modifier_properties(
            modifier, show_expanded, show_on_cage, show_in_editmode, show_viewport, show_render, use_pin_to_last
        )
        return modifier

    @staticmethod
    def get_modifiers(obj: bpy.types.Object, type: str = None) -> List[bpy.types.Modifier]:
        """Get the modifiers.

        Args:
            obj (bpy.types.Object): The object to get modifiers from.
            type (str, optional): The type of modifier to get.

        Returns:
            list: Modifiers.
        """
        return [modifier for modifier in obj.modifiers if type is None or modifier.type == type]

    @staticmethod
    def get_active(obj: bpy.types.Object, type: str, show_expanded: bool = True) -> bpy.types.Modifier:
        """Get the active modifier.

        Args:
            obj (bpy.types.Object): The object to get the modifier from.
            type (str): The type of modifier to get.
            show_expanded (bool, optional): Show expanded.

        Returns:
            bpy.types.Modifier: The active modifier.
        """
        if obj.modifiers.active.type == type:
            modifier = obj.modifiers.active
        else:
            modifier = Modifier.get_modifiers(obj, type)[-1]
            modifier.is_active = True

        modifier.show_expanded = show_expanded
        return modifier

    @staticmethod
    def show(obj: bpy.types.Object, modifier: bpy.types.Modifier, toggle: str):
        """Show the modifier.

        Args:
            obj (bpy.types.Object): The object to get the modifier from.
            modifier (bpy.types.Modifier): The modifier to show.
            toggle (str): The state to set the modifier to. Options are 'EXPANDED', 'ON_CAGE', 'IN_EDITMODE', 'VIEWPORT', 'RENDER'.
        """
        toggle_map = {
            "EXPANDED": "show_expanded",
            "ON_CAGE": "show_on_cage",
            "IN_EDITMODE": "show_in_editmode",
            "VIEWPORT": "show_viewport",
            "RENDER": "show_render",
        }
        if toggle in toggle_map:
            attr = toggle_map[toggle]
            setattr(obj.modifiers[modifier.name], attr, not getattr(obj.modifiers[modifier.name], attr))

    @staticmethod
    def switch(obj: bpy.types.Object, modifier: bpy.types.Modifier, select: str) -> bpy.types.Modifier:
        """Switch the modifier.

        Args:
            obj (bpy.types.Object): The object to get modifier from.
            modifier (bpy.types.Modifier): The modifier to switch.
            select (str): The state to switch the modifier to. Options are 'PREV' or 'NEXT'.

        Returns:
            bpy.types.Modifier: The modifier that was switched to.
        """
        modifiers = Modifier.get_modifiers(obj, modifier.type)
        index = modifiers.index(modifier)
        modifier = modifiers[index - 1] if select == "PREV" else modifiers[(index + 1) % len(modifiers)]
        modifier.is_active = True
        return modifier

    @staticmethod
    def move(modifier: bpy.types.Modifier, move: str):
        """Move the modifier in the modifier stack.

        Args:
            modifier (bpy.types.Modifier): The modifier to move.
            move (str): The direction to move the modifier. Options are 'UP' or 'DOWN'.
        """
        (
            bpy.ops.object.modifier_move_up(modifier=modifier.name)
            if move == "UP"
            else bpy.ops.object.modifier_move_down(modifier=modifier.name)
        )

    @staticmethod
    def apply(modifier: bpy.types.Modifier):
        """Apply the modifier.

        Args:
            modifier (bpy.types.Modifier): The modifier to apply.
        """
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    @staticmethod
    def copy(modifier: bpy.types.Modifier):
        """Copy the modifier.

        Args:
            modifier (bpy.types.Modifier): The modifier to copy.
        """
        bpy.ops.object.modifier_copy(modifier=modifier.name)

    @staticmethod
    def remove(obj: bpy.types.Object, modifier: bpy.types.Modifier):
        """Remove the modifier.

        Args:
            obj (bpy.types.Object): The object to remove the modifier from.
            modifier (bpy.types.Modifier): The modifier to remove.
        """
        obj.modifiers.remove(modifier)

    @staticmethod
    def removes(obj: bpy.types.Object):
        """Remove all modifiers.

        Args:
            obj (bpy.types.Object): The object to remove the modifiers from.
        """
        for modifier in obj.modifiers:
            obj.modifiers.remove(modifier)

    # TODO: work in progress...
    @staticmethod
    def sort_mod(obj: bpy.types.Object):
        modifiers = obj.modifiers
        subsurf_mods = boolean_mods = bevel_mods = mirror_mods = 0
        for mod in modifiers:
            if mod.type == "SUBSURF":
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=subsurf_mods)
                subsurf_mods += 1
            elif mod.type == "BOOLEAN":
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=subsurf_mods + boolean_mods)
                boolean_mods += 1
            elif mod.type == "BEVEL":
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=subsurf_mods + boolean_mods + bevel_mods)
                bevel_mods += 1
            elif mod.type == "MIRROR":
                bpy.ops.object.modifier_move_to_index(
                    modifier=mod.name,
                    index=subsurf_mods + boolean_mods + bevel_mods + mirror_mods,
                )
                mirror_mods += 1
            elif mod.type == "WEIGHTED_NORMAL":
                bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=len(modifiers) - 1)
