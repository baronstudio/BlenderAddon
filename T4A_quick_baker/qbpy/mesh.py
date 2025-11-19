from typing import List

import bmesh
import bpy


class Mesh:
    @staticmethod
    def add_vertex_group(obj: bpy.types.Object, name: str) -> bpy.types.VertexGroup:
        """Add vertex group to object.

        Args:
            obj (bpy.types.Object): Object to add the vertex group to.
            name (str): Name of the vertex group.

        Returns:
            bpy.types.VertexGroup: Vertex group.
        """
        return obj.vertex_groups.new(name=name)

    @staticmethod
    def create_vertex_group(obj: bpy.types.Object, modifier: bpy.types.Modifier):
        """Create a vertex group for the cloth simulation.

        Args:
            obj (bpy.types.Object): Object to create the vertex group for.
            modifier (bpy.types.Modifier): Modifier to set the vertex group to.
        """
        cloth_vgroup = obj.vertex_groups.get("Cloth")
        if not cloth_vgroup:
            cloth_vgroup = obj.vertex_groups.new(name="Cloth")

        bm = bmesh.new()
        bm.from_mesh(obj.data)

        verts = [v.index for v in bm.verts if v.is_boundary]
        cloth_vgroup.add(index=verts, weight=1.0, type="REPLACE")
        verts1 = [e.verts[0].index for e in bm.edges if e.seam]
        verts2 = [e.verts[0].index for e in bm.edges if e.seam]
        verts = verts1 + verts2
        cloth_vgroup.add(index=verts, weight=1.0, type="REPLACE")

        modifier.settings.vertex_group_mass = cloth_vgroup.name
        bm.free()

    @staticmethod
    def update_vertex_group(context, name: str) -> bpy.types.VertexGroup:
        """Update the vertex group with the selected vertices.

        Args:
            name (str): Name of the vertex group.

        Returns:
            bpy.types.VertexGroup: Vertex group with the selected vertices.
        """
        if context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        vertex_group = context.object.vertex_groups.get(name)
        if not vertex_group:
            vertex_group = context.object.vertex_groups.new(name=name)
        verts = [v.index for v in context.object.data.vertices if v.select]
        vertex_group.add(verts, 1.0, "REPLACE")
        bpy.ops.object.mode_set(mode="EDIT")

        return vertex_group

    @staticmethod
    def symmetrize(context, direction: str):
        """Symmetrize the object.

        Args:
            direction (enum in ['POSITIVE_X', 'POSITIVE_Y', 'POSITIVE_Z', 'NEGATIVE_X', 'NEGATIVE_Y', 'NEGATIVE_Z']): The direction to symmetrize the object in.
        """
        if context.mode == "OBJECT":
            for obj in context.selected_objects:
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.symmetrize(direction=direction)
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.object.mode_set(mode="OBJECT")
            context.view_layer.objects.active = context.object
        elif context.mode == "EDIT_MESH":
            bpy.ops.mesh.symmetrize(direction=direction)
        elif context.mode == "SCULPT":
            context.scene.tool_settings.sculpt.symmetrize_direction = direction
            bpy.ops.sculpt.symmetrize()

    @staticmethod
    def dupticate(obj: bpy.types.Object, name: str = "Object") -> bpy.types.Object:
        """Duplicate the object.

        Args:
            obj (bpy.types.Object): Object to duplicate.
            name (str, optional): Name of the duplicate object. Defaults to "Object".

        Returns:
            bpy.types.Object: Duplicate object.
        """
        if obj.mode == "EDIT":
            bm = bmesh.from_edit_mesh(obj.data).copy()
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.select])
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()

        return bpy.data.objects.new(name, mesh)

    @staticmethod
    def edge_decal(
        obj: bpy.types.Object, name: str, amount: float, offset: float, clamp_overlap: bool
    ) -> bpy.types.Object:
        """Edge decal from the selected edges.

        Args:
            obj (bpy.types.Object): Object to create the edge decal from.
            name (str): Name of the decal.
            amount (float): Amount of the decal offset.
            offset (float): Offset of the decal.
            clamp_overlap (bool): Clamp the width to avoid overlap.

        Returns:
            bpy.types.Object: Edge decal object.
        """
        bm = bmesh.from_edit_mesh(obj.data).copy()
        decal = bmesh.ops.bevel(
            bm,
            geom=[e for e in bm.edges if e.select],
            offset=amount,
            profile=1.0,
            segments=2,
            affect="EDGES",
            clamp_overlap=clamp_overlap,
        )
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in decal["faces"]], context="FACES")
        bmesh.ops.scale(bm, vec=(offset, offset, offset), verts=bm.verts)
        return Mesh.bmesh_to_object(bm, name)

    @staticmethod
    def bmesh_to_object(bm: bmesh.types.BMesh, name: str) -> bpy.types.Object:
        """Object from bmesh.

        Args:
            bm (bmesh.types.BMesh): bmesh to create the object from.
            name (str): Name of the object.

        Returns:
            bpy.types.Object: The new object.
        """
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()
        return bpy.data.objects.new(name, mesh)

    @staticmethod
    def _get_objects(*args, **kwargs) -> List[bpy.types.Object]:
        """Helper function to get objects based on various input types.

        Returns:
            List[bpy.types.Object]: List of objects.
        """
        objs = kwargs.get("objs", [])

        if not objs:
            if "obj" in kwargs:
                objs = [kwargs["obj"]]
            elif "name" in kwargs:
                objs = [bpy.data.objects.get(kwargs["name"])]
            elif "names" in kwargs:
                objs = [bpy.data.objects.get(name) for name in kwargs["names"]]
            elif "objects" in kwargs:
                objs = [
                    obj for obj in kwargs.get("objects", bpy.data.objects) if obj.type in kwargs.get("type", {"MESH"})
                ]
            elif args:
                if isinstance(args[0], str):
                    objs = [bpy.data.objects.get(name) for name in args]
                elif isinstance(args[0], list) and all(isinstance(item, str) for item in args[0]):
                    objs = [bpy.data.objects.get(name) for name in args[0]]
                elif isinstance(args[0], list) and all(isinstance(item, bpy.types.Object) for item in args[0]):
                    objs = args[0]
                else:
                    objs = list(args)
            else:
                objs = [bpy.context.object]

        # Convert names to objects if necessary
        return [bpy.data.objects.get(obj) if isinstance(obj, str) else obj for obj in objs]

    @staticmethod
    def shade_flat(*args, **kwargs):
        """Set the shading to flat."""
        objs = Mesh._get_objects(*args, **kwargs)

        for obj in objs:
            if obj.type != "MESH" or obj.data is None:
                continue
            obj.data.shade_flat()

    @staticmethod
    def shade_smooth(*args, **kwargs):
        """Set the shading to smooth."""
        objs = Mesh._get_objects(*args, **kwargs)

        for obj in objs:
            if obj.type != "MESH" or obj.data is None:
                continue
            obj.data.shade_smooth()
