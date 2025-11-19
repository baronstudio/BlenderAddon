import bpy
from bpy.props import EnumProperty, IntProperty
from bpy.types import Operator

from ...qbpy import Object
from ..utils.bake_group import (
    bake_group_enum_item,
    check_for_duplicates,
    get_possible_bake_groups,
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


class QBAKER_OT_group_add(Operator):
    bl_label = "Add Group"
    bl_idname = "qbaker.group_add"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def description(cls, context, properties):
        return "Add a new group\n\nShift  •  Group per object from selected objects based on suffix\nCtrl    •  Group from selected objects (active = lowpoly)"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]

        if event.shift:
            if not context.selected_objects:
                self.report({"WARNING"}, "Select the objects")
                return {"CANCELLED"}

            bake_groups = get_similar_objects(context, objects=context.selected_objects)
            for name, objects in bake_groups.items():
                if self.bake_group.groups.get(name):
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

                group = self.bake_group.groups.add()
                self.bake_group.active_group_index = len(self.bake_group.groups) - 1
                name = check_for_duplicates(check_list=self.bake_group.groups, name=name)
                group.name = name

                for obj in objects.get("high"):
                    if not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
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

        elif event.ctrl:
            if not context.selected_objects:
                self.report({"WARNING"}, "Select the objects")
                return {"CANCELLED"}

            group = self.bake_group.groups.add()
            self.bake_group.active_group_index = len(self.bake_group.groups) - 1

            for obj in context.selected_objects:
                if obj.type != "MESH":
                    continue

                if obj in [item.object for item in group.high_poly]:
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

                if obj != context.object:
                    if not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
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

                elif obj == context.object:
                    name = check_for_duplicates(check_list=self.bake_group.groups, name=obj.name)
                    group.name = name
                    item = group.low_poly.add()
                    item.name = obj.name
                    item.object = obj
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        group = self.bake_group.groups.add()
        self.bake_group.active_group_index = len(self.bake_group.groups) - 1
        name = check_for_duplicates(check_list=self.bake_group.groups, name="Group")
        group.name = name
        return {"FINISHED"}


class QBAKER_OT_group_load(Operator):
    """Auto load groups based on suffix"""

    bl_label = "Load Groups"
    bl_idname = "qbaker.group_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return get_possible_bake_groups(context)

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        bake_groups = get_possible_bake_groups(context)

        for name, objects in bake_groups.items():
            if bake_group.groups.get(name):
                for obj in objects.get("high"):
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

            group = bake_group.groups.add()
            bake_group.active_group_index = len(bake_group.groups) - 1
            group.name = name

            for obj in objects.get("high"):
                if not obj.material_slots:
                    self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
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

        return {"FINISHED"}


class QBAKER_OT_group_select(Operator):
    """Select a group"""

    bl_label = "Select Group"
    bl_idname = "qbaker.group_select"
    bl_options = {"REGISTER", "INTERNAL"}

    name: EnumProperty(
        items=bake_group_enum_item,
    )

    @classmethod
    def poll(cls, context):
        return get_possible_bake_groups(context)

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        bake_groups = get_possible_bake_groups(context)

        for name, objects in bake_groups.items():
            if bake_group.groups.get(name):
                for obj in objects.get("high"):
                    if not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
                    else:
                        for slot in obj.material_slots:
                            if not slot.material:
                                self.report(
                                    {"ERROR"},
                                    f"{obj.name}: doesn't have a material in the material slot",
                                )
            elif name == self.name:
                group = bake_group.groups.add()
                bake_group.active_group_index = len(bake_group.groups) - 1
                group.name = name

                for obj in objects.get("high"):
                    if not obj.material_slots:
                        self.report({"ERROR"}, f"{obj.name}: doesn't have a material assigned")
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

        return {"FINISHED"}


class QBAKER_OT_group_move(Operator):
    bl_label = "Move Group"
    bl_idname = "qbaker.group_move"
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
        return bake_group.groups

    @classmethod
    def description(cls, context, properties):
        return "Move the active group up/down in the list"

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if self.direction == "DOWN":
            if bake_group.active_group_index == len(bake_group.groups) - 1:
                bake_group.groups.move(bake_group.active_group_index, 0)
                bake_group.active_group_index = 0
            else:
                bake_group.groups.move(bake_group.active_group_index, bake_group.active_group_index + 1)
                bake_group.active_group_index += 1

        elif self.direction == "UP":
            if bake_group.active_group_index == 0:
                bake_group.groups.move(0, len(bake_group.groups) - 1)
                bake_group.active_group_index = len(bake_group.groups) - 1
            else:
                bake_group.groups.move(bake_group.active_group_index, bake_group.active_group_index - 1)
                bake_group.active_group_index -= 1

        return {"FINISHED"}


