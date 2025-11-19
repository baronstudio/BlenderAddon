import uuid

import bpy
from bpy.props import EnumProperty, IntProperty, StringProperty
from bpy.types import Operator

from ...qbpy import Object
from ..utils.addon import preferences
from ..utils.bake_group import (
    check_for_duplicates,
    duplicate_property,
    get_similar_objects,
)

STRING_CACHE = {}


def intern_enum_items(items):
    def intern_string(s):
        if not isinstance(s, str):
            return s

        global STRING_CACHE

        if s not in STRING_CACHE:
            STRING_CACHE[s] = s

        return STRING_CACHE[s]

    return [tuple(intern_string(s) for s in item) for item in items]


class QBAKER_OT_bake_group_add(Operator):
    bl_label = "Add Bake Group"
    bl_idname = "qbaker.bake_group_add"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Add a new bake group\n\nShift  •  Bake group from selected objects\nCtrl    •  Bake group (High to low poly) from selected objects\nAlt      •  Bake group per object from selected objects"

    def invoke(self, context, event):
        qbaker = preferences().qbaker
        baker = context.scene.qbaker
        baker.bake.batch_name = qbaker.bake.batch_name
        baker.bake.use_auto_udim = qbaker.bake.use_auto_udim

        if event.shift or event.ctrl:
            if not context.selected_objects:
                self.report({"WARNING"}, "Select the objects")
                return {"CANCELLED"}

            bake_group = baker.bake_groups.add()
            baker.active_bake_group_index = len(baker.bake_groups) - 1
            name = check_for_duplicates(check_list=baker.bake_groups, name=context.object.name)
            bake_group.name = name
            bake_group.bake.batch_name = qbaker.bake.batch_name
            bake_group.bake.use_auto_udim = qbaker.bake.use_auto_udim

            if event.shift:
                bake_group.use_high_to_low = False
                for obj in context.selected_objects:
                    if (
                        obj.type != "MESH"
                        or obj.display_type not in {"SOLID", "TEXTURED"}
                        or "_decal" in obj.name.lower()
                        or "_cage" in obj.name.lower()
                    ):
                        continue

                    elif obj in [item.object for item in bake_group.objects]:
                        if not obj.material_slots:
                            self.report(
                                {"ERROR"},
                                f"{obj.name}: doesn't have a material assigned",
                            )
                        else:
                            for slot in obj.material_slots:
                                if not slot.material:
                                    self.report(
                                        {"ERROR"},
                                        f"{obj.name}: doesn't have a material in the material slot",
                                    )
                        continue

                    elif not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")

                    new_item = bake_group.objects.add()
                    bake_group.active_object_index = len(bake_group.objects) - 1
                    new_item.name = obj.name
                    new_item.object = obj

                    for slot in new_item.object.material_slots:
                        if slot.material:
                            material_slot = new_item.materials.add()
                            new_item.active_material_index = len(new_item.materials) - 1
                            material_slot.name = slot.material.name
                            material_slot.material = slot.material
                        else:
                            self.report(
                                {"ERROR"},
                                f"{new_item.object.name}: doesn't have a material in the material slot",
                            )

            elif event.ctrl:
                bake_group.use_high_to_low = True
                bake_groups = get_similar_objects(context, objects=context.selected_objects)

                for name, objects in bake_groups.items():
                    if bake_group.groups.get(name):
                        for obj in objects.get("high"):
                            if not obj.material_slots:
                                self.report(
                                    {"ERROR"},
                                    f"{obj.name}: doesn't have a material assigned",
                                )
                            else:
                                for slot in obj.material_slots:
                                    if not slot.material:
                                        self.report(
                                            {"ERROR"},
                                            f"{obj.name}: doesn't have a material in the material slot",
                                        )
                        continue

                    group = bake_group.groups.add()
                    bake_group.active_group_index = len(bake_group.groups) - 1
                    group.name = name

                    for obj in objects.get("high"):
                        if not obj.material_slots:
                            self.report(
                                {"ERROR"},
                                f"{obj.name}: doesn't have a material assigned",
                            )
                        else:
                            for slot in obj.material_slots:
                                if not slot.material:
                                    self.report(
                                        {"ERROR"},
                                        f"{obj.name}: doesn't have a material in the material slot",
                                    )

                        item = group.high_poly.add()
                        item.name = obj.name
                        item.object = obj

                    for obj in objects.get("low"):
                        item = group.low_poly.add()
                        item.name = obj.name
                        item.object = obj

                        for obj in objects.get("cage"):
                            item.cage_object = obj

        elif event.alt:
            if not context.selected_objects:
                self.report({"WARNING"}, "Select the objects")
                return {"CANCELLED"}

            for obj in context.selected_objects:
                if (
                    obj.type != "MESH"
                    or obj.display_type not in {"SOLID", "TEXTURED"}
                    or "_decal" in obj.name.lower()
                    or "_cage" in obj.name.lower()
                ):
                    continue

                elif obj.name in [item.name for item in baker.bake_groups]:
                    if not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
                    else:
                        for slot in obj.material_slots:
                            if not slot.material:
                                self.report(
                                    {"ERROR"},
                                    f"{obj.name}: doesn't have a material in the material slot",
                                )
                    continue

                bake_group = baker.bake_groups.add()
                baker.active_bake_group_index = len(baker.bake_groups) - 1
                name = check_for_duplicates(check_list=baker.bake_groups, name=obj.name)
                bake_group.name = name
                bake_group.use_high_to_low = False
                bake_group.bake.batch_name = qbaker.bake.batch_name
                bake_group.bake.use_auto_udim = qbaker.bake.use_auto_udim

                if not obj.material_slots:
                    self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")

                new_item = bake_group.objects.add()
                new_item.name = obj.name
                new_item.object = obj

                for slot in new_item.object.material_slots:
                    if slot.material:
                        material_slot = new_item.materials.add()
                        new_item.active_material_index = len(new_item.materials) - 1
                        material_slot.name = slot.material.name
                        material_slot.material = slot.material
                    else:
                        self.report(
                            {"ERROR"},
                            f"{new_item.object.name}: doesn't have a material in the material slot",
                        )

        else:
            bake_group = baker.bake_groups.add()
            baker.active_bake_group_index = len(baker.bake_groups) - 1
            name = check_for_duplicates(check_list=baker.bake_groups, name="Bakegroup")
            bake_group.name = name
            bake_group.bake.batch_name = qbaker.bake.batch_name
            bake_group.bake.use_auto_udim = qbaker.bake.use_auto_udim

        return {"FINISHED"}


