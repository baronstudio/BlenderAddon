import bpy
from bl_ui.utils import PresetPanel
from bpy.types import Panel

from ..ops.node_bake import UNSUPPORTED_NODES
from ..utils.addon import package, preferences, version, version_str
from ..utils.icon import icons


class VIEW_3D_Panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "T4AQuick_Baker"

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == "VIEW_3D" and context.mode in {"OBJECT", "EDIT_MESH"}

    def draw_list(
        self,
        layout,
        listtype_name,
        dataptr,
        propname,
        active_propname,
        tooltip: str = "",
        rows: int = 4,
        sort_lock: bool = False,
    ):
        row = layout.row()
        row.template_list(
            listtype_name,
            "",
            dataptr=dataptr,
            active_dataptr=dataptr,
            propname=propname,
            active_propname=active_propname,
            item_dyntip_propname=tooltip,
            rows=rows,
            sort_lock=sort_lock,
        )
        col = row.column(align=True)
        return col


class NODE_EDITOR_Panel:
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Q-Baker"

    @classmethod
    def poll(cls, context):
        return context.area.ui_type == "ShaderNodeTree"

    def draw_list(
        self,
        layout,
        listtype_name,
        dataptr,
        propname,
        active_propname,
        tooltip: str = "",
        rows: int = 4,
        sort_lock: bool = False,
    ):
        row = layout.row()
        row.template_list(
            listtype_name,
            "",
            dataptr=dataptr,
            active_dataptr=dataptr,
            propname=propname,
            active_propname=active_propname,
            item_dyntip_propname=tooltip,
            rows=rows,
            sort_lock=sort_lock,
        )
        col = row.column(align=True)
        return col


class QBAKER_PT_bake_group(Panel, VIEW_3D_Panel):
    bl_label = "Bake Groups"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker

        col = self.draw_list(
            layout,
            "QBAKER_UL_bake_group",
            dataptr=baker,
            propname="bake_groups",
            active_propname="active_bake_group_index",
            # tooltip="name",
            rows=4 if len(baker.bake_groups) > 1 else 3,
        )
        col.operator("qbaker.bake_group_add", text="", icon="ADD")
        col.operator("qbaker.bake_group_copy", text="", icon="DUPLICATE")

        if len(baker.bake_groups) > 1:
            col.separator()

            col.operator("qbaker.bake_group_move", text="", icon="TRIA_UP").direction = "UP"
            col.operator("qbaker.bake_group_move", text="", icon="TRIA_DOWN").direction = "DOWN"

        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

            col = layout.column()
            col.prop(bake_group, "use_high_to_low")

            col.separator()

            if bake_group.use_high_to_low:
                col.label(text="Groups")
                col = self.draw_list(
                    layout,
                    "QBAKER_UL_group",
                    dataptr=bake_group,
                    propname="groups",
                    active_propname="active_group_index",
                    # tooltip="name",
                    rows=5 if len(bake_group.groups) > 1 else 4,
                )
                col.operator("qbaker.group_add", text="", icon="ADD")
                col.operator("qbaker.group_load", text="", icon="FILE_REFRESH")
                col.separator()
                col.operator_menu_enum("qbaker.group_select", "name", text="", icon="DOWNARROW_HLT")

                if len(bake_group.groups) > 1:
                    col.separator()

                    col.operator("qbaker.group_move", text="", icon="TRIA_UP").direction = "UP"
                    col.operator("qbaker.group_move", text="", icon="TRIA_DOWN").direction = "DOWN"

            else:
                col.label(text="Objects")
                col = self.draw_list(
                    layout,
                    "QBAKER_UL_object",
                    dataptr=bake_group,
                    propname="objects",
                    active_propname="active_object_index",
                    rows=4 if len(bake_group.objects) > 1 else 3,
                )
                col.operator("qbaker.object_add", text="", icon="ADD")
                col.operator("qbaker.object_load", text="", icon="FILE_REFRESH")

                if len(bake_group.objects) > 1:
                    col.separator()

                    col.operator("qbaker.object_move", text="", icon="TRIA_UP").direction = "UP"
                    col.operator("qbaker.object_move", text="", icon="TRIA_DOWN").direction = "DOWN"


