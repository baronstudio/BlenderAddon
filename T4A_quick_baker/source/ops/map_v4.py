import uuid

import bpy
from bpy.props import EnumProperty, IntProperty
from bpy.types import Operator

MAP_TYPES = {
    "PBR": [("", "PBR", "", "SHADING_RENDERED", 0), "PBR"],
    "BASE_COLOR": [("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"), "Base Color"],
    "EMISSION": [("EMISSION", "Emission", "Emission Map"), "Emission"],
    "GLOSSINESS": [("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"), "Glossiness"],
    "METALLIC": [("METALLIC", "Metallic", "Metallic Map"), "Metallic"],
    "NORMAL": [("NORMAL", "Normal", "Normal Map"), "Normal"],
    "OCCLUSION": [("OCCLUSION", "Occlusion", "Ambient Occlusion Map"), "Occlusion"],
    "ROUGHNESS": [("ROUGHNESS", "Roughness", "Roughness Map"), "Roughness"],
    "SPECULAR": [("SPECULAR", "Specular", "Specular Map"), "Specular"],
    "CHANNEL_PACK": [("CHANNEL_PACK", "Channel Pack", "Channel Pack Map"), "Channel Pack"],
    "MESH": [("", "Mesh", "", "MESH_DATA", 0), "Mesh"],
    "ALPHA": [("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"), "Alpha"],
    "BEVEL_NORMAL": [("BEVEL_NORMAL", "Bevel Normal", "Bevel Normal Map"), "Bevel Normal"],
    "CAVITY": [("CAVITY", "Cavity", "Cavity / Concavity Map"), "Cavity"],
    "CURVATURE": [("CURVATURE", "Curvature", "Curvature Map"), "Curvature"],
    "DISPLACEMENT": [
        (
            "DISPLACEMENT",
            "Displacement",
            "Displacement / Bump Map\nBake displacement data from Multires modifier or Displacement node",
        ),
        "Displacement",
    ],
    "EDGE": [("EDGE", "Edge", "Edge / Convexity Map"), "Edge"],
    "GRADIENT": [("GRADIENT", "Gradient", "Gradient Map"), "Gradient"],
    "HEIGHT": [
        ("HEIGHT", "Heightmap", "Height Map\nBake height data along Z axis\nUsed for large meshes e.g. Terrain"),
        "Heightmap",
    ],
    "MATERIAL_ID": [("MATERIAL_ID", "Material ID", "Material ID Map"), "Material ID"],
    "THICKNESS": [("THICKNESS", "Thickness", "Thickness / Translucency Map"), "Thickness"],
    "TOON_SHADOW": [("TOON_SHADOW", "Toon Shadow", "Toon Shadow Map"), "Toon Shadow"],
    "VDM": [("VDM", "Vector Displacement (VDM)", "Vector Displacement Map"), "Vector Displacement (VDM)"],
    "WIREFRAME": [("WIREFRAME", "Wireframe", "Wireframe / UV Layout Map"), "Wireframe"],
    "XYZ": [("XYZ", "XYZ", "XYZ Map"), "XYZ"],
    "BSDF": [("", "Principled BSDF", "", "NODE", 0), "Principled BSDF"],
    "IOR": [("IOR", "IOR", "IOR Map"), "IOR"],
    "SUBSURFACE_WEIGHT": [("SUBSURFACE_WEIGHT", "Subsurface Weight", "Subsurface Weight Map"), "Subsurface Weight"],
    "SUBSURFACE_SCALE": [("SUBSURFACE_SCALE", "Subsurface Scale", "Subsurface Scale Map"), "Subsurface Scale"],
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
    "TANGENT": [("TANGENT", "Tangent", "Tangent Map"), "Tangent"],
    "TRANSMISSION_WEIGHT": [
        ("TRANSMISSION_WEIGHT", "Transmission Weight", "Transmission Weight Map"),
        "Transmission Weight",
    ],
    "COAT_WEIGHT": [("COAT_WEIGHT", "Coat Weight", "Coat Weight Map"), "Coat Weight"],
    "COAT_ROUGHNESS": [("COAT_ROUGHNESS", "Coat Roughness", "Coat Roughness Map"), "Coat Roughness"],
    "COAT_IOR": [("COAT_IOR", "Coat IOR", "Coat IOR Map"), "Coat IOR"],
    "COAT_TINT": [("COAT_TINT", "Coat Tint", "Coat Tint Map"), "Coat Tint"],
    "COAT_NORMAL": [("COAT_NORMAL", "Coat Normal", "Coat Normal Map"), "Coat Normal"],
    "SHEEN_WEIGHT": [("SHEEN_WEIGHT", "Sheen Weight", "Sheen Weight Map"), "Sheen Weight"],
    "SHEEN_ROUGHNESS": [("SHEEN_ROUGHNESS", "Sheen Roughness", "Sheen Roughness Map"), "Sheen Roughness"],
    "SHEEN_TINT": [("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"), "Sheen Tint"],
    "EMISSION_STRENGTH": [("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"), "Emission Strength"],
    "CYCLE": [("", "Cycles", "", "SHADING_TEXTURE", 0), "Cycles"],
    "AO": [("AO", "Ambient Occlusion", "Cycles Ambient Occlusion Map"), "Ambient Occlusion"],
    "COMBINED": [("COMBINED", "Combined", "Combined Map"), "Combined"],
    "DIFFUSE": [("DIFFUSE", "Diffuse", "Diffuse Map"), "Diffuse"],
    "ENVIRONMENT": [("ENVIRONMENT", "Environment", "Environment Map"), "Environment"],
    "GLOSSY": [("GLOSSY", "Glossy", "Glossy Map"), "Glossy"],
    "POSITION": [("POSITION", "Position", "Position Map"), "Position"],
    "SHADOW": [("SHADOW", "Shadow", "Shadow Map"), "Shadow"],
    "TRANSMISSION": [("TRANSMISSION", "Transmission", "Transmission Map"), "Transmission"],
    "UV": [("UV", "UV", "UV Map"), "UV"],
}

