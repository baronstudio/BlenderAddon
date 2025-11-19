from contextlib import suppress

import bpy

from ...qbpy import Modifier, Object
from .addon import preferences


def duplicate_property(item, duplicate):
    if item.__class__ != duplicate.__class__:
        raise TypeError(
            "item and duplicate need to be of the same type\n Can not duplicate %s to %s"
            % (item.__class__, duplicate.__class__)
        )

    for prop in item.bl_rna.properties[1:]:  # exclude rna_type
        identifier = prop.identifier
        value = getattr(item, identifier)
        class_name = value.__class__.__name__

        if not hasattr(value, "id_data"):
            with suppress(AttributeError):  # catch Exception from read-only property
                setattr(duplicate, identifier, value)
            continue

        if value == value.id_data:
            setattr(duplicate, identifier, value)
            continue

        if class_name == "bpy_prop_array":
            setattr(duplicate, identifier, value)
        elif class_name == "bpy_prop_collection":
            duplicate_property(value, getattr(duplicate, identifier))
            for sub_item in value:
                sub_duplicate = getattr(duplicate, identifier).add()
                duplicate_property(sub_item, sub_duplicate)
        elif class_name == "bpy_prop_collection_idprop":
            for sub_item in value:
                sub_duplicate = getattr(duplicate, identifier).add()
                duplicate_property(sub_item, sub_duplicate)
        else:
            duplicate_property(value, getattr(duplicate, identifier))


def check_for_duplicates(check_list: list, name: str, num: int = 1) -> str:
    """Check for the same name in check_list and append .001, .002 etc. if found

    check_list (list) - List to check against.
    name (str) - Name to check.
    num (int, optional) - Starting number to append, Defaults to 1.
    return (str) - name with expansion if necessary.
    """
    split = name.split(".")
    base_name = ".".join(split[:-1]) if split[-1].isnumeric() else name
    while name in check_list:
        name = "{0}.{1:03d}".format(base_name, num)
        num += 1
    return name


def _get_basename(context, object) -> str:
    """Get the basename.

    object (bpy.types.Object) - The object to get the basename for.
    return (str) - The basename.
    """
    name = object.name.replace("_low", "").replace("_high", "").replace("_cage", "").rsplit(".", 1)
    if len(name) > 1 and not name[1].isnumeric():
        name[0] += name[1]

    return name[0]


def get_similar_objects(context, objects) -> dict:
    """Get similar objects.

    objects (list) - The objects to get similar objects for.
    return (dict) - The similar objects.
    """
    dict = {}

    for obj in objects:
        if obj.type != "MESH" or obj.display_type not in {"SOLID", "TEXTURED"} or "_decal" in obj.name.lower():
            continue

        name = _get_basename(context, obj)
        dict.setdefault(name, {"high": [], "low": [], "cage": []})

        if "high" in obj.name.lower():
            dict[name]["high"].append(obj)
        elif "low" in obj.name.lower():
            dict[name]["low"].append(obj)
        elif "cage" in obj.name.lower():
            dict[name]["cage"].append(obj)
        elif name == obj.name.split(".")[0]:
            dict[name]["low"].append(obj)

    return dict


def get_possible_bake_groups(context):
    """Get possible bake groups."""
    object_dict = get_similar_objects(context, objects=context.scene.objects)
    return {key: value for key, value in object_dict.items() if len(object_dict[key]["high"])}


def bake_group_enum_item(self, context):
    """Get the bake group enum items."""
    object_dict = get_similar_objects(context, objects=context.scene.objects)

    if bake_groups := [(name, "", "OUTLINER_COLLECTION") for name in object_dict if len(object_dict[name]["high"])]:
        return [
            (f"{bake_group[0]}", bake_group[0], bake_group[1], bake_group[2], number)
            for number, bake_group in enumerate(bake_groups)
        ]
    else:
        return [("NONE", "'_high' named objects are not available", "")]


