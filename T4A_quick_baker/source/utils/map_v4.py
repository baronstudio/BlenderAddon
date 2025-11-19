import random

import bpy

from ...qbpy import ShaderNode


class Map:
    NODE_DATA = {}

    def prepare_color_nodes(self, node_tree, input):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1

                if node.inputs[input].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs[input].links[0].from_socket,
                        input=node.inputs["Emission Color"],
                    )
                else:
                    rgb_node = ShaderNode.rgb(
                        node_tree,
                        name="QB_RGB",
                        color=node.inputs[input].default_value[:],
                    )
                    node_tree.links.new(
                        output=rgb_node.outputs["Color"],
                        input=node.inputs["Emission Color"],
                    )

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_color_nodes(node_tree=node.node_tree, input=input)

    def restore_color_nodes(self):
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Emission Color Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Color"])
                        if key == "Emission Strength Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Strength"])
                        if key == "Emission Strength Value":
                            node.inputs["Emission Strength"].default_value = value

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    def prepare_value_nodes(self, node_tree, input):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1

                if node.inputs[input].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs[input].links[0].from_socket,
                        input=node.inputs["Emission Color"],
                    )
                else:
                    value_node = ShaderNode.value(
                        node_tree,
                        name="QB_VALUE",
                        value=node.inputs[input].default_value,
                    )
                    node_tree.links.new(
                        output=value_node.outputs["Value"],
                        input=node.inputs["Emission Color"],
                    )

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_value_nodes(node_tree=node.node_tree, input=input)

    def restore_value_nodes(self):
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Emission Color Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Color"])
                        if key == "Emission Strength Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Strength"])
                        if key == "Emission Strength Value":
                            node.inputs["Emission Strength"].default_value = value

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    def prepare_vector_nodes(self, node_tree, input):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Normal"].is_linked:
                    self.NODE_DATA[node_tree]["Normal Socket"] = node.inputs["Normal"].links[0].from_socket

                if node.inputs[input].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs[input].links[0].from_socket,
                        input=node.inputs["Normal"],
                    )
                else:
                    combine_xyz_node = ShaderNode.combine_xyz(
                        node_tree,
                        name="QB_COMBINE_XYZ",
                        vector=(1, 1, 1),
                    )
                    node_tree.links.new(
                        output=combine_xyz_node.outputs["Vector"],
                        input=node.inputs["Normal"],
                    )

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_vector_nodes(node_tree=node.node_tree, input=input)

    def restore_vector_nodes(self):
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Normal Socket":
                            node_tree.links.new(output=value, input=node.inputs["Normal"])

        self.NODE_DATA.clear()

    def remove_nodes(self, node_tree):
        '''Remove all nodes starting from "QB"'''
        for node in node_tree.nodes:
            if node.name.split("_")[0] == "QB":
                node_tree.nodes.remove(node)

    ## PBR

    # Base Color
    def prepare_base_color(self):
        """Prepare Base Color"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_color_nodes(node_tree, input="Base Color")

    # Emission
    # Affected by the Emission Strength and Alpha
    # TODO : Ignore the Alpha later
    def prepare_emission_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1.0

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_emission_nodes(node_tree=node.node_tree)

    def prepare_emission(self):
        """Prepare Emission"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_emission_nodes(node_tree)

    def restore_emission(self):
        """Restore Emission"""
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Emission Strength Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Strength"])
                        if key == "Emission Strength Value":
                            node.inputs["Emission Strength"].default_value = value

        self.NODE_DATA.clear()

    # Glossiness
    # TODO : Ignore the Alpha later
    def prepare_glossiness_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1

                invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")

                if node.inputs["Roughness"].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs["Roughness"].links[0].from_socket,
                        input=invert_node.inputs["Color"],
                    )
                else:
                    # nodes
                    value_node = ShaderNode.value(
                        node_tree,
                        name="QB_VALUE",
                        value=node.inputs["Roughness"].default_value,
                    )
                    # links
                    node_tree.links.new(
                        output=value_node.outputs["Value"],
                        input=invert_node.inputs["Color"],
                    )
                node_tree.links.new(
                    output=invert_node.outputs["Color"],
                    input=node.inputs["Emission Color"],
                )

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_glossiness_nodes(node_tree=node.node_tree)

    def prepare_glossiness(self):
        """Prepare Glossiness"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_glossiness_nodes(node_tree)

    def restore_glossiness(self):
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Emission Color Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Color"])
                        if key == "Emission Strength Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Strength"])
                        if key == "Emission Strength Value":
                            node.inputs["Emission Strength"].default_value = value

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    # Metallic
    def prepare_metallic(self):
        """Prepare Metallic"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Metallic")

    # Normal
    def prepare_normal_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL":
                if node.inputs["Displacement"].is_linked:
                    self.NODE_DATA[node_tree]["Displacement Socket"] = node.inputs["Displacement"].links[0].from_socket
                    node_tree.links.remove(node.inputs["Displacement"].links[0])

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_normal_nodes(node_tree=node.node_tree)

    def prepare_normal(self):
        """Prepare Normal"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_normal_nodes(node_tree)

    def restore_normal(self):
        """Restore Normal"""
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    for key, value in values.items():
                        if key == "Displacement Socket":
                            node_tree.links.new(output=value, input=node.inputs["Displacement"])

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    # Occlusion
    def prepare_occlusion(self, map: bpy.types.PropertyGroup):
        """Prepare Ambient Occlusion"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        ambient_occlusion_node = ShaderNode.ambient_occlusion(
                            node_tree,
                            name="QB_AO",
                            samples=128,
                            only_local=map.only_local,
                            distance=map.distance,
                        )
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = not map.invert_ao
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=ambient_occlusion_node.outputs["AO"],
                            input=invert_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=emission_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_occlusion(self):
        """Restore Ambient Occlusion"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Roughness
    def prepare_roughness(self):
        """Prepare Roughness"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Roughness")

    # Specular
    def prepare_specular(self):
        """Prepare Specular IOR Level"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Specular IOR Level")

    ## Mesh

    # Alpha
    def prepare_alpha(self):
        """Prepare Alpha"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Alpha")

    # Bevel Normal
    def prepare_bevel_normal_nodes(self, node_tree, map):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bevel_node = ShaderNode.bevel(node_tree, name="QB_BEVEL", samples=128, radius=map.radius)

                if node.inputs["Normal"].is_linked:
                    self.NODE_DATA[node_tree]["Normal"] = node.inputs["Normal"].links[0].from_socket

                node_tree.links.new(output=bevel_node.outputs["Normal"], input=node.inputs["Normal"])

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_bevel_normal_nodes(node_tree=node.node_tree, map=map)

    def prepare_bevel_normal(self, map: bpy.types.PropertyGroup):
        """Prepare Edge"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_bevel_normal_nodes(node_tree, map)

    def restore_bevel_normal(self):
        """Restore Edge"""
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Normal":
                            node_tree.links.new(output=value, input=node.inputs["Normal"])

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    # Cavity
    def prepare_cavity(self, map: bpy.types.PropertyGroup):
        """Prepare Curvature"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        geometry_node = ShaderNode.geometry(node_tree, name="QB_GEOMETRY")
                        c_ramp_node = ShaderNode.color_ramp(node_tree, name="QB_COLOR_RAMP")
                        c_ramp_node.color_ramp.elements[0].position = 0.4
                        c_ramp_node.color_ramp.elements[1].position = 0.5
                        math_node = ShaderNode.math(
                            node_tree,
                            name="QB_POWER",
                            operation="POWER",
                            input_1=map.power,
                        )
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = not map.invert_cavity
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=geometry_node.outputs["Pointiness"],
                            input=c_ramp_node.inputs["Fac"],
                        )
                        node_tree.links.new(
                            output=c_ramp_node.outputs["Color"],
                            input=math_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=math_node.outputs["Value"],
                            input=invert_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=emission_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_cavity(self):
        """Restore Curvature"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Curvature
    def prepare_curvature(self, map: bpy.types.PropertyGroup):
        """Prepare Curvature"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        geometry_node = ShaderNode.geometry(node_tree, name="QB_GEOMETRY")
                        c_ramp_node = ShaderNode.color_ramp(node_tree, name="QB_COLOR_RAMP")
                        c_ramp_node.color_ramp.elements[0].position = 0.45
                        c_ramp_node.color_ramp.elements[1].position = 0.55
                        math_node = ShaderNode.math(
                            node_tree,
                            name="QB_POWER",
                            operation="POWER",
                            input_1=map.power,
                        )
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = not map.invert_curvature
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=geometry_node.outputs["Pointiness"],
                            input=c_ramp_node.inputs["Fac"],
                        )
                        node_tree.links.new(
                            output=c_ramp_node.outputs["Color"],
                            input=math_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=math_node.outputs["Value"],
                            input=invert_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=emission_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_curvature(self):
        """Restore Curvature"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Displacement
    def prepare_displacement_nodes(self, node_tree, map):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "DISPLACEMENT" and node.inputs["Height"].is_linked:
                # nodes
                invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                invert_node.mute = not map.invert_displacement
                emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                material_output_node = ShaderNode.material_output(node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES")
                node_tree.nodes.active = material_output_node

                # links
                node_tree.links.new(
                    output=node.inputs["Height"].links[0].from_socket,
                    input=invert_node.inputs["Color"],
                )
                node_tree.links.new(
                    output=invert_node.outputs["Color"],
                    input=emission_node.inputs["Color"],
                )
                node_tree.links.new(
                    output=emission_node.outputs["Emission"],
                    input=material_output_node.inputs["Surface"],
                )
            else:
                # nodes
                emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION", color=(0, 0, 0, 1))
                material_output_node = ShaderNode.material_output(node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES")
                node_tree.nodes.active = material_output_node

                # links
                node_tree.links.new(
                    output=emission_node.outputs["Emission"],
                    input=material_output_node.inputs["Surface"],
                )

            # if node.type == "GROUP":
            #     self.prepare_displacement_nodes(node_tree=node.node_tree, map=map)

    def prepare_displacement(self, map: bpy.types.PropertyGroup):
        """Prepare Displacement"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_displacement_nodes(node_tree, map)

    def restore_displacement(self):
        """Restore Displacement"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Edge
    def prepare_edge(self, map: bpy.types.PropertyGroup):
        """Prepare Edge"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        bevel_node = ShaderNode.bevel(
                            node_tree,
                            name="QB_BEVEL",
                            samples=128,
                            radius=map.radius,
                        )
                        geometry_node = ShaderNode.geometry(node_tree, name="QB_GEOMETRY")
                        dot_product_node = ShaderNode.vector_math(
                            node_tree,
                            name="QB_DOT_PRODUCT",
                            operation="DOT_PRODUCT",
                        )
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = map.invert_edge
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=bevel_node.outputs["Normal"],
                            input=dot_product_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=geometry_node.outputs["Normal"],
                            input=dot_product_node.inputs[1],
                        )
                        node_tree.links.new(
                            output=dot_product_node.outputs["Value"],
                            input=invert_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=emission_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_edge(self):
        """Restore Edge"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Gradient
    def prepare_gradient(self, map: bpy.types.PropertyGroup):
        """Prepare Gradient"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        texture_coordinate_node = ShaderNode.texture_coordinate(node_tree, name="QB_TEXTURE_COORDINATE")
                        separate_xyz_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ")
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = not map.invert_gradient
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        if map.direction == "XYZ":
                            node_tree.links.new(
                                output=texture_coordinate_node.outputs["Generated"],
                                input=invert_node.inputs["Color"],
                            )

                        elif map.direction in {"X", "Y", "Z"}:
                            node_tree.links.new(
                                output=texture_coordinate_node.outputs["Generated"],
                                input=separate_xyz_node.inputs["Vector"],
                            )
                            if map.direction == "X":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["X"],
                                    input=invert_node.inputs["Color"],
                                )
                            if map.direction == "Y":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["Y"],
                                    input=invert_node.inputs["Color"],
                                )
                            if map.direction == "Z":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["Z"],
                                    input=invert_node.inputs["Color"],
                                )

                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_gradient(self):
        """Restore Gradient"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Height
    def prepare_height(self, map: bpy.types.PropertyGroup):
        """Prepare Height"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        if map.type == "DISPLACEMENT":
                            # nodes
                            texture_coordinate_node = ShaderNode.texture_coordinate(
                                node_tree, name="QB_TEXTURE_COORDINATE"
                            )
                            separate_xyz_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ")
                            invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                            invert_node.mute = not map.invert_height
                            material_output_node = ShaderNode.material_output(
                                node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                            )
                            node_tree.nodes.active = material_output_node

                            # links
                            node_tree.links.new(
                                output=texture_coordinate_node.outputs["Generated"],
                                input=separate_xyz_node.inputs["Vector"],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["Z"],
                                input=invert_node.inputs["Color"],
                            )
                            node_tree.links.new(
                                output=invert_node.outputs["Color"],
                                input=material_output_node.inputs["Surface"],
                            )

                        elif map.type == "NORMAL":
                            # nodes
                            texture_coordinate_node = ShaderNode.texture_coordinate(
                                node_tree, name="QB_TEXTURE_COORDINATE"
                            )
                            vector_transform_node = ShaderNode.vector_transform(
                                node_tree,
                                name="QB_VECTOR_TRANSFORM",
                                vector_type="NORMAL",
                                convert_from="OBJECT",
                                convert_to="CAMERA",
                            )
                            mapping_node = ShaderNode.mapping(
                                node_tree,
                                name="QB_MAPPING",
                                vector_type="TEXTURE",
                                location=(-1, -1, 1),
                                scale=(2, 2, -2),
                            )
                            separate_xyz_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ")
                            invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                            invert_node.mute = not map.invert_height
                            combine_xyz_node = ShaderNode.combine_xyz(node_tree, name="QB_COMBINE_XYZ")
                            gamma_node = ShaderNode.gamma(node_tree, name="QB_GAMMA", gamma=2.2)
                            material_output_node = ShaderNode.material_output(
                                node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                            )
                            node_tree.nodes.active = material_output_node

                            # links
                            node_tree.links.new(
                                output=texture_coordinate_node.outputs["Normal"],
                                input=vector_transform_node.inputs["Vector"],
                            )
                            node_tree.links.new(
                                output=vector_transform_node.outputs["Vector"],
                                input=mapping_node.inputs["Vector"],
                            )
                            node_tree.links.new(
                                output=mapping_node.outputs["Vector"],
                                input=separate_xyz_node.inputs["Vector"],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["X"],
                                input=combine_xyz_node.inputs[0],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["Y"],
                                input=invert_node.inputs["Color"],
                            )
                            node_tree.links.new(
                                output=invert_node.outputs["Color"],
                                input=combine_xyz_node.inputs[1],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["Z"],
                                input=combine_xyz_node.inputs[2],
                            )
                            node_tree.links.new(
                                output=combine_xyz_node.outputs["Vector"],
                                input=gamma_node.inputs["Color"],
                            )
                            node_tree.links.new(
                                output=gamma_node.outputs["Color"],
                                input=material_output_node.inputs["Surface"],
                            )

    def restore_height(self):
        """Restore Gradient"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Material ID
    def prepare_material_id(self, map: bpy.types.PropertyGroup):
        """Prepare Material ID"""
        for object in self.context.selected_objects:
            if map.type == "OBJECT":
                object_color = (
                    random.SystemRandom().uniform(0, 1),
                    random.SystemRandom().uniform(0, 1),
                    random.SystemRandom().uniform(0, 1),
                    1,
                )
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # nodes
                        if map.type == "MATERIAL":
                            emission_node = ShaderNode.emission(
                                node_tree,
                                name="QB_EMISSION",
                                color=(
                                    random.SystemRandom().uniform(0, 1),
                                    random.SystemRandom().uniform(0, 1),
                                    random.SystemRandom().uniform(0, 1),
                                    1,
                                ),
                            )
                        elif map.type == "OBJECT":
                            emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION", color=object_color)
                        else:
                            color_attribute_node = ShaderNode.color_attribute(
                                node_tree,
                                name="QB_COLOR_ATTRIBUTE",
                                layer_name=(
                                    map.group_color_attribute
                                    if self.bake_group.use_high_to_low
                                    else map.object_color_attribute
                                ),
                            )
                            emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                            material_output_node = ShaderNode.material_output(
                                node_tree,
                                name="QB_MATERIAL_OUTPUT",
                                target="CYCLES",
                            )
                            node_tree.nodes.active = material_output_node
                            # links
                            node_tree.links.new(
                                output=color_attribute_node.outputs["Color"],
                                input=emission_node.inputs["Color"],
                            )

                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_material_id(self):
        """Restore Material ID"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Thickness
    def prepare_thickness(self, map: bpy.types.PropertyGroup):
        """Prepare Thickness"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        ambient_occlusion_node = ShaderNode.ambient_occlusion(
                            node_tree,
                            name="QB_AO",
                            samples=128,
                            inside=True,
                            only_local=True,
                            distance=map.distance,
                        )
                        invert_node = ShaderNode.invert(node_tree, name="QB_INVERT")
                        invert_node.mute = not map.invert_thickness
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=ambient_occlusion_node.outputs["AO"],
                            input=invert_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=invert_node.outputs["Color"],
                            input=emission_node.inputs["Color"],
                        )
                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_thickness(self):
        """Restore Thickness"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Toon Shadow
    def prepare_toon_shadow(self, map: bpy.types.PropertyGroup):
        """Prepare Toon Shadow"""
        if hasattr(self, "bake_group") and self.bake_group:
            self.hide_non_local_objects(map)

        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        toon_bsdf_node = ShaderNode.toon_bsdf(
                            node_tree,
                            name="QB_TOON_BSDF",
                            component="DIFFUSE",
                            color=(1, 1, 1, 1),
                            size=map.size,
                            smooth=map.smooth,
                        )
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=toon_bsdf_node.outputs["BSDF"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_toon_shadow(self):
        """Restore Toon Shadow"""
        for obj in self.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # Vector Displacement (VDM)
    def prepare_vdm(self):
        """Prepare VDM"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        texture_coordinate_node = ShaderNode.texture_coordinate(node_tree, name="QB_TEX_COORD")
                        vector_math_add_node = ShaderNode.vector_math(
                            node_tree, name="QB_VECTOR_MATH_ADD", operation="ADD", input_1=(-0.5, -0.5, -0.5)
                        )
                        vector_math_multiple_node = ShaderNode.vector_math(
                            node_tree, name="QB_VECTOR_MATH_MULTIPLY", operation="MULTIPLY", input_1=(2, 2, 2)
                        )
                        vector_math_subtract_node = ShaderNode.vector_math(
                            node_tree, name="QB_VECTOR_MATH_SUB", operation="SUBTRACT"
                        )
                        separate_xyz_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ")
                        separate_xyz1_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ_1")
                        combine_xyz_node = ShaderNode.combine_xyz(node_tree, name="QB_COMBINE_XYZ")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=texture_coordinate_node.outputs["UV"],
                            input=vector_math_add_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=vector_math_add_node.outputs["Vector"],
                            input=vector_math_multiple_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=texture_coordinate_node.outputs["Object"],
                            input=vector_math_subtract_node.inputs[0],
                        )
                        node_tree.links.new(
                            output=vector_math_multiple_node.outputs["Vector"],
                            input=vector_math_subtract_node.inputs[1],
                        )
                        node_tree.links.new(
                            output=vector_math_subtract_node.outputs["Vector"],
                            input=separate_xyz_node.inputs["Vector"],
                        )
                        node_tree.links.new(
                            output=separate_xyz_node.outputs["X"],
                            input=combine_xyz_node.inputs["X"],
                        )
                        node_tree.links.new(
                            output=separate_xyz_node.outputs["Y"],
                            input=combine_xyz_node.inputs["Y"],
                        )

                        node_tree.links.new(
                            output=texture_coordinate_node.outputs["Object"],
                            input=separate_xyz1_node.inputs["Vector"],
                        )
                        node_tree.links.new(
                            output=separate_xyz1_node.outputs["Z"],
                            input=combine_xyz_node.inputs["Z"],
                        )

                        node_tree.links.new(
                            output=combine_xyz_node.outputs["Vector"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_vdm(self):
        """Restore VDM"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    # XYZ
    def prepare_xyz(self, map: bpy.types.PropertyGroup):
        """Prepare XYZ Mask"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        texture_coordinate_node = ShaderNode.texture_coordinate(node_tree, name="QB_TEXTURE_COORDINATE")
                        separate_xyz_node = ShaderNode.separate_xyz(node_tree, name="QB_SEPARATE_XYZ")
                        combine_xyz_node = ShaderNode.combine_xyz(node_tree, name="QB_COMBINE_XYZ")
                        gradient_texture_node = ShaderNode.gradient_texture(node_tree, name="QB_TEXTURE")
                        map_range_node = ShaderNode.map_range(node_tree, name="QB_MAP_RANGE", type="SMOOTHERSTEP")
                        vector_math_node = ShaderNode.vector_math(
                            node_tree,
                            name="QB_VECTOR_MATH",
                            operation="MULTIPLY",
                            input_1=(-1, -1, -1),
                        )
                        vector_math_node.mute = not map.invert_xyz
                        emission_node = ShaderNode.emission(node_tree, name="QB_EMISSION")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=texture_coordinate_node.outputs["Normal"],
                            input=separate_xyz_node.inputs["Vector"],
                        )

                        if map.direction == "XYZ":
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["X"],
                                input=combine_xyz_node.inputs["X"],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["Y"],
                                input=combine_xyz_node.inputs["Y"],
                            )
                            node_tree.links.new(
                                output=separate_xyz_node.outputs["Z"],
                                input=combine_xyz_node.inputs["Z"],
                            )
                            node_tree.links.new(
                                output=combine_xyz_node.outputs["Vector"],
                                input=vector_math_node.inputs[0],
                            )
                            node_tree.links.new(
                                output=vector_math_node.outputs["Vector"],
                                input=emission_node.inputs["Color"],
                            )

                        elif map.direction in {"X", "Y", "Z"}:
                            if map.direction == "X":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["X"],
                                    input=vector_math_node.inputs[0],
                                )
                            if map.direction == "Y":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["Y"],
                                    input=vector_math_node.inputs[0],
                                )
                            if map.direction == "Z":
                                node_tree.links.new(
                                    output=separate_xyz_node.outputs["Z"],
                                    input=vector_math_node.inputs[0],
                                )

                            node_tree.links.new(
                                output=vector_math_node.outputs["Vector"],
                                input=gradient_texture_node.inputs["Vector"],
                            )
                            node_tree.links.new(
                                output=gradient_texture_node.outputs["Color"],
                                input=map_range_node.inputs["Value"],
                            )
                            node_tree.links.new(
                                output=map_range_node.outputs["Result"],
                                input=emission_node.inputs["Color"],
                            )

                        node_tree.links.new(
                            output=emission_node.outputs["Emission"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_xyz(self):
        """Restore XYZ Mask"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    ## Principal BSDF

    # IOR
    def prepare_ior(self):
        """Prepare IOR"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="IOR")

    # Subsurface Weight
    def prepare_subsurface_weight(self):
        """Prepare Subsurface Weight"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Subsurface Weight")

    # Subsurface Radius
    def prepare_subsurface_radius(self):
        """Prepare Subsurface Radius"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Subsurface Radius")

    # Subsurface Scale
    def prepare_subsurface_scale(self):
        """Prepare Subsurface Scale"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Subsurface Scale")

    # Subsurface IOR
    def check_subsurface_ior(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.subsurface_method != "RANDOM_WALK_SKIN":
                    continue

                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Color"].links[0])

                self.NODE_DATA[node_tree]["Emission Color Value"] = node.inputs["Emission Color"].default_value[:]
                node.inputs["Emission Color"].default_value = (1, 1, 1, 1)

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1

                if node.inputs["Subsurface IOR"].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs["Subsurface IOR"].links[0].from_socket,
                        input=node.inputs["Emission Strength"],
                    )
                else:
                    node.inputs["Emission Strength"].default_value = node.inputs["Subsurface IOR"].default_value

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.check_subsurface_ior(node_tree=node.node_tree)

    def prepare_subsurface_ior(self):
        """Prepare Subsurface IOR"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.check_subsurface_ior(node_tree)

    # Subsurface Anisotropy
    def check_subsurface_anisotropy(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.subsurface_method == "BURLEY":
                    continue

                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Color"].links[0])

                self.NODE_DATA[node_tree]["Emission Color Value"] = node.inputs["Emission Color"].default_value[:]
                node.inputs["Emission Color"].default_value = (1, 1, 1, 1)

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])

                self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs["Emission Strength"].default_value
                node.inputs["Emission Strength"].default_value = 1

                if node.inputs["Subsurface Anisotropy"].is_linked:  # input
                    node_tree.links.new(
                        output=node.inputs["Subsurface Anisotropy"].links[0].from_socket,
                        input=node.inputs["Emission Strength"],
                    )
                else:
                    node.inputs["Emission Strength"].default_value = node.inputs["Subsurface Anisotropy"].default_value

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.check_subsurface_anisotropy(node_tree=node.node_tree)

    def prepare_subsurface_anisotropy(self):
        """Prepare Subsurface Anisotropy"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.check_subsurface_anisotropy(node_tree)

    # Specular Tint
    def prepare_specular_tint(self):
        """Prepare Specular Tint"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_color_nodes(node_tree, input="Specular Tint")

    # Anisotropic
    def prepare_anisotropic(self):
        """Prepare Anisotropic"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Anisotropic")

    # Anisotropic Rotation
    def prepare_anisotropic_rotation(self):
        """Prepare Anisotropic Rotation"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Anisotropic Rotation")

    # Tangent
    def prepare_tangent(self):
        """Prepare Tangent"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_vector_nodes(node_tree, input="Tangent")

    # Transmission Weight
    def prepare_transmission_weight(self):
        """Prepare Transmission Weight"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Transmission Weight")

    # Coat Weight
    def prepare_coat_weight(self):
        """Prepare Coat Weight"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Coat Weight")

    # Coat Roughness
    def prepare_coat_roughness(self):
        """Prepare Coat Roughness"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Coat Roughness")

    # Coat IOR
    def prepare_coat_ior(self):
        """Prepare Coat IOR"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Coat IOR")

    # Coat Tint
    def prepare_coat_tint(self):
        """Prepare Coat Tint"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_color_nodes(node_tree, input="Coat Tint")

    # Coat Normal
    def prepare_coat_normal(self):
        """Prepare Coat Normal"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_vector_nodes(node_tree, input="Coat Normal")

    # Sheen Weight
    def prepare_sheen_weight(self):
        """Prepare Sheen Weight"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Sheen Weight")

    # Sheen Roughness
    def prepare_sheen_roughness(self):
        """Prepare Sheen Roughness"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_value_nodes(node_tree, input="Sheen Roughness")

    # Sheen Tint
    def prepare_sheen_tint(self):
        """Prepare Sheen Tint"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_color_nodes(node_tree, input="Sheen Tint")

    # Emission Strength
    def prepare_emission_strength_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Emission Color"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Color Socket"] = (
                        node.inputs["Emission Color"].links[0].from_socket
                    )

                if node.inputs["Emission Strength"].is_linked:
                    self.NODE_DATA[node_tree]["Emission Strength Socket"] = (
                        node.inputs["Emission Strength"].links[0].from_socket
                    )
                    node_tree.links.new(
                        output=node.inputs["Emission Strength"].links[0].from_socket,
                        input=node.inputs["Emission Color"],
                    )
                    node_tree.links.remove(node.inputs["Emission Strength"].links[0])
                    self.NODE_DATA[node_tree]["Emission Strength Value"] = node.inputs[
                        "Emission Strength"
                    ].default_value
                    node.inputs["Emission Strength"].default_value = 1
                else:
                    value_node = ShaderNode.value(
                        node_tree,
                        name="QB_VALUE",
                        value=node.inputs["Emission Strength"].default_value,
                    )
                    node_tree.links.new(
                        output=value_node.outputs["Value"],
                        input=node.inputs["Emission Color"],
                    )

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_emission_strength_nodes(node_tree=node.node_tree)

    def prepare_emission_strength(self):
        """Prepare Emission Strength"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_emission_strength_nodes(node_tree)

    def restore_emission_strength(self):
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Emission Color Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Color"])
                        if key == "Emission Strength Socket":
                            node_tree.links.new(output=value, input=node.inputs["Emission Strength"])
                        if key == "Emission Strength Value":
                            node.inputs["Emission Strength"].default_value = value

            self.remove_nodes(node_tree=node_tree)
        self.NODE_DATA.clear()

    ## Cycles

    # Ambient Occlusion
    def prepare_ambient_occlusion(self, map):
        if hasattr(self, "bake_group") and self.bake_group:
            self.hide_non_local_objects(map)

    def restore_ambient_occlusion(self):
        for obj in self.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

    # Combined
    def prepare_combined(self, map):
        if hasattr(self, "bake_group") and self.bake_group:
            self.hide_non_local_objects(map)

    def restore_combined(self):
        for obj in self.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

    # Diffuse
    def prepare_diffuse_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                # Store links
                if node.inputs["Subsurface Weight"].is_linked:
                    self.NODE_DATA[node_tree]["Subsurface Weight Socket"] = (
                        node.inputs["Subsurface Weight"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Subsurface Weight"].links[0])
                if node.inputs["Metallic"].is_linked:
                    self.NODE_DATA[node_tree]["Metallic Socket"] = node.inputs["Metallic"].links[0].from_socket
                    node_tree.links.remove(node.inputs["Metallic"].links[0])
                if node.inputs["Sheen Weight"].is_linked:
                    self.NODE_DATA[node_tree]["Sheen Weight Socket"] = node.inputs["Sheen Weight"].links[0].from_socket
                    node_tree.links.remove(node.inputs["Sheen Weight"].links[0])
                if node.inputs["Transmission Weight"].is_linked:
                    self.NODE_DATA[node_tree]["Transmission Weight Socket"] = (
                        node.inputs["Transmission Weight"].links[0].from_socket
                    )
                    node_tree.links.remove(node.inputs["Transmission Weight"].links[0])

                # Store default values
                self.NODE_DATA[node_tree]["Subsurface Weight Value"] = node.inputs["Subsurface Weight"].default_value
                self.NODE_DATA[node_tree]["Metallic Value"] = node.inputs["Metallic"].default_value
                self.NODE_DATA[node_tree]["Sheen Weight Value"] = node.inputs["Sheen Weight"].default_value
                self.NODE_DATA[node_tree]["Transmission Weight Value"] = node.inputs[
                    "Transmission Weight"
                ].default_value

                # Set default values
                node.inputs["Subsurface Weight"].default_value = 0.0
                node.inputs["Metallic"].default_value = 0.0
                node.inputs["Sheen Weight"].default_value = 0.0
                node.inputs["Transmission Weight"].default_value = 0.0

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_diffuse_nodes(node_tree=node.node_tree)

    def prepare_diffuse(self, map):
        """Prepare Diffuse"""
        if hasattr(self, "bake_group") and self.bake_group:
            self.hide_non_local_objects(map)

        for obj in self.context.scene.objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_diffuse_nodes(node_tree)

    def restore_diffuse(self):
        """Restore Diffuse"""
        for obj in self.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        # Restore links
                        if key == "Subsurface Weight Socket":
                            node_tree.links.new(output=value, input=node.inputs["Subsurface Weight"])
                        if key == "Metallic Socket":
                            node_tree.links.new(output=value, input=node.inputs["Metallic"])
                        if key == "Sheen Weight Socket":
                            node_tree.links.new(output=value, input=node.inputs["Sheen Weight"])
                        if key == "Transmission Weight Socket":
                            node_tree.links.new(output=value, input=node.inputs["Transmission Weight"])
                        # Restore default values
                        if key == "Subsurface Weight Value":
                            node.inputs["Subsurface Weight"].default_value = value
                        if key == "Metallic Value":
                            node.inputs["Metallic"].default_value = value
                        if key == "Sheen Weight Value":
                            node.inputs["Sheen Weight"].default_value = value
                        if key == "Transmission Weight Value":
                            node.inputs["Transmission Weight"].default_value = value

        self.NODE_DATA.clear()

    # Shadow
    def prepare_shadow(self, map):
        if hasattr(self, "bake_group") and self.bake_group:
            self.hide_non_local_objects(map)

    def restore_shadow(self):
        for obj in self.context.scene.objects:
            obj.hide_viewport = False
            obj.hide_render = False

    # Transmission
    def prepare_transmission_nodes(self, node_tree):
        node_tree.animation_data_clear()
        self.NODE_DATA[node_tree] = {}

        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                if node.inputs["Metallic"].is_linked:
                    self.NODE_DATA[node_tree]["Metallic Socket"] = node.inputs["Metallic"].links[0].from_socket
                    node_tree.links.remove(node.inputs["Metallic"].links[0])
                else:
                    self.NODE_DATA[node_tree]["Metallic Value"] = node.inputs["Metallic"].default_value
                    node.inputs["Metallic"].default_value = 0.0

            elif node.type == "GROUP" and node.node_tree not in self.NODE_DATA:
                self.prepare_transmission_nodes(node_tree=node.node_tree)

    def prepare_transmission(self):
        """Prepare Transmission"""
        for obj in self.context.selected_objects:
            for slot in obj.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    if node_tree in self.NODE_DATA:
                        continue
                    self.remove_nodes(node_tree=node_tree)
                    self.prepare_transmission_nodes(node_tree)

    def restore_transmission(self):
        """Restore Transmission"""
        for node_tree, values in self.NODE_DATA.items():
            for node in node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    for key, value in values.items():
                        if key == "Metallic Socket":
                            node_tree.links.new(output=value, input=node.inputs["Metallic"])
                        if key == "Metallic Value":
                            node.inputs["Metallic"].default_value = value

        self.NODE_DATA.clear()

    # UV
    def prepare_uv(self):
        """Prepare UV"""
        for object in self.context.selected_objects:
            if object.material_slots:
                for slot in object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        node_tree.animation_data_clear()
                        if node_tree in self.NODE_DATA:
                            continue
                        self.remove_nodes(node_tree=node_tree)
                        self.NODE_DATA[node_tree] = {}

                        # nodes
                        uvmap_node = ShaderNode.uvmap(node_tree, name="QB_UVMAP")
                        material_output_node = ShaderNode.material_output(
                            node_tree, name="QB_MATERIAL_OUTPUT", target="CYCLES"
                        )
                        node_tree.nodes.active = material_output_node

                        # links
                        node_tree.links.new(
                            output=uvmap_node.outputs["UV"],
                            input=material_output_node.inputs["Surface"],
                        )

    def restore_uv(self):
        """Restore UV"""
        for node_tree, _ in self.NODE_DATA.items():
            self.remove_nodes(node_tree=node_tree)

        self.NODE_DATA.clear()

    def hide_non_local_objects(self, map):
        """Only Local"""
        objects = []
        if self.bake_group.use_high_to_low:
            for group in self.bake_group.groups:
                objects.extend(item.object for item in group.high_poly)
                objects.extend(item.object for item in group.low_poly)
        else:
            objects = [item.object for item in self.bake_group.objects]

        for obj in self.context.scene.objects:
            if obj.type != "MESH":
                continue
            if self.bake_group.use_high_to_low and obj == self.cage_object:
                continue
            if map.only_local and obj not in objects:
                obj.hide_viewport = True
                obj.hide_render = True
