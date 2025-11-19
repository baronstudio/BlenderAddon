from __future__ import annotations

from typing import Union

import bpy
from mathutils import Vector

from .socket_panel import SocketPanel


class Node(SocketPanel):
    """Base class for nodes."""

    def __init__(self, node_tree, node):
        self.node_tree = node_tree
        self.node = node
        self.parent = None

    @property
    def inputs(self):
        return self.node.inputs

    @property
    def outputs(self):
        return self.node.outputs

    @staticmethod
    def group_input(
        node_tree: bpy.types.NodeTree,
        name: str = "Group Input",
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((-280, 0)),
    ) -> Node:
        """Create a Group Input node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Group Input".
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            Node: Group Input node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("NodeGroupInput")
            node.name = name

        if label is not None:
            node.label = label

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return Node(node_tree, node)

    @staticmethod
    def group_output(
        node_tree: bpy.types.NodeTree,
        name: str = "Group Output",
        label: str = None,
        show_options: bool = True,
        hide: bool = False,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> Node:
        """Create a Group Output node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Group Output".
            label (str, optional): Label of the node. Defaults to None.
            show_options (bool, optional): Show options of the node. Defaults to True.
            hide (bool, optional): Hide the node. Defaults to False.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            Node: Group Output node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("NodeGroupOutput")
            node.name = name

        if label is not None:
            node.label = label

        node.show_options = show_options
        node.hide = hide

        if parent is not None:
            node.parent = parent

        node.location = position
        return Node(node_tree, node)

    def panel(self, **kwargs) -> bpy.types.NodeTreeInterfacePanel:
        socket_panel = SocketPanel(self.node_tree, self.node)
        socket_panel.panel(**kwargs)
        return socket_panel

    def socket(
        self,
        name: str = "Socket",
        socket_type: str = "NodeSocketFloat",
        description: str = "",
        default_attribute_name: str = None,
        subtype: str = "NONE",
        default_value: bpy.types.AnyType = None,
        min_value: bpy.types.AnyType = None,
        max_value: bpy.types.AnyType = None,
        default_input: str = None,
        hide_value: bool = False,
        hide_in_modifier: bool = False,
        force_non_field: bool = False,
        parent: bpy.types.NodeTreeInterfacePanel = None,
        position: int = None,
    ) -> Union[bpy.types.NodeSocket, bpy.types.NodeTreeInterfaceSocket]:
        """Create a Socket.

        Args:
            name (str, optional): Name of the socket.
            socket_type (str, optional): Type of the socket. Defaults to "NodeSocketFloat".
            description (str, optional): Description of the socket. Defaults to "".
            default_attribute_name (str, optional): Default attribute name of the socket. Defaults to None.
            subtype (str, optional): Subtype of the socket. Defaults to "NONE".
            default_value (bpy.types.AnyType, optional): Default value of the socket. Defaults to None.
            min_value (bpy.types.AnyType, optional): Min value of the socket. Defaults to None.
            max_value (bpy.types.AnyType, optional): Max value of the socket. Defaults to None.
            default_input (str, optional): Default input of the socket. Defaults to None.
            hide_value (bool, optional): Hide the value. Defaults to False.
            hide_in_modifier (bool, optional): Hide in modifier. Defaults to False.
            force_non_field (bool, optional): Single value. Defaults to False.
            parent (bpy.types.NodeTreeInterfacePanel, optional): Parent panel. Defaults to None.
            position (int, optional): Position to insert the socket in the panel. Defaults to None.

        Returns:
            Union[bpy.types.NodeSocket, bpy.types.NodeTreeInterfaceSocket]: Socket.
        """
        if self.node.type in {"GROUP_INPUT", "GROUP_OUTPUT"}:
            if bpy.app.version >= (4, 0, 0):
                socket = next(
                    (
                        item
                        for item in self.node_tree.interface.items_tree
                        if item.item_type == "SOCKET"
                        and item.name == name
                        and item.in_out == ("INPUT" if self.node.type == "GROUP_INPUT" else "OUTPUT")
                    ),
                    None,
                )
                if not socket:
                    socket = self.node_tree.interface.new_socket(
                        name,
                        socket_type=socket_type,
                        in_out="INPUT" if self.node.type == "GROUP_INPUT" else "OUTPUT",
                    )
            else:
                socket = (
                    self.node_tree.inputs.get(name)
                    if self.node.type == "GROUP_INPUT"
                    else self.node_tree.outputs.get(name)
                )
                if not socket:
                    socket = (
                        self.node_tree.inputs.new(socket_type, name)
                        if self.node.type == "GROUP_INPUT"
                        else self.node_tree.outputs.new(socket_type, name)
                    )

        socket.description = description or name

        if default_attribute_name is not None:
            socket.default_attribute_name = default_attribute_name

        if subtype != "NONE":
            socket.subtype = subtype

        if default_value is not None:
            socket.default_value = default_value
            group_socket = (
                self.node.outputs.get(name) if self.node.type == "GROUP_INPUT" else self.node.inputs.get(name)
            )
            if group_socket:
                group_socket.default_value = default_value

        if min_value is not None:
            socket.min_value = min_value
        if max_value is not None:
            socket.max_value = max_value or socket.max_value
        if default_input is not None:
            socket.default_input = default_input or socket.default_input

        socket.hide_value = (
            self.node.type == "GROUP_OUTPUT" and hide_value or socket_type in {"NodeSocketGeometry", "NodeSocketVector"}
        ) or hide_value

        socket.hide_in_modifier = hide_in_modifier
        socket.force_non_field = force_non_field

        if bpy.app.version >= (4, 0, 0):
            socket_panel = parent or self.parent
            if socket_panel is not None:
                self.node_tree.interface.move_to_parent(
                    socket, socket_panel, len(socket_panel.interface_items) if position is None else position
                )
            else:
                self.node_tree.interface.move(
                    socket, len(self.node_tree.interface.items_tree) if position is None else position
                )
        else:
            sockets = self.node_tree.outputs if self.node.type == "GROUP_OUTPUT" else self.node_tree.inputs
            sockets.move(sockets.find(socket.name), len(sockets) if position is None else position)

        return socket

    @staticmethod
    def frame(
        node_tree: bpy.types.NodeTree,
        name: str = "Frame",
        label: str = None,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> Node:
        """Create a frame node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Frame".
            label (str, optional): Label of the node. Defaults to None.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            Node: Frame node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("NodeFrame")
            node.name = name

        if label is not None:
            node.label = label

        if parent is not None:
            node.parent = parent

        node.location = position
        return Node(node_tree, node)

    def reroute(
        node_tree: bpy.types.NodeTree,
        name: str = "Reroute",
        label: str = None,
        parent: bpy.types.NodeFrame = None,
        position: Vector = Vector((0, 0)),
    ) -> bpy.types.Node:
        """Create a Reroute node.

        Args:
            node_tree (bpy.types.NodeTree): Node tree to add the node to.
            name (str, optional): Name of the node. Defaults to "Reroute".
            label (str, optional): Label of the node. Defaults to None.
            parent (bpy.types.NodeFrame, optional): Parent node frame. Defaults to None.
            position (Vector, optional): Position to insert the node in the node tree. Defaults to Vector((0, 0)).

        Returns:
            bpy.types.Node: Reroute node.
        """
        node = node_tree.nodes.get(name)
        if not node:
            node = node_tree.nodes.new("NodeReroute")
            node.name = name

        if label is not None:
            node.label = label

        if parent is not None:
            node.parent = parent

        node.location = position
        return node
