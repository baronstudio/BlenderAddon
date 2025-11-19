import os

import bpy
from bl_operators.presets import AddPresetBase
from bpy.props import IntProperty, StringProperty
from bpy.types import Operator


class QBAKER_OT_global_map_preset_add(AddPresetBase, Operator):
    """Add a Global Map Preset"""

    bl_label = "Add Global Map Preset"
    bl_idname = "qbaker.global_map_preset_add"
    preset_menu = "QBAKER_MT_global_map_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/global"
    preset_defines = [
        "baker = bpy.context.scene.qbaker",
    ]
    preset_values = [
        "baker.maps",
    ]


class QBAKER_OT_local_map_preset_add(AddPresetBase, Operator):
    """Add a Local Map Preset"""

    bl_label = "Add Local Map Preset"
    bl_idname = "qbaker.local_map_preset_add"
    preset_menu = "QBAKER_MT_local_map_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/local"
    preset_defines = [
        "baker = bpy.context.scene.qbaker",
        "baker_group = baker.bake_groups[baker.active_bake_group_index]",
    ]
    preset_values = [
        "baker_group.maps",
    ]


class QBAKER_OT_global_bake_preset_add(AddPresetBase, Operator):
    """Add a Global Bake Preset"""

    bl_label = "Add Global Bake Preset"
    bl_idname = "qbaker.global_bake_preset_add"
    preset_menu = "QBAKER_MT_global_bake_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/global"
    preset_defines = [
        "baker = bpy.context.scene.qbaker",
    ]
    preset_values = [
        "baker.bake",
    ]


class QBAKER_OT_local_bake_preset_add(AddPresetBase, Operator):
    """Add a Local Bake Preset"""

    bl_label = "Add Local Bake Preset"
    bl_idname = "qbaker.local_bake_preset_add"
    preset_menu = "QBAKER_MT_local_bake_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/local"
    preset_defines = [
        "baker = bpy.context.scene.qbaker",
        "baker_group = baker.bake_groups[baker.active_bake_group_index]",
    ]
    preset_values = [
        "baker_group.bake",
    ]


class QBAKER_OT_folder_add(Operator):
    """Add an output folder"""

    bl_label = "Add Folder"
    bl_idname = "qbaker.folder_add"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker

        if baker.use_bake_global:
            bake = baker.bake
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            bake = bake_group.bake

        folder = bake.folders.add()
        bake.folder_index = len(bake.folders) - 1
        if os.path.basename(os.path.dirname(self.directory)):
            folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            folder.name = os.path.dirname(self.directory)
        folder.path = self.directory
        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_folder_load(Operator):
    """Load output folders"""

    bl_label = "Load Folders"
    bl_idname = "qbaker.folder_load"
    bl_options = {"REGISTER", "INTERNAL"}

    directory: StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker

        if baker.use_bake_global:
            self.bake = baker.bake
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            self.bake = bake_group.bake

        if not self.directory:
            self.report({"WARNING"}, "Select an output assets folder")
            return {"CANCELLED"}

        self.bake.folders.clear()
        self.bake.folder_index = 0

        self.root_folder = self.bake.folders.add()
        self.bake.folder_index = len(self.bake.folders) - 1
        if os.path.basename(os.path.dirname(self.directory)):
            self.root_folder.name = os.path.basename(os.path.dirname(self.directory))
        else:
            self.root_folder.name = os.path.dirname(self.directory)
        self.root_folder.path = self.directory

        for dir in os.scandir(self.directory):
            if dir.is_dir():
                folder = self.bake.folders.add()
                folder.name = os.path.basename(dir.path)
                folder.path = bpy.path.abspath(os.path.join(dir.path, ""))
                folder.use_subfolder = True

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_folder_remove(Operator):
    bl_label = "Remove Folder"
    bl_idname = "qbaker.folder_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the output folder\n\nShift  •  Remove all the output folders"

    def invoke(self, context, event):
        baker = context.scene.qbaker

        if baker.use_bake_global:
            self.bake = baker.bake
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            self.bake = bake_group.bake

        if event.shift:
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
    QBAKER_OT_global_map_preset_add,
    QBAKER_OT_local_map_preset_add,
    QBAKER_OT_global_bake_preset_add,
    QBAKER_OT_local_bake_preset_add,
    QBAKER_OT_folder_add,
    QBAKER_OT_folder_load,
    QBAKER_OT_folder_remove,
)


register, unregister = bpy.utils.register_classes_factory(classes)