class QBAKER_OT_group_include(Operator):
    bl_label = "Include Group"
    bl_idname = "qbaker.group_include"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def poll(cls, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        return bake_group.groups

    @classmethod
    def description(cls, context, properties):
        return "Include the group\n\nShift  •  Include all the groups\nCtrl    •  Isolate the group"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]
        self.group = self.bake_group.groups[self.index]
        self.include = self.group.use_include

        if event.shift:
            for group in self.bake_group.groups:
                group.use_include = not self.include
        elif event.ctrl:
            if any(group.use_include for group in self.bake_group.groups if group != self.group):
                for group in self.bake_group.groups:
                    group.use_include = False
            else:
                for group in self.bake_group.groups:
                    group.use_include = not group.use_include

            self.group.use_include = True
        else:
            self.group.use_include = not self.include

        return {"FINISHED"}


class QBAKER_OT_group_remove(Operator, Object):
    bl_label = "Remove Group"
    bl_idname = "qbaker.group_remove"
    bl_options = {"REGISTER", "INTERNAL", "UNDO_GROUPED"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the group\n\nShift  •  Remove all the groups\nCtrl    •  Remove all the other groups"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]
        self.group = self.bake_group.groups[self.index]

        if event.shift:
            self.bake_group.groups.clear()
            self.bake_group.active_group_index = 0
        elif event.ctrl:
            for group in reversed(self.bake_group.groups):
                if group != self.group:
                    self.bake_group.groups.remove(self.bake_group.groups.find(group.name))
                    self.bake_group.active_group_index = min(
                        max(0, self.bake_group.active_group_index - 1), len(self.bake_group.groups) - 1
                    )
        else:
            return self.execute(context)

        return {"FINISHED"}

    def execute(self, context):
        self.bake_group.groups.remove(self.index)
        self.bake_group.active_group_index = min(
            max(0, self.bake_group.active_group_index - 1), len(self.bake_group.groups) - 1
        )
        return {"FINISHED"}


class QBAKER_OT_high_poly_add(Operator):
    """Add a high poly object"""

    bl_label = "Add Object"
    bl_idname = "qbaker.high_poly_add"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "object"

    def object_enum(self, context):
        items = [
            (obj.name, obj.name, "", "OBJECT_DATA", index)
            for index, obj in enumerate(context.scene.objects)
            if obj.type == "MESH"
            and not obj.name.startswith(".")  # skip objects starting with a dot
            and "_decal" not in obj.name.lower()
            and "_low" not in obj.name.lower()
            and "_cage" not in obj.name.lower()
        ]

        return intern_enum_items(items)

    object: EnumProperty(items=object_enum)

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        obj = context.scene.objects.get(self.object)

        if obj in [item.object for item in group.high_poly]:
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

        new_item = group.high_poly.add()
        group.active_high_poly_index = len(group.high_poly) - 1
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


class QBAKER_OT_high_poly_load(Operator):
    """Load selected objects to the active group"""

    bl_label = "Load Objects"
    bl_idname = "qbaker.high_poly_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        for obj in context.selected_objects:
            if (
                obj.type != "MESH"
                or "_decal" in obj.name.lower()
                or "_low" in obj.name.lower()
                or "_cage" in obj.name.lower()
            ):
                continue

            elif obj in [item.object for item in group.high_poly]:
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

            new_item = group.high_poly.add()
            group.active_high_poly_index = len(group.high_poly) - 1
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


class QBAKER_OT_high_poly_remove(Operator):
    bl_label = "Remove High Poly"
    bl_idname = "qbaker.high_poly_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the high poly object\n\nShift  •  Remove all the high poly objects"

    def invoke(self, context, event):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        self.group = bake_group.groups[bake_group.active_group_index]

        if not event.shift:
            return self.execute(context)

        self.group.high_poly.clear()
        self.group.active_high_poly_index = 0
        return {"FINISHED"}

    def execute(self, context):
        self.group.high_poly.remove(self.index)
        self.group.active_high_poly_index = min(
            max(0, self.group.active_high_poly_index - 1), len(self.group.high_poly) - 1
        )
        return {"FINISHED"}


class QBAKER_OT_high_poly_move(Operator):
    bl_label = "Move High Poly"
    bl_idname = "qbaker.high_poly_move"
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
        return bake_group.groups

    @classmethod
    def description(cls, context, properties):
        return "Move the active high poly object up/down in the list"

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        if self.direction == "DOWN":
            if group.active_high_poly_index == len(group.high_poly) - 1:
                group.high_poly.move(group.active_high_poly_index, 0)
                group.active_high_poly_index = 0
            else:
                group.high_poly.move(group.active_high_poly_index, group.active_high_poly_index + 1)
                group.active_high_poly_index += 1

        elif self.direction == "UP":
            if group.active_high_poly_index == 0:
                group.high_poly.move(0, len(group.high_poly) - 1)
                group.active_high_poly_index = len(group.high_poly) - 1
            else:
                group.high_poly.move(group.active_high_poly_index, group.active_high_poly_index - 1)
                group.active_high_poly_index -= 1

        return {"FINISHED"}


class QBAKER_OT_low_poly_add(Operator):
    """Add a low poly object"""

    bl_label = "Add Object"
    bl_idname = "qbaker.low_poly_add"
    bl_options = {"REGISTER", "INTERNAL"}
    bl_property = "object"

    def object_enum(self, context):
        items = [
            (obj.name, obj.name, "", "OBJECT_DATA", index)
            for index, obj in enumerate(context.scene.objects)
            if obj.type == "MESH"
            and not obj.name.startswith(".")  # skip objects starting with a dot
            and "_high" not in obj.name.lower()
            and "_decal" not in obj.name.lower()
            and "_cage" not in obj.name.lower()
        ]

        return intern_enum_items(items)

    object: EnumProperty(items=object_enum)

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        if self.object in {item.object.name for item in group.low_poly}:
            self.report({"WARNING"}, "Low poly object already exists")
            return {"FINISHED"}

        group.low_poly.clear()
        item = group.low_poly.add()
        group.active_low_poly_index = len(group.low_poly) - 1
        item.name = self.object
        item.object = context.scene.objects.get(self.object)

        context.area.tag_redraw()
        return {"FINISHED"}


class QBAKER_OT_low_poly_load(Operator):
    """Load the active object to the active group"""

    bl_label = "Load Object"
    bl_idname = "qbaker.low_poly_load"
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        return (
            context.object
            and context.object.type == "MESH"
            and "_high" not in context.object.name.lower()
            and "_decal" not in context.object.name.lower()
            and "_cage" not in context.object.name.lower()
        )

    def execute(self, context):
        baker = context.scene.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]
        group = bake_group.groups[bake_group.active_group_index]

        if context.object in [item.object for item in group.low_poly]:
            self.report({"WARNING"}, "Low poly object already exists")
            return {"FINISHED"}

        group.low_poly.clear()
        item = group.low_poly.add()
        group.active_low_poly_index = len(group.low_poly) - 1
        item.name = context.object.name
        item.object = context.object

        return {"FINISHED"}


