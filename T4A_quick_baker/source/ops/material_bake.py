import os

import bpy
from bl_operators.presets import AddPresetBase
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import Operator


class QBAKER_OT_material_add(Operator):
    """Add a material"""

    bl_label = "Add Material"
    bl_idname = "qbaker.material_add"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "material"

    def material_enum(self, context):
        items = [
            (material.name, material.name, "", bpy.types.UILayout.icon(material), index)
            for index, material in enumerate(bpy.data.materials)
            if material.name != "Dots Stroke" and not material.name.startswith(".") and "_BAKED" not in material.name
        ]

        return items

    material: EnumProperty(items=material_enum)

    @classmethod
    def poll(cls, context):
        return bpy.data.materials

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker

        if self.material in [item.material.name for item in material_baker.materials]:
            self.report({"WARNING"}, f"{self.material}: already exists")
            return {"CANCELLED"}

        item = material_baker.materials.add()
        material_baker.active_material_index = len(material_baker.materials) - 1
        item.name = self.material
        item.material = bpy.data.materials.get(self.material)

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_material_load(Operator):
    bl_label = "Load Materials"
    bl_idname = "qbaker.material_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == "MESH" and bpy.data.materials

    @classmethod
    def description(cls, context, properties):
        if context.object.type != "MESH":
            return "Select a mesh object"

        return "Load the object materials\n\nShift  •  Load all the materials"

    def invoke(self, context, event):
        self.material_baker = context.scene.qbaker.material_baker

        if event.shift:
            for material in bpy.data.materials:
                if material.name in {"Dots Stroke"} or material.name.startswith(".") or "_BAKED" in material.name:
                    continue

                if material in [item.material for item in self.material_baker.materials]:
                    continue

                item = self.material_baker.materials.add()
                self.material_baker.active_material_index = len(self.material_baker.materials) - 1
                item.name = material.name
                item.material = material
        else:
            return self.execute(context)

        context.area.tag_redraw()
        return {"FINISHED"}

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != "MESH":
                continue

            if not obj.material_slots:
                continue

            for slot in context.object.material_slots:
                if not slot.material and not slot.material.use_nodes:
                    continue

                material = slot.material

                if material.name in {"Dots Stroke"} or material.name.startswith(".") or "_BAKED" in material.name:
                    continue

                if material in [item.material for item in self.material_baker.materials]:
                    continue

                item = self.material_baker.materials.add()
                self.material_baker.active_material_index = len(self.material_baker.materials) - 1
                item.name = material.name
                item.material = material

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_material_move(Operator):
    bl_label = "Move Material"
    bl_idname = "qbaker.material_move"
    bl_options = {"REGISTER", "INTERNAL"}

    direction: EnumProperty(
        name="Direction",
        items=(
            ("UP", "Up", ""),
            ("DOWN", "Down", ""),
        ),
    )

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker
        return material_baker.materials

    @classmethod
    def description(cls, context, properties):
        return "Move the active material up/down in the list"

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker

        if self.direction == "DOWN":
            if material_baker.active_material_index == len(material_baker.materials) - 1:
                material_baker.materials.move(material_baker.active_material_index, 0)
                material_baker.active_material_index = 0
            else:
                material_baker.materials.move(
                    material_baker.active_material_index, material_baker.active_material_index + 1
                )
                material_baker.active_material_index += 1

        elif self.direction == "UP":
            if material_baker.active_material_index == 0:
                material_baker.materials.move(0, len(material_baker.materials) - 1)
                material_baker.active_material_index = len(material_baker.materials) - 1
            else:
                material_baker.materials.move(
                    material_baker.active_material_index, material_baker.active_material_index - 1
                )
                material_baker.active_material_index -= 1

        return {"FINISHED"}


class QBAKER_OT_material_remove(Operator):
    bl_label = "Remove Materials"
    bl_idname = "qbaker.material_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the material\n\nShift  •  Remove all the materials\nCtrl    •  Remove all the other materials"

    def invoke(self, context, event):
        self.material_baker = context.scene.qbaker.material_baker
        self.material = self.material_baker.materials[self.index]

        if event.shift:
            self.material_baker.materials.clear()
            self.material_baker.active_material_index = 0
        elif event.ctrl:
            for item in reversed(self.material_baker.materials):
                if item != self.material:
                    self.material_baker.materials.remove(self.material_baker.materials.find(item.name))
                    self.material_baker.active_material_index = min(
                        max(0, self.material_baker.active_material_index - 1), len(self.material_baker.materials) - 1
                    )
        else:
            return self.execute(context)

        context.area.tag_redraw()
        return {"FINISHED"}

    def execute(self, context):
        self.material_baker.materials.remove(self.index)
        self.material_baker.active_material_index = min(
            max(0, self.material_baker.active_material_index - 1), len(self.material_baker.materials) - 1
        )
        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_global_material_map_preset_add(AddPresetBase, Operator):
    """Add a Global Material Map Preset"""

    bl_label = "Add Global Material Map Preset"
    bl_idname = "qbaker.global_material_map_preset_add"
    preset_menu = "QBAKER_MT_global_material_map_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/material_global"
    preset_defines = [
        "material_baker = bpy.context.scene.qbaker.material_baker",
    ]
    preset_values = [
        "material_baker.maps",
    ]


