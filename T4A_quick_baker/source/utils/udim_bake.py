import sys

import bpy
import numpy as np

from ...qbpy import Image

# DEVIATION = 0.0010000000000000009
# DEVIATION = 0.0001000000000000009
DEVIATION = sys.float_info.min


class Udim:
    def get_data_from_collection(self, collection, attribute, size, dtype=np.float32):
        data = np.zeros(np.prod(size), dtype=dtype)
        collection.foreach_get(attribute, data)
        return data.reshape(size)

    def create_unique_uv_coords(self, object):
        """UV vertex to unique uv vertex, and convert float to int"""
        uv_coords_for_udim = set()

        if active_uv := object.data.uv_layers.active:
            # Get UV coordinates
            uv = np.array(self.get_data_from_collection(active_uv.data, "uv", (len(active_uv.data), 2)))

            # Convert float to int
            mask = np.array(
                [
                    (abs(p[0] - round(p[0], 0)) % 1 > DEVIATION and abs(p[1] - round(p[1], 0)) % 1 > DEVIATION)
                    for p in uv
                ]
            )  # only ceil numbers which aren't integers to ignore uv on the edge of an image
            uv_coords_ceil = np.ceil(uv[mask]).astype(int)

            # Unique coordinates
            unique_udim_coords = np.unique(uv_coords_ceil, axis=0)

            # Numpy arrays to tuple
            to_list = unique_udim_coords.tolist()
            tpl = tuple((i[0], i[1] - 1) for i in to_list)

            # Unique coordinates
            uv_coords_for_udim.update(tpl)
        return uv_coords_for_udim

    def uv_coords_to_udims(self, uv_coords_for_udim):
        """Convert UV vertex position to UDIM`s"""
        croped_uv_coords_for_udim = [i for i in uv_coords_for_udim if 1 <= i[0] <= 10 and 0 <= i[1] <= 99]
        udims = [i[0] + (i[1] * 10) + 1000 for i in croped_uv_coords_for_udim]
        udims.sort()
        return udims

    def split_udims_by_group(self, lst):
        result = []
        sublist = [lst[0]]
        for i in range(1, len(lst)):
            if lst[i] - lst[i - 1] == 1:
                sublist.append(lst[i])
            else:
                result.append(sublist)
                sublist = [lst[i]]
        result.append(sublist)
        return result

    def udim_image(
        self,
        context,
        udims: list,
        name: str = "Untitled",
        width: int = 1024,
        height: int = 1024,
        non_color: bool = False,
        alpha: bool = False,
        save: bool = True,
        path: str = bpy.app.tempdir,
    ):
        if image := bpy.data.images.get(name):
            return image

        image = Image.new_image(
            name=name, width=width, height=height, non_color=non_color, alpha=alpha, tiled=True, check=False
        )

        override = bpy.context.copy()
        override["edit_image"] = image
        image.tiles.active_index = 0
        image.colorspace_settings.name = "Non-Color" if non_color else "sRGB"

        if image.tiles.active.size[0] == 0:
            with context.temp_override(**override):
                bpy.ops.image.tile_fill(width=width, height=height, alpha=alpha, float=True)

        udims_copy = udims[:]
        remove_tile = None

        if image.tiles.active.number in udims_copy:
            udims_copy.remove(image.tiles.active.number)
        else:
            remove_tile = image.tiles.active

        groups = self.split_udims_by_group(udims_copy)

        for group in groups:
            first_elem_in_group = group[0]
            tile = image.tiles.get(tile_number=first_elem_in_group)
            if not tile:
                group_size = len(group)
                with context.temp_override(**override):
                    bpy.ops.image.tile_add(
                        number=first_elem_in_group,
                        count=group_size,
                        width=width,
                        height=height,
                        alpha=alpha,
                        float=True,
                    )

        if remove_tile is not None:
            image.tiles.active = remove_tile
            with context.temp_override(**override):
                bpy.ops.image.tile_remove()

        Image.save_image(image, path=path, name=f"{name}.<UDIM>")
        image.pack()
        return image
