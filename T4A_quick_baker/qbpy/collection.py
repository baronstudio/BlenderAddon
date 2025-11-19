from typing import List, Union

import bpy


class Collection:
    @staticmethod
    def selected_collections(name_only: bool = False) -> Union[List[bpy.types.Collection], List[str]]:
        """Get selected collections.

        Args:
            name_only (bool, optional): Selected collections' names only. Defaults to False.

        Returns:
            Union[List[bpy.types.Collection], List[str]]: Selected collections.
        """
        for area in bpy.context.screen.areas:
            if area.type == "OUTLINER":
                for region in area.regions:
                    if region.type == "WINDOW":
                        with bpy.context.temp_override(area=area, region=region):
                            selected_ids = bpy.context.selected_ids
                            if collections := [
                                item.name if name_only else item
                                for item in selected_ids
                                if isinstance(item, bpy.types.Collection)
                            ]:
                                return collections
        return []

    @staticmethod
    def get_collection(
        collection: Union[bpy.types.Collection, str],
        override: bool = True,
        color_tag: str = "NONE",
        exclude: bool = False,
        hide_select: bool = False,
        hide_layer: bool = False,
        hide_viewport: bool = False,
        hide_render: bool = False,
    ) -> bpy.types.Collection:
        """Get or create a collection with properties.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection.
            override (bool, optional): Override collection properties. Defaults to True.
            color_tag (enum in ['NONE', 'COLOR_01', 'COLOR_02' ,'COLOR_03' ,'COLOR_04' ,'COLOR_05' , 'COLOR_06', 'COLOR_07', 'COLOR_08'], default 'NONE'): Color tag of the collection. Defaults to "NONE".
            exclude (bool, optional): Exclude from view layer. Defaults to False.
            hide_select (bool, optional): Hide collection in selection. Defaults to False.
            hide_layer (bool, optional): Hide from view layer. Defaults to False.
            hide_viewport (bool, optional): Disable in viewports. Defaults to False.
            hide_render (bool, optional): Disable in renders. Defaults to False.

        Returns:
            bpy.types.Collection: Collection.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)

        if override:
            Collection.set_collection(
                collection, color_tag, exclude, hide_select, hide_layer, hide_viewport, hide_render
            )
        return collection

    @staticmethod
    def get_collections(
        collections: List[Union[bpy.types.Collection, str]],
        override: bool = True,
        color_tag: str = "NONE",
        exclude: bool = False,
        hide_select: bool = False,
        hide_layer: bool = False,
        hide_viewport: bool = False,
        hide_render: bool = False,
    ) -> List[bpy.types.Collection]:
        """Get or create collections with properties.

        Args:
            collections (List[Union[bpy.types.Collection, str]]): List of collections or names of collections.
            override (bool, optional): Override collection properties. Defaults to True.
            color_tag (enum in ['NONE', 'COLOR_01', 'COLOR_02' ,'COLOR_03' ,'COLOR_04' ,'COLOR_05' , 'COLOR_06', 'COLOR_07', 'COLOR_08'], default 'NONE'): Color tag of the collection. Defaults to "NONE".
            exclude (bool, optional): Exclude from view layer. Defaults to False.
            hide_select (bool, optional): Hide collection in selection. Defaults to False.
            hide_layer (bool, optional): Hide from view layer. Defaults to False.
            hide_viewport (bool, optional): Disable in viewports. Defaults to False.
            hide_render (bool, optional): Disable in renders. Defaults to False.

        Returns:
            List[bpy.types.Collection]: List of collections.
        """
        collections_list = []

        for collection in collections:
            col = Collection.get_collection(
                collection, override, color_tag, exclude, hide_select, hide_layer, hide_viewport, hide_render
            )
            collections_list.append(col)

        return collections_list

    @staticmethod
    def get_parent_collection(collection: Union[bpy.types.Collection, str]) -> Union[bpy.types.Collection, None]:
        """Get parent collection.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection.

        Returns:
            Union[bpy.types.Collection, None]: Parent collection or None.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection)
            if not collection:
                return None

        for col in [
            bpy.context.scene.collection,
            *bpy.context.scene.collection.children_recursive,
        ]:
            if col.user_of_id(collection):
                return col

    @staticmethod
    def set_parent_collection(collection: Union[bpy.types.Collection, str], parent: Union[bpy.types.Collection, str]):
        """Set parent collection.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection to parent.
            parent (Union[bpy.types.Collection, str]): Collection to parent to.

        """
        if isinstance(parent, str):
            parent = bpy.data.collections.get(parent)
            if not parent:
                return None

        if parent_collection := Collection.get_parent_collection(collection):
            parent_collection.children.unlink(collection)
            parent.children.link(collection)

    @staticmethod
    def set_collection(
        collection: Union[bpy.types.Collection, str],
        color_tag: str = "NONE",
        exclude: bool = False,
        hide_select: bool = False,
        hide_layer: bool = False,
        hide_viewport: bool = False,
        hide_render: bool = False,
        children: bool = False,
        recursive: bool = False,
    ):
        """Set collection properties.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection.
            color_tag (enum in ['NONE', 'COLOR_01', 'COLOR_02' ,'COLOR_03' ,'COLOR_04' ,'COLOR_05' , 'COLOR_06', 'COLOR_07', 'COLOR_08'], default 'NONE'): Color tag of the collection. Defaults to "NONE".
            exclude (bool, optional): Exclude from view layer. Defaults to False.
            hide_select (bool, optional): Hide collection in selection. Defaults to False.
            hide_layer (bool, optional): Hide from view layer. Defaults to False.
            hide_viewport (bool, optional): Disable in viewports. Defaults to False.
            hide_render (bool, optional): Disable in renders. Defaults to False.
            children (bool, optional): Set children collections. Defaults to False.
            recursive (bool, optional): Set recursive. Defaults to False.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection)
            if not collection:
                return

        layer_collections = Collection.get_layer_collection(collection, children, recursive)
        if not layer_collections:
            return

        if not children and not recursive:
            layer_collections = [layer_collections]

        for layer_collection in layer_collections:
            layer_collection.collection.color_tag = color_tag
            layer_collection.collection.hide_select = hide_select
            layer_collection.collection.hide_viewport = hide_viewport
            layer_collection.collection.hide_render = hide_render
            layer_collection.exclude = exclude
            layer_collection.hide_viewport = hide_layer

    @staticmethod
    def set_collections(
        collections: List[Union[bpy.types.Collection, str]],
        color_tag: str = "NONE",
        exclude: bool = False,
        hide_select: bool = False,
        hide_layer: bool = False,
        hide_viewport: bool = False,
        hide_render: bool = False,
    ):
        """Set collections properties.

        Args:
            collections (List[Union[bpy.types.Collection, str]]): List of collections or names of collections.
            color_tag (enum in ['NONE', 'COLOR_01', 'COLOR_02' ,'COLOR_03' ,'COLOR_04' ,'COLOR_05' , 'COLOR_06', 'COLOR_07', 'COLOR_08'], default 'NONE'): Color tag of the collection. Defaults to "NONE".
            exclude (bool, optional): Exclude from view layer. Defaults to False.
            hide_select (bool, optional): Hide collection in selection. Defaults to False.
            hide_layer (bool, optional): Hide layer in viewport. Defaults to False.
            hide_viewport (bool, optional): Disable in viewports. Defaults to False.
            hide_render (bool, optional): Disable in renders. Defaults to False.
        """
        for collection in collections:
            Collection.set_collection(
                collection, color_tag, exclude, hide_select, hide_layer, hide_viewport, hide_render
            )

    @staticmethod
    def link_collection(
        collection: Union[bpy.types.Collection, str], parent_collection: bpy.types.Collection = None
    ) -> bpy.types.Collection:
        """Link collection to parent.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection to link.
            parent_collection (bpy.types.Collection, optional): Parent collection to link to. Defaults to None.

        Returns:
            bpy.types.Collection: Collection.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection)
            if not collection:
                return None

        if parent_collection is None:
            parent_collection = bpy.context.scene.collection

        if not parent_collection.children.get(collection.name):
            parent_collection.children.link(collection)

        return collection

    @staticmethod
    def remove_collection(
        collection: Union[bpy.types.Collection, str],
        children: bool = False,
        recursive: bool = False,
        empty_only: bool = False,
    ):
        """Remove collection and its children.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection to remove.
            children (bool, optional): Remove children collections of collection. Defaults to False.
            recursive (bool, optional): Remove recursive children collections of collections. Defaults to False.
            empty_only (bool, optional): Remove only empty collection. Defaults to False.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection)
            if not collection:
                return None

        if empty_only:
            if recursive:
                collections = [col for col in collection.children_recursive if not col.all_objects]
            elif children:
                collections = [col for col in collection.children if not col.all_objects]
        else:
            collections = collection.children_recursive if recursive else collection.children

        for col in reversed(collections):
            bpy.data.collections.remove(col)

        bpy.data.collections.remove(collection)

    @staticmethod
    def remove_collections(empty_only: bool = True):
        """Remove collections.

        Args:
            empty_only (bool, optional): Remove only empty collections. Defaults to True.
        """
        collections = [
            col for col in bpy.data.collections if (not empty_only) or (empty_only and not len(col.all_objects))
        ]

        for col in reversed(collections):
            bpy.data.collections.remove(col)

    @staticmethod
    def append_collection(
        filepath: str, collection: str, parent_collection: bpy.types.Collection = None
    ) -> bpy.types.Collection:
        """Append a collection from the filepath.

        Args:
            filepath (str): Filepath of the blend file.
            collection (str): Collection name.
            parent_collection (bpy.types.Collection, optional): Collection to parent the appended collection. Defaults to None.

        Raises:
            ValueError: Collection not found in the source blend file.

        Returns:
            bpy.types.Collection: Appended collection.
        """
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            if collection not in data_from.collections:
                raise ValueError(f"Collection '{collection}' not found in the source blend file.")

            data_to.collections = [collection]

        # Link the appended collections to the specified or current collection
        target_collection = parent_collection or bpy.context.scene.collection

        for col in data_to.collections:
            target_collection.children.link(col)

        return data_to.collections[0]

    @staticmethod
    def append_collections(
        filepath: str, collections: List[str], parent_collection: bpy.types.Collection = None
    ) -> List[bpy.types.Collection]:
        """Append collections from the filepath.

        Args:
            filepath (str): Filepath of the blend file.
            collections (List[str]): List of collection names.
            parent_collection (bpy.types.Collection, optional): Collection to parent the appended collections. Defaults to None.

        Raises:
            ValueError: No matching collections found in the source blend file.

        Returns:
            List[bpy.types.Collection]: Appended collections.
        """
        # Load collections from the file and filter by names
        with bpy.data.libraries.load(filepath) as (data_from, data_to):
            if not data_from.collections:
                raise ValueError("No matching collections found in the source blend file.")

            data_to.collections = [name for name in data_from.collections if name in collections]

        # Link the appended collections to the specified or current collection
        target_collection = parent_collection or bpy.context.scene.collection

        for col in data_to.collections:
            target_collection.children.link(col)

        return data_to.collections

    @staticmethod
    def find_layer_collection(
        layer_collection: bpy.types.LayerCollection, collection: Union[bpy.types.Collection, str]
    ) -> bpy.types.LayerCollection:
        """Find layer collection.

        Args:
            layer_collection (bpy.types.LayerCollection): Layer collection to find child layer collection.
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection.

        Returns:
            bpy.types.LayerCollection: Layer collection.
        """
        collection_name = collection.name if isinstance(collection, bpy.types.Collection) else collection

        if layer_collection.name == collection_name:
            return layer_collection

        for child_layer_collection in layer_collection.children:
            if result := Collection.find_layer_collection(child_layer_collection, collection_name):
                return result

    @staticmethod
    def get_layer_collection(
        collection: Union[bpy.types.Collection, str], children: bool = False, recursive: bool = False
    ) -> Union[bpy.types.LayerCollection, List[bpy.types.LayerCollection], None]:
        """Get layer collection or List of layer collections.

        Args:
            collection (Union[bpy.types.Collection, str]): Collection or name of the collection.
            children (bool, optional): Get layer collection children. Defaults to False.
            recursive (bool, optional): Get layer collection children recursively. Defaults to False.

        Returns:
            Union[bpy.types.LayerCollection, List[bpy.types.LayerCollection], None]: Get layer collection or List of layer collections.
        """
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection)
            if not collection:
                return None

        if children:
            return Collection.get_layer_collections([collection] + list(collection.children))
        elif recursive:
            return Collection.get_layer_collections([collection] + list(collection.children_recursive))
        else:
            return Collection.find_layer_collection(bpy.context.view_layer.layer_collection, collection)

    @staticmethod
    def get_layer_collections(collections: List[Union[bpy.types.Collection, str]]) -> List[bpy.types.LayerCollection]:
        """Get layer collections.

        Args:
            collections (List[Union[bpy.types.Collection, str]]): List of collections or names of collections.

        Returns:
            List[bpy.types.LayerCollection]: List of layer collections.
        """
        layer_collections = []

        for collection in collections:
            if layer_collection := Collection.find_layer_collection(
                bpy.context.view_layer.layer_collection, collection
            ):
                layer_collections.append(layer_collection)

        return layer_collections