class QBAKER_OT_local_material_map_preset_add(AddPresetBase, Operator):
    """Add a Local Material Map Preset"""

    bl_label = "Add Local Material Map Preset"
    bl_idname = "qbaker.local_material_map_preset_add"
    preset_menu = "QBAKER_MT_local_material_map_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/material_local"
    preset_defines = [
        "material_baker = bpy.context.scene.qbaker.material_baker",
        "active_material = material_baker.materials[material_baker.active_material_index]",
    ]
    preset_values = [
        "active_material.maps",
    ]


class QBAKER_OT_global_material_bake_preset_add(AddPresetBase, Operator):
    """Add a Global Material Bake Preset"""

    bl_label = "Add Global Material Bake Preset"
    bl_idname = "qbaker.global_material_bake_preset_add"
    preset_menu = "QBAKER_MT_global_material_bake_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/material_global"
    preset_defines = [
        "material_baker = bpy.context.scene.qbaker.material_baker",
    ]
    preset_values = [
        "material_baker.bake",
    ]


class QBAKER_OT_local_material_bake_preset_add(AddPresetBase, Operator):
    """Add a Local Material Bake Preset"""

    bl_label = "Add Local Material Bake Preset"
    bl_idname = "qbaker.local_material_bake_preset_add"
    preset_menu = "QBAKER_MT_local_material_bake_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/material_local"
    preset_defines = [
        "material_baker = bpy.context.scene.qbaker.material_baker",
        "active_material = material_baker.materials[material_baker.active_material_index]",
    ]
    preset_values = [
        "active_material.bake",
    ]


class QBAKER_OT_material_bake_folder_add(Operator):
    """Add an output folder"""

    bl_label = "Add Folder"
    bl_idname = "qbaker.material_bake_folder_add"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_bake_global:
            bake = material_baker.bake
        else:
            item = material_baker.materials[material_baker.active_material_index]
            bake = item.bake

        folder = bake.folders.add()
        bake.folder_index = len(bake.folders) - 1

        if os.path.basename(os.path.dirname(self.directory)):
            folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            folder.name = os.path.dirname(self.directory)

        folder.path = self.directory
        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_material_bake_folder_load(Operator):
    """Load output folders"""

    bl_label = "Load Folders"
    bl_idname = "qbaker.material_bake_folder_load"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_bake_global:
            self.bake = material_baker.bake
        else:
            item = material_baker.materials[material_baker.active_material_index]
            self.bake = item.bake

        if not self.directory:
            self.report({"WARNING"}, "Select an output assets folder")
            return {"CANCELLED"}

        self.bake.folders.clear()
        self.bake.folder_index = 0

        root_folder = self.bake.folders.add()
        self.bake.folder_index = len(self.bake.folders) - 1

        if os.path.basename(os.path.dirname(self.directory)):
            root_folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            root_folder.name = os.path.dirname(self.directory)

        root_folder.path = self.directory

        for dir in os.scandir(self.directory):
            if dir.is_dir():
                folder = self.bake.folders.add()
                folder.name = os.path.basename(dir.path)
                folder.path = bpy.path.abspath(os.path.join(dir.path, ""))
                folder.use_subfolder = True

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_material_bake_folder_remove(Operator):
    bl_label = "Remove Folder"
    bl_idname = "qbaker.material_bake_folder_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the output folder\n\nShift  •  Remove all the output folders"

    def invoke(self, context, event):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_bake_global:
            self.bake = material_baker.bake
        else:
            item = material_baker.materials[material_baker.active_material_index]
            self.bake = item.bake

        if not event.shift:
            self.bake.folders.clear()
            self.bake.folder_index = 0
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        self.bake.folders.remove(self.index)
        self.bake.folder_index = min(max(0, self.bake.folder_index - 1), len(self.bake.folders) - 1)
        return {"FINISHED"}


classes = (
    QBAKER_OT_material_add,
    QBAKER_OT_material_load,
    QBAKER_OT_material_move,
    QBAKER_OT_material_remove,
    QBAKER_OT_global_material_map_preset_add,
    QBAKER_OT_local_material_map_preset_add,
    QBAKER_OT_global_material_bake_preset_add,
    QBAKER_OT_local_material_bake_preset_add,
    QBAKER_OT_material_bake_folder_add,
    QBAKER_OT_material_bake_folder_load,
    QBAKER_OT_material_bake_folder_remove,
)


register, unregister = bpy.utils.register_classes_factory(classes)
