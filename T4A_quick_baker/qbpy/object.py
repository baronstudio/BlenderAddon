import itertools
from typing import List

import bpy
from mathutils import Matrix, Vector

from .material import Material
from .mesh import Mesh


class Object(Mesh, Material):
    @staticmethod
    def set_active(obj: bpy.types.Object):
        bpy.context.view_layer.objects.active = obj

    @staticmethod
    def apply_scale():
        """Apply the scale of the object."""
        bpy.ops.object.transform_apply(scale=True)

    @staticmethod
    def show_wire(obj: bpy.types.Object = None, show_wire: bool = True):
        """Show or hide the wireframe of the object.

        Args:
            obj (bpy.types.Object, optional): Object to show/hide wireframe. Defaults to context object.
            show_wire (bool, optional): Whether to show the wireframe. Defaults to True.
        """
        obj = obj or bpy.context.object
        obj.show_wire = show_wire

    @staticmethod
    def rename_object(obj: bpy.types.Object, name: str):
        """Rename the object and its data.

        Args:
            obj (bpy.types.Object): Object to rename.
            name (str): Name of the object.
        """
        if not obj.library:
            obj.name = name
            if obj.type in {"MESH", "ARMATURE"}:
                obj.data.name = name

    @staticmethod
    def copy_object(
        obj: bpy.types.Object, name: str, clear_transform: bool = False, check: bool = True
    ) -> bpy.types.Object:
        """Copy the object with data.

        Args:
            obj (bpy.types.Object): Object to copy.
            name (str): Name of the copied object.
            check (bool, optional): Check if the object exists. Defaults to True.
            clear_transform (bool, optional): Clear the copied object's transform to identity. Defaults to False.

        Returns:
            bpy.types.Object: The copied object.
        """
        copied_object = bpy.data.objects.get(name) if check else None
        if not copied_object:
            copied_object = obj.copy()
            copied_object.data = obj.data.copy()
            Object.rename_object(obj=copied_object, name=name)

            if clear_transform:
                copied_object.location = (0, 0, 0)
                copied_object.rotation_euler = (0, 0, 0)
                copied_object.scale = (1, 1, 1)
        return copied_object

    @staticmethod
    def parent_object(
        parent: bpy.types.Object, child: bpy.types.Object, copy_transform: bool = True, target: bpy.types.Object = None
    ):
        """Parent object to another object.

        Args:
            parent (bpy.types.Object): Parent object.
            child (bpy.types.Object): Child object.
            copy_transform (bool, optional): Copy the parent object transform. Defaults to True.
            target (bpy.types.Object, optional): Target object to transfrom from. Defaults to None.
        """
        child.parent = parent
        if copy_transform and parent:
            child.matrix_parent_inverse = target.matrix_world.inverted() if target else parent.matrix_world.inverted()

    @staticmethod
    def object_origin(obj: bpy.types.Object, origin):
        """
        Change object origin location.

        obj (bpy.types.Object) - The object to change origin of.
        origin (3D Vector) - The location to change the origin to.
        """
        local_origin = obj.matrix_world.inverted() @ origin
        obj.data.transform(Matrix.Translation(-local_origin))
        obj.matrix_world.translation += origin - obj.matrix_world.translation

    @staticmethod
    def remove_object(obj: bpy.types.Object):
        """
        Remove object.

        obj (bpy.types.Object) - The object to remove.
        """
        if obj.type in {"MESH"}:
            bpy.data.meshes.remove(obj.data)
        else:
            bpy.data.objects.remove(obj)

    @staticmethod
    def get_object(*args, **kwargs) -> bpy.types.Object:
        """Get an object.

        Args:
            *args: Object or name of the object.
            **kwargs: Object or name of the object.

        Returns:
            bpy.types.Object: The object.
        """
        obj = kwargs.get("obj", None)

        if not obj:
            if "name" in kwargs:
                obj = bpy.data.objects.get(kwargs["name"])
            elif args:
                if isinstance(args[0], str):
                    obj = bpy.data.objects.get(args[0])
                elif isinstance(args[0], bpy.types.Object):
                    obj = args[0]
            else:
                obj = bpy.context.object

        # Convert name to object if necessary
        if isinstance(obj, str):
            obj = bpy.data.objects.get(obj)

        return obj

    @staticmethod
    def get_objects(*args, **kwargs) -> List[bpy.types.Object]:
        """Get the objects.

        Args:
            *args: List of objects or names of objects.
            **kwargs: List of objects or names of objects.

        Returns:
            List[bpy.types.Object]: List of objects.
        """
        objs = kwargs.get("objs", [])

        if not objs:
            if args:
                if isinstance(args[0], str):  # for get_objects("Cube", "Suzanne")
                    objs = [bpy.data.objects.get(name) for name in args]
                elif isinstance(args[0], list) and all(
                    isinstance(item, str) for item in args[0]
                ):  # get_objects(["Cube", "Suzanne"])
                    objs = [bpy.data.objects.get(name) for name in args[0]]
                elif isinstance(args[0], list) and all(
                    isinstance(item, bpy.types.Object) for item in args[0]
                ):  # for get_objects([bpy.data.objects["Cube"], bpy.data.objects["Suzanne"]])
                    objs = args[0]
                else:  # for get_objects(bpy.data.objects["Cube"], bpy.data.objects["Suzanne"])
                    objs = list(args)
            elif "names" in kwargs:  # for get_objects(names=["Cube", "Suzanne"])
                objs = [bpy.data.objects.get(name) for name in kwargs["names"]]
            else:  # for get_objects(objects=bpy.data.objects, type={"MESH"})
                objs = [
                    obj for obj in kwargs.get("objects", bpy.data.objects) if obj.type in kwargs.get("type", {"MESH"})
                ]

        # Convert names to objects if necessary
        return [bpy.data.objects.get(obj) if isinstance(obj, str) else obj for obj in objs]

    @staticmethod
    def link_object(obj: bpy.types.Object, collection: bpy.types.Collection = None, unlink: bool = True):
        """Link object to collection. If collection is None, link to scene collection.

        Args:
            obj (bpy.types.Object): Object to link.
            collection (bpy.types.Collection, optional): Collection to link to. Defaults to None.
            unlink (bool, optional): Unlink object from all the collections first. Defaults to True.
        """
        if unlink:
            Object.unlink_object(obj)

        if collection:
            if not collection.objects.get(obj.name):
                collection.objects.link(obj)

        elif not bpy.context.scene.collection.objects.get(obj.name):
            bpy.context.scene.collection.objects.link(obj)

    @staticmethod
    def unlink_object(obj: bpy.types.Object):
        """Unlink object from all the collections.

        Args:
            obj (bpy.types.Object): Object to unlink.
        """
        for col in obj.users_collection:
            col.objects.unlink(obj)

    @staticmethod
    def bound_to_diagonal(bound: list) -> Vector:
        """Diagonal of the bounding box.

        Args:
            bound (list): List of vectors representing the bounding box.

        Returns:
            Vector: Diagonal of the bounding box.
        """
        minimum = []
        maximum = []

        for i in range(len(bound[0])):
            var = [vec[i] for vec in bound]
            minimum.append(min(var))
            maximum.append(max(var))

        return Vector(minimum), Vector(maximum)

    @staticmethod
    def bound_to_point(obj: bpy.types.Object, axis: str = "POS_X") -> Vector:
        """Minimum and maximum points of the bounding box.

        Args:
            obj (bpy.types.Object): Object to get the bounding box.
            axis (enum in ['POS_X', 'POS_Y', 'POS_Z', 'NEG_X', 'NEG_Y', 'NEG_Z'], optional): Axis to get the bounding box. Defaults to "POS_X".

        Returns:
            Vector: Minimum and maximun points of the bounding box.
        """
        location, rotation, scale = obj.matrix_world.decompose()
        matrix_scale = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
        scale = Matrix.Diagonal((*scale, 1))
        bounds = [scale @ Vector(v) for v in obj.bound_box]
        min_corner, max_corner = Object.bound_to_diagonal(bounds)
        center = (min_corner + max_corner) / 2

        min = min_corner - center
        max = max_corner - center

        index = "XYZ".index(axis[-1])
        points = [min, max] if axis.startswith("POS") else [max, min]

        for vec, i in itertools.product(points, range(3)):
            if i != index:
                vec[i] = 0.0

        return points

    @staticmethod
    def dimension_axis(obj: bpy.types.Object, maximum: bool = True) -> str:
        """Axis from maximum or minimum dimension of an object.

        Args:
            obj (bpy.types.Object): Object to get the dimension.
            maximum (bool, optional): Whether to find the maximum dimension. If False, find the minimum dimension. Defaults to True.

        Returns:
            str: Dimension axis.
        """
        if maximum:
            if obj.dimensions.x >= obj.dimensions.y and obj.dimensions.x >= obj.dimensions.z:
                return "POS_X"
            elif obj.dimensions.y >= obj.dimensions.x and obj.dimensions.y >= obj.dimensions.z:
                return "POS_Y"
            else:
                return "POS_Z"
        else:
            if obj.dimensions.x <= obj.dimensions.y and obj.dimensions.x <= obj.dimensions.z:
                return "POS_X"
            elif obj.dimensions.y <= obj.dimensions.x and obj.dimensions.y <= obj.dimensions.z:
                return "POS_Y"
            else:
                return "POS_Z"

    @staticmethod
    def location(*args, **kwargs) -> Vector:
        """Get or Set the location of an object.

        Args:
            *args: Object and location.
            **kwargs: Object and location.

        Raises:
            ValueError: No arguments provided and no context object available.
            ValueError: Object must be provided.

        Returns:
            Vector: Location of the object.
        """
        if len(args) == 0 and len(kwargs) == 0:
            if bpy.context.object:
                return bpy.context.object.location
            else:
                raise ValueError("No arguments provided and no context object available.")

        obj = None
        if len(args) > 0:
            obj = args[0]
        elif "obj" in kwargs:
            obj = kwargs["obj"]

        if obj is None:
            raise ValueError("Object must be provided.")

        if len(args) == 2 and isinstance(args[1], (Vector, tuple, list, set)):
            obj.location = args[1]
        else:
            if "x" in kwargs:
                obj.location.x = kwargs["x"]
            if "y" in kwargs:
                obj.location.y = kwargs["y"]
            if "z" in kwargs:
                obj.location.z = kwargs["z"]

        return obj.location

    @staticmethod
    def rotation(*args, **kwargs) -> Vector:
        """Get or Set the rotation of an object.

        Args:
            *args: Object and rotation.
            **kwargs: Object and rotation.

        Raises:
            ValueError: No arguments provided and no context object available.
            ValueError: Object must be provided.

        Returns:
            Vector: Rotation of the object.
        """
        if len(args) == 0 and len(kwargs) == 0:
            if bpy.context.object:
                return bpy.context.object.rotation_euler
            else:
                raise ValueError("No arguments provided and no context object available.")

        obj = None
        if len(args) > 0:
            obj = args[0]
        elif "obj" in kwargs:
            obj = kwargs["obj"]

        if obj is None:
            raise ValueError("Object must be provided.")

        if len(args) == 2 and isinstance(args[1], (Vector, tuple, list, set)):
            obj.rotation_euler = args[1]
        else:
            if "x" in kwargs:
                obj.rotation_euler.x = kwargs["x"]
            if "y" in kwargs:
                obj.rotation_euler.y = kwargs["y"]
            if "z" in kwargs:
                obj.rotation_euler.z = kwargs["z"]

        return obj.rotation_euler

    @staticmethod
    def scale(*args, **kwargs) -> Vector:
        """Get or Set the scale of an object.

        Args:
            *args: Object and scale.
            **kwargs: Object and scale.

        Raises:
            ValueError: No arguments provided and no context object available.
            ValueError: Object must be provided.

        Returns:
            Vector: Scale of the object.
        """
        if len(args) == 0 and len(kwargs) == 0:
            if bpy.context.object:
                return bpy.context.object.scale
            else:
                raise ValueError("No arguments provided and no context object available.")

        obj = None
        if len(args) > 0:
            obj = args[0]
        elif "obj" in kwargs:
            obj = kwargs["obj"]

        if obj is None:
            raise ValueError("Object must be provided.")

        if len(args) == 2 and isinstance(args[1], (Vector, tuple, list, set)):
            obj.scale = args[1]
        else:
            if "x" in kwargs:
                obj.scale.x = kwargs["x"]
            if "y" in kwargs:
                obj.scale.y = kwargs["y"]
            if "z" in kwargs:
                obj.scale.z = kwargs["z"]

        return obj.scale
