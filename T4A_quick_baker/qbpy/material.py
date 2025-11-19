from typing import List, Union

import bpy


class Material:
    @staticmethod
    def get_material(name: str, use_nodes: bool = True) -> bpy.types.Material:
        """Get material by name.

        Args:
            name (str): Name of the material.
            use_nodes (bool, optional): Use shader nodes to render the material. Defaults to True.

        Returns:
            bpy.types.Material: Material.
        """
        material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        material.use_nodes = use_nodes
        return material

    @staticmethod
    def get_materials(obj: bpy.types.Object, name_only: bool = False) -> List[Union[bpy.types.Material, str]]:
        """Get materials from object.

        Args:
            obj (bpy.types.Object): Object to get materials from.
            name_only (bool, optional): Get only names. Defaults to False.

        Returns:
            List[Union[bpy.types.Material, str]]: List of materials or names.
        """
        if obj.type != "MESH":
            return []
        return [material.name if name_only else material for material in obj.data.materials if material]

    @staticmethod
    def set_material(obj: bpy.types.Object, material: Union[bpy.types.Material, str], index: int = -1):
        """Set material to object.

        Args:
            obj (bpy.types.Object): Object to set material to.
            material (Union[bpy.types.Material, str]): Material to set.
            index (int): Index of material slot. Defaults to -1.
        """
        if obj.type != "MESH":
            return

        if isinstance(material, str):
            material = Material.get_material(name=material)

        if 0 <= index < len(obj.data.materials):
            obj.data.materials[index] = material
        elif material not in obj.data.materials[:]:
            obj.data.materials.append(material)

    @staticmethod
    def remove_material(obj: bpy.types.Object, material: Union[bpy.types.Material, str]):
        """Remove the material.

        Args:
            obj (bpy.types.Object): Object to remove material from.
            material (Union[bpy.types.Material, str]): Material to remove.
        """
        if obj.type == "MESH" and obj.material_slots:
            for slot in obj.material_slots:
                if slot.material and slot.material == material:
                    slot.material = None

    @staticmethod
    def remove_materials(obj: bpy.types.Object):
        """Remove all the materials from material slots.

        Args:
            obj (bpy.types.Object): Object to remove materials from.
        """
        if obj.type == "MESH" and obj.material_slots:
            for slot in obj.material_slots:
                if slot.material:
                    slot.material = None

    @staticmethod
    def remove_material_slots(obj: bpy.types.Object):
        """Remove all the material slots.

        Args:
            obj (bpy.types.Object): Object to remove material slots from.
        """
        if obj.type == "MESH" and obj.material_slots:
            obj.data.materials.clear()