class QBAKER_PT_high_poly(Panel, VIEW_3D_Panel):
    bl_label = "High Poly"
    bl_parent_id = "QBAKER_PT_bake_group"

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            return bool(bake_group.use_high_to_low and bake_group.groups)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.groups:
            self.draw_high_poly(bake_group, layout)

    def draw_high_poly(self, bake_group, layout):
        group = bake_group.groups[bake_group.active_group_index]
        col = self.draw_list(
            layout,
            "QBAKER_UL_high_poly",
            dataptr=group,
            propname="high_poly",
            active_propname="active_high_poly_index",
            rows=4 if len(group.high_poly) > 1 else 3,
        )
        col.operator("qbaker.high_poly_add", text="", icon="ADD")
        col.operator("qbaker.high_poly_load", text="", icon="FILE_REFRESH")

        if len(group.high_poly) > 1:
            col.separator()

            col.operator("qbaker.high_poly_move", text="", icon="TRIA_UP").direction = "UP"
            col.operator("qbaker.high_poly_move", text="", icon="TRIA_DOWN").direction = "DOWN"


class QBAKER_PT_low_poly(Panel, VIEW_3D_Panel):
    bl_label = "Low Poly"
    bl_parent_id = "QBAKER_PT_bake_group"

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            return bool(bake_group.use_high_to_low and bake_group.groups)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.groups:
            self.draw_low_poly(bake_group, layout)

    def draw_low_poly(self, bake_group, layout):
        group = bake_group.groups[bake_group.active_group_index]
        col = self.draw_list(
            layout,
            "QBAKER_UL_low_poly",
            dataptr=group,
            propname="low_poly",
            active_propname="active_low_poly_index",
            rows=1,
        )
        col.operator("qbaker.low_poly_add", text="", icon="ADD")
        col.operator("qbaker.low_poly_load", text="", icon="FILE_REFRESH")


class QBAKER_PT_cage(Panel, VIEW_3D_Panel):
    bl_label = ""
    bl_parent_id = "QBAKER_PT_bake_group"

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            if bake_group.groups:
                group = bake_group.groups[bake_group.active_group_index]
                return bool(bake_group.use_high_to_low and bake_group.groups and group.low_poly)

    def draw_header(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        self.layout.prop(group, "use_auto_cage")

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        # layout.use_property_split = True

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]
        item = group.low_poly[group.active_low_poly_index]

        col = layout.column()

        if not group.use_auto_cage:
            col.prop(item, "cage_object", text="")
            subcol = col.column()
            subcol.enabled = bool(group.use_auto_cage)
            subcol.prop(item, "cage_extrusion")
        else:
            col.prop(item, "cage_extrusion")
        col.prop(item, "ray_distance")


class QBAKER_PT_uv_map(Panel, VIEW_3D_Panel):
    bl_label = ""
    bl_parent_id = "QBAKER_PT_bake_group"

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

            if bake_group.use_high_to_low and bake_group.groups:
                group = bake_group.groups[bake_group.active_group_index]
                return group.low_poly
            if not bake_group.use_high_to_low and bake_group.objects:
                return bake_group.objects

    def draw_header(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        self.layout.prop(bake_group, "use_uvmap_global")

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.use_uvmap_global:
            col = layout.column()
            col.use_property_split = True

            if bake_group.use_high_to_low:
                col.alert = not bake_group.group_uv_map
                col.prop(bake_group, "group_uv_map", text="")
            else:
                col.alert = not bake_group.object_uv_map
                col.prop(bake_group, "object_uv_map", text="")

        elif bake_group.use_high_to_low and bake_group.groups:
            group = bake_group.groups[bake_group.active_group_index]

            if group.low_poly:
                item = group.low_poly[group.active_low_poly_index]
                if item.object:
                    col = layout.column()
                    col.use_property_split = True

                    col.alert = not item.uv_map
                    col.prop(item, "uv_map", text="")

        elif bake_group.objects:
            col = layout.column()
            item = bake_group.objects[bake_group.active_object_index]
            if item.object:
                col.use_property_split = True

                col.alert = not item.uv_map
                col.prop(item, "uv_map", text="")

        col = layout.column()
        col.operator("qbaker.uvmap_add")


class QBAKER_PT_material_group(Panel, VIEW_3D_Panel):
    bl_label = "Material Groups"
    bl_parent_id = "QBAKER_PT_bake_group"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

            if not bake_group.use_high_to_low and bake_group.objects:
                item = bake_group.objects[bake_group.active_object_index]
                return item.object and item.object.material_slots

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.objects:
            return

        item = bake_group.objects[bake_group.active_object_index]
        if not item.object:
            return

        if item.synchronize_material:
            col = self.draw_list(
                layout,
                "QBAKER_UL_material_group",
                dataptr=item.object,
                propname="material_slots",
                active_propname="active_material_index",
                rows=4 if len(item.object.material_slots) > 1 else 3,
            )
        else:
            layout.alert = not item.materials
            col = self.draw_list(
                layout,
                "QBAKER_UL_material_group",
                dataptr=item,
                propname="materials",
                active_propname="active_material_index",
                rows=4 if len(item.materials) > 1 else 3,
            )
        col.operator("qbaker.material_group_add", text="", icon="ADD")
        col.operator("qbaker.material_group_load", text="", icon="FILE_REFRESH")


class QBAKER_PT_map_global_preset(PresetPanel, Panel):
    bl_label = "Global Map Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_global_map_preset")


