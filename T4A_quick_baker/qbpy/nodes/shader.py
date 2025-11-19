import bpy
from mathutils import Vector

from .node import Node


class ShaderNode(Node):
    """Shader node class for creating shader nodes."""

    @staticmethod
    def node_group(
        node_tree: bpy.types.ShaderNodeTree,
        name: str = "Node Group",
        label: str = None,
        node_group: bpy.types.ShaderNodeTree = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.ShaderNodeGroup:
        """Create a Node Group node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Node Group".
            label (str, optional): Label of the node. Defaults to None.
            node_group (bpy.types.ShaderNodeTree, optional): Node group to use. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.ShaderNodeGroup: Node Group node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeGroup")
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

    # Input
    @staticmethod
    def ambient_occlusion(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        samples: int = 16,
        inside: bool = False,
        only_local: bool = False,
        color: tuple = (1, 1, 1, 1),
        distance: float = 1.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Ambient Occlusion node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            samples (int, optional): Number of rays to trace per shader evaluation. Defaults to 16.
            inside (bool, optional): Trace rays towards the inside of the object. Defaults to False.
            only_local (bool, optional): Only consider the object itself when computing AO. Defaults to False.
            color (tuple, optional): Color of the amobient occlusion. Defaults to (1, 1, 1, 1).
            distance (float, optional): Distace of the ambient occlution. Defaults to 1.0.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Ambient Occlusion node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeAmbientOcclusion")
            node.name = name

        if label is not None:
            node.label = label

        node.samples = samples
        node.inside = inside
        node.only_local = only_local
        node.inputs["Color"].default_value = color
        node.inputs["Distance"].default_value = distance
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def bevel(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        samples: int = 4,
        radius: float = 0.05,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Bevel node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            samples (int, optional): Number of rays to trace per shader evaluation. Defaults to 4.
            radius (float, optional): Radius of the bevel. Defaults to 0.05.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Bevel node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBevel")
            node.name = name

        if label is not None:
            node.label = label

        node.samples = samples
        node.inputs["Radius"].default_value = radius
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def color_attribute(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        layer_name: str = "",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Color Attribute node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            layer_name (str, optional): The UV layer name.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Color Attribute node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeVertexColor")
            node.name = name

        if label is not None:
            node.label = label

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        node.layer_name = layer_name
        return node

    @staticmethod
    def geometry(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Geometry node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Geometry node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeNewGeometry")
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
    def texture_coordinate(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Texture Coordinate node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Texture Coordinate node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeTexCoord")
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
    def rgb(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (0.5, 0.5, 0.5, 1.0),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a RGB node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple, optional): The output color. Defaults to (0.5, 0.5, 0.5, 1.0).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: RGB node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeRGB")
            node.name = name

        if label is not None:
            node.label = label

        if color is not None:
            node.outputs["Color"].default_value = color

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def uvmap(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        from_instancer: bool = False,
        uv_map: str = "",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an UV Map node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            from_instancer (bool, optional): Use the parent of the instance object if possible. Defaults to False.
            uv_map (str, optional): UV coordinates to be used for mapping. Defaults to "".
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: UV Map node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeUVMap")
            node.name = name

        if label is not None:
            node.label = label

        node.from_instancer = from_instancer
        node.uv_map = uv_map
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def value(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        value: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Value node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            value (float, optional): The float factor.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Value node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeValue")
            node.name = name

        if label is not None:
            node.label = label

        if value is not None:
            node.outputs["Value"].default_value = value
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Output
    @staticmethod
    def material_output(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        target: str = "ALL",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Material Output node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            target (enum in ['ALL', 'EEVEE', 'CYCLES'], default 'ALL'): The target of the material output node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Material Output node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeOutputMaterial")
            node.name = name

        if label is not None:
            node.label = label

        node.target = target
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Shader

    @staticmethod
    def add_shader(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Add Shader node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Add Shader node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeAddShader")
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
    def diffuse_bsdf(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (0.8, 0.8, 0.8, 1),
        roughness: float = 0.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Diffuse BSDF node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple, optional): The color of the diffuse BSDF node.
            roughness (float, optional): The roughness of the diffuse BSDF node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Diffuse BSDF node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBsdfDiffuse")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Color"].default_value = color
        node.inputs["Roughness"].default_value = roughness
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def emission(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (1, 1, 1, 1),
        strength: float = 1.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Emission node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple, optional): The color of the emission node. Defaults to (1, 1, 1, 1).
            strength (float, optional): The strength of the emission node. Defaults to 1.0.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Emission node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeEmission")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Color"].default_value = color
        node.inputs["Strength"].default_value = strength
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def mix_shader(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        fac: float = 0.5,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mix Shader node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            fac (float, optional): The float factor.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mix Shader node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMixShader")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Fac"].default_value = fac
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def toon_bsdf(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        component="DIFFUSE",
        color: tuple = (0.8, 0.8, 0.8, 1),
        size: float = 0.5,
        smooth: float = 0.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Toon BSDF node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            component (enum in ['DIFFUSE', 'GLOSSY'], default 'DIFFUSE'): The component of the toon BSDF node.
            color (tuple, optional): The color of the toon BSDF node.
            size (float, optional): The size of the toon BSDF node.
            smooth (float, optional): The smooth of the toon BSDF node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Toon BSDF node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBsdfToon")
            node.name = name

        if label is not None:
            node.label = label

        node.component = component
        node.inputs["Color"].default_value = color
        node.inputs["Size"].default_value = size
        node.inputs["Smooth"].default_value = smooth
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def translucent_bsdf(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (0.8, 0.8, 0.8, 1),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Translucent BSDF node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple, optional): The color of the translucent BSDF node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Translucent BSDF node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBsdfTranslucent")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Color"].default_value = color
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Texture
    @staticmethod
    def gradient_texture(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        gradient_type: str = "LINEAR",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Gradient Texture node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            gradient_type (enum in ['LINEAR', 'QUADRATIC', 'EASING', 'DIAGONAL', 'SPHERICAL', 'QUADRATIC_SPHERE', 'RADIAL'], default 'LINEAR'): The type of the gradient.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Gradient Texture node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeTexGradient")
            node.name = name

        if label is not None:
            node.label = label

        node.gradient_type = gradient_type
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def image_texture(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        image: bpy.types.Image = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Image Texture node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            image (bpy.types.Image, optional): The image to use. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Image Texture node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeTexImage")
            node.name = name

        if label is not None:
            node.label = label

        node.image = image
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Color

    @staticmethod
    def gamma(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (1, 1, 1, 1),
        gamma: float = 1.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Gamma node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple, optional): The color of the gamma node. Defaults to (1, 1, 1, 1).
            bright (float, optional): The bright of the gamma node. Defaults to 0.0.
            contrast (float, optional): The contrast of the gamma node. Defaults to 0.0.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Gamma node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeGamma")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Color"].default_value = color
        node.inputs["Gamma"].default_value = gamma
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def bright_contrast(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        color: tuple = (1, 1, 1, 1),
        bright: float = 0.0,
        contrast: float = 0.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Bright/Contrast node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            color (tuple): The color of the bright_contrast node.
            bright (float): The bright of the bright_contrast node.
            contrast (float): The contrast of the bright_contrast node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Bright/Contrast node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBrightContrast")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Color"].default_value = color
        node.inputs["Bright"].default_value = bright
        node.inputs["Contrast"].default_value = contrast
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def invert(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        fac: float = 1.0,
        color: tuple = (0, 0, 0, 1),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Invert node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            fac (float): The factor to use.
            color (tuple): The color of the invert node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Invert node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeInvert")
            node.name = name

        if label is not None:
            node.label = label

        node.inputs["Fac"].default_value = fac
        node.inputs["Color"].default_value = color
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def mix_rgb(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        blend_type: str = "MIX",
        clamp: bool = False,
        fac: float = 0.5,
        color_1: float = (0.5, 0.5, 0.5, 1.0),
        color_2: float = (0.5, 0.5, 0.5, 1.0),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mix RGB node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            blend_type (enum in ['MIX', 'DARKEN', 'MULTIPLY', 'BURN', 'LIGHTEN', 'SCREEN', 'DODGE', 'ADD', 'OVERLAY', 'SOFT_LIGHT', 'LINEAR_LIGHT', 'DIFFERENCE', 'SUBTRACT', 'DIVIDE', 'HUE', 'SATURATION', 'COLOR', 'VALUE'], default 'MIX'): The blend type.
            clamp (bool): Whether to clamp.
            fac (float): The factor to use.
            color_1 (tuple): The color 1.
            color_2 (tuple): The color 2.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mix RGB node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMixRGB")
            node.name = name

        if label is not None:
            node.label = label

        node.blend_type = blend_type
        node.use_clamp = clamp
        node.inputs["Fac"].default_value = fac
        node.inputs["Color1"].default_value = color_1
        node.inputs["Color2"].default_value = color_2
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def mix(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        data_type: str = "FLOAT",
        blend_type: str = "MIX",
        clamp_result: bool = False,
        clamp_factor: bool = True,
        factor: float = 0.5,
        float_a: float = 0.0,
        float_b: float = 0.0,
        vector_a: Vector = Vector((0.0, 0.0, 0.0)),
        vector_b: Vector = Vector((0.0, 0.0, 0.0)),
        color_a: tuple = (0.5, 0.5, 0.5, 1.0),
        color_b: tuple = (0.5, 0.5, 0.5, 1.0),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mix node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            data_type (str, optional): The data type. Defaults to "FLOAT".
            blend_type (str, optional): The blend type. Defaults to "MIX".
            clamp_result (bool, optional): Clamp the result to [0, 1] range. Defaults to False.
            clamp_factor (bool, optional): Clamp the factor to [0, 1] range. Defaults to True.
            factor (float, optional): Amount of mixing between the A and B inputs. Defaults to 0.5.
            float_a (float, optional): Value of the A input if data_type is "FLOAT". Defaults to 0.0.
            float_b (float, optional): Value of the B input if data_type is "FLOAT". Defaults to 0.0.
            vector_a (Vector, optional): Value of the A input if data_type is "VECTOR". Defaults to Vector((0.0, 0.0, 0.0)).
            vector_b (Vector, optional): Value of the B input if data_type is "VECTOR". Defaults to Vector((0.0, 0.0, 0.0)).
            color_a (tuple, optional): Value of the A input if data_type is "RGBA". Defaults to (0.5, 0.5, 0.5, 1.0).
            color_b (tuple, optional): Value of the B input if data_type is "RGBA". Defaults to (0.5, 0.5, 0.5, 1.0).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mix node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMix")
            node.name = name

        if label is not None:
            node.label = label

        node.data_type = data_type
        node.blend_type = blend_type
        node.clamp_result = clamp_result
        node.clamp_factor = clamp_factor

        node.inputs["Factor"].default_value = factor
        if node.data_type == "FLOAT":
            node.inputs["A"].default_value = float_a
            node.inputs["B"].default_value = float_b
        elif node.data_type == "VECTOR":
            node.inputs["A"].default_value = vector_a
            node.inputs["B"].default_value = vector_b
        elif node.data_type == "RGBA":
            node.inputs["A"].default_value = color_a
            node.inputs["B"].default_value = color_b

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Vector
    @staticmethod
    def displacement(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        space: str = "OBJECT",
        height: float = 0.0,
        midlevel: float = 0.5,
        scale: float = 1.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Displacement node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            space (enum in ['OBJECT', 'WORLD'], default 'OBJECT'): Space of the input height.
            height (float, optional): Default value of input height.
            midlevel (float, optional): Default value of input midlevel.
            scale (float, optional): Default value of input scale.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Displacement node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeDisplacement")
            node.name = name

        if label is not None:
            node.label = label

        node.space = space
        node.inputs["Height"].default_value = height
        node.inputs["Midlevel"].default_value = midlevel
        node.inputs["Scale"].default_value = scale
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def mapping(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        vector_type: str = "POINT",
        vector: Vector = Vector((0.0, 0.0, 0.0)),
        location: Vector = Vector((0.0, 0.0, 0.0)),
        rotation: Vector = Vector((0.0, 0.0, 0.0)),
        scale: Vector = Vector((1.0, 1.0, 1.0)),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Mapping node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            vector_type (enum in ['POINT', 'TEXTURE', 'VECTOR', 'NORMAL'], default 'POINT'): Type of vector that the mapping transforms.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Mapping node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMapping")
            node.name = name

        if label is not None:
            node.label = label

        node.vector_type = vector_type
        node.inputs["Location"].default_value = location
        node.inputs["Rotation"].default_value = rotation
        node.inputs["Scale"].default_value = scale
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def normal_map(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        space: str = "TANGENT",
        uv_map: str = "",
        strength: float = 1.0,
        color: tuple = (0.5, 0.5, 1, 1),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Normal node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            space (str, optional): Space of the input normal. Defaults to 'TANGENT'.
            uv_map (str, optional): UV Map for tangent space maps. Defaults to "".
            strength (float, optional): Strength of the normal map. Defaults to 1.0.
            color (tuple, optional): Color of the normal map. Defaults to (0.5, 0.5, 1, 1).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Normal node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeNormalMap")
            node.name = name

        if label is not None:
            node.label = label

        node.space = space
        node.uv_map = uv_map
        node.inputs["Strength"].default_value = strength
        node.inputs["Color"].default_value = color
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def bump(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        invert: bool = False,
        strength: float = 1.0,
        distance: float = 1.0,
        height: float = 1.0,
        normal: tuple = (0.0, 0.0, 0.0),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Bump node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            invert (bool, optional): Invert the bump mapping. Defaults to False.
            strength (float, optional): Strength of the bump mapping. Defaults to 1.0.
            distance (float, optional): Distance of the bump mapping. Defaults to 1.0.
            height (float, optional): Height input value. Defaults to 1.0.
            normal (tuple, optional): Normal input value. Defaults to (0.0, 0.0, 0.0).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Bump node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeBump")
            node.name = name

        if label is not None:
            node.label = label

        node.invert = invert
        node.inputs["Strength"].default_value = strength
        node.inputs["Distance"].default_value = distance
        node.inputs["Height"].default_value = height
        node.inputs["Normal"].default_value = normal
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def vector_rotate(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        type: str = None,
        invert: bool = False,
        center: Vector = None,
        axis: Vector = None,
        angle: float = None,
        rotation: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Add a Vector Rotate node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            type (enum in ['AXIS_ANGLE', 'X_AXIS', 'Y_AXIS', 'Z_AXIS', 'EULER_XYZ'], default 'AXIS_ANGLE'): The type of the vector rotate node.
            invert (bool, optional): Invert the rotation.
            center (3D Vector, optional): The center of the rotation.
            axis (3D Vector, optional): The axis of the rotation.
            angle (float, optional): The angle of the rotation.
            rotation (3D Vector, optional): The rotation of the rotation.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Vector Rotate node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeVectorRotate")
            node.name = name

        if label is not None:
            node.label = label

        if type is not None:
            node.rotation_type = type

        if node.rotation_type in {
            "AXIS_ANGLE",
            "X_AXIS",
            "Y_AXIS",
            "Z_AXIS",
            "EULER_XYZ",
        }:
            if center is not None:
                node.inputs[1].default_value[0] = center[0]
                node.inputs[1].default_value[1] = center[1]
                node.inputs[1].default_value[2] = center[2]
            if node.rotation_type in {"AXIS_ANGLE"} and axis is not None:
                node.inputs[2].default_value[0] = axis[0]
                node.inputs[2].default_value[1] = axis[1]
                node.inputs[2].default_value[2] = axis[2]
            if node.rotation_type in {"EULER_XYZ"}:
                if rotation is not None:
                    node.inputs[4].default_value[0] = rotation[0]
                    node.inputs[4].default_value[1] = rotation[1]
                    node.inputs[4].default_value[2] = rotation[2]
            elif angle is not None:
                node.inputs[3].default_value = angle

        node.invert = invert
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def vector_transform(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        vector_type: str = "VECTOR",
        convert_from: str = "WORLD",
        convert_to: str = "OBJECT",
        vector: Vector = Vector((0.5, 0.5, 0.5)),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Add a Vector Transform node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            vector_type (enum in ['POINT', 'VECTOR', 'NORMAL'], default 'POINT'): The type of the vector transform node.
            convert_from (enum in ['WORLD', 'OBJECT', 'CAMERA'], default 'WORLD'): Space to convert from.
            convert_to (enum in ['WORLD', 'OBJECT', 'CAMERA'], default 'OBJECT'): Space to convert to.
            vector (3D Vector, optional): The vector inputs.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Vector Transform node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeVectorTransform")
            node.name = name
        if label is not None:
            node.label = label

        node.vector_type = vector_type
        node.convert_from = convert_from
        node.convert_to = convert_to
        node.inputs[0].default_value = vector
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Converter

    @staticmethod
    def combine_color(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        mode: str = "RGB",
        input_0: float = 0.0,
        input_1: float = 0.0,
        input_2: float = 0.0,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Combine Color node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (enum in ['RGB', 'HSV', 'HSL'], default 'RGB'): Mode of color processing.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Combine Color node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeCombineColor")
            node.name = name

        if label is not None:
            node.label = label

        node.mode = mode
        node.inputs[0].default_value = input_0
        node.inputs[1].default_value = input_1
        node.inputs[2].default_value = input_2
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def combine_xyz(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        vector: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Combine XYZ node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            vector (Vector, optional): The vector inputs.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Combine XYZ node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeCombineXYZ")
            node.name = name

        if label is not None:
            node.label = label

        if vector is not None:
            node.inputs[0].default_value = vector[0]
            node.inputs[1].default_value = vector[1]
            node.inputs[2].default_value = vector[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def color_ramp(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Color Ramp node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Color Ramp node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeValToRGB")
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
    def map_range(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        type: str = None,
        clamp: bool = False,
        input_0: float = None,
        input_1: float = None,
        input_2: float = None,
        input_3: float = None,
        input_4: float = None,
        input_5: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Map Range node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            type (enum in ['LINEAR', 'STEPPED', 'SMOOTHSTEP', 'SMOOTHERSTEP'], default 'LINEAR'): The type of the map range node.
            clamp (bool, optional): Clamp the values.
            input_0 (float, optional): The input 0 of the map range node.
            input_1 (float, optional): The input 1 of the map range node.
            input_2 (float, optional): The input 2 of the map range node.
            input_3 (float, optional): The input 3 of the map range node.
            input_4 (float, optional): The input 4 of the map range node.
            input_5 (float, optional): The input 5 of the map range node.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Map Range node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMapRange")
            node.name = name
        if type is not None:
            node.interpolation_type = type

        if label is not None:
            node.label = label

        if input_0 is not None:
            node.inputs[0].default_value = input_0
        if input_1 is not None:
            node.inputs[1].default_value = input_1
        if input_2 is not None:
            node.inputs[2].default_value = input_2
        if input_3 is not None:
            node.inputs[3].default_value = input_3
        if input_4 is not None:
            node.inputs[4].default_value = input_4
        if node.interpolation_type in {"LINEAR", "STEPPED"}:
            node.clamp = clamp
        if node.interpolation_type in {"STEPPED"}:
            node.inputs[5].default_value = input_5
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def math(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        operation: str = None,
        use_clamp: bool = False,
        input_0: float = None,
        input_1: float = None,
        input_2: float = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Math node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            operation (enum in [
            'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'MULTIPLY_ADD', 'POWER', 'LOGARITHM', 'SQRT', 'INVERSE_SQRT', 'ABSOLUTE', 'EXPONENT',
            'MINIMUM', 'MAXIMUM', 'LESS_THAN', 'GREATER_THAN', 'SIGN', 'COMPARE', 'SMOOTH_MIN', 'SMOOTH_MAX', 'ROUND', 'FLOOR', 'CEIL', 'TRUNC',
            'FRACT', 'MODULO', 'WRAP', 'SNAP', 'PINGPONG', 'SINE', 'COSINE', 'TANGENT', 'ARCSINE', 'ARCCOSINE', 'ARCTANGENT', 'ARCTAN2', 'SINH',
            'COSH', 'TANH', 'RADIANS', 'DEGREES'], default 'ADD'): The operation of the math node.
            use_clamp (bool, optional): Use clamp.
            input_0 (float, optional): The input 0.
            input_1 (float, optional): The input 1.
            input_2 (float, optional): The input 2.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Math node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeMath")
            node.name = name
        node.use_clamp = use_clamp
        if operation is not None:
            node.operation = operation

        if label is not None:
            node.label = label

        if (
            operation
            in {
                "SQRT",
                "INVERSE_SQRT",
                "ABSOLUTE",
                "EXPONENT",
                "SIGN",
                "ROUND",
                "FLOOR",
                "CEIL",
                "TRUNC",
                "FRACT",
                "SINE",
                "COSINE",
                "TANGENT",
                "ARCSINE",
                "ARCCOSINE",
                "ARCTANGENT",
                "SINH",
                "COSH",
                "TANH",
                "RADIANS",
                "DEGREES",
            }
            and input_0 is not None
        ):
            node.inputs[0].default_value = input_0
        if input_0 is not None:
            node.inputs[0].default_value = input_0
        if input_1 is not None:
            node.inputs[1].default_value = input_1
        if operation in {"MULTIPLY_ADD", "COMPARE", "SMOOTH_MIN", "SMOOTH_MAX", "WRAP"} and input_2 is not None:
            node.inputs[2].default_value = input_2
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def separate_color(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        mode: str = "RGB",
        color: tuple = (0.8, 0.8, 0.8, 1),
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Separate Color node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (enum in ['RGB', 'HSV', 'HSL'], default 'RGB'): The mode of the separate color node.
            color (tuple, optional): The color input. Defaults to (0.8, 0.8, 0.8, 1).
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Separate Color node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeSeparateColor")
            node.name = name

        if label is not None:
            node.label = label

        node.mode = mode
        node.inputs["Color"].default_value = color
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def separate_xyz(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        vector: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Separate XYZ node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            vector (Vector, optional): The vector inputs.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Separate XYZ node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeSeparateXYZ")
            node.name = name

        if label is not None:
            node.label = label

        if vector is not None:
            node.inputs[0].default_value[0] = vector[0]
            node.inputs[0].default_value[1] = vector[1]
            node.inputs[0].default_value[2] = vector[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def vector_math(
        node_tree: bpy.types.ShaderNodeTree,
        name: str,
        label: str = None,
        operation: str = None,
        input_0: Vector = None,
        input_1: Vector = None,
        input_2: Vector = None,
        input_3: Vector = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Vector Math node.

        Args:
            node_tree (bpy.types.ShaderNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            operation (enum in [
            'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'MULTIPLY_ADD',
            'CROSS_PRODUCT', 'PROJECT', 'REFLECT', 'REFRACT', 'FACEFORWARD', 'DOT_PRODUCT',
            'DISTANCE', 'LENGTH', 'SCALE',
            'NORMALIZE',
            'ABSOLUTE', 'MINIMUM', 'MAXIMUM', 'FLOOR', 'CEIL', 'FRACTION', 'MODULO', 'WRAP', 'SNAP',
            'SINE', 'COSINE', 'TANGENT'
            ], default 'ADD'): The operation of the vector math node.
            input_0 (3D Vector, optional): The first vector input.
            input_1 (3D Vector, optional): The second vector input.
            input_2 (3D Vector, optional): The third vector input.
            input_3 (float, optional): The fourth float input.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Vector Math node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("ShaderNodeVectorMath")
            node.name = name
        if operation is not None:
            node.operation = operation

        if label is not None:
            node.label = label

        if operation in {
            "MULTIPLY_ADD",
            "DOT_PRODUCT",
            "REFRACT",
            "FACEFORWARD",
            "WRAP",
        }:
            if input_0 is not None:
                node.inputs[0].default_value[0] = input_0[0]
                node.inputs[0].default_value[1] = input_0[1]
                node.inputs[0].default_value[2] = input_0[2]
            if input_1 is not None:
                node.inputs[1].default_value[0] = input_1[0]
                node.inputs[1].default_value[1] = input_1[1]
                node.inputs[1].default_value[2] = input_1[2]
            if operation in {"REFRACT"}:
                if input_0 is not None:
                    node.inputs[0].default_value[0] = input_0[0]
                    node.inputs[0].default_value[1] = input_0[1]
                    node.inputs[0].default_value[2] = input_0[2]
                if input_1 is not None:
                    node.inputs[1].default_value[0] = input_1[0]
                    node.inputs[1].default_value[1] = input_1[1]
                    node.inputs[1].default_value[2] = input_1[2]
                if input_3 is not None:
                    node.inputs[3].default_value = input_3
            elif input_2 is not None:
                node.inputs[2].default_value[0] = input_2[0]
                node.inputs[2].default_value[1] = input_2[1]
                node.inputs[2].default_value[2] = input_2[2]
        if input_0 is not None:
            node.inputs[0].default_value[0] = input_0[0]
            node.inputs[0].default_value[1] = input_0[1]
            node.inputs[0].default_value[2] = input_0[2]
        if operation not in {
            "MULTIPLY_ADD",
            "LENGTH",
            "NORMALIZE",
            "ABSOLUTE",
            "FLOOR",
            "CEIL",
            "FRACTION",
            "SINE",
            "COSINE",
            "TANGENT",
        }:
            if operation in {"SCALE"}:
                if input_3 is not None:
                    node.inputs[3].default_value = input_3
            elif input_1 is not None:
                node.inputs[1].default_value[0] = input_1[0]
                node.inputs[1].default_value[1] = input_1[1]
                node.inputs[1].default_value[2] = input_1[2]
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node