class QBAKER_OT_low_poly_remove(Operator):
    bl_label = "Remove Low Poly"
    bl_idname = "qbaker.low_poly_remove"
    bl_options = {"REGISTER", "INTERNAL"}

    index: IntProperty()

    @classmethod
    def description(cls, context, properties):
        return "Remove the low poly object\n\nShift  •  Remove all the low poly objects"

    def invoke(self, context, event):
        self.baker = context.scene.qbaker
        self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]
        if self.baker.bake_groups:
            self.bake_group = self.baker.bake_groups[self.baker.active_bake_group_index]
            if self.bake_group.groups and self.bake_group.groups[self.bake_group.active_group_index].low_poly:
                self.group = self.bake_group.groups[self.bake_group.active_group_index]

        if not event.shift:
            return self.execute(context)

        self.group.low_poly.clear()
        self.group.active_low_poly_index = 0
        return {"FINISHED"}

    def execute(self, context):
        self.group.low_poly.remove(self.index)
        self.group.active_low_poly_index = min(
            max(0, self.group.active_low_poly_index - 1), len(self.group.low_poly) - 1
        )
        return {"FINISHED"}


classes = (
    QBAKER_OT_group_add,
    QBAKER_OT_group_load,
    QBAKER_OT_group_select,
    QBAKER_OT_group_move,
    QBAKER_OT_group_include,
    QBAKER_OT_group_remove,
    QBAKER_OT_high_poly_add,
    QBAKER_OT_high_poly_load,
    QBAKER_OT_high_poly_remove,
    QBAKER_OT_high_poly_move,
    QBAKER_OT_low_poly_add,
    QBAKER_OT_low_poly_load,
    QBAKER_OT_low_poly_remove,
)


register, unregister = bpy.utils.register_classes_factory(classes)