# Socket name to map type mapping
PRINCIPLED_SOCKET_MAP = {
    "Base Color": "BASE_COLOR",
    "Metallic": "METALLIC",
    "Roughness": "ROUGHNESS",
    "IOR": "IOR",
    "Alpha": "ALPHA",
    "Normal": "NORMAL",
    "Subsurface Weight": "SUBSURFACE_WEIGHT",
    "Subsurface Scale": "SUBSURFACE_SCALE",
    "Subsurface IOR": "SUBSURFACE_IOR",
    "Subsurface Anisotropy": "SUBSURFACE_ANISOTROPY",
    "Specular IOR Level": "SPECULAR",
    "Specular Tint": "SPECULAR_TINT",
    "Anisotropic": "ANISOTROPIC",
    "Anisotropic Rotation": "ANISOTROPIC_ROTATION",
    "Tangent": "TANGENT",
    "Transmission Weight": "TRANSMISSION_WEIGHT",
    "Coat Weight": "COAT_WEIGHT",
    "Coat Roughness": "COAT_ROUGHNESS",
    "Coat IOR": "COAT_IOR",
    "Coat Tint": "COAT_TINT",
    "Coat Normal": "COAT_NORMAL",
    "Sheen Weight": "SHEEN_WEIGHT",
    "Sheen Roughness": "SHEEN_ROUGHNESS",
    "Sheen Tint": "SHEEN_TINT",
    "Emission Color": "EMISSION",
    "Emission Strength": "EMISSION_STRENGTH",
}

