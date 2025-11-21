import json
import os
import sys
import time
from functools import partial

import bpy
import numpy

from ...qbpy import Collection, Image, Material, Modifier, Object, Property, ShaderNode
from .map_v4 import Map
from .udim_bake import Udim


class Bake(Udim, Map):
    baked_maps = {}
    TYPE_IMAGE = 0

    def prepare_render_settings(
        self, context, view_from: str = "ABOVE_SURFACE", samples: int = 1, tile_size: int = 2048
    ):
        self.render_settings = {context.scene.render: {}, context.scene.render.bake: {}, context.scene.cycles: {}}

        self.render_settings[context.scene.render]["engine"] = context.scene.render.engine
        context.scene.render.engine = "CYCLES"

        if context.scene.cycles.device:
            self.render_settings[context.scene.cycles]["device"] = context.scene.cycles.device
            context.scene.cycles.device = "GPU"

        self.render_settings[context.scene.render.bake]["view_from"] = context.scene.render.bake.view_from
        context.scene.render.bake.view_from = view_from

        self.render_settings[context.scene.cycles]["samples"] = context.scene.cycles.samples
        context.scene.cycles.samples = samples

        self.render_settings[context.scene.cycles]["use_denoising"] = context.scene.cycles.use_denoising
        context.scene.cycles.use_denoising = False

        self.render_settings[context.scene.cycles]["use_auto_tile"] = context.scene.cycles.use_auto_tile
        context.scene.cycles.use_auto_tile = True

        self.render_settings[context.scene.cycles]["tile_size"] = context.scene.cycles.tile_size
        context.scene.cycles.tile_size = tile_size

    def restore_render_settings(self, context):
        for data, values in self.render_settings.items():
            for property, value in values.items():
                Property.set_property_value(data, property, value)

    def bake(
        self,
        type: str,
        pass_filter=None,
        normal_space: str = "TANGENT",
        normal_r: str = "POS_X",
        normal_g: str = "POS_Y",
        normal_b: str = "POS_Z",
    ):
        """Bake

        type (str) - Type of pass to bake
        pass_filter (enum in ['NONE', 'COLOR', 'DIFFUSE', 'DIRECT', 'EMIT', 'GLOSSY', 'INDIRECT', 'TRANSMISSION'], default 'COLOR')- Pass Filter, Filter to combined, diffuse, glossy, transmission and subsurface passes
        normal_space (enum in ['OBJECT', 'TANGENT'], default 'TANGENT') - Choose normal space for baking normal
        normal_r (enum in ['POS_X', 'POS_Y', 'POS_Z', 'NEG_X', 'NEG_Y', 'NEG_Z'], default 'POS_X') - Axis to bake in red channel
        normal_g (enum in ['POS_X', 'POS_Y', 'POS_Z', 'NEG_X', 'NEG_Y', 'NEG_Z'], default 'POS_Y') - Axis to bake in green channel
        normal_b (enum in ['POS_X', 'POS_Y', 'POS_Z', 'NEG_X', 'NEG_Y', 'NEG_Z'], default 'POS_Z') - Axis to bake in blue channel
        """
        if pass_filter is None:
            pass_filter = {"COLOR"}

        bpy.ops.object.bake(
            type=type,
            pass_filter=pass_filter,
            margin_type=self.bake_settings.margin_type,
            margin=self.bake_settings.margin,
            normal_space=normal_space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
            use_selected_to_active=self.bake_group.use_high_to_low,
            use_cage=True,
            cage_object=self.cage_object.name if self.bake_group.use_high_to_low and self.cage_object else "",
            max_ray_distance=self.ray_distance if self.bake_group.use_high_to_low else 0,
            use_clear=self.use_clear,
            uv_layer=self.uv_layer if self.uv_layer else "",
        )

    def setup_multires_bake(
        self, context, map: bpy.types.PropertyGroup, bake_type: str, non_color: bool = True
    ) -> bpy.types.Image:
        """Multires Bake.

        map (bpy.types.PropertyGroup) - The type of the map.
        bake_type (enum in ['NORMALS', 'DISPLACEMENT']) - Type of pass to bake..
        return (bpy.types.Image) - Baked Map.
        """
        if image_id := self.baked_maps.get(map.type):
            return bpy.data.images[image_id]

        node = ShaderNode.image_texture(self.node_tree, name=map.name)
        node.select = True
        self.node_tree.nodes.active = node

        if bake_type == "NORMALS":
            context.scene.cycles.samples = map.normal.samples
            context.scene.cycles.use_denoising = map.normal.denoise
            if map.normal.custom:
                width = (
                    (map.normal.bake.width * int(map.normal.bake.anti_aliasing))
                    if map.normal.bake.size == "CUSTOM"
                    else int(map.normal.bake.size) * int(map.normal.bake.anti_aliasing)
                )
                height = (
                    (map.normal.bake.height * int(map.normal.bake.anti_aliasing))
                    if map.normal.bake.size == "CUSTOM"
                    else int(map.normal.bake.size) * int(map.normal.bake.anti_aliasing)
                )
            else:
                width = (
                    (self.bake_settings.width * int(self.bake_settings.anti_aliasing))
                    if self.bake_settings.size == "CUSTOM"
                    else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
                )
                height = (
                    (self.bake_settings.height * int(self.bake_settings.anti_aliasing))
                    if self.bake_settings.size == "CUSTOM"
                    else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
                )
        else:
            context.scene.cycles.samples = map.displacement.samples
            context.scene.cycles.use_denoising = map.displacement.denoise
            if map.displacement.custom:
                width = (
                    (map.displacement.bake.width * int(map.displacement.bake.anti_aliasing))
                    if map.displacement.bake.size == "CUSTOM"
                    else int(map.displacement.bake.size) * int(map.displacement.bake.anti_aliasing)
                )
                height = (
                    (map.displacement.bake.height * int(map.displacement.bake.anti_aliasing))
                    if map.displacement.bake.size == "CUSTOM"
                    else int(map.displacement.bake.size) * int(map.displacement.bake.anti_aliasing)
                )
            else:
                width = (
                    (self.bake_settings.width * int(self.bake_settings.anti_aliasing))
                    if self.bake_settings.size == "CUSTOM"
                    else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
                )
                height = (
                    (self.bake_settings.height * int(self.bake_settings.anti_aliasing))
                    if self.bake_settings.size == "CUSTOM"
                    else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
                )

        if bake_type == "NORMALS" and map.normal.image:
            image = map.normal.image
            image.name = map.name
            self.use_clear = False
        elif bake_type == "DISPLACEMENT" and map.displacement.image:
            image = map.displacement.image
            image.name = map.name
            self.use_clear = False
        elif self.bake_settings.use_auto_udim and len(self.udims) > 1:
            image = self.udim_image(context, self.udims, name=map.name, width=width, height=height, non_color=non_color)
        else:
            image = Image.new_image(name=map.name, width=width, height=height, non_color=non_color)

        node.image = image
        context.scene.render.use_bake_multires = True
        context.scene.render.bake_type = bake_type
        context.scene.render.use_bake_clear = self.use_clear
        context.scene.render.bake_margin = self.bake_settings.margin

    def bake_multires_bake(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        bpy.ops.object.bake_image()
        context.scene.render.use_bake_multires = False
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    def prepare_image(self, context, map, type, non_color=False, alpha=False):
        node = ShaderNode.image_texture(self.node_tree, name=map.name)
        node.select = True
        self.node_tree.nodes.active = node

        if type.custom:
            width = (
                (type.bake.width * int(type.bake.anti_aliasing))
                if type.bake.size == "CUSTOM"
                else int(type.bake.size) * int(type.bake.anti_aliasing)
            )
            height = (
                (type.bake.height * int(type.bake.anti_aliasing))
                if type.bake.size == "CUSTOM"
                else int(type.bake.size) * int(type.bake.anti_aliasing)
            )
        else:
            width = (
                (self.bake_settings.width * int(self.bake_settings.anti_aliasing))
                if self.bake_settings.size == "CUSTOM"
                else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
            )
            height = (
                (self.bake_settings.height * int(self.bake_settings.anti_aliasing))
                if self.bake_settings.size == "CUSTOM"
                else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
            )

        if type.image:
            image = type.image
            image.name = map.name
            self.use_clear = False
        elif self.bake_settings.use_auto_udim and len(self.udims) > 1:
            image = self.udim_image(
                context, self.udims, name=map.name, width=width, height=height, non_color=non_color, alpha=alpha
            )
        else:
            image = Image.new_image(name=map.name, width=width, height=height, non_color=non_color, alpha=alpha)

        node.image = image
        context.scene.cycles.samples = type.samples
        context.scene.cycles.use_denoising = type.denoise
        return image

    ## PBR

    # Base Color
    def setup_base_color(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Base Color Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Base Color image
        """
        self.prepare_image(context, map, map.base_color, alpha=map.base_color.use_alpha)
        if map.base_color.use_alpha:
            self.prepare_diffuse(map.base_color)
        else:
            self.prepare_base_color()

    def bake_base_color(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        if map.base_color.use_alpha:
            self.bake("DIFFUSE")
            self.restore_diffuse()
        else:
            self.bake("EMIT")
            self.restore_color_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Emission
    def setup_emission(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Emission Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Emission image
        """
        self.prepare_image(context, map, map.emission, non_color=map.emission.non_color, alpha=False)
        self.prepare_emission()

    def bake_emission(self, context, map: bpy.types.PropertyGroup):
        context.scene.render.bake.view_from = map.emission.view_from
        self.bake("EMIT")
        self.restore_emission()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Glossiness
    def setup_glossiness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Glossiness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Glossiness Map.
        """
        self.prepare_image(context, map, map.glossiness, non_color=non_color)
        self.prepare_glossiness()

    def bake_glossiness(self, context, map: bpy.types.PropertyGroup):
        self.bake("EMIT")
        self.restore_glossiness()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Metallic
    def setup_metallic(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Metallic Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Metallic Map.
        """
        self.prepare_image(context, map, map.metallic, non_color=non_color)
        self.prepare_metallic()

    def bake_metallic(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Normal
    def setup_normal(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Normal Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Normal Map.
        """
        self.prepare_image(context, map, map.normal, non_color=non_color)
        # self.prepare_normal()

    def bake_normal(self, context, map: bpy.types.PropertyGroup):
        if map.normal.type == "DIRECTX":
            normal_r = "POS_X"
            normal_g = "NEG_Y"
            normal_b = "POS_Z"
        elif map.normal.type == "OPENGL":
            normal_r = "POS_X"
            normal_g = "POS_Y"
            normal_b = "POS_Z"
        else:
            normal_r = map.normal.r
            normal_g = map.normal.g
            normal_b = map.normal.b

        self.bake(
            "NORMAL",
            normal_space=map.normal.space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
        )
        # self.restore_normal()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Occlusion
    def setup_occlusion(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Occlusion Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Occlusion image
        """
        self.prepare_image(context, map, map.occlusion, non_color=non_color)
        self.prepare_occlusion(map=map.occlusion)

    def bake_occlusion(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_occlusion()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Roughness
    def setup_roughness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Roughness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Roughness Map.
        """
        self.prepare_image(context, map, map.roughness, non_color=non_color)
        self.prepare_roughness()

    def bake_roughness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Specular
    def setup_specular(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Specular Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Specular Map.
        """
        self.prepare_image(context, map, map.specular, non_color=non_color)
        self.prepare_specular()

    def bake_specular(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    ## Mesh

    # Alpha
    def setup_alpha(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Alpha Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Alpha image
        """
        self.prepare_image(context, map, map.alpha, non_color=non_color)
        self.prepare_alpha()

    def bake_alpha(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Bevel Normal
    def setup_bevel_normal(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Bevel normal Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Bevel normal Map.
        """
        self.prepare_image(context, map, map.bevel_normal, non_color=non_color)

    def bake_bevel_normal(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        if map.bevel_normal.type == "DIRECTX":
            normal_r = "POS_X"
            normal_g = "NEG_Y"
            normal_b = "POS_Z"
        elif map.bevel_normal.type == "OPENGL":
            normal_r = "POS_X"
            normal_g = "POS_Y"
            normal_b = "POS_Z"
        else:
            normal_r = map.bevel_normal.r
            normal_g = map.bevel_normal.g
            normal_b = map.bevel_normal.b

        self.prepare_bevel_normal(map=map.bevel_normal)
        self.bake(
            "NORMAL",
            normal_space=map.bevel_normal.space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
        )
        self.restore_bevel_normal()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Cavity
    def setup_cavity(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Cavity Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Cavity image
        """
        self.prepare_image(context, map, map.cavity, non_color=non_color)
        self.prepare_cavity(map=map.cavity)

    def bake_cavity(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_cavity()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Curvature
    def setup_curvature(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Curvature Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Curvature image
        """
        self.prepare_image(context, map, map.curvature, non_color=non_color)
        self.prepare_curvature(map=map.curvature)

    def bake_curvature(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_curvature()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Displacement
    def setup_displacement(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Displacement Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Displacement image
        """
        self.prepare_image(context, map, map.displacement, non_color=non_color)
        self.prepare_displacement(map=map.displacement)

    def bake_displacement(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_displacement()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Edge
    def setup_edge(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Edge Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Edge image
        """
        self.prepare_image(context, map, map.edge, non_color=non_color)
        self.prepare_edge(map=map.edge)

    def bake_edge(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_edge()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Gradient
    def setup_gradient(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Gradient Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Gradient image
        """
        self.prepare_image(context, map, map.gradient, non_color=non_color)
        self.prepare_gradient(map=map.gradient)

    def bake_gradient(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_gradient()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Height
    def setup_height(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Height Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Height image
        """
        self.prepare_image(context, map, map.height, non_color=non_color)
        self.prepare_height(map=map.height)

    def bake_height(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_height()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Material ID
    def setup_material_id(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Material ID Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Metarial ID Map.
        """
        self.prepare_image(context, map, map.material_id, alpha=True)
        self.prepare_material_id(map=map.material_id)

    def bake_material_id(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_material_id()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Thickness
    def setup_thickness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Thickness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Thickness image
        """
        self.prepare_image(context, map, map.thickness, non_color=non_color)
        self.prepare_thickness(map=map.thickness)

    def bake_thickness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_thickness()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Toon Shadow
    def setup_toon_shadow(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Toon Shadow Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Toon Shadow image
        """
        self.prepare_image(context, map, map.toon_shadow, non_color=non_color)
        self.prepare_toon_shadow(map=map.toon_shadow)

    def bake_toon_shadow(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        pass_filter = {"DIRECT"}

        if map.toon_shadow.use_pass_direct:
            pass_filter.add("DIRECT")
        if map.toon_shadow.use_pass_indirect:
            pass_filter.add("INDIRECT")

        self.bake("DIFFUSE", pass_filter)
        self.restore_toon_shadow()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # VDM
    def setup_vdm(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake VDM Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - VDM image
        """
        self.prepare_image(context, map, map.vdm, non_color=non_color)
        self.prepare_vdm()

    def bake_vdm(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_vdm()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # XYZ
    def setup_xyz(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake XYZ Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - XYZ image
        """
        self.prepare_image(context, map, map.xyz, non_color=non_color)
        self.prepare_xyz(map=map.xyz)

    def bake_xyz(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_xyz()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    ## Principled BSDF

    # IOR
    def setup_ior(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake IOR Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - IOR Map.
        """
        self.prepare_image(context, map, map.ior, non_color=non_color)
        self.prepare_ior()

    def bake_ior(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface Weight
    def setup_subsurface_weight(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Subsurface Weight Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Weight Map.
        """
        self.prepare_image(context, map, map.subsurface_weight, non_color=non_color)
        self.prepare_subsurface_weight()

    def bake_subsurface_weight(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface Scale
    def setup_subsurface_scale(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Subsurface Scale Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Scale Map.
        """
        self.prepare_image(context, map, map.subsurface_scale, non_color=non_color)
        self.prepare_subsurface_scale()

    def bake_subsurface_scale(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface IOR
    def setup_subsurface_ior(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Subsurface IOR Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface IOR Map.
        """
        self.prepare_image(context, map, map.subsurface_ior, non_color=non_color)
        self.prepare_subsurface_ior()

    def bake_subsurface_ior(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface Anisotropy
    def setup_subsurface_anisotropy(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Subsurface Anisotropy Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Anisotropy Map.
        """
        self.prepare_image(context, map, map.subsurface_anisotropy, non_color=non_color)
        self.prepare_subsurface_anisotropy()

    def bake_subsurface_anisotropy(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Specular Tint
    def setup_specular_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Specular Tint Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Specular Tint Map.
        """
        self.prepare_image(context, map, map.specular_tint, alpha=True)
        self.prepare_specular_tint()

    def bake_specular_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_color_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Anisotropic
    def setup_anisotropic(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Anisotropic Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Anisotropic Map.
        """
        self.prepare_image(context, map, map.anisotropic, non_color=non_color)
        self.prepare_anisotropic()

    def bake_anisotropic(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Anisotropic Rotation
    def setup_anisotropic_rotation(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Anisotropic Rotation Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Anisotropic Rotation Map.
        """
        self.prepare_image(context, map, map.anisotropic_rotation, non_color=non_color)
        self.prepare_anisotropic_rotation()

    def bake_anisotropic_rotation(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Tangent
    def setup_tangent(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Tangent Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Tangent Map.
        """
        self.prepare_image(context, map, map.tangent, non_color=non_color)
        self.prepare_tangent()

    def bake_tangent(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        if map.tangent.type == "DIRECTX":
            normal_r = "POS_X"
            normal_g = "NEG_Y"
            normal_b = "POS_Z"
        elif map.tangent.type == "OPENGL":
            normal_r = "POS_X"
            normal_g = "POS_Y"
            normal_b = "POS_Z"
        else:
            normal_r = map.tangent.r
            normal_g = map.tangent.g
            normal_b = map.tangent.b

        self.bake(
            "NORMAL",
            normal_space=map.tangent.space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
        )
        self.restore_vector_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Transmission Weight
    def setup_transmission_weight(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Transmission Weight Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Transmission Weight Map.
        """
        self.prepare_image(context, map, map.transmission_weight, non_color=non_color)
        self.prepare_transmission_weight()

    def bake_transmission_weight(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Coat Weight
    def setup_coat_weight(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Coat Weight Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Coat Weight Map.
        """
        self.prepare_image(context, map, map.coat_weight, non_color=non_color)
        self.prepare_coat_weight()

    def bake_coat_weight(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Coat Roughness
    def setup_coat_roughness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Coat Roughness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Coat Roughness Map.
        """
        self.prepare_image(context, map, map.coat_roughness, non_color=non_color)
        self.prepare_coat_roughness()

    def bake_coat_roughness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Coat IOR
    def setup_coat_ior(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Coat IOR Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Coat IOR Map.
        """
        self.prepare_image(context, map, map.coat_ior, non_color=non_color)
        self.prepare_coat_ior()

    def bake_coat_ior(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Coat Tint
    def setup_coat_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Coat Tint Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Coat Tint Map.
        """
        self.prepare_image(context, map, map.coat_tint, alpha=True)
        self.prepare_coat_tint()

    def bake_coat_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.bake("EMIT")
        self.restore_color_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Coat Normal
    def setup_coat_normal(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.coat_normal, non_color=non_color)
        self.prepare_coat_normal()

    def bake_coat_normal(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Coat Normal Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Coat Normal Map.
        """
        if map.coat_normal.type == "DIRECTX":
            normal_r = "POS_X"
            normal_g = "NEG_Y"
            normal_b = "POS_Z"
        elif map.coat_normal.type == "OPENGL":
            normal_r = "POS_X"
            normal_g = "POS_Y"
            normal_b = "POS_Z"
        else:
            normal_r = map.coat_normal.r
            normal_g = map.coat_normal.g
            normal_b = map.coat_normal.b

        self.bake(
            "NORMAL",
            normal_space=map.coat_normal.space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
        )
        self.restore_vector_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Sheen Weight
    def setup_sheen_weight(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.sheen_weight, non_color=non_color)
        self.prepare_sheen_weight()

    def bake_sheen_weight(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Sheen Weight Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Sheen Weight Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Sheen Roughness
    def setup_sheen_roughness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.sheen_roughness, non_color=non_color)
        self.prepare_sheen_roughness()

    def bake_sheen_roughness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Sheen Roughness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Sheen Roughness Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Sheen Tint
    def setup_sheen_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.sheen_tint, alpha=True)
        self.prepare_sheen_tint()

    def bake_sheen_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Sheen Tint Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Sheen Tint Map.
        """
        self.bake("EMIT")
        self.restore_color_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Emission Strength
    def setup_emission_strength(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.emission_strength, non_color=non_color)
        self.prepare_emission_strength()

    def bake_emission_strength(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Specular Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Specular Map.
        """
        self.bake("EMIT")
        self.restore_emission_strength()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    ## Cycles

    # Ambient Occlusion
    def setup_ambient_occlusion(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.ambient_occlusion, non_color=non_color)
        self.prepare_ambient_occlusion(map.ambient_occlusion)

    def bake_ambient_occlusion(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Ambient Occlusion Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Ambient Occlusion image
        """
        self.bake("AO")
        self.restore_ambient_occlusion()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Combined
    def setup_combined(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.combined, non_color=map.combined.non_color, alpha=map.combined.use_alpha)
        self.prepare_combined(map=map.combined)

    def bake_combined(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Combined Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Combined image
        """
        pass_filter = set()

        if map.combined.use_pass_direct:
            pass_filter.add("DIRECT")
        if map.combined.use_pass_indirect:
            pass_filter.add("INDIRECT")
        if map.combined.use_pass_diffuse:
            pass_filter.add("DIFFUSE")
        if map.combined.use_pass_glossy:
            pass_filter.add("GLOSSY")
        if map.combined.use_pass_transmission:
            pass_filter.add("TRANSMISSION")
        if map.combined.use_pass_emit:
            pass_filter.add("EMIT")

        context.scene.render.bake.view_from = map.combined.view_from
        self.bake("COMBINED", pass_filter)
        self.restore_combined()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Diffuse
    def setup_diffuse(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.diffuse, alpha=map.diffuse.use_alpha)
        self.prepare_diffuse(map.diffuse)

    def bake_diffuse(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Diffuse Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Diffuse image
        """
        pass_filter = set()

        if map.diffuse.use_pass_direct:
            pass_filter.add("DIRECT")
        if map.diffuse.use_pass_indirect:
            pass_filter.add("INDIRECT")
        if map.diffuse.use_pass_color:
            pass_filter.add("COLOR")

        context.scene.render.bake.view_from = map.diffuse.view_from
        self.bake("DIFFUSE", pass_filter)
        self.restore_diffuse()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Environment
    def setup_environment(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.environment, alpha=True)

    def bake_environment(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Environment Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Environment image
        """
        self.bake("ENVIRONMENT")
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Glossy
    def setup_glossy(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.glossy, alpha=True)

    def bake_glossy(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Glossy Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Glossy image
        """
        pass_filter = set()

        if map.glossy.use_pass_direct:
            pass_filter.add("DIRECT")
        if map.glossy.use_pass_indirect:
            pass_filter.add("INDIRECT")
        if map.glossy.use_pass_color:
            pass_filter.add("COLOR")

        context.scene.render.bake.view_from = map.glossy.view_from
        self.bake("GLOSSY", pass_filter)
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Position
    def setup_position(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.position, non_color=non_color)

    def bake_position(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Position Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Position image
        """
        self.bake("POSITION")
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Shadow
    def setup_shadow(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.shadow, non_color=non_color)
        self.prepare_shadow(map=map.shadow)

    def bake_shadow(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Shadow Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Shadow image
        """
        context.scene.render.bake.view_from = map.shadow.view_from
        self.bake("SHADOW")
        self.restore_shadow()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Transmission
    def setup_transmission(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.transmission, non_color=non_color, alpha=map.transmission.use_alpha)
        self.prepare_transmission()

    def bake_transmission(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Transmission Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Transmission image
        """
        pass_filter = set()

        if map.transmission.use_pass_direct:
            pass_filter.add("DIRECT")
        if map.transmission.use_pass_indirect:
            pass_filter.add("INDIRECT")
        if map.transmission.use_pass_color:
            pass_filter.add("COLOR")

        context.scene.render.bake.view_from = map.transmission.view_from
        self.bake("TRANSMISSION", pass_filter)
        self.restore_transmission()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # UV
    def setup_uv(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.uv, non_color=non_color)
        self.prepare_uv()

    def bake_uv(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake UV Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - UV image
        """
        self.bake("UV")
        self.restore_uv()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Channel Pack
    def setup_channel_map(
        self, context, map: bpy.types.PropertyGroup, channel: bpy.types.PointerProperty, channel_label: str
    ) -> bpy.types.Image:
        """Bake channel map.

        Args:
            map (bpy.types.PropertyGroup): The type of the map.
            channel (bpy.types.PointerProperty): Channel map type.
            channel_label (str): Channel map label.

        Returns:
            bpy.types.Image: The channel map.
        """
        if self.baked_maps.get(channel):
            return

        origin_map_id = map.name
        map.name = f"{map.name}_{channel_label}"

        def mapping_helper(context, map, channel_map, func):
            self.channel_map_size(map, channel_map=channel_map)
            return func(context, map)

        def mapping_helper_non_color(context, map, channel_map, func):
            self.channel_map_size(map, channel_map=channel_map)
            return func(context, map, non_color=True)

        def mapping_normal_multires_helper(context, map, channel_map, func):
            self.channel_map_size(map, channel_map=channel_map)

            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    if map.channel_pack.normal.source == "MULTIRES":
                        modifier.show_viewport = True
                        modifier.levels = 0
                        return self.setup_multires_bake(context, map, bake_type="NORMALS", non_color=False)

                    modifier.show_render = map.channel_pack.normal.source == "SHADER_MULTIRES"
                    return func(context, map, non_color=False)

            return func(context, map, non_color=False)

        def mapping_displacement_multires_helper(context, map, channel_map, func):
            self.channel_map_size(map, channel_map=channel_map)

            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    modifier.show_viewport = True
                    modifier.levels = 0
                    return self.setup_multires_bake(context, map, bake_type="DISPLACEMENT", non_color=False)

            return func(context, map, non_color=False)

        mapping = {  # using lambda to only call partial if necessary / speedup mapping
            # PBR
            "BASE_COLOR": lambda: partial(mapping_helper, channel_map=map.base_color, func=self.setup_base_color),
            "EMISSION": lambda: partial(mapping_helper, channel_map=map.emission, func=self.setup_emission),
            "GLOSSINESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.glossiness, func=self.setup_glossiness
            ),
            "METALLIC": lambda: partial(mapping_helper_non_color, channel_map=map.metallic, func=self.setup_metallic),
            "NORMAL": lambda: partial(mapping_normal_multires_helper, channel_map=map.normal, func=self.setup_normal),
            "OCCLUSION": lambda: partial(
                mapping_helper_non_color, channel_map=map.occlusion, func=self.setup_occlusion
            ),
            "ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.roughness, func=self.setup_roughness
            ),
            "SPECULAR": lambda: partial(mapping_helper_non_color, channel_map=map.specular, func=self.setup_specular),
            # Mesh
            "ALPHA": lambda: partial(mapping_helper_non_color, channel_map=map.alpha, func=self.setup_alpha),
            "BEVEL_NORMAL": lambda: partial(
                mapping_helper_non_color, channel_map=map.bevel_normal, func=self.setup_bevel_normal
            ),
            "CAVITY": lambda: partial(mapping_helper_non_color, channel_map=map.cavity, func=self.setup_cavity),
            "CURVATURE": lambda: partial(
                mapping_helper_non_color, channel_map=map.curvature, func=self.setup_curvature
            ),
            "DISPLACEMENT": lambda: partial(
                mapping_displacement_multires_helper, channel_map=map.displacement, func=self.setup_displacement
            ),
            "EDGE": lambda: partial(mapping_helper_non_color, channel_map=map.edge, func=self.setup_edge),
            "GRADIENT": lambda: partial(mapping_helper_non_color, channel_map=map.gradient, func=self.setup_gradient),
            "HEIGHT": lambda: partial(mapping_helper_non_color, channel_map=map.height, func=self.setup_height),
            "MATERIAL_ID": lambda: partial(mapping_helper, channel_map=map.material_id, func=self.setup_material_id),
            "THICKNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.thickness, func=self.setup_thickness
            ),
            "TOON_SHADOW": lambda: partial(
                mapping_helper_non_color, channel_map=map.toon_shadow, func=self.setup_toon_shadow
            ),
            "VDM": lambda: partial(mapping_helper_non_color, channel_map=map.vdm, func=self.setup_vdm),
            "XYZ": lambda: partial(mapping_helper_non_color, channel_map=map.xyz, func=self.setup_xyz),
            # Principled BSDF
            "IOR": lambda: partial(mapping_helper_non_color, channel_map=map.ior, func=self.setup_ior),
            "SUBSURFACE_WEIGHT": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_weight, func=self.setup_subsurface_weight
            ),
            "SUBSURFACE_SCALE": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_scale, func=self.setup_subsurface_scale
            ),
            "SUBSURFACE_IOR": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_ior, func=self.setup_subsurface_ior
            ),
            "SUBSURFACE_ANISOTROPY": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_anisotropy, func=self.setup_subsurface_anisotropy
            ),
            "SPECULAR_TINT": lambda: partial(
                mapping_helper, channel_map=map.specular_tint, func=self.setup_specular_tint
            ),
            "ANISOTROPIC": lambda: partial(
                mapping_helper_non_color, channel_map=map.anisotropic, func=self.setup_anisotropic
            ),
            "ANISOTROPIC_ROTATION": lambda: partial(
                mapping_helper_non_color, channel_map=map.anisotropic_rotation, func=self.setup_anisotropic_rotation
            ),
            "TANGENT": lambda: partial(mapping_helper_non_color, channel_map=map.tangent, func=self.setup_tangent),
            "TRANSMISSION_WEIGHT": lambda: partial(
                mapping_helper_non_color, channel_map=map.transmission_weight, func=self.setup_transmission_weight
            ),
            "COAT_WEIGHT": lambda: partial(
                mapping_helper_non_color, channel_map=map.coat_weight, func=self.setup_coat_weight
            ),
            "COAT_ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.coat_roughness, func=self.setup_coat_roughness
            ),
            "COAT_IOR": lambda: partial(mapping_helper_non_color, channel_map=map.coat_ior, func=self.setup_coat_ior),
            "COAT_TINT": lambda: partial(mapping_helper, channel_map=map.coat_tint, func=self.setup_coat_tint),
            "COAT_NORMAL": lambda: partial(
                mapping_helper_non_color, channel_map=map.coat_normal, func=self.setup_coat_normal
            ),
            "SHEEN_WEIGHT": lambda: partial(
                mapping_helper_non_color, channel_map=map.sheen_weight, func=self.setup_sheen_weight
            ),
            "SHEEN_ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.sheen_roughness, func=self.setup_sheen_roughness
            ),
            "SHEEN_TINT": lambda: partial(mapping_helper, channel_map=map.sheen_tint, func=self.setup_sheen_tint),
            "EMISSION_STRENGTH": lambda: partial(
                mapping_helper_non_color, channel_map=map.emission_strength, func=self.setup_emission_strength
            ),
            # Cycles
            "AO": lambda: partial(
                mapping_helper_non_color, channel_map=map.ambient_occlusion, func=self.setup_ambient_occlusion
            ),
            "COMBINED": lambda: partial(mapping_helper, channel_map=map.combined, func=self.setup_combined),
            "DIFFUSE": lambda: partial(mapping_helper, channel_map=map.diffuse, func=self.setup_diffuse),
            "ENVIRONMENT": lambda: partial(mapping_helper, channel_map=map.environment, func=self.setup_environment),
            "GLOSSY": lambda: partial(mapping_helper, channel_map=map.glossy, func=self.setup_glossy),
            "POSITION": lambda: partial(mapping_helper, channel_map=map.position, func=self.setup_position),
            "SHADOW": lambda: partial(mapping_helper_non_color, channel_map=map.shadow, func=self.setup_shadow),
            "TRANSMISSION": lambda: partial(mapping_helper, channel_map=map.transmission, func=self.setup_transmission),
            "UV": lambda: partial(mapping_helper_non_color, channel_map=map.uv, func=self.setup_uv),
        }
        if func := mapping.get(channel, lambda: None)():
            func(context, map)

        map.name = origin_map_id

    def bake_channel_map(
        self, context, map: bpy.types.PropertyGroup, channel: bpy.types.PointerProperty, channel_label: str
    ) -> bpy.types.Image:
        """Bake channel map.

        Args:
            map (bpy.types.PropertyGroup): The type of the map.
            channel (bpy.types.PointerProperty): Channel map type.
            channel_label (str): Channel map label.

        Returns:
            bpy.types.Image: The channel map.
        """
        if image_id := self.baked_maps.get(channel):
            channel_image = bpy.data.images[image_id]
            print("QB: Baked Map")
            sys.stdout.flush()
            return channel_image

        origin_map_id = map.name
        map.name = f"{map.name}_{channel_label}"

        def normal_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    if map.channel_pack.normal.source == "MULTIRES":
                        modifier.show_viewport = True
                        modifier.levels = 0
                        return self.bake_multires_bake(context, map)

                    modifier.show_render = map.channel_pack.normal.source == "SHADER_MULTIRES"
                    return func(context, map)

            return func(context, map)

        def displacement_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    modifier.show_viewport = True
                    modifier.levels = 0
                    return self.bake_multires_bake(context, map)

            return func(context, map)

        mapping = {
            "BASE_COLOR": self.bake_base_color,
            "EMISSION": self.bake_emission,
            "GLOSSINESS": self.bake_glossiness,
            "METALLIC": self.bake_metallic,
            "NORMAL": partial(normal_multires_helper, func=self.bake_normal),
            "OCCLUSION": self.bake_occlusion,
            "ROUGHNESS": self.bake_roughness,
            "SPECULAR": self.bake_specular,
            "ALPHA": self.bake_alpha,
            "BEVEL_NORMAL": self.bake_bevel_normal,
            "CAVITY": self.bake_cavity,
            "CURVATURE": self.bake_curvature,
            "DISPLACEMENT": partial(displacement_multires_helper, func=self.bake_displacement),
            "EDGE": self.bake_edge,
            "GRADIENT": self.bake_gradient,
            "HEIGHT": self.bake_height,
            "MATERIAL_ID": self.bake_material_id,
            "THICKNESS": self.bake_thickness,
            "TOON_SHADOW": self.bake_toon_shadow,
            "VDM": self.bake_vdm,
            "XYZ": self.bake_xyz,
            "IOR": self.bake_ior,
            "SUBSURFACE_WEIGHT": self.bake_subsurface_weight,
            "SUBSURFACE_SCALE": self.bake_subsurface_scale,
            "SUBSURFACE_IOR": self.bake_subsurface_ior,
            "SUBSURFACE_ANISOTROPY": self.bake_subsurface_anisotropy,
            "SPECULAR_TINT": self.bake_specular_tint,
            "ANISOTROPIC": self.bake_anisotropic,
            "ANISOTROPIC_ROTATION": self.bake_anisotropic_rotation,
            "TANGENT": self.bake_tangent,
            "TRANSMISSION_WEIGHT": self.bake_transmission_weight,
            "COAT_WEIGHT": self.bake_coat_weight,
            "COAT_ROUGHNESS": self.bake_coat_roughness,
            "COAT_IOR": self.bake_coat_ior,
            "COAT_TINT": self.bake_coat_tint,
            "COAT_NORMAL": self.bake_coat_normal,
            "SHEEN_WEIGHT": self.bake_sheen_weight,
            "SHEEN_ROUGHNESS": self.bake_sheen_roughness,
            "SHEEN_TINT": self.bake_sheen_tint,
            "EMISSION_STRENGTH": self.bake_emission_strength,
            "AO": self.bake_ambient_occlusion,
            "COMBINED": self.bake_combined,
            "DIFFUSE": self.bake_diffuse,
            "ENVIRONMENT": self.bake_environment,
            "GLOSSY": self.bake_glossy,
            "POSITION": self.bake_position,
            "SHADOW": self.bake_shadow,
            "TRANSMISSION": self.bake_transmission,
            "UV": self.bake_uv,
        }

        if func := mapping.get(channel, None):
            channel_image = func(context, map)
        else:
            channel_image = None

        map.name = origin_map_id

        if channel_image:
            name = f"{map.name}_{channel_label}"

            if self.bake_settings.use_auto_udim and len(self.udims) > 1:
                name = f"{map.name}_{channel_label}.<UDIM>"

            Image.save_image(
                channel_image,
                path=self.bake_path,
                name=name,
                file_format=map.channel_pack.bake.format if map.channel_pack.custom else self.bake_settings.format,
            )

            self.baked_maps[channel] = f"{map.name}_{channel_label}"
            print("QB: Baked Map")
            sys.stdout.flush()

        self.baked_maps.pop("CHANNEL_PACK", None)
        return channel_image

    def channel_map_size(self, map, channel_map):
        channel_map.custom = map.channel_pack.custom
        channel_map.bake.size = map.channel_pack.bake.size
        channel_map.bake.width = map.channel_pack.bake.width
        channel_map.bake.height = map.channel_pack.bake.height

    def wait_for_file(self, path):
        while not os.path.isfile(path):
            time.sleep(0.05)

    def safe_load_image(self, filepath: str, check_existing: bool = False):
        self.wait_for_file(filepath)
        image = bpy.data.images.load(filepath, check_existing=check_existing)
        while image.size[0] == 0:
            time.sleep(0.05)
            image = bpy.data.images.load(filepath, check_existing=False)
        return image

    def pack_image_channels(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        image_rgb = image_r = image_g = image_b = image_a = None

        file_format = map.channel_pack.bake.format if map.channel_pack.custom else self.bake_settings.format
        if file_format == "OPEN_EXR":
            file_format = "EXR"

        if map.channel_pack.mode == "RGBA":
            if id_image_r := self.baked_maps.get(map.channel_pack.r_channel):
                path = f"{self.bake_path}{self.index}_{id_image_r}.{file_format.lower()}"
                image_r = self.safe_load_image(path, check_existing=True)

            if id_image_g := self.baked_maps.get(map.channel_pack.g_channel):
                path = f"{self.bake_path}{self.index}_{id_image_g}.{file_format.lower()}"
                image_g = self.safe_load_image(path, check_existing=True)

            if id_image_b := self.baked_maps.get(map.channel_pack.b_channel):
                path = f"{self.bake_path}{self.index}_{id_image_b}.{file_format.lower()}"
                image_b = self.safe_load_image(path, check_existing=True)

            if id_image_a := self.baked_maps.get(map.channel_pack.a_channel):
                path = f"{self.bake_path}{self.index}_{id_image_a}.{file_format.lower()}"
                image_a = self.safe_load_image(path, check_existing=True)

            pack_order = [
                (image_r, (0, 0)),
                (image_g, (0, 1)),
                (image_b, (0, 2)),
                (image_a, (0, 3)),
            ]
        else:
            if id_image_rgb := self.baked_maps.get(map.channel_pack.rgb_channel):
                path = f"{self.bake_path}{self.index}_{id_image_rgb}.{file_format.lower()}"
                image_rgb = self.safe_load_image(path, check_existing=True)
            if id_image_a := self.baked_maps.get(map.channel_pack.a_channel):
                path = f"{self.bake_path}{self.index}_{id_image_a}.{file_format.lower()}"
                image_a = self.safe_load_image(path, check_existing=True)

            pack_order = [
                (image_rgb, (0, 0), (1, 1), (2, 2)),
                (image_a, (0, 3)),
            ]

        dst_array = None

        # Build the packed pixel array
        for pack_item in pack_order:
            image = pack_item[0]
            if not image:
                continue

            # Initialize arrays on the first iteration
            if dst_array is None:
                width, height = image.size
                src_array = numpy.empty(width * height * 4, dtype=numpy.float32)
                dst_array = numpy.ones(width * height * 4, dtype=numpy.float32)

            assert image.size[:] == (width, height), "Images must be same size"

            # Fetch pixels from the source image and copy channels
            image.pixels.foreach_get(src_array)
            for src_chan, dst_chan in pack_item[1:]:
                dst_array[dst_chan::4] = src_array[src_chan::4]

        # Create image from the packed pixels
        image = Image.new_image(name=map.name, width=width, height=height, non_color=True, alpha=(image_a is not None))
        image.alpha_mode = "CHANNEL_PACKED"
        image.pixels.foreach_set(dst_array)
        image.pack()
        self.baked_maps[map.type] = map.name
        print("QB: Baked Map")
        return image

    def pack_udim_image_channels(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        # Create image from the packed pixels
        width = (
            (self.bake_settings.width * int(self.bake_settings.anti_aliasing))
            if self.bake_settings.size == "CUSTOM"
            else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
        )
        height = (
            (self.bake_settings.height * int(self.bake_settings.anti_aliasing))
            if self.bake_settings.size == "CUSTOM"
            else int(self.bake_settings.size) * int(self.bake_settings.anti_aliasing)
        )

        image = self.udim_image(
            context,
            self.udims,
            path=self.bake_path,
            name=map.name,
            width=width,
            height=height,
            non_color=False,
            alpha=True,
        )
        image.alpha_mode = "CHANNEL_PACKED"

        file_format = map.channel_pack.bake.format if map.channel_pack.custom else self.bake_settings.format
        if file_format == "OPEN_EXR":
            file_format = "EXR"

        for udim in self.udims:
            dest_image = self.safe_load_image(f"{self.bake_path}{map.name}.{udim}.png")

            if map.channel_pack.mode == "RGBA":
                red_image = green_image = blue_image = alpha_image = None
                if id_image_r := self.baked_maps.get(map.channel_pack.r_channel):
                    if image_r := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_r}.{udim}.{file_format.lower()}"
                    ):
                        red_image = image_r

                if id_image_g := self.baked_maps.get(map.channel_pack.g_channel):
                    if image_g := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_g}.{udim}.{file_format.lower()}"
                    ):
                        green_image = image_g

                if id_image_b := self.baked_maps.get(map.channel_pack.b_channel):
                    if image_b := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_b}.{udim}.{file_format.lower()}"
                    ):
                        blue_image = image_b

                if id_image_a := self.baked_maps.get(map.channel_pack.a_channel):
                    if image_a := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_a}.{udim}.{file_format.lower()}"
                    ):
                        alpha_image = image_a

                pack_order = [
                    (red_image, (0, 0)),
                    (green_image, (0, 1)),
                    (blue_image, (0, 2)),
                    (alpha_image, (0, 3)),
                ]
            else:
                rgb_image = alpha_image = None
                if id_image_rgb := self.baked_maps.get(map.channel_pack.rgb_channel):
                    if image_rgb := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_rgb}.{udim}.{file_format.lower()}"
                    ):
                        rgb_image = image_rgb

                if id_image_a := self.baked_maps.get(map.channel_pack.a_channel):
                    if image_a := self.safe_load_image(
                        f"{self.bake_path}{self.index}_{id_image_a}.{udim}.{file_format.lower()}"
                    ):
                        alpha_image = image_a

                pack_order = [
                    (rgb_image, (0, 0), (1, 1), (2, 2)),
                    (alpha_image, (0, 3)),
                ]

            dst_array = None
            has_alpha = False

            # Build the packed pixel array
            for pack_item in pack_order:
                src_image = pack_item[0]
                if not src_image:
                    continue

                # Initialize arrays on the first iteration
                if dst_array is None:
                    width, height = src_image.size
                    src_array = numpy.empty(width * height * 4, dtype=numpy.float32)
                    dst_array = numpy.ones(width * height * 4, dtype=numpy.float32)

                assert src_image.size[:] == (width, height), "Images must be same size"

                # Fetch pixels from the source src_image and copy channels
                src_image.pixels.foreach_get(src_array)
                for src_chan, dst_chan in pack_item[1:]:
                    if dst_chan == 3:
                        has_alpha = True
                    dst_array[dst_chan::4] = src_array[src_chan::4]
            dest_image.pixels.foreach_set(dst_array)
            dest_image.pack()
            dest_image.save()

        image.pack()
        image.reload()
        self.baked_maps[map.type] = map.name
        print("QB: Baked Map")
        return image

    def setup_channel_pack(self, context, map: bpy.types.PropertyGroup, channel):
        """Bake Channel Pack Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        """
        if channel is None:
            return
        self.setup_channel_map(context, map, getattr(map.channel_pack, f"{channel}_channel"), channel)

    def bake_channel_pack(self, context, map: bpy.types.PropertyGroup, channel):
        if channel is None:
            return
        self.bake_channel_map(context, map, getattr(map.channel_pack, f"{channel}_channel"), channel)

    def pack_channel_image(self, context, map: bpy.types.PropertyGroup):
        if self.bake_settings.use_auto_udim and len(self.udims) > 1:
            return self.pack_udim_image_channels(context, map)
        else:
            return self.pack_image_channels(context, map)

    def get_operations(self, map: bpy.types.PropertyGroup, channel):
        """Get the operations for the map.

        Args:
            map (bpy.types.PropertyGroup): The type of the map.
            channel (_type_): The channel map type.
        """

        def setup_normal_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    if map.normal.source == "MULTIRES":
                        modifier.show_viewport = True
                        modifier.levels = 0
                        return self.setup_multires_bake(context, map, bake_type="NORMALS")

                    modifier.show_render = map.normal.source == "SHADER_MULTIRES"
                    return func(context, map)

            return func(context, map)

        def bake_normal_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    if map.normal.source == "MULTIRES":
                        modifier.show_viewport = True
                        modifier.levels = 0
                        return self.bake_multires_bake(context, map)

                    modifier.show_render = map.normal.source == "SHADER_MULTIRES"
                    return func(context, map)

            return func(context, map)

        def setup_displacement_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    modifier.show_viewport = True
                    modifier.levels = 0
                    return self.setup_multires_bake(context, map, bake_type="DISPLACEMENT")

            return func(context, map)

        def bake_displacement_multires_helper(context, map, func):
            for modifier in context.object.modifiers:
                if modifier.type == "MULTIRES":
                    modifier.show_viewport = True
                    modifier.levels = 0
                    return self.bake_multires_bake(context, map)

            return func(context, map)

        def combined_helper(context, map, func):
            if not (
                (map.combined.use_pass_direct or map.combined.use_pass_indirect)
                and (
                    map.combined.use_pass_diffuse
                    or map.combined.use_pass_glossy
                    or map.combined.use_pass_transmission
                    or map.combined.use_pass_emit
                )
            ):
                print("QB: Baked Map (Skipped not valid)")
                sys.stdout.flush()
                return
            return func(context, map)

        mapping = {
            # PBR
            "BASE_COLOR": (self.setup_base_color, self.bake_base_color),
            "EMISSION": (self.setup_emission, self.bake_emission),
            "GLOSSINESS": (self.setup_glossiness, self.bake_glossiness),
            "METALLIC": (self.setup_metallic, self.bake_metallic),
            "NORMAL": (
                partial(setup_normal_multires_helper, func=self.setup_normal),
                partial(bake_normal_multires_helper, func=self.bake_normal),
            ),
            "OCCLUSION": (self.setup_occlusion, self.bake_occlusion),
            "ROUGHNESS": (self.setup_roughness, self.bake_roughness),
            "SPECULAR": (self.setup_specular, self.bake_specular),
            "CHANNEL_PACK": (
                partial(self.setup_channel_pack, channel=channel),
                partial(self.bake_channel_pack, channel=channel),
            ),
            # Mesh
            "ALPHA": (self.setup_alpha, self.bake_alpha),
            "BEVEL_NORMAL": (self.setup_bevel_normal, self.bake_bevel_normal),
            "CAVITY": (self.setup_cavity, self.bake_cavity),
            "CURVATURE": (self.setup_curvature, self.bake_curvature),
            "DISPLACEMENT": (
                partial(setup_displacement_multires_helper, func=self.setup_displacement),
                partial(bake_displacement_multires_helper, func=self.bake_displacement),
            ),
            "EDGE": (self.setup_edge, self.bake_edge),
            "GRADIENT": (self.setup_gradient, self.bake_gradient),
            "HEIGHT": (self.setup_height, self.bake_height),
            "MATERIAL_ID": (self.setup_material_id, self.bake_material_id),
            "THICKNESS": (self.setup_thickness, self.bake_thickness),
            "TOON_SHADOW": (self.setup_toon_shadow, self.bake_toon_shadow),
            "VDM": (self.setup_vdm, self.bake_vdm),
            "XYZ": (self.setup_xyz, self.bake_xyz),
            # Principled BSDF
            "IOR": (self.setup_ior, self.bake_ior),
            "SUBSURFACE_WEIGHT": (self.setup_subsurface_weight, self.bake_subsurface_weight),
            "SUBSURFACE_SCALE": (self.setup_subsurface_scale, self.bake_subsurface_scale),
            "SUBSURFACE_IOR": (self.setup_subsurface_ior, self.bake_subsurface_ior),
            "SUBSURFACE_ANISOTROPY": (self.setup_subsurface_anisotropy, self.bake_subsurface_anisotropy),
            "SPECULAR_TINT": (self.setup_specular_tint, self.bake_specular_tint),
            "ANISOTROPIC": (self.setup_anisotropic, self.bake_anisotropic),
            "ANISOTROPIC_ROTATION": (self.setup_anisotropic_rotation, self.bake_anisotropic_rotation),
            "TANGENT": (self.setup_tangent, self.bake_tangent),
            "TRANSMISSION_WEIGHT": (self.setup_transmission_weight, self.bake_transmission_weight),
            "COAT_WEIGHT": (self.setup_coat_weight, self.bake_coat_weight),
            "COAT_ROUGHNESS": (self.setup_coat_roughness, self.bake_coat_roughness),
            "COAT_IOR": (self.setup_coat_ior, self.bake_coat_ior),
            "COAT_TINT": (self.setup_coat_tint, self.bake_coat_tint),
            "COAT_NORMAL": (self.setup_coat_normal, self.bake_coat_normal),
            "SHEEN_WEIGHT": (self.setup_sheen_weight, self.bake_sheen_weight),
            "SHEEN_ROUGHNESS": (self.setup_sheen_roughness, self.bake_sheen_roughness),
            "SHEEN_TINT": (self.setup_sheen_tint, self.bake_sheen_tint),
            "EMISSION_STRENGTH": (self.setup_emission_strength, self.bake_emission_strength),
            # Cycles
            "AO": (self.setup_ambient_occlusion, self.bake_ambient_occlusion),
            "COMBINED": (
                partial(combined_helper, func=self.setup_combined),
                partial(combined_helper, func=self.bake_combined),
            ),
            "DIFFUSE": (self.setup_diffuse, self.bake_diffuse),
            "ENVIRONMENT": (self.setup_environment, self.bake_environment),
            "GLOSSY": (self.setup_glossy, self.bake_glossy),
            "POSITION": (self.setup_position, self.bake_position),
            "SHADOW": (self.setup_shadow, self.bake_shadow),
            "TRANSMISSION": (self.setup_transmission, self.bake_transmission),
            "UV": (self.setup_uv, self.bake_uv),
        }
        return mapping[map.type]

    def bake_map(self, context, map: bpy.types.PropertyGroup, bake_operation):
        if image_id := self.baked_maps.get(map.type) and map.type != "CHANNEL_PACK":
            image = bpy.data.images[image_id]
        else:
            image = bake_operation(context, map)

        if image:
            name = map.name
            if self.bake_settings.use_auto_udim and len(self.udims) > 1:
                name = f"{map.name}.<UDIM>"

            Image.save_image(image=image, path=self.bake_path, name=name)

            print("QB: Baked Map")
            sys.stdout.flush()

    def passthrough_image(
        self,
        image: bpy.types.Image,
        filepath: str,
        map: bpy.types.PointerProperty,  # map.base_color
        map_name: str,
    ):
        """Passthrough image.

        Args:
            image (bpy.types.Image): The image to passthrough.
            filepath (str): The filepath of the image.
            map (bpy.types.PointerProperty): The type of the map.
            map_name (str): The name of the map.
        """
        # Build filename using centralized naming logic from the bake settings
        try:
            batch_name = self.bake_settings.build_filename(bpy.context, bake_group_name=self.bake_group.name.strip(), map_suffix=map.suffix.strip())
        except Exception:
            # Fallback to legacy behaviour if something goes wrong
            batch_name = (
                self.bake_settings.batch_name.replace("$name", self.bake_group.name.strip())
                .replace("$size", self.size_name)
                .replace("$type", map.suffix.strip())
                if getattr(self.bake_settings, "batch_name", None)
                else f"{self.bake_group.name.strip()}_{map.suffix.strip()}"
            )

        source = "TILED" if self.bake_settings.use_auto_udim and len(self.udims) > 1 else "FILE"
        color_space = "sRGB" if image.alpha_mode == "CHANNEL_PACKED" else image.colorspace_settings.name

        print(
            "%s\n"
            % json.dumps(
                {
                    "type": self.TYPE_IMAGE,
                    "active_bake_group_index": self.index,
                    "name": batch_name,
                    "suffix": map.suffix.strip(),
                    "path": filepath,
                    "source": source,
                    "color_space": color_space,
                    "alpha_mode": image.alpha_mode,
                    "map_name": map_name,
                }
            )
        )

        sys.stdout.flush()

    def save_map_image(
        self,
        image: bpy.types.Image,
        map: bpy.types.PointerProperty,  # map.base_color
        map_name: str,  # map.name
        file_format: str = None,
        color_mode: str = "RGB",
    ):
        """Save the map image.

        Args:
            image (bpy.types.Image): The image to save.
            map (bpy.types.PointerProperty): The type of the map.
            map_name (str): The name of the map.
            file_format (str, optional): File format of the image. Defaults to None.
            color_mode (str, optional): Color mode of the image. Defaults to "RGB".
        """
        bake = map.bake if map.custom else self.bake_settings
        self.size_name = (
            f"{bake.width}x{bake.height}"
            if bake.size == "CUSTOM"
            else bpy.types.UILayout.enum_item_name(bake, "size", bake.size)
        )

        if bake.anti_aliasing != "1":
            width, height = image.size[0] // int(bake.anti_aliasing), image.size[1] // int(bake.anti_aliasing)
            image.scale(width=width, height=height)

        self.file_format = file_format or bake.format
        self.color_depth = (
            bake.color_depth_exr
            if self.file_format == "OPEN_EXR"
            else "8"
            if self.file_format in {"TARGA", "WEBP"}
            else bake.color_depth
        )
        self.compression = bake.compression
        self.quality = bake.quality
        self.exr_codec = bake.exr_codec
        self.tiff_codec = bake.tiff_codec

        path = self.bake_path
        if self.bake_settings.folders:
            if path := self.bake_settings.folders[self.bake_settings.folder_index].path:
                if self.bake_settings.use_sub_folder:
                    path = os.path.join(path, self.bake_group.name)
        ## Create the name of the image using the centralized builder
        try:
            name = self.bake_settings.build_filename(bpy.context, bake_group_name=self.bake_group.name.strip(), map_suffix=map.suffix.strip())
        except Exception:
            # Fallback to legacy behaviour if build_filename is unavailable
            name = (
                self.bake_settings.batch_name.replace("$name", self.bake_group.name.strip())
                .replace("$size", self.size_name)
                .replace("$type", map.suffix.strip())
                if getattr(self.bake_settings, "batch_name", None)
                else f"{self.bake_group.name.strip()}_{map.suffix.strip()}"
            )

        if self.bake_settings.use_auto_udim and len(self.udims) > 1:
            name += ".<UDIM>"

        filepath = Image.save_image_as(
            image,
            path=path,
            name=name,
            file_format=self.file_format,
            color_mode=color_mode,
            color_depth=self.color_depth,
            compression=self.compression,
            quality=self.quality,
            exr_codec=self.exr_codec,
            tiff_codec=self.tiff_codec,
            view_transform=bpy.context.scene.view_settings.view_transform,
        )

        self.passthrough_image(image, filepath, map, map_name)

    def save_map(self, context, map: bpy.types.PropertyGroup):
        """Save the map.

        Args:
            map (bpy.types.PropertyGroup): The type of the map.
        """
        map_types = {
            "BASE_COLOR": ("base_color", "RGBA" if map.base_color.use_alpha else "RGB"),
            "EMISSION": ("emission", "RGB"),
            "GLOSSINESS": ("glossiness", "BW"),
            "METALLIC": ("metallic", "BW"),
            "NORMAL": ("normal", "RGB"),
            "OCCLUSION": ("occlusion", "BW"),
            "ROUGHNESS": ("roughness", "BW"),
            "SPECULAR": ("specular", "BW"),
            "CHANNEL_PACK": ("channel_pack", "RGBA"),
            "ALPHA": ("alpha", "BW"),
            "BEVEL_NORMAL": ("bevel_normal", "RGB"),
            "CAVITY": ("cavity", "BW"),
            "CURVATURE": ("curvature", "BW"),
            "DISPLACEMENT": ("displacement", "RGB"),
            "EDGE": ("edge", "BW"),
            "GRADIENT": ("gradient", "RGB"),
            "HEIGHT": ("height", "BW"),
            "MATERIAL_ID": ("material_id", "RGB"),
            "THICKNESS": ("thickness", "BW"),
            "TOON_SHADOW": ("toon_shadow", "BW"),
            "VDM": ("vdm", "RGB"),
            "XYZ": ("xyz", "RGB"),
            "IOR": ("ior", "BW"),
            "SUBSURFACE_WEIGHT": ("subsurface_weight", "BW"),
            "SUBSURFACE_SCALE": ("subsurface_scale", "BW"),
            "SUBSURFACE_IOR": ("subsurface_ior", "BW"),
            "SUBSURFACE_ANISOTROPY": ("subsurface_anisotropy", "BW"),
            "SPECULAR_TINT": ("specular_tint", "RGB"),
            "ANISOTROPIC": ("anisotropic", "BW"),
            "ANISOTROPIC_ROTATION": ("anisotropic_rotation", "BW"),
            "TANGENT": ("tangent", "RGB"),
            "TRANSMISSION_WEIGHT": ("transmission_weight", "BW"),
            "COAT_WEIGHT": ("coat_weight", "BW"),
            "COAT_ROUGHNESS": ("coat_roughness", "BW"),
            "COAT_IOR": ("coat_ior", "BW"),
            "COAT_TINT": ("coat_tint", "RGB"),
            "COAT_NORMAL": ("coat_normal", "RGB"),
            "SHEEN_WEIGHT": ("sheen_weight", "BW"),
            "SHEEN_TINT": ("sheen_tint", "RGB"),
            "SHEEN_ROUGHNESS": ("sheen_roughness", "BW"),
            "EMISSION_STRENGTH": ("emission_strength", "BW"),
            "AO": ("ambient_occlusion", "BW"),
            "COMBINED": ("combined", "RGBA" if map.combined.use_alpha else "RGB"),
            "DIFFUSE": ("diffuse", "RGBA" if map.diffuse.use_alpha else "RGB"),
            "ENVIRONMENT": ("environment", "RGB"),
            "GLOSSY": ("glossy", "RGB"),
            "POSITION": ("position", "RGB"),
            "SHADOW": ("shadow", "BW"),
            "TRANSMISSION": ("transmission", "RGBA" if map.transmission.use_alpha else "RGB"),
            "UV": ("uv", "RGB"),
        }

        map_attr, color_mode = map_types.get(map.type, (None, None))
        if map_attr:
            if map.type == "CHANNEL_PACK":
                image = self.pack_channel_image(context, map)
            else:
                image = Image.get_image(name=self.baked_maps.get(map.type, ""))

            if image:
                self.save_map_image(image=image, map=getattr(map, map_attr), map_name=map.name, color_mode=color_mode)

    def cleanup_baked_maps(self, map: bpy.types.PropertyGroup, channel: str):
        """Cleanup baked maps.

        Args:
            map (bpy.types.PropertyGroup): The type of the map.
            channel (str): The channel of the map.
        """
        map_type = getattr(map.channel_pack, f"{channel}_channel") if channel else map.type
        map_name = f"{map.name}_{channel}" if channel else map.name

        if self.baked_maps.get(map_type) == map_name:
            self.baked_maps.pop(map_type, None)

    def deselect_nodes(self, node_tree: bpy.types.ShaderNodeTree):
        if not node_tree:
            return

        node_tree.nodes.active = None
        for node in node_tree.nodes:
            node.select = False

    def bake_high_to_low(self, context, bake_group: bpy.types.PropertyGroup, maps: list, bake_path: str):
        """Bake high to low.

        Args:
            bake_group (bpy.types.PropertyGroup): Bake group to bake.
            maps (list): Maps to bake.
            bake_path (str): Path to bake to.
        """
        baker = context.scene.qbaker
        self.context = context
        self.bake_group = bake_group
        self.maps = maps
        self.bake_path = bake_path
        self.bake_settings = baker.bake if baker.use_bake_global else bake_group.bake
        self.prepare_render_settings(context)

        # Unhide all collections and objects
        for col in context.scene.collection.children_recursive:
            col.hide_select = col.hide_viewport = col.hide_render = False
            layer_col = Collection.get_layer_collection(collection=col)
            layer_col.exclude = layer_col.hide_viewport = False

        for map, channel in self.maps:
            if not map.use_include or map.type == "WIREFRAME":
                continue

            self.use_clear = True
            setup_operation, bake_operation = self.get_operations(map, channel)
            self.cage_objects = []

            if not self.baked_maps.get(map.type):
                # Check for UDIMs
                self.udims = set()
                for group in self.bake_group.groups:
                    for item in group.low_poly:
                        if item.object:
                            self.udims.update(self.uv_coords_to_udims(self.create_unique_uv_coords(item.object)))
                self.udims = list(self.udims)

                for group in self.bake_group.groups:
                    if not group.use_include:
                        continue

                    # Deselect all objects
                    for obj in context.selected_objects:
                        obj.select_set(False)

                    # Prepare high poly objects
                    for item in group.high_poly:
                        item.object.hide_select = item.object.hide_viewport = item.object.hide_render = False
                        item.object.hide_set(False)
                        item.object.select_set(True)

                        # Check for decals
                        if any("_decal" in child.name.lower() for child in item.object.children):
                            decal_objects = []

                            # Apply modifiers
                            for mod in item.object.modifiers:
                                if mod.type == "MULTIRES":
                                    continue
                                with bpy.context.temp_override(object=item.object):
                                    bpy.ops.object.modifier_apply(modifier=mod.name)

                            # Apply decal modifiers
                            for child in item.object.children:
                                if child.type == "MESH" and "_decal" in child.name.lower():
                                    for mod in child.modifiers:
                                        with bpy.context.temp_override(object=child):
                                            bpy.ops.object.modifier_apply(modifier=mod.name)
                                    decal_objects.append(child)

                            # Join decals to parent object
                            if decal_objects:
                                decal_objects.append(item.object)
                                with context.temp_override(
                                    active_object=item.object, selected_editable_objects=decal_objects
                                ):
                                    bpy.ops.object.join()

                    # Prepare low poly objects
                    for item in group.low_poly:
                        self.ray_distance = item.ray_distance
                        self.uv_layer = item.uv_map

                        if group.use_auto_cage and item.object:
                            self.cage_object = Object.copy_object(
                                obj=item.object, name=f"{item.object.name}_auto_cage", clear_transform=True
                            )
                            # self.cage_object = item.object.copy()
                            # self.cage_object.name = f"{item.object.name}_auto_cage"
                            self.cage_objects.append(self.cage_object)
                            self.cage_object.hide_select = True
                            Object.link_object(obj=self.cage_object, collection=item.object.users_collection[0])
                            Object.parent_object(parent=item.object, child=self.cage_object, copy_transform=False)
                            Modifier.displace(obj=self.cage_object, name="qbaker_cage", strength=item.cage_extrusion)
                        else:
                            self.cage_object = item.cage_object

                        item.object.hide_select = item.object.hide_viewport = item.object.hide_render = False
                        item.object.hide_set(False)
                        item.object.select_set(True)
                        context.view_layer.objects.active = item.object
                        Material.remove_material_slots(obj=item.object)
                        material = Material.get_material(name=f"{item.object.name}_BAKED")
                        Material.set_material(obj=item.object, material=material)
                        self.node_tree = material.node_tree
                        self.deselect_nodes(material.node_tree)
                        self.cleanup_baked_maps(map=map, channel=channel)
                        setup_operation(context, map)

                    self.bake_map(context, map, bake_operation)

                    # for obj in self.cage_objects:
                    #     Object.remove_object(obj=obj)

                    self.cage_objects.clear()
                    self.use_clear = False

            if channel is None:
                self.save_map(context, map)

    def bake_decals(self, context, bake_group: bpy.types.PropertyGroup, maps: list, bake_path: str):
        """Bake decals.

        Args:
            bake_group (bpy.types.PropertyGroup): Bake group to bake.
            maps (list): Maps to bake.
            bake_path (str): Path to bake to.
        """
        baker = context.scene.qbaker
        self.context = context
        self.bake_group = bake_group
        self.maps = maps
        self.bake_path = bake_path
        self.bake_group.use_high_to_low = True
        self.ray_distance = 0.0
        self.uv_layer = ""
        self.bake_settings = baker.bake if baker.use_bake_global else bake_group.bake
        self.prepare_render_settings(context)

        # Unhide all collections and objects
        for col in context.scene.collection.children_recursive:
            col.hide_select = col.hide_viewport = col.hide_render = False
            layer_col = Collection.get_layer_collection(collection=col)
            layer_col.exclude = layer_col.hide_viewport = False

        for map, channel in self.maps:
            if not map.use_include or map.type == "WIREFRAME":
                continue

            self.use_clear = True
            setup_operation, bake_operation = self.get_operations(map, channel)
            self.cage_objects = []

            if not self.baked_maps.get(map.type):
                # Check for UDIMs
                self.udims = set()
                for group in self.bake_group.groups:
                    for item in group.low_poly:
                        if item.object:
                            self.udims.update(self.uv_coords_to_udims(self.create_unique_uv_coords(item.object)))
                self.udims = list(self.udims)

                # Deselect all objects
                for obj in context.selected_objects:
                    obj.select_set(False)

                joined_groups = {}

                for item in self.bake_group.objects:
                    decal_object = Object.copy_object(
                        obj=item.object, name=f"{item.object.name}_high_decal", clear_transform=True
                    )
                    Object.link_object(obj=decal_object, collection=item.object.users_collection[0])
                    decal_objects = [decal_object]

                    for child in item.object.children:
                        if child.type == "MESH" and "_decal" in child.name.lower():
                            for mod in child.modifiers:
                                with context.temp_override(active_object=child):
                                    bpy.ops.object.modifier_apply(modifier=mod.name)
                            decal_objects.append(child)

                    # Join decals to parent object
                    if decal_object and decal_objects:
                        with context.temp_override(active_object=decal_object, selected_editable_objects=decal_objects):
                            bpy.ops.object.join()

                    joined_groups[decal_object] = item.object
                    Material.remove_material_slots(obj=item.object)

                for high_poly, low_poly in joined_groups.items():
                    high_poly.hide_select = high_poly.hide_viewport = high_poly.hide_render = False
                    high_poly.hide_set(False)
                    high_poly.select_set(True)

                    self.cage_object = Object.copy_object(
                        obj=low_poly, name=f"{low_poly.name}_auto_cage", clear_transform=True
                    )
                    # self.cage_object = low_poly.copy()
                    # self.cage_object.name = f"{low_poly.name}_auto_cage"
                    self.cage_objects.append(self.cage_object)
                    self.cage_object.hide_select = True
                    Object.link_object(obj=self.cage_object, collection=low_poly.users_collection[0])
                    Object.parent_object(parent=low_poly, child=self.cage_object, copy_transform=False)
                    Modifier.displace(obj=self.cage_object, name="qbaker_cage", strength=0.05)

                    low_poly.hide_select = low_poly.hide_viewport = low_poly.hide_render = False
                    low_poly.hide_set(False)
                    low_poly.select_set(True)
                    context.view_layer.objects.active = low_poly
                    Material.remove_material_slots(obj=low_poly)
                    material = Material.get_material(name=f"{low_poly.name}_BAKED")
                    Material.set_material(obj=low_poly, material=material)
                    self.node_tree = material.node_tree
                    self.deselect_nodes(material.node_tree)
                    self.cleanup_baked_maps(map=map, channel=channel)
                    setup_operation(context, map)
                    self.bake_map(context, map, bake_operation)

                    for obj in self.cage_objects:
                        Object.remove_object(obj=obj)

                    self.cage_objects.clear()
                    self.use_clear = False

            if channel is None:
                self.save_map(context, map)

    def bake_objects(self, context, bake_group: bpy.types.PropertyGroup, maps: list, bake_path: str):
        """Bake objects.

        Args:
            bake_group (bpy.types.PropertyGroup): Bake group to bake.
            maps (list): Maps to bake.
            bake_path (str): Path to bake to.
        """
        baker = context.scene.qbaker
        self.context = context
        self.bake_group = bake_group
        self.maps = maps
        self.bake_path = bake_path
        self.cage = None
        self.uv_layer = ""
        self.bake_settings = baker.bake if baker.use_bake_global else bake_group.bake
        self.prepare_render_settings(context)

        # Unhide all collections and objects
        for col in context.scene.collection.children_recursive:
            col.hide_select = col.hide_viewport = col.hide_render = False
            layer_col = Collection.get_layer_collection(collection=col)
            layer_col.exclude = layer_col.hide_viewport = False

        # Deselect all objects
        for obj in context.selected_objects:
            obj.select_set(False)

        for map, channel in self.maps:
            if not map.use_include or map.type == "WIREFRAME":
                continue

            self.use_clear = True
            setup_operation, bake_operation = self.get_operations(map, channel)
            need_bake = False

            if self.baked_maps.get(map.type) is None:
                # Check for UDIMs
                self.udims = set()
                for item in self.bake_group.objects:
                    self.udims.update(self.uv_coords_to_udims(self.create_unique_uv_coords(item.object)))
                self.udims = list(self.udims)

                for item in self.bake_group.objects:
                    item.synchronize_material = False
                    item.object.hide_select = item.object.hide_viewport = item.object.hide_render = False
                    item.object.hide_set(False)
                    item.object.select_set(True)
                    context.view_layer.objects.active = item.object

                    if item.object.material_slots:
                        for slot in item.object.material_slots:
                            if slot.material not in [mat.material for mat in item.materials]:
                                index = item.object.data.materials.find(slot.name)
                                if index != -1:
                                    item.object.data.materials[index] = None

                        for slot in item.object.material_slots:
                            if slot.material and slot.material.use_nodes:
                                self.node_tree = slot.material.node_tree
                                self.deselect_nodes(self.node_tree)
                                setup_operation(context, map)
                                need_bake = True
                    else:
                        print("WARNING: Material not found")
                        sys.stdout.flush()
                    item.object.select_set(False)

            if need_bake:
                for item in self.bake_group.objects:
                    item.object.select_set(True)
                self.bake_map(context, map, bake_operation)
                self.use_clear = False
            else:
                print("WARNING: No Material to bake")
                sys.stdout.flush()

            if channel is None:
                self.save_map(context, map)
