import os
import time

import bpy
from bl_operators.presets import AddPresetBase
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator

from ...qbpy import Image, ShaderNode
from ..utils.addon import preferences

if bpy.app.version >= (4, 0, 0):
    from ..utils.bake_v4 import Bake
else:
    from ..utils.bake_v3 import Bake


UNSUPPORTED_NODES = {
    "BSDF_PRINCIPLED",
    "ADD_SHADER",
    "BSDF_DIFFUSE",
    "EMISSION",
    "BSDF_GLASS",
    "BSDF_GLOSSY",
    "HOLDOUT",
    "MIX_SHADER",
    "PRINCIPLED_VOLUME",
    "BSDF_REFRACTION",
    "EEVEE_SPECULAR",
    "SUBSURFACE_SCATTERING",
    "BSDF_TRANSLUCENT",
    "BSDF_TRANSPARENT",
    "VOLUME_ABSORPTION",
    "VOLUME_SCATTER",
    "TEX_IMAGE",
    "OUTPUT_MATERIAL",
    "OUTPUT_AOV",
    "OUTPUT_LIGHT",
    "SCRIPT",
    "GROUP_INPUT",
    "GROUP_OUTPUT",
    "FRAME",
    "REROUTE",
}


class QBAKER_OT_node_bake(Operator, Bake):
    bl_label = "Bake"
    bl_idname = "qbaker.node_bake"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return (
            context.area.type == "NODE_EDITOR"
            and context.material
            and context.active_node
            and context.active_node.type not in UNSUPPORTED_NODES
            and context.active_object
            and context.selected_nodes
            and context.mode == "OBJECT"
        )

    @classmethod
    def description(cls, context, properties):
        if (
            context.area.type == "NODE_EDITOR"
            and context.material
            and context.active_node
            and context.active_node.type in UNSUPPORTED_NODES
        ):
            return f"Can't bake: {context.active_node.name} node"
        elif context.mode != "OBJECT":
            return "Switch to object mode"

        return "Bake the selected nodes\n\nShift  •  Replace the linked sockets of the selected nodes with the baked textures."

    def invoke(self, context, event):
        self.prefs = preferences()
        self.node_baker = context.scene.qbaker.node_baker
        self.prepare_render_settings(context, samples=self.node_baker.samples)
        self.is_shift = bool(event.shift)
        self.selected_nodes = context.selected_nodes
        self.active_node = context.active_node
        self.start_time = time.time()
        self.offset = 32

        if self.active_node.outputs and self.node_baker.socket not in self.active_node.outputs:
            self.node_baker.socket = self.active_node.outputs[0].name

        context.active_object.hide_select = False
        context.active_object.hide_viewport = False
        context.active_object.hide_render = False

        for col in context.scene.collection.children_recursive:
            col.hide_render = False

        # check for UDIMs
        self.udims = set()
        self.udims.update(self.uv_coords_to_udims(self.create_unique_uv_coords(context.object)))
        self.udims = list(self.udims)

        self.node_socket = self.node_baker.socket
        self.bake_node = self.bake_nodes(context)
        self.timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}


    def create_image(self, context, name, non_color) -> bpy.types.Image:
        if img := bpy.data.images.get(name):
            bpy.data.images.remove(img)

        if self.prefs.qbaker.bake.use_auto_udim and len(self.udims) > 1:
            return self.udim_image(
                context,
                self.udims,
                name,
                width=self.node_baker.width if self.node_baker.size == "CUSTOM" else int(self.node_baker.size),
                height=self.node_baker.height if self.node_baker.size == "CUSTOM" else int(self.node_baker.size),
                non_color=non_color,
            )
        else:
            return Image.new_image(
                name=name,
                width=self.node_baker.width if self.node_baker.size == "CUSTOM" else int(self.node_baker.size),
                height=self.node_baker.height if self.node_baker.size == "CUSTOM" else int(self.node_baker.size),
                non_color=non_color,
            )

    def setup_image_node(self, context, node, output, node_position) -> tuple:
        non_color = output.type != "RGBA"

        size = (
            f"{self.node_baker.width}x{self.node_baker.height}"
            if self.node_baker.size == "CUSTOM"
            else bpy.types.UILayout.enum_item_name(self.node_baker, "size", self.node_baker.size)
        )

        try:
            extra_tokens = {"socket": output.name, "uvmap": self.node_baker.uv_map}
            # include object/material tokens when available so naming_name_source can resolve $name
            try:
                obj = bpy.context.object
                if obj is not None:
                    extra_tokens["object"] = obj.name
                    if getattr(obj, "active_material", None):
                        extra_tokens["material"] = obj.active_material.name
            except Exception:
                pass

            name = self.node_baker.build_filename(
                context,
                bake_group_name=node.name,
                map_suffix=output.name,
                extra_tokens=extra_tokens,
            )
        except Exception:
            # Fallback: construct a simple, deterministic name (avoid chained .replace usage)
            name = f"{node.name}_{output.name}_{size}"

        name = str(name)
        image = self.create_image(context, name, non_color)
        image.colorspace_settings.name = "sRGB" if output.type == "RGBA" else "Non-Color"

        image_node = ShaderNode.image_texture(
            self.node_tree,
            name=f"{node.name} {output.name}",
            parent=node.parent,
            position=(node.location.x, node.location.y + node_position),
        )
        image_node.width = node.width
        image_node.hide = True
        image_node.image = image
        self.node_tree.nodes.active = image_node
        return image_node, image

    def setup_material_output_node(self, node, node_position):
        return ShaderNode.material_output(
            self.node_tree,
            name="QB_MATERIAL_OUTPUT",
            label="Baking...",
            target="CYCLES",
            parent=node.parent,
            position=(node.location.x, node.location.y + node_position),
        )

    def bake_image(self, context, image):
        context.object.select_set(True)
        context.view_layer.objects.active = context.object

        while bpy.ops.object.bake(
            "INVOKE_DEFAULT",
            type="EMIT",
            margin_type=self.node_baker.margin_type,
            margin=self.node_baker.margin,
            use_clear=True,
        ) != {"RUNNING_MODAL"}:
            yield 1

        while not image.is_dirty:
            yield 1

    def save_image(self, image, node):
        if self.node_baker.folders:
            if path := self.node_baker.folders[self.node_baker.folder_index].path:
                if self.node_baker.use_sub_folder:
                    # Determine folder name based on naming_name_source
                    folder_name = node.name
                    try:
                        name_source = getattr(self.node_baker, "naming_name_source", "BAKEGROUP")
                    except Exception:
                        name_source = "BAKEGROUP"
                    if name_source == "OBJECT":
                        try:
                            obj = bpy.context.object
                            if obj is not None:
                                folder_name = obj.name
                        except Exception:
                            pass
                    elif name_source == "MATERIAL":
                        try:
                            obj = bpy.context.object
                            if obj is not None and getattr(obj, "active_material", None):
                                folder_name = obj.active_material.name
                        except Exception:
                            pass

                    path = os.path.join(path, folder_name)

                if self.prefs.qbaker.bake.use_auto_udim and len(self.udims) > 1:
                    filepath = Image.save_image_as(image, path=path, name=f"{image.name}.<UDIM>")
                    try:
                        Image.enqueue_expected_rename(filepath, f"{image.name}.<UDIM>")
                    except Exception:
                        pass
                else:
                    filepath = Image.save_image_as(image, path=path)
                    try:
                        Image.enqueue_expected_rename(filepath, image.name)
                    except Exception:
                        pass

    def bake_nodes(self, context):
        yield 1

        for node in self.selected_nodes:
            self.node_tree = node.id_data
            if node.type in UNSUPPORTED_NODES:
                self.report({"WARNING"}, f"Can't bake: {node.name}")
                continue

            if self.node_baker.use_sockets:
                node_position = self.offset * len(node.outputs)
                for output in node.outputs:
                    if output.type == "SHADER":
                        self.report({"WARNING"}, f"Can't bake: {output.name}")
                        continue

                    self.material_output_node = self.setup_material_output_node(node, node_position)
                    self.material_output_node.width = node.width
                    self.material_output_node.hide = True
                    non_color = output.type != "RGBA"
                    self.node_tree.links.new(output=output, input=self.material_output_node.inputs["Surface"])

                    image_node, image = self.setup_image_node(context, node, output, node_position)

                    for uv in context.object.data.uv_layers:
                        if uv.name == self.node_baker.uv_map:
                            uv.active = True

                    yield from self.bake_image(context, image)
                    self.save_image(image, node)

                    if self.is_shift and output.is_linked:
                        self.node_tree.links.new(output=image_node.outputs["Color"], input=output.links[0].to_socket)

                    image_node.select = False
                    node_position -= self.offset
            else:
                if node == self.active_node:
                    output = node.outputs[self.node_socket]
                else:
                    output = node.outputs[0]

                self.material_output_node = self.setup_material_output_node(node, self.offset)
                self.material_output_node.width = node.width
                self.material_output_node.hide = True
                non_color = output.type != "RGBA"
                self.node_tree.links.new(output=output, input=self.material_output_node.inputs["Surface"])

                image_node, image = self.setup_image_node(context, node, output, self.offset)

                for uv in context.object.data.uv_layers:
                    if uv.name == self.node_baker.uv_map:
                        uv.active = True

                yield from self.bake_image(context, image)
                self.save_image(image, node)

                if self.is_shift and output.is_linked:
                    self.node_tree.links.new(output=image_node.outputs["Color"], input=output.links[0].to_socket)

                image_node.select = False

        if self.node_tree and self.material_output_node:
            self.node_tree.nodes.remove(self.material_output_node)
            self.node_tree.nodes.active = self.active_node

        self.restore_render_settings(context)
        
        
        yield 0

    def modal(self, context, event):
        if event.type == "TIMER":
            result = next(self.bake_node)

            if result == 0:
                self.finish(context)
                return {"FINISHED"}

        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.cancel(context)
            return {"CANCELLED"}

        return {"PASS_THROUGH"}

    def finish(self, context):
        print(f"Bake Time: {round((time.time() - self.start_time), 2)} sec")
        if self.timer:
            context.window_manager.event_timer_remove(self.timer)

        # Flush any enqueued expected renames now that baking finished
        try:
            Image.flush_expected_renames()
        except Exception:
            pass

    def cancel(self, context):
        self.finish(context)


