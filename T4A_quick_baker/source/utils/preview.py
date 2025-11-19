from ...qbpy import ShaderNode

LOCATION = (1000000000, 0)


class QBAKER_map_preview:
    def disable_other_previews(self, context, current_map):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        maps = baker.maps if baker.use_map_global else bake_group.maps

        if context.space_data.shading.type not in {"MATERIAL", "RENDERED"}:
            context.space_data.shading.type = "MATERIAL"

        for map in maps:
            if hasattr(map, "occlusion") and map.occlusion != current_map:
                map.occlusion.use_preview = False
            if hasattr(map, "cavity") and map.cavity != current_map:
                map.cavity.use_preview = False
            if hasattr(map, "curvature") and map.curvature != current_map:
                map.curvature.use_preview = False
            if hasattr(map, "edge") and map.edge != current_map:
                map.edge.use_preview = False
            if hasattr(map, "gradient") and map.gradient != current_map:
                map.gradient.use_preview = False
            if hasattr(map, "height") and map.height != current_map:
                map.height.use_preview = False
            if hasattr(map, "thickness") and map.thickness != current_map:
                map.thickness.use_preview = False
            if hasattr(map, "toon_shadow") and map.toon_shadow != current_map:
                map.toon_shadow.use_preview = False
            if hasattr(map, "xyz") and map.xyz != current_map:
                map.xyz.use_preview = False

    def setup_nodes(self, context, node_setup_func):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        maps = baker.maps if baker.use_map_global else bake_group.maps

        for item in bake_group.objects:
            if maps and item.object.material_slots:
                for slot in item.object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        self.node_tree = slot.material.node_tree
                        node_setup_func(context)

    def occlusion_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_occlusion_nodes(context):
            ao_node = ShaderNode.ambient_occlusion(
                self.node_tree,
                name="QB_AMBIENT_OCCLUSION",
                samples=128,
                only_local=self.only_local,
                distance=self.distance,
                position=LOCATION,
            )
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = not self.invert_ao
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(ao_node.outputs["AO"], invert_node.inputs["Color"])
            self.node_tree.links.new(invert_node.outputs["Color"], emission_node.inputs["Color"])
            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_occlusion_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def cavity_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_cavity_nodes(context):
            geometry_node = ShaderNode.geometry(self.node_tree, name="QB_GEOMETRY", position=LOCATION)
            c_ramp_node = ShaderNode.color_ramp(self.node_tree, name="QB_COLOR_RAMP", position=LOCATION)
            c_ramp_node.color_ramp.elements[0].position = 0.4
            c_ramp_node.color_ramp.elements[1].position = 0.5
            math_node = ShaderNode.math(
                self.node_tree, name="QB_MATH", operation="POWER", input_1=self.power, position=LOCATION
            )
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = not self.invert_cavity
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(geometry_node.outputs["Pointiness"], c_ramp_node.inputs["Fac"])
            self.node_tree.links.new(c_ramp_node.outputs["Color"], math_node.inputs[0])
            self.node_tree.links.new(math_node.outputs["Value"], invert_node.inputs["Color"])
            self.node_tree.links.new(invert_node.outputs["Color"], emission_node.inputs["Color"])
            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_cavity_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def curvature_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_curvature_nodes(context):
            geometry_node = ShaderNode.geometry(self.node_tree, name="QB_GEOMETRY", position=LOCATION)
            c_ramp_node = ShaderNode.color_ramp(self.node_tree, name="QB_COLOR_RAMP", position=LOCATION)
            c_ramp_node.color_ramp.elements[0].position = 0.45
            c_ramp_node.color_ramp.elements[1].position = 0.55
            math_node = ShaderNode.math(
                self.node_tree, name="QB_MATH", operation="POWER", input_1=self.power, position=LOCATION
            )
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = not self.invert_curvature
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(geometry_node.outputs["Pointiness"], c_ramp_node.inputs["Fac"])
            self.node_tree.links.new(c_ramp_node.outputs["Color"], math_node.inputs[0])
            self.node_tree.links.new(math_node.outputs["Value"], invert_node.inputs["Color"])
            self.node_tree.links.new(invert_node.outputs["Color"], emission_node.inputs["Color"])
            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_curvature_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def edge_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_edge_nodes(context):
            bevel_node = ShaderNode.bevel(
                self.node_tree, name="QB_EDGE_BEVEL", samples=128, radius=self.radius, position=LOCATION
            )
            geometry_node = ShaderNode.geometry(self.node_tree, name="QB_GEOMETRY", position=LOCATION)
            vector_math_node = ShaderNode.vector_math(
                self.node_tree, name="QB_DOT_PRODUCT", operation="DOT_PRODUCT", position=LOCATION
            )
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = self.invert_edge
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(bevel_node.outputs["Normal"], vector_math_node.inputs[0])
            self.node_tree.links.new(geometry_node.outputs["Normal"], vector_math_node.inputs[1])
            self.node_tree.links.new(vector_math_node.outputs["Value"], invert_node.inputs["Color"])
            self.node_tree.links.new(invert_node.outputs["Color"], emission_node.inputs["Color"])
            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_edge_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def gradient_preview(self, context):
        if self.direction == "X":
            self.suffix = "Gradient_X"
        elif self.direction == "XYZ":
            self.suffix = "Gradient_XYZ"
        elif self.direction == "Y":
            self.suffix = "Gradient_Y"
        elif self.direction == "Z":
            self.suffix = "Gradient_Z"

        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_gradient_nodes(context):
            texture_coordinate_node = ShaderNode.texture_coordinate(
                self.node_tree, name="QB_TEXTURE_COORDINATE", position=LOCATION
            )
            separate_xyz_node = ShaderNode.separate_xyz(self.node_tree, name="QB_SEPARATE_XYZ", position=LOCATION)
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = not self.invert_gradient
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            if self.direction == "XYZ":
                self.node_tree.links.new(texture_coordinate_node.outputs["Generated"], invert_node.inputs["Color"])
            else:
                self.node_tree.links.new(
                    texture_coordinate_node.outputs["Generated"], separate_xyz_node.inputs["Vector"]
                )
                self.node_tree.links.new(separate_xyz_node.outputs[self.direction], invert_node.inputs["Color"])

            self.node_tree.links.new(invert_node.outputs["Color"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_gradient_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def heightmap_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_heightmap_nodes(context):
            if self.type == "DISPLACEMENT":
                texture_coordinate_node = ShaderNode.texture_coordinate(
                    self.node_tree, name="QB_TEXTURE_COORDINATE", position=LOCATION
                )
                separate_xyz_node = ShaderNode.separate_xyz(self.node_tree, name="QB_SEPARATE_XYZ", position=LOCATION)
                invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
                invert_node.mute = not self.invert_height
                material_output_node = ShaderNode.material_output(
                    self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
                )
                self.node_tree.nodes.active = material_output_node

                self.node_tree.links.new(
                    texture_coordinate_node.outputs["Generated"], separate_xyz_node.inputs["Vector"]
                )
                self.node_tree.links.new(separate_xyz_node.outputs["Z"], invert_node.inputs["Color"])
                self.node_tree.links.new(invert_node.outputs["Color"], material_output_node.inputs["Surface"])

            elif self.type == "NORMAL":
                texture_coordinate_node = ShaderNode.texture_coordinate(
                    self.node_tree, name="QB_TEXTURE_COORDINATE", position=LOCATION
                )
                vector_transform_node = ShaderNode.vector_transform(
                    self.node_tree,
                    name="QB_VECTOR_TRANSFORM",
                    vector_type="NORMAL",
                    convert_from="OBJECT",
                    convert_to="CAMERA",
                    position=LOCATION,
                )
                mapping_node = ShaderNode.mapping(
                    self.node_tree,
                    name="QB_MAPPING",
                    vector_type="TEXTURE",
                    location=(-1, -1, 1),
                    scale=(2, 2, -2),
                    position=LOCATION,
                )
                separate_xyz_node = ShaderNode.separate_xyz(self.node_tree, name="QB_SEPARATE_XYZ", position=LOCATION)
                invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
                invert_node.mute = not self.invert_height
                combine_xyz_node = ShaderNode.combine_xyz(self.node_tree, name="QB_COMBINE_XYZ", position=LOCATION)
                gamma_node = ShaderNode.gamma(self.node_tree, name="QB_GAMMA", gamma=2.2, position=LOCATION)
                material_output_node = ShaderNode.material_output(
                    self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
                )
                self.node_tree.nodes.active = material_output_node

                self.node_tree.links.new(
                    texture_coordinate_node.outputs["Normal"], vector_transform_node.inputs["Vector"]
                )
                self.node_tree.links.new(vector_transform_node.outputs["Vector"], mapping_node.inputs["Vector"])
                self.node_tree.links.new(mapping_node.outputs["Vector"], separate_xyz_node.inputs["Vector"])
                self.node_tree.links.new(separate_xyz_node.outputs["X"], combine_xyz_node.inputs[0])
                self.node_tree.links.new(separate_xyz_node.outputs["Y"], invert_node.inputs["Color"])
                self.node_tree.links.new(invert_node.outputs["Color"], combine_xyz_node.inputs[1])
                self.node_tree.links.new(separate_xyz_node.outputs["Z"], combine_xyz_node.inputs[2])
                self.node_tree.links.new(combine_xyz_node.outputs["Vector"], gamma_node.inputs["Color"])
                self.node_tree.links.new(gamma_node.outputs["Color"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_heightmap_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def thickness_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_thickness_nodes(context):
            ao_node = ShaderNode.ambient_occlusion(
                self.node_tree,
                name="QB_AMBIENT_OCCLUSION",
                samples=128,
                inside=True,
                only_local=True,
                distance=self.distance,
                position=LOCATION,
            )
            invert_node = ShaderNode.invert(self.node_tree, name="QB_INVERT", position=LOCATION)
            invert_node.mute = not self.invert_thickness
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(ao_node.outputs["AO"], invert_node.inputs["Color"])
            self.node_tree.links.new(invert_node.outputs["Color"], emission_node.inputs["Color"])
            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_thickness_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def toon_shadow_preview(self, context):
        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_toon_shadow_nodes(context):
            toon_bsdf_node = ShaderNode.toon_bsdf(
                self.node_tree,
                name="QB_TOON_BSDF",
                component="DIFFUSE",
                color=(1, 1, 1, 1),
                size=self.size,
                smooth=self.smooth,
                position=LOCATION,
            )
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(toon_bsdf_node.outputs["BSDF"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_toon_shadow_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def xyz_preview(self, context):
        if self.direction == "X":
            self.suffix = "X"
        elif self.direction == "XYZ":
            self.suffix = "XYZ"
        elif self.direction == "Y":
            self.suffix = "Y"
        elif self.direction == "Z":
            self.suffix = "Z"

        if self.use_preview:
            self.disable_other_previews(context, self)

        def setup_xyz_nodes(context):
            texture_coordinate_node = ShaderNode.texture_coordinate(
                self.node_tree, name="QB_TEXTURE_COORDINATE", position=LOCATION
            )
            separate_xyz_node = ShaderNode.separate_xyz(self.node_tree, name="QB_SEPARATE_XYZ", position=LOCATION)
            combine_xyz_node = ShaderNode.combine_xyz(self.node_tree, name="QB_COMBINE_XYZ", position=LOCATION)
            gradient_texture_node = ShaderNode.gradient_texture(self.node_tree, name="QB_TEXTURE", position=LOCATION)
            map_range_node = ShaderNode.map_range(
                self.node_tree, name="QB_MAP_RANGE", type="SMOOTHERSTEP", position=LOCATION
            )
            vector_math_node = ShaderNode.vector_math(
                self.node_tree, name="QB_VECTOR_MATH", operation="MULTIPLY", input_1=(-1, -1, -1), position=LOCATION
            )
            vector_math_node.mute = not self.invert_xyz
            emission_node = ShaderNode.emission(self.node_tree, name="QB_EMISSION", position=LOCATION)
            material_output_node = ShaderNode.material_output(
                self.node_tree, name="QB_MATERIAL_OUTPUT", target="ALL", position=LOCATION
            )
            self.node_tree.nodes.active = material_output_node

            self.node_tree.links.new(texture_coordinate_node.outputs["Normal"], separate_xyz_node.inputs["Vector"])

            if self.direction == "XYZ":
                self.node_tree.links.new(separate_xyz_node.outputs["X"], combine_xyz_node.inputs["X"])
                self.node_tree.links.new(separate_xyz_node.outputs["Y"], combine_xyz_node.inputs["Y"])
                self.node_tree.links.new(separate_xyz_node.outputs["Z"], combine_xyz_node.inputs["Z"])
                self.node_tree.links.new(combine_xyz_node.outputs["Vector"], vector_math_node.inputs[0])
                self.node_tree.links.new(vector_math_node.outputs["Vector"], emission_node.inputs["Color"])
            else:
                self.node_tree.links.new(separate_xyz_node.outputs[self.direction], vector_math_node.inputs[0])
                self.node_tree.links.new(vector_math_node.outputs["Vector"], gradient_texture_node.inputs["Vector"])
                self.node_tree.links.new(gradient_texture_node.outputs["Color"], map_range_node.inputs["Value"])
                self.node_tree.links.new(map_range_node.outputs["Result"], emission_node.inputs["Color"])

            self.node_tree.links.new(emission_node.outputs["Emission"], material_output_node.inputs["Surface"])

        self.setup_nodes(context, setup_xyz_nodes)

        if not self.use_preview:
            self.remove_nodes(context)

    def remove_nodes(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        maps = baker.maps if baker.use_map_global else bake_group.maps

        for item in bake_group.objects:
            if maps and item.object.material_slots:
                for slot in item.object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        self.node_tree = slot.material.node_tree
                        for node in self.node_tree.nodes:
                            if node.name.split("_")[0] == "QB":
                                self.node_tree.nodes.remove(node)
