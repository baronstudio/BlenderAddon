import uuid

import bpy
from bpy.props import EnumProperty, IntProperty
from bpy.types import Operator

MAP_TYPES = {
    "PBR": [("", "PBR", "", "SHADING_RENDERED", 0), "PBR"],
    "BASE_COLOR": [("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"), "Base Color"],
    "DISPLACEMENT": [
        (
            "DISPLACEMENT",
            "Displacement",
            "Displacement / Bump Map\nBake displacement data from Multires modifier or Displacement node",
        ),
        "Displacement",
    ],
    "EMISSION": [("EMISSION", "Emission", "Emission Map"), "Emission"],
    "GLOSSINESS": [("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"), "Glossiness"],
    "METALLIC": [("METALLIC", "Metallic", "Metallic Map"), "Metallic"],
    "NORMAL": [("NORMAL", "Normal", "Normal Map"), "Normal"],
    "ROUGHNESS": [("ROUGHNESS", "Roughness", "Roughness Map"), "Roughness"],
    "SPECULAR": [("SPECULAR", "Specular", "Specular Map"), "Specular"],
    "CHANNEL_PACK": [("CHANNEL_PACK", "Channel Pack", "Channel Pack Map"), "Channel Pack"],
    "BSDF": [("", "Principled BSDF", "", "NODE", 0), "Principled BSDF"],
    "ALPHA": [("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"), "Alpha"],
    "SUBSURFACE": [("SUBSURFACE", "Subsurface", "Subsurface Map"), "Subsurface"],
    "SUBSURFACE_COLOR": [("SUBSURFACE_COLOR", "Subsurface Color", "Subsurface Color Map"), "Subsurface Color"],
    "SUBSURFACE_IOR": [("SUBSURFACE_IOR", "Subsurface IOR", "Subsurface IOR Map"), "Subsurface IOR"],
    "SUBSURFACE_ANISOTROPY": [
        ("SUBSURFACE_ANISOTROPY", "Subsurface Anisotropy", "Subsurface Anisotropy Map"),
        "Subsurface Anisotropy",
    ],
    "SPECULAR_TINT": [("SPECULAR_TINT", "Specular Tint", "Specular Tint Map"), "Specular Tint"],
    "ANISOTROPIC": [("ANISOTROPIC", "Anisotropic", "Anisotropic Map"), "Anisotropic"],
    "ANISOTROPIC_ROTATION": [
        ("ANISOTROPIC_ROTATION", "Anisotropic Rotation", "Anisotropic Rotation Map"),
        "Anisotropic Rotation",
    ],
    "SHEEN": [("SHEEN", "Sheen", "Sheen Map"), "Sheen"],
    "SHEEN_TINT": [("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"), "Sheen Tint"],
    "CLEARCOAT": [("CLEARCOAT", "Clearcoat", "Clearcoat Map"), "Clearcoat"],
    "CLEARCOAT_ROUGHNESS": [
        ("CLEARCOAT_ROUGHNESS", "Clearcoat Roughness", "Clearcoat Roughness Map"),
        "Clearcoat Roughness",
    ],
    "IOR": [("IOR", "IOR", "IOR Map"), "IOR"],
    "TRANSMISSION_ROUGHNESS": [
        ("TRANSMISSION_ROUGHNESS", "Transmission Roughness", "Transmission Roughness Map"),
        "Transmission Roughness",
    ],
    "EMISSION_STRENGTH": [("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"), "Emission Strength"],
    "CLEARCOAT_NORMAL": [("CLEARCOAT_NORMAL", "Clearcoat Normal", "Clearcoat Normal Map"), "Clearcoat Normal"],
    "TANGENT": [("TANGENT", "Tangent", "Tangent Map"), "Tangent"],
}


class QBAKER_OT_material_bake_map_add(Operator):
    """Add a map to be baked"""

    bl_label = "Add Map"
    bl_idname = "qbaker.material_bake_map_add"
    bl_options = {"REGISTER", "INTERNAL"}

    def items_type(self, context):
        return [
            *list(value[0] for value in MAP_TYPES.values()),
        ]

    type: EnumProperty(
        name="Map Type",
        description="Type of map to bake",
        items=items_type,
    )

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps.add()
        active_material.active_map_index = len(active_material.maps) - 1
        map.name = uuid.uuid4().hex[:8]
        map.label = MAP_TYPES[self.type][1]
        map.type = self.type

        return {"FINISHED"}