class QBAKER_OT_node_bake_preset_add(AddPresetBase, Operator):
    """Add a node bake preset"""

    bl_label = "Add Node Bake Preset"
    bl_idname = "qbaker.node_bake_preset_add"
    preset_menu = "QBAKER_MT_node_bake_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/node"
    preset_defines = [
        "node_baker = bpy.context.scene.qbaker.node_baker",
    ]
    preset_values = [
        "node_baker.batch_name",
        "node_baker.size",
        "node_baker.width",
        "node_baker.height",
        "node_baker.margin_type",
        "node_baker.margin",
        "node_baker.samples",
    ]


class QBAKER_OT_node_bake_folder_add(Operator):
    """Add an output folder"""

    bl_label = "Add Folder"
    bl_idname = "qbaker.node_bake_folder_add"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        node_baker = context.scene.qbaker.node_baker

        folder = node_baker.folders.add()
        node_baker.folder_index = len(node_baker.folders) - 1
        if os.path.basename(os.path.dirname(self.directory)):
            folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            folder.name = os.path.dirname(self.directory)

        folder.path = self.directory
        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_node_bake_folder_load(Operator):
    """Load output folders"""

    bl_label = "Load Folders"
    bl_idname = "qbaker.node_bake_folder_load"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        node_baker = context.scene.qbaker.node_baker

        if not self.directory:
            self.report({"WARNING"}, "Select an output assets folder")
            return {"CANCELLED"}

        node_baker.folders.clear()
        node_baker.folder_index = 0

        root_folder = node_baker.folders.add()
        node_baker.folder_index = len(node_baker.folders) - 1

        if os.path.basename(os.path.dirname(self.directory)):
            root_folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            root_folder.name = os.path.dirname(self.directory)

        root_folder.path = self.directory

        for dir in os.scandir(self.directory):
            if dir.is_dir():
                folder = node_baker.folders.add()
                folder.name = os.path.basename(dir.path)
                folder.path = bpy.path.abspath(os.path.join(dir.path, ""))
                folder.use_subfolder = True

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_node_bake_folder_remove(Operator):
    bl_label = "Remove Folder"
    bl_idname = "qbaker.node_bake_folder_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the output folder\n\nShift  •  Remove all the output folders"

    def invoke(self, context, event):
        self.node_baker = context.scene.qbaker.node_baker

        if event.shift:
            self.node_baker.folders.clear()
            self.node_baker.folder_index = 0
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        self.node_baker.folders.remove(self.index)
        self.node_baker.folder_index = min(max(0, self.node_baker.folder_index - 1), len(self.node_baker.folders) - 1)
        return {"FINISHED"}


classes = (
    QBAKER_OT_node_bake,
    QBAKER_OT_node_bake_preset_add,
    QBAKER_OT_node_bake_folder_add,
    QBAKER_OT_node_bake_folder_load,
    QBAKER_OT_node_bake_folder_remove,
)


register, unregister = bpy.utils.register_classes_factory(classes)
