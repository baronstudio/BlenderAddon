import subprocess

import bpy
from bpy.types import Operator


class NODE_OT_node_tree_to_script(Operator):
    """Convert active node tree into a script"""

    bl_label = "Node Tree to Script"
    bl_idname = "node.node_tree_to_script"
    bl_options = {"REGISTER", "UNDO"}

    copy_to_clipboard: bpy.props.BoolProperty(
        name="Copy to Clipboard",
        default=True,
    )

    paste_to_editor: bpy.props.BoolProperty(
        name="Paste to Editor",
        default=True,
    )

    def execute(self, context):
        if not context.active_node:
            self.report({"ERROR"}, "Select a node")
            return {"CANCELLED"}

        node_tree = context.active_node.id_data
        self.lines = f"# Blender {'.'.join(map(str, bpy.app.version))}\n"
        self.lines += f"import bpy\n\n\n"
        lines = self.extract(context, node_tree)

        if self.copy_to_clipboard:
            self.clipboard(lines)
            self.report({"INFO"}, f"Copied: {node_tree.name.lower().replace(' ', '_')} to the clipboard")

        if self.paste_to_editor:
            text = bpy.data.texts.get(f"{node_tree.name.lower().replace(' ', '_')}_script.py")
            if not text:
                text = bpy.data.texts.new(f"{node_tree.name.lower().replace(' ', '_')}_script.py")

            text.clear()
            text.write(lines)
            self.report({"INFO"}, f"Created a new text block: {text.name}")

        return {"FINISHED"}

    def extract(self, context, node_tree):
        node_types_order = [
            "FRAME",
            "GROUP",
            "GROUP_INPUT",
            "OTHERS",
            "GROUP_OUTPUT",
            "BSDF_PRINCIPLED",
            "OUTPUT_MATERIAL",
        ]
        nodes = {
            node: node.location
            for node in sorted(
                node_tree.nodes,
                key=lambda n: (
                    node_types_order.index(n.type) if n.type in node_types_order else node_types_order.index("OTHERS")
                ),
            )
        }

        node_links = [(link.from_socket, link.to_socket) for link in node_tree.links]

        # TODO: Fix this
        for link in node_tree.links:
            link.to_node.name, link.from_socket.node.outputs.find(link.from_socket.name)

        for node, location in nodes.items():
            if node.type == "GROUP" and node.node_tree:
                self.lines = self.extract(context, node.node_tree)

        self.lines += f"# node_group\n"

        node_tree_name = node_tree.name.lower().replace(" ", "_")
        self.lines += f"{node_tree_name} = bpy.data.node_groups.get('{node_tree.name}')\n"
        self.lines += f"if {node_tree_name} is None:\n"
        self.lines += f"    {node_tree_name} = bpy.data.node_groups.new('{node_tree.name}', '{node_tree.rna_type.identifier}')\n\n"

        self.lines += f"{node_tree_name}.interface.clear()\n\n"

        self.lines += f"# nodes\n"

        for node, location in nodes.items():
            name = node.name.lower().replace(" ", "_").replace("/", "_")
            self.lines += f"{name} = {node_tree_name}.nodes.new('{node.rna_type.identifier}')\n"
            self.lines += f"{name}.name = '{name}'\n"

            # write group sockets
            if node.rna_type.identifier in {"NodeGroupInput", "NodeGroupOutput"}:
                in_out = "INPUT" if node.rna_type.identifier == "NodeGroupInput" else "OUTPUT"
                for socket in node.id_data.interface.items_tree:
                    if socket.item_type == "SOCKET" and socket.in_out == in_out:
                        if socket.socket_type in {"NodeSocketVirtual"}:
                            continue
                        socket_name = f"{in_out.lower()}_socket"
                        self.lines += f"{socket_name} = {node_tree_name}.interface.new_socket('{socket.name}', in_out='{in_out}', socket_type='{socket.socket_type}')\n"
                        for attr in ["socket_type", "subtype", "default_value", "min_value", "max_value", "hide_value"]:
                            if hasattr(socket, attr):
                                value = getattr(socket, attr)
                                if attr == "default_value" and socket.socket_type in {"NodeSocketGeometry"}:
                                    continue
                                if attr == "default_value" and socket.socket_type in {
                                    "NodeSocketColor",
                                    "NodeSocketVector",
                                }:
                                    value = value[:]
                                if isinstance(value, str):
                                    self.lines += f"{socket_name}.{attr} = '{value}'\n"
                                else:
                                    self.lines += f"{socket_name}.{attr} = {value}\n"

                # for socket in node.outputs if in_out == "INPUT" else node.inputs:
                #     if socket.rna_type.identifier in {"NodeSocketVirtual", "NodeSocketGeometry"}:
                #         continue
                #     socket_name = f"{in_out.lower()}_socket"
                #     self.lines += f"{socket_name} = {node_tree_name}.interface.new_socket('{socket.name}', in_out='{in_out}', socket_type='{socket.rna_type.identifier}')\n"
                #     for attr in ["socket_type", "subtype", "default_value", "min_value", "max_value", "hide_value"]:
                #         if hasattr(socket, attr):
                #             value = getattr(socket, attr)
                #             if attr == "default_value" and socket.rna_type.identifier in {"NodeSocketColor", "NodeSocketVector"}:
                #                 value = value[:]
                #             self.lines += f"{socket_name}.{attr} = {value}\n"

            if node.type == "GROUP":
                if node.node_tree:
                    self.lines += f"{name}.node_tree = {node.node_tree.name.lower().replace(' ', '_')}\n"

            # write inputs
            processed_inputs = set()

            for input in node.inputs:
                if input.name in processed_inputs:
                    continue
                elif (
                    input.rna_type.identifier in {"NodeSocketVirtual", "NodeSocketObject"}
                    or node.inputs.get(input.name) is None
                    or input.hide_value
                ):
                    continue
                elif (
                    hasattr(input, "default_value")
                    and input.default_value is not None
                    and input.default_value != ""
                    and not input.is_linked
                ):
                    if input.rna_type.identifier in {"NodeSocketColor", "NodeSocketVector"}:
                        self.lines += f"{name}.inputs['{input.name}'].default_value = {input.default_value[:]}\n"
                    else:
                        self.lines += f"{name}.inputs['{input.name}'].default_value = {input.default_value}\n"
                processed_inputs.add(input.name)

            # write properties
            for prop in node.bl_rna.properties:
                if hasattr(prop, "enum_items_static_ui") and prop.identifier not in {
                    "type",
                    "warning_propagation",
                    "bl_icon",
                    "bl_static_type",
                }:
                    if prop.type in {"ENUM", "STRING"}:
                        self.lines += f'{name}.{prop.identifier} = "{getattr(node, prop.identifier)}"\n'
                    else:
                        self.lines += f"{name}.{prop.identifier} = {getattr(node, prop.identifier)}\n"

            if node.parent:
                self.lines += f"{name}.parent = {node.parent.name.lower().replace(' ', '_').replace('/', '_')}\n"
            self.lines += f"{name}.location = {location[:]}\n\n"

        self.lines += f"# links\n"

        for from_socket, to_socket in node_links:
            from_socket_name = from_socket.node.name.lower().replace(" ", "_").lstrip(".").replace("/", "_")
            to_socket_name = to_socket.node.name.lower().replace(" ", "_").lstrip(".").replace("/", "_")
            print(to_socket.name)
            from_socket_index = from_socket.node.outputs.find(from_socket.name)
            to_socket_index = to_socket.node.inputs.find(to_socket.name)
            self.lines += f"{node_tree_name}.links.new({from_socket_name}.outputs[{from_socket_index}], {to_socket_name}.inputs[{to_socket_index}])\n"

        self.lines += "\n\n"
        return self.lines

    def clipboard(self, txt):
        process = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
        process.communicate(input=txt.encode("utf-8"))


def draw_ui(self, context):
    op = self.layout.operator(NODE_OT_node_tree_to_script.bl_idname, icon="FILE_SCRIPT")
    op.copy_to_clipboard = True
    op.paste_to_editor = True


def register():
    bpy.utils.register_class(NODE_OT_node_tree_to_script)
    bpy.types.NODE_PT_active_node_generic.append(draw_ui)


def unregister():
    bpy.utils.unregister_class(NODE_OT_node_tree_to_script)
    bpy.types.NODE_PT_active_node_generic.remove(draw_ui)
