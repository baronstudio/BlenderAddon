import bpy

from ..nodes import GeometryNode


class GeometryNodeTree(GeometryNode):
    """Create a Geometry Node group.

    Args:
        name (str, optional): Name of the node group. Defaults to "Geometry Nodes".
    """

    def __init__(self, name: str = "Geometry Nodes"):
        self.node_tree = bpy.data.node_groups.get(name) or bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.parent = None

    def frame(self, **kwargs) -> bpy.types.Node:
        frame = GeometryNode.frame(self.node_tree, **kwargs, parent=self.parent)
        self.parent = frame.node
        return self

    def node_group(self, **kwargs) -> bpy.types.GeometryNodeGroup:
        return GeometryNode.node_group(self.node_tree, **kwargs, parent=self.parent)

    def group_input(self, **kwargs) -> bpy.types.NodeGroupInput:
        return GeometryNode.group_input(self.node_tree, **kwargs, parent=self.parent)

    def group_output(self, **kwargs) -> bpy.types.NodeGroupOutput:
        return GeometryNode.group_output(self.node_tree, **kwargs, parent=self.parent)

    def resample_curve(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.resample_curve(self.node_tree, **kwargs, parent=self.parent)

    def set_spline_cyclic(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.set_spline_cyclic(self.node_tree, **kwargs, parent=self.parent)

    def curve_spiral(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.curve_spiral(self.node_tree, **kwargs, parent=self.parent)

    def set_position(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.set_position(self.node_tree, **kwargs, parent=self.parent)

    def transform(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.transform(self.node_tree, **kwargs, parent=self.parent)

    def active_camera(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.active_camera(self.node_tree, **kwargs, parent=self.parent)

    def object_info(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.object_info(self.node_tree, **kwargs, parent=self.parent)

    def self_object(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.self_object(self.node_tree, **kwargs, parent=self.parent)

    def vector_math(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.vector_math(self.node_tree, **kwargs, parent=self.parent)

    def switch(self, **kwargs) -> bpy.types.GeometryNode:
        return GeometryNode.switch(self.node_tree, **kwargs, parent=self.parent)

    # FunctionNodes

    def compare(self, **kwargs) -> bpy.types.FunctionNode:
        return GeometryNode.compare(self.node_tree, **kwargs, parent=self.parent)
