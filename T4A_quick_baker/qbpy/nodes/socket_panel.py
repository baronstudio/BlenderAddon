from __future__ import annotations

from typing import Union

import bpy


class SocketPanel:
    def __init__(self, node_tree, node):
        self.node_tree = node_tree
        self.node = node
        self.parent = None

    def panel(
        self,
        name: str = "Panel",
        description: str = "",
        default_closed: bool = False,
        position: int = None,
    ) -> bpy.types.NodeTreeInterfacePanel:
        if self.node.type in {"GROUP_INPUT", "GROUP_OUTPUT"} and bpy.app.version >= (4, 0, 0):
            panel = next(
                (
                    item
                    for item in self.node_tree.interface.items_tree
                    if item.item_type == "PANEL" and item.name == name
                ),
                None,
            )
            if not panel:
                panel = self.node_tree.interface.new_panel(name, description=description, default_closed=default_closed)

            panel.description = description
            panel.default_closed = default_closed

            if position is not None:
                self.node_tree.interface.move(panel, position)

            self.parent = panel
            return panel

    def socket(
        self,
        name: str = "Socket",
        socket_type: str = "NodeSocketGeometry",
        description: str = "",
        default_attribute_name: str = None,
        subtype: str = "NONE",
        default: bpy.types.AnyType = None,
        min_value: bpy.types.AnyType = None,
        max_value: bpy.types.AnyType = None,
        default_input: str = None,
        hide_value: bool = False,
        hide_in_modifier: bool = False,
        force_non_field: bool = False,
        parent: bpy.types.NodeTreeInterfacePanel = None,
    ) -> Union[bpy.types.NodeSocket, bpy.types.NodeTreeInterfaceSocket]:
        """Create a Socket.

        Args:
            name (str, optional): Name of the socket. Defaults to "Socket".
            socket_type (str, optional): Type of the socket. Defaults to "NodeSocketGeometry".
            description (str, optional): Description of the socket. Defaults to "".
            default_attribute_name (str, optional): Default attribute name of the socket. Defaults to None.
            subtype (str, optional): Subtype of the socket. Defaults to "NONE".
            default (bpy.types.AnyType, optional): Default value of the socket. Defaults to None.
            min_value (bpy.types.AnyType, optional): Min value of the socket. Defaults to None.
            max_value (bpy.types.AnyType, optional): Max value of the socket. Defaults to None.
            default_input (str, optional): Default input of the socket. Defaults to None.
            hide_value (bool, optional): Hide the value. Defaults to False.
            hide_in_modifier (bool, optional): Hide in modifier. Defaults to False.
            force_non_field (bool, optional): Single value. Defaults to False.
            parent (bpy.types.NodeTreeInterfacePanel, optional): Parent panel. Defaults to None.

        Returns:
            Union[bpy.types.NodeSocket, bpy.types.NodeTreeInterfaceSocket]: Socket.
        """
        if self.node.type in {"GROUP_INPUT", "GROUP_OUTPUT"} and bpy.app.version >= (4, 0, 0):
            in_out = "INPUT" if self.node.type == "GROUP_INPUT" else "OUTPUT"
            socket = next(
                (
                    item
                    for item in self.node_tree.interface.items_tree
                    if item.item_type == "SOCKET" and item.name == name and item.in_out == in_out
                ),
                None,
            )
            if not socket:
                socket = self.node_tree.interface.new_socket(name, socket_type=socket_type, in_out=in_out)

        socket.description = description
        if default_attribute_name is not None:
            socket.default_attribute_name = default_attribute_name
        if subtype != "NONE":
            socket.subtype = subtype
        if default is not None:
            socket.default_value = default
        if min_value is not None:
            socket.min_value = min_value
        if max_value is not None:
            socket.max_value = max_value
        if default_input is not None:
            socket.default_input = default_input
        socket.hide_value = True if self.node.type == "GROUP_OUTPUT" else hide_value
        socket.hide_in_modifier = hide_in_modifier
        socket.force_non_field = force_non_field

        if parent is not None:
            self.node_tree.interface.move_to_parent(socket, parent, len(parent.interface_items))
        elif self.parent is not None:
            self.node_tree.interface.move_to_parent(socket, self.parent, len(self.parent.interface_items))

        return socket
