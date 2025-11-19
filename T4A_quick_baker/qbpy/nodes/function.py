import bpy
from mathutils import Vector

from .node import Node


class FunctionNode(Node):
    """Base class for function nodes."""

    # Input
    @staticmethod
    def vector(
        node_tree: bpy.types.NodeTree,
        name: str,
        label: str = None,
        vector: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Vector node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            vector (Vector, optional): Vector of the vector name. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Vector node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("FunctionNodeInputVector")
            node.name = name
        if label is not None:
            node.label = label
        if vector is not None:
            node.vector[0] = vector[0]
            node.vector[1] = vector[1]
            node.vector[2] = vector[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Utilities

    @staticmethod
    def compare(
        node_tree: bpy.types.NodeTree,
        name: str,
        label: str = None,
        data_type: str = "FLOAT",
        mode: str = "ELEMENT",
        operation: str = "GREATER_THAN",
        float_a: float = 0.0,
        float_b: float = 0.0,
        vector_a: Vector = Vector((0, 0, 0)),
        vector_b: Vector = Vector((0, 0, 0)),
        string_a: str = "",
        string_b: str = "",
        color_a: Vector = Vector((0.8, 0.8, 0.8, 1)),
        color_b: Vector = Vector((0.8, 0.8, 0.8, 1)),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Compare node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            data_type (str, optional): Data type of the compare node. Defaults to "FLOAT".
            mode (str, optional): Mode of the compare node. Defaults to "ELEMENT".
            operation (str, optional): Operation of the compare node. Defaults to "GREATER_THAN".
            float_a (float, optional): First float input. Defaults to 0.0.
            float_b (float, optional): Second float input. Defaults to 0.0.
            vector_a (Vector, optional): First vector input. Defaults to Vector((0, 0, 0)).
            vector_b (Vector, optional): Second vector input. Defaults to Vector((0, 0, 0)).
            string_a (str, optional): First string input. Defaults to "".
            string_b (str, optional): Second string input. Defaults to "".
            color_a (Vector, optional): First color input. Defaults to Vector((0.8, 0.8, 0.8, 1)).
            color_b (Vector, optional): Second color input. Defaults to Vector((0.8, 0.8, 0.8, 1)).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Compare node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("FunctionNodeCompare")
            node.name = name
        if label is not None:
            node.label = label

        node.data_type = data_type
        node.mode = mode
        node.operation = operation
        if data_type == "FLOAT":
            node.inputs["A"].default_value = float_a
            node.inputs["B"].default_value = float_b
        elif data_type == "VECTOR":
            node.inputs["A"].default_value = vector_a
            node.inputs["A"].default_value = vector_b
        elif data_type == "STRING":
            node.inputs["A"].default_value = string_a
            node.inputs["B"].default_value = string_b
        elif data_type == "RGBA":
            node.inputs["A"].default_value = color_a
            node.inputs["B"].default_value = color_b

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def align_euler_to_vector(
        node_tree: bpy.types.NodeTree,
        name: str,
        label: str = None,
        axis: str = None,
        pivot: str = None,
        factor: float = None,
        vector: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Align Euler to Vector node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            axis (str, optional): Axis of the align euler to vector node. Defaults to None.
            pivot (str, optional): Pivot of the align euler to vector node. Defaults to None.
            factor (float, optional): Factor of the align euler to vector node. Defaults to None.
            vector (Vector, optional): Vector of the align euler to vector node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Align Euler to Vector node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("FunctionNodeAlignEulerToVector")
            node.name = name
        if label is not None:
            node.label = label
        if axis is not None:
            node.axis = axis
        if pivot is not None:
            node.pivot = pivot
        if factor is not None:
            node.inputs[1].default_value = factor
        if vector is not None:
            node.inputs[2].default_value[0] = vector[0]
            node.inputs[2].default_value[1] = vector[1]
            node.inputs[2].default_value[2] = vector[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def random_value(
        node_tree: bpy.types.NodeTree,
        name: str,
        label: str = None,
        type: str = None,
        min: list = None,
        max: list = None,
        probability: float = None,
        seed: int = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Random value node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            type (str, optional): Data type of the random value node. Defaults to None.
            min (list, optional): Minimum value. Defaults to None.
            max (list, optional): Maximum value. Defaults to None.
            probability (float, optional): Probability. Defaults to None.
            seed (int, optional): Seed. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Random Value node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("FunctionNodeRandomValue")
            node.name = name
        if type is not None:
            node.data_type = type
        if label is not None:
            node.label = label
        if node.data_type in {"FLOAT"}:
            if min is not None:
                node.inputs[2].default_value = min[0]
            if max is not None:
                node.inputs[3].default_value = max[0]
        if node.data_type in {"INT"}:
            if min is not None:
                node.inputs[4].default_value = min[0]
            if max is not None:
                node.inputs[5].default_value = max[0]
        if node.data_type in {"FLOAT_VECTOR"}:
            if min is not None:
                node.inputs[0].default_value[0] = min[0]
                node.inputs[0].default_value[1] = min[1]
                node.inputs[0].default_value[2] = min[2]
            if max is not None:
                node.inputs[1].default_value[0] = max[0]
                node.inputs[1].default_value[1] = max[1]
                node.inputs[1].default_value[2] = max[2]
        if node.data_type in {"BOOLEAN"} and probability is not None:
            node.inputs[6].default_value = probability
        if seed is not None:
            node.inputs[8].default_value = seed

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def rotate_euler(
        node_tree: bpy.types.NodeTree,
        name: str,
        label: str = None,
        type: str = None,
        space: str = None,
        axis: list = None,
        rotate: list = None,
        angle: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Rotate Euler node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            type (str, optional): The type of the rotate euler node. Defaults to 'EULER'.
            space (str, optional): The space of the rotate euler node. Defaults to 'OBJECT'.
            axis (list, optional): The axis of the rotate euler node.
            rotate (list, optional): The rotate euler.
            angle (float, optional): The angle.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Rotate Euler node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("FunctionNodeRotateEuler")
            node.name = name
        if label is not None:
            node.label = label
        if type is not None:
            node.type = type
        if space is not None:
            node.space = space
        if type == "EULER" and rotate is not None:
            node.inputs[1].default_value[0] = rotate[0]
            node.inputs[1].default_value[1] = rotate[1]
            node.inputs[1].default_value[2] = rotate[2]
        if type == "AXIS_ANGLE":
            if axis is not None:
                node.inputs[2].default_value[0] = axis[0]
                node.inputs[2].default_value[1] = axis[1]
                node.inputs[2].default_value[2] = axis[2]
            if angle is not None:
                node.inputs[3].default_value = angle

        if parent is not None:
            node.parent = parent

        node.location = position
        return node