class QBAKER_OT_bake_group_copy(Operator):
    """Duplicate the active bake group"""

    bl_label = "Duplicate Bake Group"
    bl_idname = "qbaker.bake_group_copy"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.scene.qbaker.bake_groups

    def execute(self, context):
        bake_groups = context.scene.qbaker.bake_groups
        active_bake_group = bake_groups[context.scene.qbaker.active_bake_group_index]
        duplicate_bake_group = bake_groups.add()
        duplicate_property(active_bake_group, duplicate_bake_group)

        for map in duplicate_bake_group.maps:
            map.name = uuid.uuid4().hex[:8]

        return {"FINISHED"}


class QBAKER_OT_bake_group_move(Operator):
    bl_label = "Move Bake Group"
    bl_idname = "qbaker.bake_group_move"
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
        return context.scene.qbaker.bake_groups

    @classmethod
    def description(cls, context, properties):
        return "Move the active bake group up/down in the list"

    def execute(self, context):
        qbaker = context.scene.qbaker

        if self.direction == "DOWN":
            if qbaker.active_bake_group_index == len(qbaker.bake_groups) - 1:
                qbaker.bake_groups.move(qbaker.active_bake_group_index, 0)
                qbaker.active_bake_group_index = 0
            else:
                qbaker.bake_groups.move(qbaker.active_bake_group_index, qbaker.active_bake_group_index + 1)
                qbaker.active_bake_group_index += 1

        elif self.direction == "UP":
            if qbaker.active_bake_group_index == 0:
                qbaker.bake_groups.move(0, len(qbaker.bake_groups) - 1)
                qbaker.active_bake_group_index = len(qbaker.bake_groups) - 1
            else:
                qbaker.bake_groups.move(qbaker.active_bake_group_index, qbaker.active_bake_group_index - 1)
                qbaker.active_bake_group_index -= 1

        return {"FINISHED"}


