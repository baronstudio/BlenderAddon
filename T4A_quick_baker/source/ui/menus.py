import os

import bpy
from bpy.types import Menu


def operator_preset(layout, text, filepath, menu):
    result = layout.operator("script.execute_preset", text=text)
    result.filepath = filepath
    result.menu_idname = menu
    return result


class QBAKER_MT_global_map_preset(Menu):
    bl_label = "Global Map Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/global"
    preset_add_operator = "qbaker.global_map_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_global_map_preset"}

    def draw(self, context):
        layout = self.layout.column()

        preset_dir = os.path.join(os.path.dirname(__file__), "../../presets/maps")
        operator_preset(
            layout,
            "Unity (Standard)",
            f"{preset_dir}/global/unity_standard.py",
            "QBAKER_MT_global_map_preset",
        )

        if bpy.app.version >= (4, 0, 0):
            operator_preset(
                layout,
                " Unity (Standard Specular)",
                f"{preset_dir}/global/unity_standard_specular.py",
                "QBAKER_MT_global_map_preset",
            )
        operator_preset(
            layout,
            "Unity (Autodesk Interactive)",
            f"{preset_dir}/global/unity_autodesk_interactive.py",
            "QBAKER_MT_global_map_preset",
        )
        operator_preset(
            layout,
            "Unity (URP Lit)",
            f"{preset_dir}/global/unity_URP_lit.py",
            "QBAKER_MT_global_map_preset",
        )
        operator_preset(
            layout,
            "Unity (URP Autodesk Interactive)",
            f"{preset_dir}/global/unity_URP_autodesk_interactive.py",
            "QBAKER_MT_global_map_preset",
        )
        operator_preset(
            layout,
            "Unity (HDRP Lit)",
            f"{preset_dir}/global/unity_HDRP_lit.py",
            "QBAKER_MT_global_map_preset",
        )
        operator_preset(
            layout,
            "Unity (HDRP Autodesk Interactive)",
            f"{preset_dir}/global/unity_HDRP_autodesk_interactive.py",
            "QBAKER_MT_global_map_preset",
        )
        layout.separator()
        operator_preset(
            layout,
            "Unreal",
            f"{preset_dir}/global/unreal.py",
            "QBAKER_MT_global_map_preset",
        )
        operator_preset(
            layout,
            "Unreal Packed",
            f"{preset_dir}/global/unreal_packed.py",
            "QBAKER_MT_global_map_preset",
        )
        layout.separator()

        self.draw_preset(context)


class QBAKER_MT_local_map_preset(Menu):
    bl_label = "Local Map Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/local"
    preset_add_operator = "qbaker.local_map_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_local_map_preset"}

    def draw(self, context):
        layout = self.layout.column()

        preset_dir = os.path.join(os.path.dirname(__file__), "../../presets/maps")
        operator_preset(
            layout,
            "Unity (Standard)",
            f"{preset_dir}/local/unity_standard.py",
            "QBAKER_MT_local_map_preset",
        )

        if bpy.app.version >= (4, 0, 0):
            operator_preset(
                layout,
                " Unity (Standard Specular)",
                f"{preset_dir}/local/unity_standard_specular.py",
                "QBAKER_MT_local_map_preset",
            )
        operator_preset(
            layout,
            "Unity (Autodesk Interactive)",
            f"{preset_dir}/local/unity_autodesk_interactive.py",
            "QBAKER_MT_local_map_preset",
        )
        operator_preset(
            layout,
            "Unity (URP Lit)",
            f"{preset_dir}/local/unity_URP_lit.py",
            "QBAKER_MT_local_map_preset",
        )
        operator_preset(
            layout,
            "Unity (URP Autodesk Interactive)",
            f"{preset_dir}/local/unity_URP_autodesk_interactive.py",
            "QBAKER_MT_local_map_preset",
        )
        operator_preset(
            layout,
            "Unity (HDRP Lit)",
            f"{preset_dir}/local/unity_HDRP_lit.py",
            "QBAKER_MT_local_map_preset",
        )
        operator_preset(
            layout,
            "Unity (HDRP Autodesk Interactive)",
            f"{preset_dir}/local/unity_HDRP_autodesk_interactive.py",
            "QBAKER_MT_local_map_preset",
        )
        layout.separator()
        operator_preset(
            layout,
            "Unreal",
            f"{preset_dir}/local/unreal.py",
            "QBAKER_MT_local_map_preset",
        )
        operator_preset(
            layout,
            "Unreal Packed",
            f"{preset_dir}/local/unreal_packed.py",
            "QBAKER_MT_local_map_preset",
        )
        layout.separator()

        self.draw_preset(context)


class QBAKER_MT_global_bake_preset(Menu):
    bl_label = "Global Bake Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/global"
    preset_add_operator = "qbaker.global_bake_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_global_bake_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_local_bake_preset(Menu):
    bl_label = "Local Bake Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/local"
    preset_add_operator = "qbaker.local_bake_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_local_bake_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_global_material_map_preset(Menu):
    bl_label = "Global Material Map Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/material_global"
    preset_add_operator = "qbaker.global_material_map_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_global_material_map_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_local_material_map_preset(Menu):
    bl_label = "Local Material Map Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/maps/material_local"
    preset_add_operator = "qbaker.local_material_map_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_local_material_map_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_global_material_bake_preset(Menu):
    bl_label = "Global Material Bake Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/material_global"
    preset_add_operator = "qbaker.global_material_bake_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_global_material_bake_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_local_material_bake_preset(Menu):
    bl_label = "Local Material Bake Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/material_local"
    preset_add_operator = "qbaker.local_material_bake_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_local_material_bake_preset"}

    def draw(self, context):
        self.draw_preset(context)


class QBAKER_MT_node_bake_preset(Menu):
    bl_label = "Node Bake Presets"
    preset_operator = "script.execute_preset"
    preset_subdir = "quick_baker/v2.7.0/bake/node"
    preset_add_operator = "qbaker.node_bake_preset_add"
    preset_operator_defaults = {"menu_idname": "QBAKER_MT_node_bake_preset"}

    def draw(self, context):
        self.draw_preset(context)


classes = (
    QBAKER_MT_global_map_preset,
    QBAKER_MT_local_map_preset,
    QBAKER_MT_global_bake_preset,
    QBAKER_MT_local_bake_preset,
    QBAKER_MT_global_material_map_preset,
    QBAKER_MT_local_material_map_preset,
    QBAKER_MT_global_material_bake_preset,
    QBAKER_MT_local_material_bake_preset,
    QBAKER_MT_node_bake_preset,
)


register, unregister = bpy.utils.register_classes_factory(classes)