class QBAKER_PT_map_local_preset(PresetPanel, Panel):
    bl_label = "Local Map Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_local_map_preset")


class QBAKER_PT_map(Panel, VIEW_3D_Panel):
    bl_label = ""

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        return bool(baker.bake_groups and context.mode == "OBJECT")

    def draw_header(self, context):
        baker = context.scene.qbaker
        self.layout.prop(baker, "use_map_global")

    def draw_header_preset(self, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            QBAKER_PT_map_global_preset.draw_panel_header(self.layout)
        else:
            QBAKER_PT_map_local_preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker
        row = layout.row(align=True)

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        row = layout.row(align=True)
        row.operator_menu_enum("qbaker.map_add", "type")
        row.operator("qbaker.map_load", text="", icon="FILE_REFRESH")

        col = layout.column()
        col.template_list(
            "QBAKER_UL_map",
            "",
            dataptr=bake_group,
            propname="maps",
            active_dataptr=bake_group,
            active_propname="active_map_index",
            item_dyntip_propname="label",
            rows=5 if len(bake_group.maps) > 1 else 4,
        )


class QBAKER_PT_map_properties(Panel, VIEW_3D_Panel):
    bl_label = "Properties"
    bl_parent_id = "QBAKER_PT_map"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            return baker.maps
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            return bake_group.maps

        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.draw(context, layout)


class QBAKER_PT_red_channel(Panel, VIEW_3D_Panel):
    bl_label = "R"
    bl_parent_id = "QBAKER_PT_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.maps:
            return False

        map = bake_group.maps[bake_group.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.r_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.r_channel).draw_channel(context, layout)


class QBAKER_PT_green_channel(Panel, VIEW_3D_Panel):
    bl_label = "G"
    bl_parent_id = "QBAKER_PT_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.maps:
            return False

        map = bake_group.maps[bake_group.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.g_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.g_channel).draw_channel(context, layout)


class QBAKER_PT_blue_channel(Panel, VIEW_3D_Panel):
    bl_label = "B"
    bl_parent_id = "QBAKER_PT_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.maps:
            return False

        map = bake_group.maps[bake_group.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.b_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.b_channel).draw_channel(context, layout)


class QBAKER_PT_rgb_channel(Panel, VIEW_3D_Panel):
    bl_label = "RGB"
    bl_parent_id = "QBAKER_PT_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.maps:
            return False

        map = bake_group.maps[bake_group.active_map_index]
        return map.type == "CHANNEL_PACK" and map.use_include and map.channel_pack.mode == "RGB_A"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.channel_pack.get_multi_channel_map(map.channel_pack.rgb_channel).draw_channel(context, layout)


class QBAKER_PT_alpha_channel(Panel, VIEW_3D_Panel):
    bl_label = "A"
    bl_parent_id = "QBAKER_PT_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.maps:
            return False

        map = bake_group.maps[bake_group.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode in {"RGBA", "RGB_A"}
            and map.channel_pack.a_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        baker = context.scene.qbaker

        if baker.use_map_global:
            bake_group = baker
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

        map = bake_group.maps[bake_group.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.a_channel).draw_channel(context, layout)


class QBAKER_PT_bake_global_preset(PresetPanel, Panel):
    bl_label = "Global Bake Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_global_bake_preset")
        context.area.tag_redraw()


class QBAKER_PT_bake_local_preset(PresetPanel, Panel):
    bl_label = "Local Bake Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_local_bake_preset")
        context.area.tag_redraw()