class QBAKER_OT_bake_group_include(Operator):
    bl_label = "Include Bake Group"
    bl_idname = "qbaker.bake_group_include"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        return context.scene.qbaker.bake_groups

    @classmethod
    def description(cls, context, properties):
        return "Include the bake group\n\nShift  •  Include all the bake groups\nCtrl    •  Isolate the bake group"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.index]
        self.include = self.bake_group.use_include

        if event.shift:
            for bake_group in self.baker.bake_groups:
                bake_group.use_include = not self.include
        elif event.ctrl:
            if any(bake_group.use_include for bake_group in self.baker.bake_groups if bake_group != self.bake_group):
                for bake_group in self.baker.bake_groups:
                    bake_group.use_include = False
            else:
                for bake_group in self.baker.bake_groups:
                    bake_group.use_include = not bake_group.use_include

            self.bake_group.use_include = True
        else:
            self.bake_group.use_include = not self.include

        return {"FINISHED"}


class QBAKER_OT_bake_group_remove(Operator, Object):
    bl_label = "Remove Bake Group"
    bl_idname = "qbaker.bake_group_remove"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return (
            "Remove the bake group\n\nShift  •  Remove all the bake groups\nCtrl    •  Remove all the other bake groups"
        )

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.index]

        if event.shift:
            for bake_group in self.baker.bake_groups:
                self.remove_nodes(bake_group)

            self.baker.bake_groups.clear()
            self.baker.active_bake_group_index = 0

            if self.baker.use_map_global:
                self.baker.maps.clear()
                self.baker.active_map_index = 0
        elif event.ctrl:
            for bake_group in reversed(self.baker.bake_groups):
                if bake_group != self.bake_group:
                    self.remove_nodes(bake_group)
                    self.baker.bake_groups.remove(self.baker.bake_groups.find(bake_group.name))
                    self.baker.active_bake_group_index = min(
                        max(0, self.baker.active_bake_group_index - 1), len(self.baker.bake_groups) - 1
                    )

                    if self.baker.use_map_global and len(self.baker.bake_groups) == 0:
                        self.baker.maps.clear()
                        self.baker.active_map_index = 0
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        self.remove_nodes(self.bake_group)
        self.baker.bake_groups.remove(self.index)
        self.baker.active_bake_group_index = min(
            max(0, self.baker.active_bake_group_index - 1), len(self.baker.bake_groups) - 1
        )

        if self.baker.use_map_global and len(self.baker.bake_groups) == 0:
            self.baker.maps.clear()
            self.baker.active_map_index = 0

        return {"FINISHED"}

    def remove_nodes(self, bake_group):
        for item in bake_group.objects:
            if item.object and item.object.material_slots:
                for slot in item.object.material_slots:
                    if slot.material and slot.material.use_nodes:
                        node_tree = slot.material.node_tree
                        for node in node_tree.nodes:
                            if node.name.split("_")[0] == "QB":
                                node_tree.nodes.remove(node)


class QBAKER_OT_object_add(Operator):
    """Add an object"""

    bl_label = "Add Object"
    bl_idname = "qbaker.object_add"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "object"

    def object_enum(self, context):
        items = [
            (obj.name, obj.name, "", "OBJECT_DATA", index)
            for index, obj in enumerate(context.scene.objects)
            if obj.type == "MESH"
            and not obj.name.startswith(".")
            and "_decal" not in obj.name.lower()
            and "_cage" not in obj.name.lower()
        ]

        return intern_enum_items(items)

    object: EnumProperty(items=object_enum)

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        return baker.bake_groups

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        obj = context.scene.objects.get(self.object)

        if obj in [item.object for item in bake_group.objects]:
            if not obj.material_slots:
                self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
            else:
                for slot in obj.material_slots:
                    if not slot.material:
                        self.report(
                            {"ERROR"},
                            f"{obj.name}: doesn't have a material in the material slot",
                        )
            return {"CANCELLED"}

        elif not obj.material_slots:
            self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")

        new_item = bake_group.objects.add()
        bake_group.active_object_index = len(bake_group.objects) - 1
        new_item.name = obj.name
        new_item.object = obj

        for slot in new_item.object.material_slots:
            if slot.material:
                material_slot = new_item.materials.add()
                new_item.active_material_index = len(new_item.materials) - 1
                material_slot.name = slot.material.name
                material_slot.material = slot.material
            else:
                self.report(
                    {"ERROR"},
                    f"{new_item.object.name}: doesn't have a material in the material slot",
                )

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_object_load(Operator):
    """Load selected object"""

    bl_label = "Load Objects"
    bl_idname = "qbaker.object_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        for obj in context.selected_objects:
            if (
                obj.type != "MESH"
                or obj.display_type not in {"SOLID", "TEXTURED"}
                or "_decal" in obj.name.lower()
                or "_cage" in obj.name.lower()
            ):
                continue

            elif obj in [item.object for item in bake_group.objects]:
                if not obj.material_slots:
                    self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
                else:
                    for slot in obj.material_slots:
                        if not slot.material:
                            self.report(
                                {"ERROR"},
                                f"{obj.name}: doesn't have a material in the material slot",
                            )
                continue

            elif not obj.material_slots:
                self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")

            new_item = bake_group.objects.add()
            bake_group.active_object_index = len(bake_group.objects) - 1
            new_item.name = obj.name
            new_item.object = obj

            for slot in new_item.object.material_slots:
                if slot.material:
                    material_slot = new_item.materials.add()
                    new_item.active_material_index = len(new_item.materials) - 1
                    material_slot.name = slot.material.name
                    material_slot.material = slot.material
                else:
                    self.report(
                        {"ERROR"},
                        f"{new_item.object.name}: doesn't have a material in the material slot",
                    )

        return {"FINISHED"}