def add_cage(context, group, item):
    """Add a cage."""
    qbaker = preferences().qbaker

    if group.use_auto_cage:
        cage_object = Object.copy_object(obj=item.object, name=f"{item.object.name}_auto_cage", clear_transform=True)
        cage_object.data.materials.clear()
        cage_object.hide_select = True
        Object.link_object(obj=cage_object, collection=item.object.users_collection[0])
        Object.parent_object(parent=item.object, child=cage_object, copy_transform=False)
        cage_object.show_wire = qbaker.cage.show_wireframe

        material = Object.get_material(name=".CAGE", use_nodes=False)
        material.diffuse_color = qbaker.cage.color
        # material.blend_method = "BLEND"
        Object.set_material(obj=cage_object, material=material)

        item.auto_cage_object = cage_object
        Modifier.displace(obj=cage_object, name="qbaker_cage", strength=item.cage_extrusion)

    elif item.cage_object:
        item.cage_object.data.materials.clear()
        item.cage_object.show_wire = qbaker.cage.show_wireframe

        material = Object.get_material(name=".CAGE", use_nodes=False)
        material.diffuse_color = qbaker.cage.color
        # material.blend_method = "BLEND"
        Object.set_material(obj=item.cage_object, material=material)
        # Modifier.displace(obj=item.cage_object, name="qbaker_cage", strength=item.cage_extrusion)


def remove_cages(context):
    baker = context.scene.qbaker
    if not baker.bake_groups:
        return

    baker_group = baker.bake_groups[baker.active_bake_group_index]
    if not baker_group.groups:
        return

    # Check if Alt was pressed to determine scope of cage removal
    try:
        alt_pressed = bpy.ops.qbaker.check_alt("INVOKE_DEFAULT") == {"FINISHED"}
    except RuntimeError:
        # Suppress error when operator can't be called during drawing/rendering
        alt_pressed = False

    # If Alt was pressed, remove cages from ALL groups; otherwise just active group
    groups_to_clean = baker_group.groups if alt_pressed else [baker_group.groups[baker_group.active_group_index]]

    for group in groups_to_clean:
        if not group.low_poly:
            continue

        for item in group.low_poly:
            if group.use_auto_cage and item.auto_cage_object:
                Object.remove_object(obj=item.auto_cage_object)


def remove_cage(group, item):
    if group.use_auto_cage and item.auto_cage_object:
        Object.remove_object(obj=item.auto_cage_object)


def extrude_cage(self, context):
    """Extrude the cage."""
    if not self.get("extrusion_user_hold", False):
        return

    baker = context.scene.qbaker
    if not baker.bake_groups:
        return

    baker_group = baker.bake_groups[baker.active_bake_group_index]
    if not baker_group.groups:
        return

    group = baker_group.groups[baker_group.active_group_index]
    if not group.low_poly:
        return

    try:
        alt_pressed = bpy.ops.qbaker.check_alt("INVOKE_DEFAULT") == {"FINISHED"}
    except RuntimeError:
        # Suppress error when operator can't be called during drawing/rendering
        alt_pressed = False

    if context.space_data.shading.type not in {"SOLID"}:
        context.space_data.shading.type = "SOLID"

    # Determine which groups to process based on Alt key
    groups_to_process = baker_group.groups if alt_pressed else [group]

    for current_group in groups_to_process:
        if not current_group.low_poly:
            continue

        for item in current_group.low_poly:
            # Remove cages from other items when Alt is not pressed and it's not the current item
            if not alt_pressed and self != item:
                remove_cage(current_group, item)
                continue

            item["extrusion_user_hold"] = self.get("extrusion_user_hold", False)
            add_cage(context, current_group, item)

            if current_group.use_auto_cage:
                displace = Modifier.displace(obj=item.auto_cage_object, name="qbaker_cage")
            # elif item.cage_object:
            #     displace = Modifier.displace(obj=item.cage_object, name="qbaker_cage")

            displace.strength = self.get("cage_extrusion", 0.1)
            item["cage_extrusion"] = self.get("cage_extrusion", 0.1)