class QBAKER_PT_bake(Panel, VIEW_3D_Panel):
    bl_label = ""

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        return bool(baker.bake_groups and context.mode == "OBJECT")

    def draw_header(self, context):
        baker = context.scene.qbaker
        self.layout.prop(baker, "use_bake_global")

    def draw_header_preset(self, context):
        baker = context.scene.qbaker

        if baker.use_bake_global:
            QBAKER_PT_bake_global_preset.draw_panel_header(self.layout)
        else:
            QBAKER_PT_bake_local_preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        baker = context.scene.qbaker

        if baker.use_bake_global:
            bake = baker.bake
        else:
            bake_group = baker.bake_groups[baker.active_bake_group_index]
            bake = bake_group.bake

        bake.draw_path(context, layout)
        bake.draw(context, layout=layout)

        col = layout.column()
        col.scale_y = 1.6

        if baker.progress >= 0:
            self.draw_progress(col, baker)
        else:
            col.operator("qbaker.bake")

    def draw_progress(self, col, baker):
        row = col.row(align=True)
        row.scale_x = 1.3
        subrow = row.row(align=True)
        subrow.enabled = False
        subrow.prop(baker, "progress", text="Baking...", slider=True)
        row.operator("qbaker.bake_cancel", icon="X", text="")


class QBAKER_PT_vertex_color(Panel, VIEW_3D_Panel):
    bl_label = "Vertex Color"

    @classmethod
    def poll(cls, context):
        qbaker = preferences().qbaker
        return context.mode == "EDIT_MESH" or (context.mode == "OBJECT" and qbaker.use_vertex_color_object_mode)

    hex = [
        "FF0000",
        "00FF00",
        "0000FF",
        "FFFF00",
        "FF00FF",
        "00FFFF",
        "F44336",
        "E91E63",
        "9C27B0",
        "673AB7",
        "3F51B5",
        "2196F3",
        "03A9F4",
        "00BCD4",
        "009688",
        "4CAF50",
        "8BC34A",
        "CDDC39",
        "FFEB3B",
        "FFC107",
        "FF9800",
        "FF5722",
        "795548",
        "9E9E9E",
        "607D8B",
    ]

    def hex_to_rgb(self, hex):
        rgb = [int(hex[i : i + 2], 16) for i in (0, 2, 4)]
        r = pow(rgb[0] / 255, 1)
        g = pow(rgb[1] / 255, 1)
        b = pow(rgb[2] / 255, 1)
        return r, g, b

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        baker = context.scene.qbaker

        col = layout.column()
        col.prop(baker, "vertex_color_name")
        # col.prop(context.space_data.shading, "color_type", text="Viewport Color")

        col = layout.column()
        grid = col.grid_flow(row_major=True, columns=6, even_columns=True, even_rows=True, align=True)

        for h in self.hex:
            col = grid.column(align=True)
            col.prop(baker, f"vc_{h}", text="")
            col.operator("qbaker.vertex_color_preset", icon="VPAINT_HLT").preset = self.hex_to_rgb(h)

        col = layout.column(align=True)
        col.prop(baker, "vertex_color")
        col.operator("qbaker.vertex_color", icon="VPAINT_HLT")


class QBAKER_PT_material(Panel, NODE_EDITOR_Panel):
    bl_label = "Material Bake"

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        col = self.draw_list(
            layout,
            "QBAKER_UL_material",
            dataptr=material_baker,
            propname="materials",
            active_propname="active_material_index",
            rows=4 if len(material_baker.materials) > 1 else 3,
        )
        col.operator("qbaker.material_add", text="", icon="ADD")
        col.operator("qbaker.material_load", text="", icon="FILE_REFRESH")

        if len(material_baker.materials) > 1:
            col.separator()

            col.operator("qbaker.material_move", text="", icon="TRIA_UP").direction = "UP"
            col.operator("qbaker.material_move", text="", icon="TRIA_DOWN").direction = "DOWN"


class QBAKER_PT_material_map_global_preset(PresetPanel, Panel):
    bl_label = "Global Map Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"

        layout.menu_contents("QBAKER_MT_global_material_map_preset")


