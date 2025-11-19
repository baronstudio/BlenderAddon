import bpy
from bpy.types import Operator

from ..shader import ShaderNodeTree


class NODE_OT_test(Operator):
    """Dev Test"""

    bl_label = "Test"
    bl_idname = "node.test"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        self.prepare(context)
        return {"FINISHED"}

    def prepare(self, context):
        node_group = ShaderNodeTree(name="Node Group")

        frame = node_group.frame(name="Frame")

        group_input = frame.group_input(name="Group Input")
        group_input.socket(name="Socket", socket_type="NodeSocketFloat")
        panel = group_input.panel(name="Panel")
        panel.socket(name="Input", socket_type="NodeSocketFloat")

        group_output = frame.group_output(name="Group Output")
        group_output.socket(name="Socket", socket_type="NodeSocketFloat")
        panel = group_output.panel(name="Panel")
        panel.socket(name="Output", socket_type="NodeSocketFloat")

        return node_group.node_tree


def draw_ui(self, context):
    self.layout.operator(NODE_OT_test.bl_idname, icon="FILE_SCRIPT")


def register():
    bpy.utils.register_class(NODE_OT_test)
    bpy.types.NODE_PT_active_node_generic.append(draw_ui)


def unregister():
    bpy.utils.unregister_class(NODE_OT_test)
    bpy.types.NODE_PT_active_node_generic.remove(draw_ui)