# Default values for sockets that need checking
SOCKET_DEFAULTS = {
    "Base Color": (0.800000011920929, 0.800000011920929, 0.800000011920929, 1.0),
    "Metallic": 0.0,
    "Roughness": 0.5,
    "IOR": 1.5,
    "Alpha": 1.0,
    "Subsurface Weight": 0.0,
    "Subsurface Scale": 0.05000000074505806,
    "Subsurface IOR": 1.399999976158142,
    "Subsurface Anisotropy": 0.0,
    "Specular IOR Level": 0.5,
    "Specular Tint": (1.0, 1.0, 1.0, 1.0),
    "Anisotropic": 0.0,
    "Anisotropic Rotation": 0.0,
    "Transmission Weight": 0.0,
    "Coat Weight": 0.0,
    "Coat Roughness": 0.029999999329447746,
    "Coat IOR": 1.5,
    "Coat Tint": (1.0, 1.0, 1.0, 1.0),
    "Sheen Weight": 0.0,
    "Sheen Roughness": 0.5,
    "Sheen Tint": (1.0, 1.0, 1.0, 1.0),
    "Emission Color": (1.0, 1.0, 1.0, 1.0),
    "Emission Strength": 0.0,
}


class QBAKER_OT_map_add(Operator):
    "Add a map to be baked"

    bl_label = "Add Map"
    bl_idname = "qbaker.map_add"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        return baker.bake_groups

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
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps.add()
        bake_group.active_map_index = len(bake_group.maps) - 1
        map.name = uuid.uuid4().hex[:8]
        map.label = MAP_TYPES[self.type][1]
        map.type = self.type
        return {"FINISHED"}


class QBAKER_OT_map_load(Operator):
    bl_label = "Load Maps"
    bl_idname = "qbaker.map_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        return bake_group.groups if bake_group.use_high_to_low else bake_group.objects

    @classmethod
    def description(cls, context, properties):
        return "Load maps based on Principled BSDF input sockets and values\n\nShift  •  Load maps based on Principled BSDF input sockets"

    def process_node_tree(self, node_tree, maps, check_values=True):
        """Process node tree to find map types based on BSDF inputs"""
        for node in node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                for input in node.inputs:
                    socket_name = input.name

                    # Skip sockets that don't map to our known types
                    if socket_name not in PRINCIPLED_SOCKET_MAP:
                        continue

                    map_type = None

                    # Special handling for inputs that need additional conditions
                    if socket_name == "Subsurface IOR" and node.subsurface_method != "RANDOM_WALK_SKIN":
                        continue
                    elif socket_name == "Subsurface Anisotropy" and node.subsurface_method == "BURLEY":
                        continue
                    elif socket_name in ("Normal", "Tangent", "Coat Normal"):
                        if input.is_linked:
                            map_type = PRINCIPLED_SOCKET_MAP[socket_name]
                    else:
                        # Check if input is linked or has non-default value
                        if input.is_linked:
                            map_type = PRINCIPLED_SOCKET_MAP[socket_name]
                        elif check_values and socket_name in SOCKET_DEFAULTS:
                            # Compare with default values
                            if hasattr(input.default_value, "__len__"):
                                if input.default_value[:] != SOCKET_DEFAULTS[socket_name]:
                                    map_type = PRINCIPLED_SOCKET_MAP[socket_name]
                            elif input.default_value != SOCKET_DEFAULTS[socket_name]:
                                map_type = PRINCIPLED_SOCKET_MAP[socket_name]

                    # Add the map if it doesn't exist
                    if map_type and all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.map_add(type=map_type)

            # Handle node groups recursively
            elif node.type == "GROUP":
                self.process_node_tree(node.node_tree, maps, check_values)

            # Check for displacement in output nodes
            elif node.type == "OUTPUT_MATERIAL":
                if node.inputs["Displacement"].is_linked:
                    map_type = "DISPLACEMENT"
                    if all(map.type != map_type for map in maps):
                        bpy.ops.qbaker.map_add(type=map_type)

    def invoke(self, context, event):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        maps = baker.maps if baker.use_map_global else bake_group.maps

        # Get all objects from either high-to-low groups or direct objects
        objects = []
        if bake_group.use_high_to_low:
            objects = [item.object for group in bake_group.groups for item in group.low_poly]
        else:
            objects = [item.object for item in bake_group.objects]

        for obj in objects:
            if not obj.material_slots:
                continue

            for slot in obj.material_slots:
                if not slot.material:
                    self.report({"WARNING"}, "Slot has no material")
                    continue

                if not slot.material.use_nodes:
                    self.report({"WARNING"}, f"Enable nodes on the '{slot.material.name}'")
                    continue

                # Check node tree with appropriate method based on shift key
                self.process_node_tree(slot.material.node_tree, maps, check_values=not event.shift)

        return {"FINISHED"}