class QBAKER_PT_material_map_local_preset(PresetPanel, Panel):
    bl_label = "Local Map Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"

        layout.menu_contents("QBAKER_MT_local_material_map_preset")


class QBAKER_PT_material_map(Panel, NODE_EDITOR_Panel):
    bl_label = ""
    bl_parent_id = "QBAKER_PT_material"

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker
        return material_baker.materials

    def draw_header(self, context):
        material_baker = context.scene.qbaker.material_baker
        self.layout.prop(material_baker, "use_map_global")

    def draw_header_preset(self, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            QBAKER_PT_material_map_global_preset.draw_panel_header(self.layout)
        else:
            QBAKER_PT_material_map_local_preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker
        row = layout.row(align=True)

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        row = layout.row(align=True)
        row.operator_menu_enum("qbaker.material_bake_map_add", "type")
        row.operator("qbaker.material_bake_map_load", text="", icon="FILE_REFRESH")

        col = layout.column()
        col.template_list(
            "QBAKER_UL_material_map",
            "",
            dataptr=active_material,
            propname="maps",
            active_dataptr=active_material,
            active_propname="active_map_index",
            item_dyntip_propname="id",
            rows=5 if len(active_material.maps) > 1 else 4,
            sort_lock=True,
        )


class QBAKER_PT_material_map_properties(Panel, NODE_EDITOR_Panel):
    bl_label = "Properties"
    bl_parent_id = "QBAKER_PT_material_map"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        return active_material.maps

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.draw(context, layout)


class QBAKER_PT_material_map_red_channel(Panel, NODE_EDITOR_Panel):
    bl_label = "R"
    bl_parent_id = "QBAKER_PT_material_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.r_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.r_channel).draw_channel(context, layout)


class QBAKER_PT_material_map_green_channel(Panel, NODE_EDITOR_Panel):
    bl_label = "G"
    bl_parent_id = "QBAKER_PT_material_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.g_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.g_channel).draw_channel(context, layout)


class QBAKER_PT_material_map_blue_channel(Panel, NODE_EDITOR_Panel):
    bl_label = "B"
    bl_parent_id = "QBAKER_PT_material_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode == "RGBA"
            and map.channel_pack.b_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.b_channel).draw_channel(context, layout)


class QBAKER_PT_material_map_rgb_channel(Panel, NODE_EDITOR_Panel):
    bl_label = "RGB"
    bl_parent_id = "QBAKER_PT_material_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        return map.type == "CHANNEL_PACK" and map.use_include and map.channel_pack.mode == "RGB_A"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.channel_pack.get_multi_channel_map(map.channel_pack.rgb_channel).draw_channel(context, layout)


class QBAKER_PT_material_map_alpha_channel(Panel, NODE_EDITOR_Panel):
    bl_label = "A"
    bl_parent_id = "QBAKER_PT_material_map_properties"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        return (
            map.type == "CHANNEL_PACK"
            and map.use_include
            and map.channel_pack.mode in {"RGBA", "RGB_A"}
            and map.channel_pack.a_channel != "NONE"
        )

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_map_global:
            active_material = material_baker
        else:
            active_material = material_baker.materials[material_baker.active_material_index]

        map = active_material.maps[active_material.active_map_index]
        map.channel_pack.get_single_channel_map(map.channel_pack.a_channel).draw_channel(context, layout)


class QBAKER_PT_material_bake_global_preset(PresetPanel, Panel):
    bl_label = "Global Material Bake Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_global_material_bake_preset")
        context.area.tag_redraw()


class QBAKER_PT_material_bake_local_preset(PresetPanel, Panel):
    bl_label = "Local Material Bake Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_local_material_bake_preset")
        context.area.tag_redraw()


