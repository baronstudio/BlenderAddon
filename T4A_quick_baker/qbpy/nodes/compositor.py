import bpy
from mathutils import Vector

from .node import Node


class CompositorNode(Node):
    """Compositor node class for creating compositor nodes."""

    # Input
    @staticmethod
    def image(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        image: bpy.types.Image = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create an Image node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            image (bpy.types.Image, optional): Image data-block referencing an external or packed image.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Image node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeImage")
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

    # Output

    @staticmethod
    def composite(
        node_tree: bpy.types.CompositorNodeTree,
        name: str = "Composite",
        label: str = None,
        use_alpha: bool = True,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Composite node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str, optional): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            use_alpha (bool, optional): Colors are treated alpha premultiplied or colors output straight (alpha gets set to 1). Defaults to True.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Composite node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeComposite")
            node.name = name
        if label is not None:
            node.label = label
        node.use_alpha = use_alpha
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def file_output(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        base_path: str = bpy.app.tempdir,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a File Output node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            base_path (str, optional): Base output path for the image. Defaults to bpy.app.tempdir.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: File Output node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeOutputFile")
            node.name = name
        if label is not None:
            node.label = label
        node.base_path = base_path
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def viewer(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        use_alpha: bool = True,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Viewer node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            use_alpha (bool, optional): Colors are treated alpha premultiplied or colors output straight (alpha gets set to 1). Defaults to True.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Viewer node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeViewer")
            node.name = name
        if label is not None:
            node.label = label
        node.use_alpha = use_alpha
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Converter

    @staticmethod
    def combine_color(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        mode: str = "RGB",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Combine Color node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (str, optional): Mode of color processing. Defaults to "RGB".
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Combine Color node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeCombineColor")
            node.name = name
        if label is not None:
            node.label = label
        node.mode = mode
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    @staticmethod
    def separate_color(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        mode: str = "RGB",
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Separate Color node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            mode (str, optional): Mode of color processing. Defaults to "RGB".
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Separate Color node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeSeparateColor")
            node.name = name
        if label is not None:
            node.label = label
        node.mode = mode
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node

    # Filter

    @staticmethod
    def denoise(
        node_tree: bpy.types.CompositorNodeTree,
        name: str,
        label: str = None,
        prefilter: str = "ACCURATE",
        use_hdr: bool = True,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Denoise node.

        Args:
            node_tree (bpy.types.CompositorNodeTree): Node tree to add the node to.
            name (str): Name of the node.
            label (str, optional): Label of the node. Defaults to None.
            prefilter (str, optional): Denoise image and guiding passes together. Improves quality when guiding passes are noisy using least amount of extra processing time. Defaults to 'ACCURATE'.
            use_hdr (bool, optional): Process HDR images. Defaults to True.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Denoise node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("CompositorNodeDenoise")
            node.name = name
        if label is not None:
            node.label = label
        node.prefilter = prefilter
        node.use_hdr = use_hdr
        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return node
