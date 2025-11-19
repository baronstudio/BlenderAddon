import bpy
from bpy.props import BoolProperty
from bpy.types import UIList


class QBAKER_UL_List(UIList):
    def draw_filter(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_invert", text="", icon="ARROW_LEFTRIGHT")
        row.separator()
        row.prop(self, "use_filter_sort_alpha", text="", icon="SORTALPHA")
        row.prop(
            self,
            "use_filter_sort_reverse",
            text="",
            icon="SORT_ASC" if not self.use_filter_sort_reverse else "SORT_DESC",
        )


class QBAKER_UL_bake_group(QBAKER_UL_List):
    # Custom properties, saved with .blend file.
    use_filter_sort_alpha: BoolProperty(
        name="Sort by Name",
        description="Sort items by their name",
        default=True,
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", icon="RENDERLAYERS", emboss=False)
        row.operator(
            "qbaker.bake_group_include",
            text="",
            icon="CHECKBOX_HLT" if item.use_include else "CHECKBOX_DEHLT",
            emboss=False,
        ).index = index
        row.operator("qbaker.bake_group_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_group(UIList):
    # Custom properties, saved with .blend file.
    use_filter_sort_alpha: BoolProperty(
        name="Sort by Name",
        description="Sort items by their name",
        default=True,
    )

    use_filter_missing_groups: BoolProperty(
        name="Filter Missing Groups",
        description="Filter groups that have no high or low poly objects",
        default=False,
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        icon = (
            "GROUP"
            if not item.high_poly and not item.low_poly
            else "COLLECTION_COLOR_01"
            if not item.high_poly or not item.low_poly
            else "OUTLINER_COLLECTION"
        )

        row.prop(item, "name", text="", icon=icon, emboss=False)
        row.operator(
            "qbaker.group_include", text="", icon="CHECKBOX_HLT" if item.use_include else "CHECKBOX_DEHLT", emboss=False
        ).index = index
        row.operator("qbaker.group_remove", text="", icon="X", emboss=False).index = index

    def draw_filter(self, context, layout):
        """Draw the filter options for the group list."""
        row = layout.row(align=True)
        row.prop(self, "filter_name", text="")
        row.prop(self, "use_filter_invert", text="", icon="ARROW_LEFTRIGHT")
        row.separator()
        row.prop(self, "use_filter_sort_alpha", text="", icon="SORTALPHA")
        row.prop(
            self,
            "use_filter_sort_reverse",
            text="",
            icon="SORT_ASC" if not self.use_filter_sort_reverse else "SORT_DESC",
        )
        row.prop(self, "use_filter_missing_groups", text="", icon="COLLECTION_COLOR_01")

    def filter_items(self, context, data, property):
        # This function gets the collection property (as the usual tuple (data, propname)), and must return two lists:
        # * The first one is for filtering, it must contain 32bit integers were self.bitflag_filter_item marks the
        #   matching item as filtered (i.e. to be shown). The upper 16 bits (including self.bitflag_filter_item) are
        #   reserved for internal use, the lower 16 bits are free for custom use. Here we use the first bit to mark
        #   VGROUP_EMPTY.
        # * The second one is for reordering, it must return a list containing the new indices of the items (which
        #   gives us a mapping org_idx -> new_idx).
        # Please note that the default UI_UL_list defines helper functions for common tasks (see its doc for more info).
        # If you do not make filtering and/or ordering, return empty list(s) (this will be more efficient than
        # returning full lists doing nothing!).
        groups = getattr(data, property)
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Use default filtering behavior when use_filter_missing_groups is disabled
        # Filtering by name
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, groups, "name")

        # Reorder by name.
        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(groups, "name")

        # If use_filter_missing_groups is enabled, ignore all other filters
        if self.use_filter_missing_groups:
            flt_flags = [self.bitflag_filter_item] * len(groups)

            for idx, group in enumerate(groups):
                # Show groups that are missing either high_poly or low_poly (or both)
                is_missing_groups = not group.high_poly or not group.low_poly
                if not is_missing_groups:
                    flt_flags[idx] &= ~self.bitflag_filter_item

        return flt_flags, flt_neworder


class QBAKER_UL_high_poly(QBAKER_UL_List):
    # Custom properties, saved with .blend file.
    use_filter_sort_alpha: BoolProperty(
        name="Sort by Name",
        description="Sort items by their name",
        default=True,
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if item.object:
            row.prop(item.object, "name", text="", icon="OBJECT_DATA", emboss=False)
        else:
            row.label(text="")

        row.operator("qbaker.high_poly_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_low_poly(QBAKER_UL_List):
    # Custom properties, saved with .blend file.
    use_filter_sort_alpha: BoolProperty(
        name="Sort by Name",
        description="Sort items by their name",
        default=True,
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if item.object:
            row.prop(item.object, "name", text="", icon="OBJECT_DATA", emboss=False)
        else:
            row.label(text="")

        row.operator("qbaker.low_poly_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_object(QBAKER_UL_List):
    # Custom properties, saved with .blend file.
    use_filter_sort_alpha: BoolProperty(
        name="Sort by Name",
        description="Sort items by their name",
        default=True,
    )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if item.object:
            row.prop(item.object, "name", text="", icon="OBJECT_DATA", emboss=False)
        else:
            row.label(text="")

        row.operator("qbaker.object_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_material_group(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if item.material:
            icon = bpy.types.UILayout.icon(item.material)
            row.prop(item.material, "name", text="", icon_value=icon, emboss=False)
        else:
            row.label(text="")

        row.operator("qbaker.material_group_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_material(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        if item.material:
            icon = bpy.types.UILayout.icon(item.material)
            row.prop(item.material, "name", text="", icon_value=icon, emboss=False)
        else:
            row.label(text="")

        row.operator("qbaker.material_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_map(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "label", text="", icon="TEXTURE", emboss=False)

        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if not bake_group.use_high_to_low:
            self.draw_use_preview(item, row)

        row.operator(
            "qbaker.map_include", text="", icon="CHECKBOX_HLT" if item.use_include else "CHECKBOX_DEHLT", emboss=False
        ).index = index
        row.operator("qbaker.map_remove", text="", icon="X", emboss=False).index = index

    def draw_use_preview(self, item, row):
        type_to_attr = {
            "OCCLUSION": "occlusion",
            "CAVITY": "cavity",
            "CURVATURE": "curvature",
            "EDGE": "edge",
            "GRADIENT": "gradient",
            "HEIGHT": "height",
            "THICKNESS": "thickness",
            "TOON_SHADOW": "toon_shadow",
            "XYZ": "xyz",
        }

        if item.type in type_to_attr:
            attr = getattr(item, type_to_attr[item.type])
            row.prop(
                attr,
                "use_preview",
                text="",
                icon="RESTRICT_VIEW_OFF" if attr.use_preview else "RESTRICT_VIEW_ON",
                emboss=False,
            )


class QBAKER_UL_material_map(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "label", text="", icon="TEXTURE", emboss=False)
        row.operator(
            "qbaker.material_bake_map_include",
            text="",
            icon="CHECKBOX_HLT" if item.use_include else "CHECKBOX_DEHLT",
            emboss=False,
        ).index = index
        row.operator("qbaker.material_bake_map_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_folder(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        if item.use_subfolder:
            row.label(text="", icon="BLANK1")
        row.operator("wm.path_open", text="", icon="FILE_FOLDER", emboss=False).filepath = item.path
        row.prop(item, "name", text="", emboss=False)
        row.operator("qbaker.folder_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_material_folder(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        if item.use_subfolder:
            row.label(text="", icon="BLANK1")
        row.operator("wm.path_open", text="", icon="FILE_FOLDER", emboss=False).filepath = item.path
        row.prop(item, "name", text="", emboss=False)
        row.operator("qbaker.material_bake_folder_remove", text="", icon="X", emboss=False).index = index


class QBAKER_UL_node_folder(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        if item.use_subfolder:
            row.label(text="", icon="BLANK1")
        row.operator("wm.path_open", text="", icon="FILE_FOLDER", emboss=False).filepath = item.path
        row.prop(item, "name", text="", emboss=False)
        row.operator("qbaker.node_bake_folder_remove", text="", icon="X", emboss=False).index = index


classes = (
    QBAKER_UL_bake_group,
    QBAKER_UL_group,
    QBAKER_UL_high_poly,
    QBAKER_UL_low_poly,
    QBAKER_UL_object,
    QBAKER_UL_material_group,
    QBAKER_UL_material,
    QBAKER_UL_map,
    QBAKER_UL_material_map,
    QBAKER_UL_folder,
    QBAKER_UL_material_folder,
    QBAKER_UL_node_folder,
)


register, unregister = bpy.utils.register_classes_factory(classes)
