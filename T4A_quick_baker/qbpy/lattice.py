import collections
from typing import List

import bpy
from mathutils import Matrix, Vector

from .blender import preferences
from .modifier import Modifier
from .object import Object


class Lattice:
    @staticmethod
    def bounds(local_coords, orientation=None) -> collections.namedtuple:
        if orientation:
            coords = [(orientation @ Vector(p[:])).to_tuple() for p in local_coords]
        else:
            coords = [p[:] for p in local_coords]

        bounds = {}
        for axis, values in zip("xyz", zip(*coords)):
            bounds[axis] = {"min": min(values), "max": max(values), "distance": max(values) - min(values)}

        return collections.namedtuple("Bounds", bounds.keys())(**bounds)

    @staticmethod
    def create_lattice() -> bpy.types.Object:
        lattice_data = bpy.data.lattices.new(name="Lattice")
        lattice_obj = bpy.data.objects.new(name="Lattice", object_data=lattice_data)
        Object.link_object(lattice_obj)
        return lattice_obj

    @staticmethod
    def set_selection(lattice):
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        lattice.select_set(True)
        bpy.context.view_layer.objects.active = lattice

    @staticmethod
    def get_coords_from_verts(objects: List[bpy.types.Object]) -> tuple:
        worldspace_verts = []
        vert_mapping = {}

        for obj in objects:
            bpy.ops.object.mode_set(mode="OBJECT")
            vert_indices = [v.index for v in obj.data.vertices if v.select]
            worldspace_verts.extend(obj.matrix_world @ v.co for v in obj.data.vertices if v.select)
            vert_mapping[obj.name] = vert_indices

        return worldspace_verts, vert_mapping

    @staticmethod
    def get_coords_from_object(obj: bpy.types.Object) -> list:
        return [obj.matrix_world @ Vector(p[:]) for p in obj.bound_box]

    @staticmethod
    def get_coords_from_objects(objects: List[bpy.types.Object]) -> list:
        return [obj.matrix_world @ Vector(p[:]) for obj in objects for p in obj.bound_box]

    @staticmethod
    def update_lattice(context, lattice: bpy.types.Object, coords, matrix, orientation):
        prefs = preferences()
        rotation = Matrix.Identity(4) if orientation == "GLOBAL" else matrix.to_quaternion().to_matrix().to_4x4()
        bbox = Lattice.bounds(coords, rotation.inverted() if orientation == "LOCAL" else None)

        bound_min = Vector((bbox.x.min, bbox.y.min, bbox.z.min))
        bound_max = Vector((bbox.x.max, bbox.y.max, bbox.z.max))
        offset = (bound_min + bound_max) * 0.5

        location = rotation @ offset
        scale = bound_max - bound_min

        lattice.data.points_u = prefs.lattice.points_u
        lattice.data.points_v = prefs.lattice.points_v
        lattice.data.points_w = prefs.lattice.points_w

        lattice.data.interpolation_type_u = prefs.lattice.interpolation
        lattice.data.interpolation_type_v = prefs.lattice.interpolation
        lattice.data.interpolation_type_w = prefs.lattice.interpolation

        lattice.location = location
        lattice.rotation_euler = rotation.to_euler()
        lattice.scale = scale * prefs.lattice.scale

    @staticmethod
    def add_lattice_modifiers(objects: List[bpy.types.Object], lattice: bpy.types.Object, group_mapping):
        for obj in objects:
            modifier = Modifier.lattice(obj, object=lattice)
            if group_mapping:
                modifier.name = modifier.vertex_group = group_mapping[obj.name]
            obj.update_tag()

    @staticmethod
    def cleanup(objects: List[bpy.types.Object]):
        for obj in objects:
            obsolete_modifiers = [mod for mod in obj.modifiers if mod.type == "LATTICE" and not mod.vertex_group]
            used_vertex_groups = {
                mod.vertex_group for mod in obj.modifiers if mod.type == "LATTICE" and mod.vertex_group
            }
            obsolete_groups = [
                vgrup for vgrup in obj.vertex_groups if "Lattice" in vgrup.name and vgrup.name not in used_vertex_groups
            ]

            for modifier in obsolete_modifiers:
                obj.modifiers.remove(modifier)

            for group in obsolete_groups:
                obj.vertex_groups.remove(group)

    @staticmethod
    def set_vertex_groups(objects: List[bpy.types.Object], vert_mapping):
        group_mapping = {}
        for obj in objects:
            if obj.mode == "EDIT":
                bpy.ops.object.mode_set(mode="OBJECT")

            group = obj.vertex_groups.new(name="Lattice")
            group.add(vert_mapping[obj.name], 1.0, "REPLACE")
            group_mapping[obj.name] = group.name
        return group_mapping

    @staticmethod
    def for_edit_mode():
        try:
            bpy.ops.transform.create_orientation(name="Lattice_Orientation", use=False, overwrite=True)
        except:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.transform.create_orientation(name="Lattice_Orientation", use=False, overwrite=True)

        active_object = bpy.context.view_layer.objects.active
        if active_object.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.empty_add()
            bpy.ops.object.delete()

            for obj in bpy.context.selected_objects:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = active_object

            bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.ed.undo_push()

    @staticmethod
    def kill_lattice_modifer(modifier: bpy.types.Modifier, target: bpy.types.Object) -> str:
        if modifier.type == "LATTICE" and modifier.object == target:
            if bpy.context.active_object != modifier.id_data:
                Object.set_active(modifier.id_data)

            vertex_group = modifier.vertex_group or ""

            if modifier.show_viewport and modifier.id_data.mode != "OBJECT":
                bpy.ops.object.editmode_toggle()

            bpy.ops.object.modifier_remove(modifier=modifier.name)
            return vertex_group

        return ""

    @staticmethod
    def kill_vertex_groups(obj: bpy.types.Object, vertex_groups: List[str]):
        if not vertex_groups:
            return

        used_vertex_groups = {mod.vertex_group for mod in obj.modifiers if mod.type == "LATTICE" and mod.vertex_group}
        obsolete_groups = [group for group in vertex_groups if group not in used_vertex_groups]

        for group in obsolete_groups:
            if vg := obj.vertex_groups.get(group):
                obj.vertex_groups.remove(vg)
                obj.vertex_groups.remove(vg)