class QBAKER_OT_map_include(Operator):
    bl_label = "Include Map"
    bl_idname = "qbaker.map_include"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            return baker.maps
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            return bake_group.maps

        return False

    @classmethod
    def description(cls, context, properties):
        return "Include the map\n\nShift  •  Include all the maps\nCtrl    •  Isolate the map"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker

        if self.baker.use_map_global:
            self.bake_group = self.baker
        else:
            self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]

        self.map = self.bake_group.maps[self.index]
        self.include = self.map.use_include

        if event.shift:
            for group in self.bake_group.maps:
                group.use_include = not self.include
        elif event.ctrl:
            if any(group.use_include for group in self.bake_group.maps if group != self.map):
                for group in self.bake_group.maps:
                    group.use_include = False
            else:
                for group in self.bake_group.maps:
                    group.use_include = not group.use_include

            self.map.use_include = True
        else:
            self.map.use_include = not self.include

        return {"FINISHED"}


class QBAKER_OT_map_remove(Operator):
    bl_label = "Remove"
    bl_idname = "qbaker.map_remove"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            return baker.maps
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            return bake_group.maps

        return False

    @classmethod
    def description(cls, context, properties):
        return "Remove the map\n\nShift  •  Remove all the maps\nCtrl    •  Remove all the other maps"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker

        if self.baker.use_map_global:
            self.bake_group = self.baker
        else:
            self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]

        self.map = self.bake_group.maps[self.index]

        if hasattr(self.map, "occlusion") and self.map.occlusion.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "cavity") and self.map.cavity.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "curvature") and self.map.curvature.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "edge") and self.map.edge.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "gradient") and self.map.gradient.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "height") and self.map.height.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "thickness") and self.map.thickness.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "toon_shadow") and self.map.toon_shadow.use_preview:
            self.remove_nodes()
        elif hasattr(self.map, "xyz") and self.map.xyz.use_preview:
            self.remove_nodes()

        if event.shift:
            self.bake_group.maps.clear()
            self.bake_group.active_map_index = 0
        elif event.ctrl:
            for map in reversed(self.bake_group.maps):
                if map != self.map:
                    self.bake_group.maps.remove(self.bake_group.maps.find(map.name))
                    self.bake_group.active_map_index = min(
                        max(0, self.bake_group.active_map_index - 1), len(self.bake_group.maps) - 1
                    )
        else:
            self.bake_group.maps.remove(self.index)
            self.bake_group.active_map_index = min(
                max(0, self.bake_group.active_map_index - 1), len(self.bake_group.maps) - 1
            )

        return {"FINISHED"}

    def remove_nodes(self):
        bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]

        def remove_qb_nodes(material_slots):
            for slot in material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    for node in node_tree.nodes:
                        if node.name.split("_")[0] == "QB":
                            node_tree.nodes.remove(node)

        if bake_group.use_high_to_low:
            for group in bake_group.groups:
                for item in group.low_poly:
                    remove_qb_nodes(item.object.material_slots)
        else:
            for item in bake_group.objects:
                remove_qb_nodes(item.object.material_slots)


classes = (
    QBAKER_OT_map_add,
    QBAKER_OT_map_load,
    QBAKER_OT_map_include,
    QBAKER_OT_map_remove,
)

register, unregister = bpy.utils.register_classes_factory(classes)