class QBAKER_OT_material_bake_map_load(Operator):
    bl_label = "Load Material Maps"
    bl_idname = "qbaker.material_bake_map_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker
        return material_baker.materials

    @classmethod
    def description(cls, context, properties):
        return "Load maps based on Principled BSDF input sockets and values\n\nShift  •  Load maps based on Principled BSDF input sockets"

    def check_inputs_sockets_values(self, node_tree, maps):
        map_type = None
        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                for input in node.inputs:
                    if input.name == "Base Color":
                        if input.is_linked or input.default_value[:] != (
                            0.800000011920929,
                            0.800000011920929,
                            0.800000011920929,
                            1.0,
                        ):
                            map_type = "BASE_COLOR"
                    elif input.name == "Subsurface":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "SUBSURFACE"
                    elif input.name == "Subsurface Color":
                        if input.is_linked or input.default_value[:] != (
                            0.800000011920929,
                            0.800000011920929,
                            0.800000011920929,
                            1.0,
                        ):
                            map_type = "SUBSURFACE_COLOR"
                    elif input.name == "Subsurface IOR":
                        if input.is_linked or input.default_value != 1.399999976158142:
                            map_type = "SUBSURFACE_IOR"
                    elif input.name == "Subsurface Anisotropy":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "SUBSURFACE_ANISOTROPY"
                    elif input.name == "Metallic":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "METALLIC"
                    elif input.name == "Specular":
                        if input.is_linked or input.default_value != 0.5:
                            map_type = "SPECULAR"
                    elif input.name == "Specular Tint":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "SPECULAR_TINT"
                    elif input.name == "Roughness":
                        if input.is_linked or input.default_value != 0.5:
                            map_type = "ROUGHNESS"
                    elif input.name == "Anisotropic":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "ANISOTROPIC"
                    elif input.name == "Anisotropic Rotation":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "ANISOTROPIC_ROTATION"
                    elif input.name == "Sheen":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "SHEEN"
                    elif input.name == "Sheen Tint":
                        if input.is_linked or input.default_value != 0.5:
                            map_type = "SHEEN_TINT"
                    elif input.name == "Clearcoat":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "CLEARCOAT"
                    elif input.name == "Clearcoat Roughness":
                        if input.is_linked or input.default_value != 0.029999999329447746:
                            map_type = "CLEARCOAT_ROUGHNESS"
                    elif input.name == "IOR":
                        if input.is_linked or input.default_value != 1.4500000476837158:
                            map_type = "IOR"
                    elif input.name == "Transmission":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "TRANSMISSION"
                    elif input.name == "Transmission Roughness":
                        if input.is_linked or input.default_value != 0.0:
                            map_type = "TRANSMISSION_ROUGHNESS"
                    elif input.name == "Emission":
                        if input.is_linked or input.default_value[:] != (
                            0.0,
                            0.0,
                            0.0,
                            1.0,
                        ):
                            map_type = "EMISSION"
                    elif input.name == "Emission Strength":
                        if input.is_linked or input.default_value != 1.0:
                            map_type = "EMISSION_STRENGTH"
                    elif input.name == "Alpha":
                        if input.is_linked or input.default_value != 1.0:
                            map_type = "ALPHA"
                    elif input.name == "Normal" and input.is_linked:
                        map_type = "NORMAL"
                    elif input.name == "Clearcoat Normal" and input.is_linked:
                        map_type = "CLEARCOAT_NORMAL"
                    elif input.name == "Tangent" and input.is_linked:
                        map_type = "TANGENT"

                    if map_type and all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.material_bake_map_add(type=map_type)

            elif node.type == "GROUP":
                self.check_inputs_sockets_values(node_tree=node.node_tree, maps=maps)

            elif node.type == "OUTPUT_MATERIAL":
                if node.inputs["Displacement"].is_linked:
                    map_type = "DISPLACEMENT"

                    if map_type and all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.material_bake_map_add(type=map_type)

    def check_inputs_sockets(self, node_tree, maps):
        map_type = None
        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                for input in node.inputs:
                    if input.name == "Base Color" and input.is_linked:
                        map_type = "BASE_COLOR"
                    elif input.name == "Subsurface" and input.is_linked:
                        map_type = "SUBSURFACE"
                    elif input.name == "Subsurface Color" and input.is_linked:
                        map_type = "SUBSURFACE_COLOR"
                    elif input.name == "Subsurface IOR" and input.is_linked:
                        map_type = "SUBSURFACE_IOR"
                    elif input.name == "Subsurface Anisotropy" and input.is_linked:
                        map_type = "SUBSURFACE_ANISOTROPY"
                    elif input.name == "Metallic" and input.is_linked:
                        map_type = "METALLIC"
                    elif input.name == "Specular" and input.is_linked:
                        map_type = "SPECULAR"
                    elif input.name == "Specular Tint" and input.is_linked:
                        map_type = "SPECULAR_TINT"
                    elif input.name == "Roughness" and input.is_linked:
                        map_type = "ROUGHNESS"
                    elif input.name == "Anisotropic" and input.is_linked:
                        map_type = "ANISOTROPIC"
                    elif input.name == "Anisotropic Rotation" and input.is_linked:
                        map_type = "ANISOTROPIC_ROTATION"
                    elif input.name == "Sheen" and input.is_linked:
                        map_type = "SHEEN"
                    elif input.name == "Sheen Tint" and input.is_linked:
                        map_type = "SHEEN_TINT"
                    elif input.name == "Clearcoat" and input.is_linked:
                        map_type = "CLEARCOAT"
                    elif input.name == "Clearcoat Roughness" and input.is_linked:
                        map_type = "CLEARCOAT_ROUGHNESS"
                    elif input.name == "IOR" and input.is_linked:
                        map_type = "IOR"
                    elif input.name == "Transmission" and input.is_linked:
                        map_type = "TRANSMISSION"
                    elif input.name == "Transmission Roughness" and input.is_linked:
                        map_type = "TRANSMISSION_ROUGHNESS"
                    elif input.name == "Emission" and input.is_linked:
                        map_type = "EMISSION"
                    elif input.name == "Emission Strength" and input.is_linked:
                        map_type = "EMISSION_STRENGTH"
                    elif input.name == "Alpha" and input.is_linked:
                        map_type = "ALPHA"
                    elif input.name == "Normal" and input.is_linked:
                        map_type = "NORMAL"
                    elif input.name == "Clearcoat Normal" and input.is_linked:
                        map_type = "CLEARCOAT_NORMAL"
                    elif input.name == "Tangent" and input.is_linked:
                        map_type = "TANGENT"

                    if map_type and all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.material_bake_map_add(type=map_type)

            elif node.type == "GROUP":
                self.check_inputs_sockets(node_tree=node.node_tree, maps=maps)

            elif node.type == "OUTPUT_MATERIAL":
                if node.inputs["Displacement"].is_linked:
                    map_type = "DISPLACEMENT"

                    if map_type and all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.material_bake_map_add(type=map_type)

    def invoke(self, context, event):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            materials = [item.material for item in material_baker.materials]
            maps = material_baker.maps
        else:
            active_material = material_baker.materials[material_baker.active_material_index]
            materials = [active_material.material]
            maps = active_material.maps

        for material in materials:
            node_tree = material.node_tree

            if event.shift:
                self.check_inputs_sockets(node_tree, maps)
            else:
                self.check_inputs_sockets_values(node_tree, maps)

        return {"FINISHED"}


