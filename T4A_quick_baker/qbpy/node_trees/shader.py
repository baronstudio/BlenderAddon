import bpy

from ..nodes import ShaderNode


class ShaderNodeTree(ShaderNode):
    """Create a Node Group.

    Args:
        name (str, optional): Name of the node group. Defaults to "Shaders Nodes".
    """

    def __init__(self, name: str = "Shaders Nodes"):
        self.node_tree = bpy.data.node_groups.get(name) or bpy.data.node_groups.new(name, "ShaderNodeTree")
        self.parent = None

    def frame(self, **kwargs) -> bpy.types.Node:
        frame = ShaderNode.frame(self.node_tree, **kwargs, parent=self.parent)
        self.parent = frame.node
        return self

    def node_group(self, **kwargs) -> bpy.types.ShaderNodeGroup:
        return ShaderNode.node_group(self.node_tree, **kwargs, parent=self.parent)

    def group_input(self, **kwargs) -> bpy.types.NodeGroupInput:
        return ShaderNode.group_input(self.node_tree, **kwargs, parent=self.parent)

    def group_output(self, **kwargs) -> bpy.types.NodeGroupOutput:
        return ShaderNode.group_output(self.node_tree, **kwargs, parent=self.parent)

    def ambient_occlusion(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.ambient_occlusion(self.node_tree, **kwargs, parent=self.parent)

    def bevel(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.bevel(self.node_tree, **kwargs, parent=self.parent)

    def color_attribute(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.color_attribute(self.node_tree, **kwargs, parent=self.parent)

    def geometry(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.geometry(self.node_tree, **kwargs, parent=self.parent)

    def texture_coordinate(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.texture_coordinate(self.node_tree, **kwargs, parent=self.parent)

    def rgb(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.rgb(self.node_tree, **kwargs, parent=self.parent)

    def uvmap(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.uvmap(self.node_tree, **kwargs, parent=self.parent)

    def value(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.value(self.node_tree, **kwargs, parent=self.parent)

    def material_output(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.material_output(self.node_tree, **kwargs, parent=self.parent)

    def diffuse_bsdf(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.diffuse_bsdf(self.node_tree, **kwargs, parent=self.parent)

    def toon_bsdf(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.toon_bsdf(self.node_tree, **kwargs, parent=self.parent)

    def emission(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.emission(self.node_tree, **kwargs, parent=self.parent)

    def mix_shader(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.mix_shader(self.node_tree, **kwargs, parent=self.parent)

    def gradient_texture(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.gradient_texture(self.node_tree, **kwargs, parent=self.parent)

    def image_texture(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.image_texture(self.node_tree, **kwargs, parent=self.parent)

    def gamma(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.gamma(self.node_tree, **kwargs, parent=self.parent)

    def bright_contrast(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.bright_contrast(self.node_tree, **kwargs, parent=self.parent)

    def invert(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.invert(self.node_tree, **kwargs, parent=self.parent)

    def mix_rgb(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.mix_rgb(self.node_tree, **kwargs, parent=self.parent)

    def mix(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.mix(self.node_tree, **kwargs, parent=self.parent)

    def displacement(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.displacement(self.node_tree, **kwargs, parent=self.parent)

    def mapping(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.mapping(self.node_tree, **kwargs, parent=self.parent)

    def normal_map(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.normal_map(self.node_tree, **kwargs, parent=self.parent)

    def bump(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.bump(self.node_tree, **kwargs, parent=self.parent)

    def vector_rotate(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.vector_rotate(self.node_tree, **kwargs, parent=self.parent)

    def vector_transform(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.vector_transform(self.node_tree, **kwargs, parent=self.parent)

    def combine_color(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.combine_color(self.node_tree, **kwargs, parent=self.parent)

    def combine_xyz(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.combine_xyz(self.node_tree, **kwargs, parent=self.parent)

    def color_ramp(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.color_ramp(self.node_tree, **kwargs, parent=self.parent)

    def map_range(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.map_range(self.node_tree, **kwargs, parent=self.parent)

    def math(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.math(self.node_tree, **kwargs, parent=self.parent)

    def separate_color(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.separate_color(self.node_tree, **kwargs, parent=self.parent)

    def separate_xyz(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.separate_xyz(self.node_tree, **kwargs, parent=self.parent)

    def vector_math(self, **kwargs) -> bpy.types.ShaderNode:
        return ShaderNode.vector_math(self.node_tree, **kwargs, parent=self.parent)
