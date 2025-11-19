import math
from collections import defaultdict
from contextlib import suppress
from typing import Union

import bpy


class Property:
    @staticmethod
    def get_property_value(data: bpy.types.AnyType, property: str, index: int = None):
        """Get the value of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.
            index (int, optional): Index of the property. Defaults to None.

        Returns:
            bpy.types.AnyType: Value of the property.
        """
        return getattr(data, property) if index is None else getattr(data, property)[index]

    @staticmethod
    def set_property_value(
        data: bpy.types.AnyType,
        property: str,
        value: bpy.types.AnyType,
        index: int = None,
    ):
        """Set the value of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.
            value (bpy.types.AnyType): The value to set the property.
            index (int, optional): Index of the property. Defaults to None.
        """
        if index is None:
            setattr(data, property, value)
        else:
            Property.get_property_value(data, property)[index] = value

    @staticmethod
    def toggle_property_value(data: bpy.types.AnyType, property: str, index: int = None):
        """Toggle the value of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.
            index (int, optional): The index of the property. Defaults to None.
        """
        value = not Property.get_property_value(data, property, index)
        Property.set_property_value(data, property, value, index)
        label = Property.label_from_rna(data, property)
        print(f"INFO: {label} {value}")

    @staticmethod
    def get_enums(data: bpy.types.AnyType, property: str) -> (list, bool):
        """Get the enums of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            tuple: A tuple containing a list of enums and a boolean indicating if it is an enum flag.
        """
        enums = [], False
        if hasattr(data, property):
            pdef = data.rna_type.properties[property]
            if pdef.type == "ENUM":
                enums = pdef.enum_items.keys(), pdef.is_enum_flag
        return enums

    @staticmethod
    def get_next_enum(data: bpy.types.AnyType, property: str) -> str:
        """Get the next enum of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            str: The next enum of the property.
        """
        enum, is_enum_flag = Property.get_enums(data, property)
        curr = getattr(data, property)
        index = enum.index(curr)
        return enum[(index + 1) % len(enum)]

    @staticmethod
    def label_from_rna(data: bpy.types.AnyType, property: str) -> str:
        """Get the label of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            str: The label of the property.
        """
        return data.rna_type.properties[property].name if hasattr(data, property) else ""

    @staticmethod
    def type_from_rna(data: bpy.types.AnyType, property: str) -> tuple:
        """Get the type and subtype of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            tuple: The type and subtype of the property.
        """
        types = "NONE", "NONE"
        if hasattr(data, property):
            pdef = data.rna_type.properties[property]
            types = pdef.type, pdef.subtype
        return types

    @staticmethod
    def limit_from_rna(data: bpy.types.AnyType, property: str):
        """Get the limits of a property.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            tuple: The limits of the property (min, max, type).
        """
        typ = "NONE"
        res = -1e64, 1e64, typ
        if hasattr(data, property):
            pdef = data.rna_type.properties[property]
            typ = pdef.type
            if typ in {"INT", "FLOAT"}:
                res = pdef.hard_min, pdef.hard_max, typ
        return res

    @staticmethod
    def limit_value(data: bpy.types.AnyType, property: str, value: bpy.types.AnyType):
        """Limit value using rna_type definition

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.
            value (bpy.types.AnyType): The value to limit.

        Returns:
            bpy.types.AnyType: The limited value.
        """
        if value != 0:
            mini, maxi, type = Property.limit_from_rna(data, property)
            res = max(mini, min(maxi, value))
            if type == "INT":
                res = int(res)
            return res
        return value

    @staticmethod
    def input_as_value(data: bpy.types.AnyType, property: str, input_value: float):
        """Convert string input into float or int using rna_type definition.

        Args:
            data (bpy.types.AnyType): Data from which to take property.
            property (str): Identifier of property in data.

        Returns:
            bpy.types.AnyType: The converted value.
        """
        value = 0
        type, subtype = Property.type_from_rna(data, property)

        if type == "FLOAT":
            value = float(input_value)
            if subtype == "ANGLE":
                value = math.radians(value)
        elif type == "INT":
            value = int(input_value)
        return Property.limit_value(data, property, value)

    @staticmethod
    def get_pointer_property_as_dict(property: bpy.types.PointerProperty, exclude: list, depth: int) -> dict:
        """Converts a Blender PointerProperty to a python dict.

        Note:
            Used internally for property_to_python, please use property_to_python to convert any Blender Property.

        Args:
            property (bpy.types.PointerProperty): Blender Property to convert.
            exclude (list): Property values to exclude. To exclude deeper values, use the form <value>.<sub-value>.
            The <value>.<sub-value> can only be used if the value is of type CollectionProperty or PointerProperty.
            depth (int): Depth to extract the value, needed because some Properties have recursive definitions.

        Returns:
            dict: Python dict based on property.
        """
        data = {}  # PointerProperty
        main_exclude = []
        sub_exclude = defaultdict(list)
        for x in exclude:
            prop = x.split(".")
            if len(prop) > 1:
                sub_exclude[prop[0]].append(".".join(prop[1:]))
            else:
                main_exclude.append(prop[0])
        main_exclude = set(main_exclude)
        for attr in property.bl_rna.properties[1:]:  # exclude rna_type
            identifier = attr.identifier
            if identifier not in main_exclude:
                data[identifier] = Property.property_to_python(
                    getattr(property, identifier),
                    sub_exclude.get(identifier, []),
                    depth - 1,
                )
        return data

    @staticmethod
    def property_to_python(property: bpy.types.Property, exclude: list = [], depth: int = 5) -> Union[list, dict, str]:
        """Converts any Blender Property to a python object, only needed for Property with complex structure.

        Args:
            property (bpy.types.Property): Blender Property to convert.
            exclude (list, optional): Property values to exclude. To exclude deeper values, use the form <value>.<sub-value>.
            The <value>.<sub-value> can only be used if the value is of type CollectionProperty or PointerProperty.
            Defaults to [].
            depth (int, optional): Depth to extract the value, needed because some Properties have recursive definitions.
            Defaults to 5.

        Returns:
            Union[list, dict, str]: Converts Collection, Arrays to lists and PointerProperty to dict.
        """
        # CollectionProperty are a list of PointerProperties
        if depth <= 0:
            return "max depth"

        if hasattr(property, "id_data"):
            id_object = property.id_data

            # exclude conversions of same property
            if property == id_object:
                return property

            class_name = property.__class__.__name__
            if class_name == "bpy_prop_collection" and hasattr(property, "bl_rna"):
                data = Property.get_pointer_property_as_dict(property, exclude, depth)
                data["items"] = [Property.property_to_python(item, exclude, depth) for item in property]
                return data
            elif class_name in [
                "bpy_prop_collection",
                "bpy_prop_collection_idprop",
                "bpy_prop_array",
            ]:
                return [Property.property_to_python(item, exclude, depth) for item in property]
            else:
                # PointerProperty
                return Property.get_pointer_property_as_dict(property, exclude, depth)

        if isinstance(property, set):
            property = list(property)

        return property

    @staticmethod
    def apply_data_to_item(property: bpy.types.Property, data, key=""):
        """Apply given python data to a property.

        Used to convert python data (from property_to_python) to Blender Property.
        - list to CollectionsProperty or ArrayProperty (add new elements to the collection)
        - dict to PointerProperty
        - single data (like int, string, etc.) with a given key

        Args:
            property (bpy.types.Property): Blender Property to apply the data to.
            data (any): Data to apply.
            key (str, optional): Used to apply a single value of a given Blender Property dynamic. Defaults to "".
        """
        if isinstance(data, list):
            item = property
            if key:
                item = getattr(property, key)
                if isinstance(item, set):  # EnumProperty with EnumFlag
                    setattr(property, key, set(data))
                    return
                elif isinstance(item, bpy.types.bpy_prop_array):  # ArrayProperty
                    setattr(property, key, data)
                    return
            if isinstance(item, (set, bpy.types.bpy_prop_array)):  # EnumProperty with EnumFlag but no key
                return
            for element in data:
                Property.apply_data_to_item(item.add(), element)
        elif isinstance(data, dict):
            if key:
                property = getattr(property, key)
            for key, value in data.items():
                Property.apply_data_to_item(property, value, key)
        elif hasattr(property, key):
            with suppress(AttributeError):  # catch Exception from read-only property
                setattr(property, key, data)