class QBAKER_OT_material_bake_map_include(Operator):
    bl_label = "Include Material Map"
    bl_idname = "qbaker.material_bake_map_include"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            return material_baker.maps
        else:
            active_material = material_baker.bake_groups[material_baker.active_material_index]
            return active_material.maps

        return False

    @classmethod
    def description(cls, context, properties):
        return "Include the map\n\nShift  •  Include all the map\nCtrl    •  Isolate the map"

    def invoke(self, context, event):
        self.material_baker = context.scene.qbaker.material_baker

        if self.material_baker.use_map_global:
            self.active_material = self.material_baker
        else:
            self.active_material = self.material_baker.bake_groups[self.material_baker.active_material_index]

        self.map = self.active_material.maps[self.index]
        self.include = self.map.use_include

        if event.shift:
            for map in self.active_material.maps:
                map.use_include = not self.include
        elif event.ctrl:
            if any(map.use_include for map in self.active_material.maps if map != self.map):
                for map in self.active_material.maps:
                    map.use_include = False
            else:
                for map in self.active_material.maps:
                    map.use_include = not map.use_include

            self.map.use_include = True
        else:
            self.map.use_include = not self.include

        return {"FINISHED"}


class QBAKER_OT_material_bake_map_remove(Operator):
    bl_label = "Material Remove"
    bl_idname = "qbaker.material_bake_map_remove"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            return material_baker.maps
        else:
            active_material = material_baker.bake_groups[material_baker.active_material_index]
            return active_material.maps

        return False

    @classmethod
    def description(cls, context, properties):
        return "Remove the material map\n\nShift  •  Remove all the material maps\nCtrl    •  Remove all the other material maps"

    def invoke(self, context, event):
        self.material_baker = context.scene.qbaker.material_baker

        if self.material_baker.use_map_global:
            self.active_material = self.material_baker
        else:
            self.active_material = self.material_baker.bake_groups[self.material_baker.active_material_index]

        self.map = self.active_material.maps[self.index]

        if event.shift:
            self.active_material.maps.clear()
            self.active_material.active_map_index = 0
        elif event.ctrl:
            for map in reversed(self.active_material.maps):
                if map != self.map:
                    self.active_material.maps.remove(self.active_material.maps.find(map.name))
                    self.active_material.active_map_index = min(
                        max(0, self.active_material.active_map_index - 1), len(self.active_material.maps) - 1
                    )
        else:
            self.active_material.maps.remove(self.index)
            self.active_material.active_map_index = min(
                max(0, self.active_material.active_map_index - 1), len(self.active_material.maps) - 1
            )

        return {"FINISHED"}


classes = (
    QBAKER_OT_material_bake_map_add,
    QBAKER_OT_material_bake_map_load,
    QBAKER_OT_material_bake_map_include,
    QBAKER_OT_material_bake_map_remove,
)


register, unregister = bpy.utils.register_classes_factory(classes)