class QBAKER_PT_material_bake(Panel, NODE_EDITOR_Panel):
    bl_label = ""
    bl_parent_id = "QBAKER_PT_material"

    @classmethod
    def poll(cls, context):
        material_baker = context.scene.qbaker.material_baker
        return material_baker.materials

    def draw_header(self, context):
        material_baker = context.scene.qbaker.material_baker
        self.layout.prop(material_baker, "use_bake_global")

    def draw_header_preset(self, context):
        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_bake_global:
            QBAKER_PT_material_bake_global_preset.draw_panel_header(self.layout)
        else:
            QBAKER_PT_material_bake_local_preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False

        material_baker = context.scene.qbaker.material_baker

        if material_baker.use_bake_global:
            bake = material_baker.bake
        else:
            active_material = material_baker.materials[material_baker.active_material_index]
            bake = active_material.bake

        bake.draw_path(context, layout)
        bake.draw(context, layout=layout)

        col = layout.column()
        col.scale_y = 1.6

        if material_baker.progress >= 0:
            self.draw_progress(col, material_baker)
        else:
            col.operator("qbaker.material_bake")

    def draw_progress(self, col, baker):
        row = col.row(align=True)
        row.scale_x = 1.3
        subrow = row.row(align=True)
        subrow.enabled = False
        subrow.prop(baker, "progress", text="Baking...", slider=True)
        row.operator("qbaker.material_bake_cancel", icon="X", text="")


class QBAKER_PT_node_bake_preset(PresetPanel, Panel):
    bl_label = "Node Bake Presets"

    def draw(self, context):
        layout = self.layout
        layout.emboss = "PULLDOWN_MENU"
        layout.operator_context = "EXEC_DEFAULT"
        layout.menu_contents("QBAKER_MT_node_bake_preset")
        context.area.tag_redraw()


class QBAKER_PT_node_bake(Panel, NODE_EDITOR_Panel):
    bl_label = "Node Bake"

    def draw_header_preset(self, context):
        QBAKER_PT_node_bake_preset.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout

        node_baker = context.scene.qbaker.node_baker
        node_baker.draw_path(context, layout)
        node_baker.draw(context, layout)

        col = layout.column()
        col.scale_y = 1.6
        nodes = [node for node in context.selected_nodes if node.type not in UNSUPPORTED_NODES]
        col.operator("qbaker.node_bake", text=f"Bake ({len(nodes)} Nodes)" if len(nodes) > 1 else "Bake")


class QBAKER_PT_help:
    bl_label = f"Help - v{version_str}"
    bl_category = "M-Bridge"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context):
        layout = self.layout
        layout.operator("preferences.addon_show", icon="PREFERENCES", emboss=False).module = package

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        if version >= (1, 0, 1):
            col.operator("qbaker.changelog", icon="RECOVER_LAST")
        col.operator("wm.url_open", text="Documentation", icon="HELP").url = "https://github.com/baronstudio/BlenderAddon/tree/master/T4A_quick_baker"
        
        


class QBAKER_PT_view3d_help(Panel, VIEW_3D_Panel, QBAKER_PT_help):
    pass


class QBAKER_PT_node_editor_help(Panel, NODE_EDITOR_Panel, QBAKER_PT_help):
    pass


classes = (
    QBAKER_PT_bake_group,
    QBAKER_PT_high_poly,
    QBAKER_PT_low_poly,
    QBAKER_PT_cage,
    QBAKER_PT_uv_map,
    QBAKER_PT_material_group,
    QBAKER_PT_map_global_preset,
    QBAKER_PT_map_local_preset,
    QBAKER_PT_map,
    QBAKER_PT_map_properties,
    QBAKER_PT_red_channel,
    QBAKER_PT_green_channel,
    QBAKER_PT_blue_channel,
    QBAKER_PT_rgb_channel,
    QBAKER_PT_alpha_channel,
    QBAKER_PT_bake_global_preset,
    QBAKER_PT_bake_local_preset,
    QBAKER_PT_bake,
    QBAKER_PT_vertex_color,
    QBAKER_PT_material,
    QBAKER_PT_material_map_global_preset,
    QBAKER_PT_material_map_local_preset,
    QBAKER_PT_material_map,
    QBAKER_PT_material_map_properties,
    QBAKER_PT_material_map_red_channel,
    QBAKER_PT_material_map_green_channel,
    QBAKER_PT_material_map_blue_channel,
    QBAKER_PT_material_map_rgb_channel,
    QBAKER_PT_material_map_alpha_channel,
    QBAKER_PT_material_bake_global_preset,
    QBAKER_PT_material_bake_local_preset,
    QBAKER_PT_material_bake,
    QBAKER_PT_node_bake_preset,
    QBAKER_PT_node_bake,
    QBAKER_PT_view3d_help,
    QBAKER_PT_node_editor_help,
)


register, unregister = bpy.utils.register_classes_factory(classes)
