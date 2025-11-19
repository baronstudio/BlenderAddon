import bpy

from ...qbpy import Collection, Material, Object
from .addon import preferences


def post_bake(context):
    prefs = preferences()
    baker = context.scene.qbaker

    qbaked_collection = Collection.get_collection("Q-Baked")
    Collection.link_collection(qbaked_collection)

    for bake_group in baker.bake_groups:
        if not bake_group.use_include:
            continue

        # remove the unused image nodes
        if prefs.qbaker.bake.use_remove_disabled_maps:
            if material := bpy.data.materials.get(f"{bake_group.name}_BAKED"):
                maps = baker.maps if baker.use_map_global else bake_group.maps

                for node in material.node_tree.nodes:
                    if node.type == "TEX_IMAGE":
                        if not node.image or node.name not in [map.name for map in maps if map.use_include]:
                            if node.outputs[0].links and node.outputs[0].links[0].to_node.type != "BSDF_PRINCIPLED":
                                material.node_tree.nodes.remove(node.outputs[0].links[0].to_node)
                            material.node_tree.nodes.remove(node)

        if bake_group.use_high_to_low:
            high_poly_objects = [
                item.object for group in bake_group.groups if group.use_include for item in group.high_poly
            ]
            selected_objects = [
                item.object for group in bake_group.groups if group.use_include for item in group.low_poly
            ]
        else:
            selected_objects = [item.object for item in bake_group.objects]

        bake_settings = baker.bake if baker.use_bake_global else bake_group.bake

        if bake_settings.use_duplicate_objects and bake_settings.use_join_objects:
            baked_object = bpy.data.objects.get(f"{bake_group.name}_BAKED")
            if not baked_object:
                baked_object_data = bpy.data.meshes.new(f"{bake_group.name}_BAKED")
                baked_object = bpy.data.objects.new(f"{bake_group.name}_BAKED", baked_object_data)
                qbaked_collection.objects.link(baked_object)
                duplicate_objects = [baked_object]

                for obj in selected_objects:
                    # copy the object
                    duplicate_object = Object.copy_object(obj=obj, name=f"{obj.name}_temp_BAKED")
                    Object.link_object(obj=duplicate_object, collection=qbaked_collection)
                    for attribute in reversed(duplicate_object.data.color_attributes):
                        duplicate_object.data.color_attributes.remove(attribute)
                    duplicate_objects.append(duplicate_object)

                with context.temp_override(active_object=baked_object, selected_editable_objects=duplicate_objects):
                    bpy.ops.object.join()

            # remove and assign the material
            Material.remove_material_slots(obj=baked_object)
            if material := bpy.data.materials.get(f"{bake_group.name}_BAKED"):
                Material.set_material(obj=baked_object, material=material)

            # remove the UVMaps
            # if bake_group.use_uvmap_global:
            #     for uv in reversed(baked_object.data.uv_layers):
            #         if uv.name != bake_group.object_uv_map:
            #             baked_object.data.uv_layers.remove(uv)

        elif bake_settings.use_duplicate_objects and not bake_settings.use_join_objects:
            for obj in selected_objects:
                duplicate_object = bpy.data.objects.get(f"{obj.name}_BAKED")
                if not duplicate_object:
                    # copy the object
                    duplicate_object = Object.copy_object(obj=obj, name=f"{obj.name}_BAKED")
                    Object.link_object(obj=duplicate_object, collection=qbaked_collection)
                    for attribute in reversed(duplicate_object.data.color_attributes):
                        duplicate_object.data.color_attributes.remove(attribute)

                # remove and assign the material
                Material.remove_material_slots(obj=duplicate_object)
                if material := bpy.data.materials.get(f"{bake_group.name}_BAKED"):
                    Material.set_material(obj=duplicate_object, material=material)

                # remove the UVMaps
                # if bake_group.use_uvmap_global:
                #     for uv in reversed(duplicate_object.data.uv_layers):
                #         if uv.name != bake_group.object_uv_map:
                #             duplicate_object.data.uv_layers.remove(uv)

        if bake_settings.use_duplicate_objects and bake_settings.use_hide_objects:
            objects_to_hide = (high_poly_objects if "high_poly_objects" in locals() else []) + selected_objects
            for obj in objects_to_hide:
                obj.hide_set(True)
