# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os

import bpy


class ExportUVLayout:
    def wireframe(self, context, bake_group, map):
        if bake_group.use_high_to_low:
            objects = [item.object for group in bake_group.groups for item in group.high_poly]
        else:
            objects = [item.object for item in bake_group.objects]

        for obj in objects:
            for polygon in obj.data.polygons:
                polygon.select = True

        self.size = int(map.wireframe.size)
        self.size_name = bpy.types.UILayout.enum_item_name(map.wireframe, "size", map.wireframe.size)

        # Use centralized filename builder on the bake group (fallback to legacy template)
        try:
            name = bake_group.bake.build_filename(bpy.context, bake_group_name=bake_group.name.strip(), map_suffix=map.wireframe.suffix.strip())
        except Exception:
            # Fallback: simple default name to avoid chained .replace usage
            name = f"{bake_group.name.strip()}_{map.wireframe.suffix.strip()}"

        if path := self.bake_settings.folders[self.bake_settings.folder_index].path:
            if self.bake_settings.use_sub_folder:
                filepath = os.path.join(path, f"{bake_group.name}", name)
            else:
                filepath = os.path.join(path, name)
        else:
            filepath = bpy.app.tempdir + name

        filepath = bpy.path.ensure_ext(filepath, f".{map.wireframe.format.lower()}")

        # main process
        meshes = list(self.iter_meshes_to_export(context, objects, map))
        polygon_data = list(self.iter_polygon_data_to_draw(context, meshes, map))
        different_colors = {color for _, color in polygon_data}

        if map.wireframe.modified:
            depsgraph = context.evaluated_depsgraph_get()
            for obj in self.iter_objects_to_export(context, objects):
                obj_eval = obj.evaluated_get(depsgraph)
                obj_eval.to_mesh_clear()

        tiles = self.tiles_to_export(polygon_data, map)
        export = self.get_exporter(map)
        dirname, filename = os.path.split(filepath)

        # Strip UDIM or UV numbering, and extension
        import re

        name_regex = r"^(.*?)"
        udim_regex = r"(?:\.[0-9]{4})?"
        uv_regex = r"(?:\.u[0-9]+_v[0-9]+)?"
        ext_regex = r"(?:\.png|\.eps|\.svg)?$"

        if map.wireframe.export_tiles == "NONE":
            match = re.match(name_regex + ext_regex, filename)
        elif map.wireframe.export_tiles == "UDIM":
            match = re.match(name_regex + udim_regex + ext_regex, filename)
        elif map.wireframe.export_tiles == "UV":
            match = re.match(name_regex + uv_regex + ext_regex, filename)

        if match:
            filename = match.groups()[0]

        for tile in sorted(tiles):
            filepath = os.path.join(dirname, filename)

            if map.wireframe.export_tiles == "UDIM":
                filepath += f".{1001 + tile[0] + tile[1] * 10:04}"
            elif map.wireframe.export_tiles == "UV":
                filepath += f".u{tile[0] + 1}_v{tile[1] + 1}"

            filepath = bpy.path.ensure_ext(filepath, f".{map.wireframe.format.lower()}")

            export(filepath, tile, polygon_data, different_colors, self.size, self.size, map.wireframe)
            # export(filepath, polygon_data, different_colors, self.size, self.size, map.wireframe)

    def iter_meshes_to_export(self, context, objects, map):
        depsgraph = context.evaluated_depsgraph_get()
        for obj in self.iter_objects_to_export(context, objects):
            if map.wireframe.modified:
                yield obj.evaluated_get(depsgraph).to_mesh()
            else:
                yield obj.data

    @staticmethod
    def iter_objects_to_export(context, objects):
        for obj in objects:
            if obj.type != "MESH":
                continue
            mesh = obj.data
            if mesh.uv_layers.active is None:
                continue
            yield obj

    def tiles_to_export(self, polygon_data, map):
        """Get a set of tiles containing UVs.
        This assumes there is no UV edge crossing an otherwise empty tile.
        """
        if map.wireframe.export_tiles == "NONE":
            return {(0, 0)}

        from math import floor

        tiles = set()
        for poly in polygon_data:
            for uv in poly[0]:
                # Ignore UVs at corners - precisely touching the right or upper edge
                # of a tile should not load its right/upper neighbor as well.
                # From intern/cycles/scene/attribute.cpp
                u, v = uv[0], uv[1]
                x, y = floor(u), floor(v)
                if x > 0 and u < x + 1e-6:
                    x -= 1
                if y > 0 and v < y + 1e-6:
                    y -= 1
                if x >= 0 and y >= 0:
                    tiles.add((x, y))
        return tiles

    @staticmethod
    def currently_image_image_editor(context):
        return isinstance(context.space_data, bpy.types.SpaceImageEditor)

    def get_currently_opened_image(self, context):
        return context.space_data.image if self.currently_image_image_editor(context) else None

    def get_image_size(self, context):
        # fallback if not in image context
        image_width = self.size[0]
        image_height = self.size[1]

        # get size of "active" image if some exist
        image = self.get_currently_opened_image(context)
        if image is not None:
            width, height = image.size
            if width and height:
                image_width = width
                image_height = height

        return image_width, image_height

    def iter_polygon_data_to_draw(self, context, meshes, map):
        for mesh in meshes:
            uv_layer = mesh.uv_layers.active.data
            for polygon in mesh.polygons:
                if map.wireframe.export_all or polygon.select:
                    start = polygon.loop_start
                    end = start + polygon.loop_total
                    uvs = tuple(tuple(uv.uv) for uv in uv_layer[start:end])
                    yield (uvs, self.get_polygon_color(mesh, polygon))

    @staticmethod
    def get_polygon_color(mesh, polygon, default=(0.8, 0.8, 0.8)):
        if polygon.material_index < len(mesh.materials):
            material = mesh.materials[polygon.material_index]
            if material is not None:
                return tuple(material.diffuse_color)[:3]
        return default

    def get_exporter(self, map):
        if map.wireframe.format == "PNG":
            from . import export_uv_png

            return export_uv_png.export
        elif map.wireframe.format == "EPS":
            from . import export_uv_eps

            return export_uv_eps.export
        elif map.wireframe.format == "SVG":
            from . import export_uv_svg

            return export_uv_svg.export
        else:
            assert False