class QBAKER_OT_object_move(Operator):
    bl_label = "Move Object"
    bl_idname = "qbaker.object_move"
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
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        return bake_group.objects

    @classmethod
    def description(cls, context, properties):
        return "Move the active object up/down in the list"

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if self.direction == "DOWN":
            if bake_group.active_object_index == len(bake_group.objects) - 1:
                bake_group.objects.move(bake_group.active_object_index, 0)
                bake_group.active_object_index = 0
            else:
                bake_group.objects.move(bake_group.active_object_index, bake_group.active_object_index + 1)
                bake_group.active_object_index += 1

        elif self.direction == "UP":
            if bake_group.active_object_index == 0:
                bake_group.objects.move(0, len(bake_group.objects) - 1)
                bake_group.active_object_index = len(bake_group.objects) - 1
            else:
                bake_group.objects.move(bake_group.active_object_index, bake_group.active_object_index - 1)
                bake_group.active_object_index -= 1

        return {"FINISHED"}


class QBAKER_OT_object_remove(Operator):
    bl_label = "Remove Objects"
    bl_idname = "qbaker.object_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the object\n\nShift  •  Remove all the objects\nCtrl    •  Remove all the other objects"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]
        self.object = self.bake_group.objects[self.index]

        if event.shift:
            for item in self.bake_group.objects:
                self.remove_nodes(item)

            self.bake_group.objects.clear()
            self.bake_group.active_object_index = 0
        elif event.ctrl:
            for item in reversed(self.bake_group.objects):
                if item != self.object:
                    self.remove_nodes(item)
                    self.bake_group.objects.remove(self.bake_group.objects.find(item.name))
                    self.bake_group.active_object_index = min(
                        max(0, self.bake_group.active_object_index - 1), len(self.bake_group.objects) - 1
                    )
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        self.remove_nodes(item=self.object)
        self.bake_group.objects.remove(self.index)
        self.bake_group.active_object_index = min(
            max(0, self.bake_group.active_object_index - 1), len(self.bake_group.objects) - 1
        )
        return {"FINISHED"}

    def remove_nodes(self, item):
        if item.object and item.object.material_slots:
            for slot in item.object.material_slots:
                if slot.material and slot.material.use_nodes:
                    node_tree = slot.material.node_tree
                    for node in node_tree.nodes:
                        if node.name.split("_")[0] == "QB":
                            node_tree.nodes.remove(node)


class QBAKER_OT_uvmap_add(Operator):
    """Add a new UV Map"""

    bl_label = "Add UV Map"
    bl_idname = "qbaker.uvmap_add"
    bl_options = {"REGISTER", "INTERNAL"}

    name: StringProperty(
        name="Name",
        description="Name of the UV Map",
        default="QBMap",
    )

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        layout.prop(self, "name")

    def invoke(self, context, event):
        context.window_manager.invoke_props_dialog(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.use_uvmap_global:
            if bake_group.use_high_to_low:
                for group in bake_group.groups:
                    for item in group.low_poly:
                        uv_map = item.object.data.uv_layers.get(self.name) or item.object.data.uv_layers.new(
                            name=self.name
                        )
                        item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]
                bake_group.group_uv_map = self.name

            else:
                for item in bake_group.objects:
                    uv_map = item.object.data.uv_layers.get(self.name) or item.object.data.uv_layers.new(name=self.name)
                    item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]
                bake_group.object_uv_map = self.name

        elif bake_group.use_high_to_low and bake_group.groups:
            group = bake_group.groups[bake_group.active_group_index]

            if group.low_poly:
                for item in group.low_poly:
                    uv_map = item.object.data.uv_layers.get(self.name) or item.object.data.uv_layers.new(name=self.name)
                    item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]
                    item.uv_map = self.name

        elif bake_group.objects:
            item = bake_group.objects[bake_group.active_object_index]
            uv_map = item.object.data.uv_layers.get(self.name) or item.object.data.uv_layers.new(name=self.name)
            item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]
            item.uv_map = self.name

        return {"FINISHED"}


