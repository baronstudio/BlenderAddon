import bpy
from mathutils import Vector

from .function import FunctionNode
from .node import Node
from .shader import ShaderNode


class GeometryNode(ShaderNode, FunctionNode, Node):
    """Geometry node class for creating geometry nodes."""

    @staticmethod
    def node_group(
        node_tree: bpy.types.GeometryNodeTree,
        name: str = "Node Group",
        label: str = None,
        node_group: bpy.types.GeometryNodeTree = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.GeometryNodeGroup:
        """Create a Node Group node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Node Group".
            label (str, optional): Label of the node. Defaults to None.
            node_group (bpy.types.GeometryNodeTree, optional): Node group to use. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.GeometryNodeGroup: Node Group node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeGroup")
            node.name = name

        if label is not None:
            node.label = label

        node.node_tree = node_group
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Curve
    @staticmethod
    def resample_curve(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        mode: str = None,
        count: int = None,
        length: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Resample Curve node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (str, optional): Mode of the resample curve node. Defaults to None.
            count (int, optional): Count of the resample curve node. Defaults to None.
            length (float, optional): Length of the resample curve node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Resample Curve node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeResampleCurve")
            node.name = name
        if label is not None:
            node.label = label
        if mode is not None:
            node.mode = mode
        if node.mode == "COUNT" and count is not None:
            node.count = count
        if node.mode == "LENGTH" and length is not None:
            node.length = length
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def set_spline_cyclic(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        cyclic: bool = False,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Set Spline Cyclic node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            cyclic (bool, optional): Set the spline to cyclic.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Set Spline Cyclic node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeSetSplineCyclic")
            node.name = name
        if label is not None:
            node.label = label
        if cyclic is not None:
            node.inputs[2].default_value = cyclic
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Curve Primitives
    @staticmethod
    def curve_spiral(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        resolution: int = None,
        rotation: float = None,
        start_radius: float = None,
        end_radius: float = None,
        height: float = None,
        reverse: bool = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Spiral Curve node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            resolution (int, optional): The resolution of the spiral curve. Defaults to None.
            rotation (float, optional): The rotation of the spiral curve. Defaults to None.
            start_radius (float, optional): The start radius of the spiral curve. Defaults to None.
            end_radius (float, optional): The end radius of the spiral curve. Defaults to None.
            height (float, optional): The height of the spiral curve. Defaults to None.
            reverse (bool, optional): Reverse the spiral curve. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Spiral Curve node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeCurveSpiral")
            node.name = name
        if label is not None:
            node.label = label
        if resolution is not None:
            node.inputs[0].default_value = resolution
        if rotation is not None:
            node.inputs[1].default_value = rotation
        if start_radius is not None:
            node.inputs[2].default_value = start_radius
        if end_radius is not None:
            node.inputs[3].default_value = end_radius
        if height is not None:
            node.inputs[4].default_value = height
        if reverse is not None:
            node.inputs[5].default_value = reverse
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Geometry
    @staticmethod
    def set_position(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        offset: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Set Position node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            offset (Vector, optional): The offset of the set position node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Set Position node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeSetPosition")
            node.name = name
        if label is not None:
            node.label = label
        if offset is not None:
            node.inputs[3].default_value[0] = offset[0]
            node.inputs[3].default_value[1] = offset[1]
            node.inputs[3].default_value[2] = offset[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def transform(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        translation: Vector = None,
        rotation: Vector = None,
        scale: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Transform node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            translation (Vector, optional): The translation of the transform node.
            rotation (Vector, optional): The rotation of the transform node.
            scale (Vector, optional): The scale of the transform node.
            hide (bool, optional): Hide the node. Defaults to False.

        Returns:
            bpy.types.Node: Transform node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeTransform")
            node.name = name
        if label is not None:
            node.label = label
        if translation is not None:
            node.inputs[1].default_value[0] = translation[0]
            node.inputs[1].default_value[1] = translation[1]
            node.inputs[1].default_value[2] = translation[2]
        if rotation is not None:
            node.inputs[2].default_value[0] = rotation[0]
            node.inputs[2].default_value[1] = rotation[1]
            node.inputs[2].default_value[2] = rotation[2]
        if scale is not None:
            node.inputs[3].default_value[0] = scale[0]
            node.inputs[3].default_value[1] = scale[1]
            node.inputs[3].default_value[2] = scale[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Input

    @staticmethod
    def active_camera(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Active Camera node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Active Camera node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeInputActiveCamera")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def object_info(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        transform_space: str = None,
        object: bpy.types.Object = None,
        as_instance: bool = False,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Object Info node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            transform_space (str, optional): The transformation of the vector and geometry outputs. Defaults to 'ORIGINAL'.
            object (bpy.types.Object, optional): The object to use.
            as_instance (bool, optional): Use the object as an instance. Defaults to False.
            show_options (bool, optional): Show the options of the compare node. Defaults to False.
            hide (bool, optional): Hide the compare node. Defaults to False.
            position (Vector, optional): The position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Object Info node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeObjectInfo")
            node.name = name
        if label is not None:
            node.label = label
        if transform_space is not None:
            node.transform_space = transform_space
        if object is not None:
            node.inputs[0].default_value = object
        node.inputs[1].default_value = as_instance
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def self_object(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Self Object node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Self Object node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeSelfObject")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def input_id(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an ID node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: ID node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeInputID")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def input_position(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Position node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Position node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeInputPosition")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Instance

    def instance_on_points(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        pick_instance: bool = False,
        rotation: float = None,
        scale: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Instance on Points node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            pick_instance (bool, optional): Pick an instance to use.
            rotation (float, optional): The rotation of the instance on point node.
            scale (float, optional): The scale of the instance on point node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Instance on Points node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeInstanceOnPoints")
            node.name = name
        if label is not None:
            node.label = label
        if rotation is not None:
            node.inputs[5].default_value = rotation
        if scale is not None:
            node.inputs[6].default_value = scale
        node.inputs[3].default_value = pick_instance
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def realize_instances(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Realize Instance node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Realize Instance node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeRealizeInstances")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Mesh
    @staticmethod
    def mesh_to_curve(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mesh to Curve node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mesh to Curve node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeMeshToCurve")
            node.name = name
        if label is not None:
            node.label = label
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Mesh Primitives
    @staticmethod
    def mesh_line(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        mode: str = None,
        count_mode: str = None,
        count: int = None,
        resolution: float = None,
        start_location: Vector = None,
        end_location: Vector = None,
        offset: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mesh Line node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (str, optional): The mode of the mesh line node. Defaults to 'OFFSET'.
            count_mode (str, optional): The count mode of the mesh line node. Defaults to 'TOTAL'.
            count (int, optional): The count of the mesh line node. Defaults to None.
            resolution (float, optional): The resolution of the mesh line node. Defaults to None.
            start_location (Vector, optional): The start location of the mesh line node. Defaults to None.
            end_location (Vector, optional): The end location of the mesh line node. Defaults to None.
            offset (Vector, optional): The offset of the mesh line node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mesh Line node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeMeshLine")
            node.name = name
        if label is not None:
            node.label = label
        if mode is not None:
            node.mode = mode
        if count_mode is not None:
            node.count_mode = count_mode
        if node.count_mode == "TOTAL" and count is not None:
            node.inputs[0].default_value = count
        if node.count_mode == "RESOLUTION" and resolution is not None:
            node.inputs[0].default_value = resolution
        if node.mode == "OFFSET":
            if start_location is not None:
                node.inputs[2].default_value[0] = start_location[0]
                node.inputs[2].default_value[1] = start_location[1]
                node.inputs[2].default_value[2] = start_location[2]
            if offset is not None:
                node.inputs[3].default_value[0] = offset[0]
                node.inputs[3].default_value[1] = offset[1]
                node.inputs[3].default_value[2] = offset[2]
        if node.mode == "END_POINTS":
            if start_location is not None:
                node.inputs[2].default_value[0] = start_location[0]
                node.inputs[2].default_value[1] = start_location[1]
                node.inputs[2].default_value[2] = start_location[2]
            if end_location is not None:
                node.inputs[3].default_value[0] = end_location[0]
                node.inputs[3].default_value[1] = end_location[1]
                node.inputs[3].default_value[2] = end_location[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Utilities
    @staticmethod
    def switch(
        node_tree: bpy.types.GeometryNodeTree,
        name: str,
        label: str = None,
        input_type: str = "GEOMETRY",
        default: bool = False,
        false: bpy.types.AnyType = None,
        true: bpy.types.AnyType = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Switch node.

        Args:
            node_tree (bpy.types.GeometryNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            input_type (str, optional): The type of the switch node. Defaults to 'GEOMETRY'.
            default (bool, optional): Set the switch node. Defaults to False.
            false (bpy.types.AnyType, optional): The false value of the switch node. Defaults to None.
            true (bpy.types.AnyType, optional): The true value of the switch node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Switch node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("GeometryNodeSwitch")
            node.name = name
        if label is not None:
            node.label = label

        node.input_type = input_type
        node.inputs["Switch"].default_value = default
        if input_type not in {"GEOMETRY", "MATRIX"}:
            node.inputs["False"].default_value = false
            node.inputs["True"].default_value = true
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node