class QBAKER_OT_material_group_add(Operator):
    """Add a material"""

    bl_label = "Add Material"
    bl_idname = "qbaker.material_group_add"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "material"

    def material_enum(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        materials = {}

        item = bake_group.objects[bake_group.active_object_index]
        if item.object and item.object.material_slots:
            for i, slot in enumerate(item.object.material_slots):
                if slot.material and not slot.material.name.startswith("."):
                    icon = bpy.types.UILayout.icon(slot.material)
                    materials[slot.material] = (slot.name, slot.name, "", icon, i)

        item = bake_group.objects[bake_group.active_object_index]
        for slot in item.materials:
            materials.pop(slot.material, None)

        return list(materials.values())

    material: EnumProperty(items=material_enum)

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        item = bake_group.objects[bake_group.active_object_index]
        return item.object.material_slots

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        item = bake_group.objects[bake_group.active_object_index]
        item.synchronize_material = False  # updates the internal materials if needed

        new_item = item.materials.add()
        item.active_material_index = len(item.materials) - 1
        new_item.name = item.object.material_slots[self.material].material.name
        new_item.material = item.object.material_slots[self.material].material

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_material_group_load(Operator):
    """Load object materials"""

    bl_label = "Load Materials"
    bl_idname = "qbaker.material_group_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker

        if baker.bake_groups:
            bake_group = baker.bake_groups[baker.active_bake_group_index]

            if bake_group.objects:
                item = bake_group.objects[bake_group.active_object_index]
                return item.object and item.object.material_slots

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        item = bake_group.objects[bake_group.active_object_index]

        item.synchronize_material = True  # loads the material through set function

        for slot in item.object.material_slots:
            if slot.material:
                continue
            self.report({"WARNING"}, f"{item.object.name} doesn't have material assigned")

        return {"FINISHED"}


class QBAKER_OT_material_group_remove(Operator):
    bl_label = "Remove Materials"
    bl_idname = "qbaker.material_group_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the material\n\nShift  •  Remove all the materials"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]

        if not event.shift:
            return self.execute(context)

        item = self.bake_group.objects[self.bake_group.active_object_index]
        item.synchronize_material = False
        item.materials.clear()
        item.active_material_index = 0

        return {"FINISHED"}

    def execute(self, context):
        item = self.bake_group.objects[self.bake_group.active_object_index]
        item.synchronize_material = False
        item.materials.remove(self.index)
        item.active_material_index = min(max(0, item.active_material_index - 1), len(item.materials) - 1)
        return {"FINISHED"}


class QBAKER_OT_check_alt(Operator):
    bl_label = "Check alt"
    bl_idname = "qbaker.check_alt"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        return {"FINISHED"} if event.alt else {"CANCELLED"}

    def execute(self, context):
        return {"FINISHED"}


class QBAKER_OT_check_press(Operator, Object):
    bl_label = "Left Click"
    bl_idname = "qbaker.check_press"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            return {"CANCELLED"}
        # material = self.get_material(name='.CAGE', use_nodes=False)
        # bpy.data.materials.remove(material)
        return {"FINISHED"}

    def execute(self, context):
        return {"FINISHED"}


classes = (
    QBAKER_OT_bake_group_add,
    QBAKER_OT_bake_group_copy,
    QBAKER_OT_bake_group_move,
    QBAKER_OT_bake_group_include,
    QBAKER_OT_bake_group_remove,
    QBAKER_OT_object_add,
    QBAKER_OT_object_load,
    QBAKER_OT_object_move,
    QBAKER_OT_object_remove,
    QBAKER_OT_uvmap_add,
    QBAKER_OT_material_group_add,
    QBAKER_OT_material_group_load,
    QBAKER_OT_material_group_remove,
    QBAKER_OT_check_alt,
    QBAKER_OT_check_press,
)


register, unregister = bpy.utils.register_classes_factory(classes)
