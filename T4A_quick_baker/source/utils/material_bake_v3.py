import json
import os
import sys
import time
from functools import partial

import bpy
import numpy

from ...qbpy import Collection, Image, Property, ShaderNode
from .map_v3 import Map
from .udim_bake import Udim


class Bake(Udim, Map):
    baked_maps = {}
    TYPE_IMAGE = 0
    TYPE_RENDER = 1

    def prepare_render_settings(self, context, samples: int = 1, tile_size: int = 2048):
        self.render_settings = {context.scene.render: {}, context.scene.cycles: {}}

        self.render_settings[context.scene.render]["engine"] = context.scene.render.engine
        context.scene.render.engine = "CYCLES"

        if context.scene.cycles.device:
            self.render_settings[context.scene.cycles]["device"] = context.scene.cycles.device
            context.scene.cycles.device = "GPU"

        self.render_settings[context.scene.cycles]["use_adaptive_sampling"] = context.scene.cycles.use_adaptive_sampling
        context.scene.cycles.use_adaptive_sampling = False

        self.render_settings[context.scene.cycles]["samples"] = context.scene.cycles.samples
        context.scene.cycles.samples = samples

        self.render_settings[context.scene.cycles]["use_denoising"] = context.scene.cycles.use_denoising
        context.scene.cycles.use_denoising = False

        self.render_settings[context.scene.cycles]["denoiser"] = context.scene.cycles.denoiser
        context.scene.cycles.denoiser = (
            "OPTIX"
            if bpy.context.preferences.addons["cycles"].preferences.compute_device_type == "CUDA"
            else "OPENIMAGEDENOISE"
        )

        self.render_settings[context.scene.cycles]["denoising_prefilter"] = context.scene.cycles.denoising_prefilter
        context.scene.cycles.denoising_prefilter = "FAST"

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
            use_clear=self.use_clear,
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
        self.prepare_image(context, map, map.emission, alpha=False)
        self.prepare_emission()

    def bake_emission(self, context, map: bpy.types.PropertyGroup):
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

    # Subsurface
    def setup_subsurface(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.subsurface, non_color=non_color)
        self.prepare_subsurface()

    def bake_subsurface(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Subsurface Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface Color
    def setup_subsurface_color(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.subsurface_color, alpha=True)
        self.prepare_subsurface_color()

    def bake_subsurface_color(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Subsurface Color Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Color Map.
        """
        self.bake("EMIT")
        self.restore_color_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface IOR
    def setup_subsurface_ior(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.subsurface_ior, non_color=non_color)
        self.prepare_subsurface_ior()

    def bake_subsurface_ior(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Subsurface IOR Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface IOR Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Subsurface Anisotropy
    def setup_subsurface_anisotropy(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.subsurface_anisotropy, non_color=non_color)
        self.prepare_subsurface_anisotropy()

    def bake_subsurface_anisotropy(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Subsurface Anisotropy Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Subsurface Anisotropy Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Specular Tint
    def setup_specular_tint(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.specular_tint, non_color=non_color)
        self.prepare_specular_tint()

    def bake_specular_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Specular Tint Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Specular Tint Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Anisotropic
    def setup_anisotropic(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.anisotropic, non_color=non_color)
        self.prepare_anisotropic()

    def bake_anisotropic(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Anisotropic Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Anisotropic Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Anisotropic Rotation
    def setup_anisotropic_rotation(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.anisotropic_rotation, non_color=non_color)
        self.prepare_anisotropic_rotation()

    def bake_anisotropic_rotation(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Anisotropic Rotation Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Anisotropic Rotation Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Sheen
    def setup_sheen(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.sheen, non_color=non_color)
        self.prepare_sheen()

    def bake_sheen(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Sheen Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Sheen Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Sheen Tint
    def setup_sheen_tint(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.sheen_tint, non_color=non_color)
        self.prepare_sheen_tint()

    def bake_sheen_tint(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Sheen Tint Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Sheen Tint Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Clearcoat
    def setup_clearcoat(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.clearcoat, non_color=non_color)
        self.prepare_clearcoat()

    def bake_clearcoat(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Clearcoat Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Clearcoat Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Clearcoat Roughness
    def setup_clearcoat_roughness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.clearcoat_roughness, non_color=non_color)
        self.prepare_clearcoat_roughness()

    def bake_clearcoat_roughness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Clearcoat Roughness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Clearcoat Roughness Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # IOR
    def setup_ior(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.ior, non_color=non_color)
        self.prepare_ior()

    def bake_ior(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake IOR Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - IOR Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Transmission Roughness
    def setup_transmission_roughness(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.transmission_roughness, non_color=non_color)
        self.prepare_transmission_roughness()

    def bake_transmission_roughness(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Transmission Roughness Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Transmission Roughness Map.
        """
        self.bake("EMIT")
        self.restore_value_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Emission Strength
    def setup_emission_strength(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.emission_strength, non_color=non_color)
        self.prepare_emission_strength()

    def bake_emission_strength(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        """Bake Emission Strength Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Emission Strength Map.
        """
        self.bake("EMIT")
        self.restore_emission_strength()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Clearcoat Normal
    def setup_clearcoat_normal(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.clearcoat_normal, non_color=non_color)
        self.prepare_clearcoat_normal()

    def bake_clearcoat_normal(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Clearcoat Normal Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Clearcoat Normal Map.
        """
        if map.clearcoat_normal.type == "DIRECTX":
            normal_r = "POS_X"
            normal_g = "NEG_Y"
            normal_b = "POS_Z"
        elif map.clearcoat_normal.type == "OPENGL":
            normal_r = "POS_X"
            normal_g = "POS_Y"
            normal_b = "POS_Z"
        else:
            normal_r = map.clearcoat_normal.r
            normal_g = map.clearcoat_normal.g
            normal_b = map.clearcoat_normal.b

        self.bake(
            "NORMAL",
            normal_space=map.clearcoat_normal.space,
            normal_r=normal_r,
            normal_g=normal_g,
            normal_b=normal_b,
        )
        self.restore_vector_nodes()
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Tangent
    def setup_tangent(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.tangent, non_color=non_color)
        self.prepare_tangent()

    def bake_tangent(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Tangent Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Tangent Map.
        """
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

    ## Cycles

    # Ambient Occlusion
    def setup_ambient_occlusion(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.ambient_occlusion, non_color=non_color)

    def bake_ambient_occlusion(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Ambient Occlusion Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Ambient Occlusion image
        """
        self.bake("AO")
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Combined
    def setup_combined(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.combined, alpha=True)

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

        self.bake("COMBINED", pass_filter)
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Diffuse
    def setup_diffuse(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        self.prepare_image(context, map, map.diffuse, alpha=True)
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

    def bake_shadow(self, context, map: bpy.types.PropertyGroup) -> bpy.types.Image:
        """Bake Shadow Map.

        map (bpy.types.PropertyGroup) - The type of the map.
        return (bpy.types.Image) - Shadow image
        """
        self.bake("SHADOW")
        self.baked_maps[map.type] = map.name
        return bpy.data.images[map.name]

    # Transmission
    def setup_transmission(self, context, map: bpy.types.PropertyGroup, non_color=True) -> bpy.types.Image:
        self.prepare_image(context, map, map.transmission, non_color=non_color)
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
            return func(context, map, non_color=False)

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
            # Map
            "BASE_COLOR": lambda: partial(mapping_helper, channel_map=map.base_color, func=self.setup_base_color),
            "EMISSION": lambda: partial(mapping_helper, channel_map=map.emission, func=self.setup_emission),
            "NORMAL": lambda: partial(mapping_normal_multires_helper, channel_map=map.normal, func=self.setup_normal),
            "CLEARCOAT_NORMAL": lambda: partial(
                mapping_helper_non_color, channel_map=map.clearcoat_normal, func=self.setup_clearcoat_normal
            ),
            "SUBSURFACE_COLOR": lambda: partial(
                mapping_helper, channel_map=map.subsurface_color, func=self.setup_subsurface_color
            ),
            "TANGENT": lambda: partial(mapping_helper_non_color, channel_map=map.tangent, func=self.setup_tangent),
            # Channel
            # PBR
            "DISPLACEMENT": lambda: partial(
                mapping_displacement_multires_helper, channel_map=map.displacement, func=self.setup_displacement
            ),
            "GLOSSINESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.glossiness, func=self.setup_glossiness
            ),
            "METALLIC": lambda: partial(mapping_helper_non_color, channel_map=map.metallic, func=self.setup_metallic),
            "ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.roughness, func=self.setup_roughness
            ),
            "SPECULAR": lambda: partial(mapping_helper_non_color, channel_map=map.specular, func=self.setup_specular),
            # Principled BSDF
            "ALPHA": lambda: partial(mapping_helper_non_color, channel_map=map.alpha, func=self.setup_alpha),
            "SUBSURFACE": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface, func=self.setup_subsurface
            ),
            "SUBSURFACE_IOR": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_ior, func=self.setup_subsurface_ior
            ),
            "SUBSURFACE_ANISOTROPY": lambda: partial(
                mapping_helper_non_color, channel_map=map.subsurface_anisotropy, func=self.setup_subsurface_anisotropy
            ),
            "SPECULAR_TINT": lambda: partial(
                mapping_helper_non_color, channel_map=map.specular_tint, func=self.setup_specular_tint
            ),
            "ANISOTROPIC": lambda: partial(
                mapping_helper_non_color, channel_map=map.anisotropic, func=self.setup_anisotropic
            ),
            "ANISOTROPIC_ROTATION": lambda: partial(
                mapping_helper_non_color, channel_map=map.anisotropic_rotation, func=self.setup_anisotropic_rotation
            ),
            "SHEEN": lambda: partial(mapping_helper_non_color, channel_map=map.sheen, func=self.setup_sheen),
            "SHEEN_TINT": lambda: partial(
                mapping_helper_non_color, channel_map=map.sheen_tint, func=self.setup_sheen_tint
            ),
            "CLEARCOAT": lambda: partial(
                mapping_helper_non_color, channel_map=map.clearcoat, func=self.setup_clearcoat
            ),
            "CLEARCOAT_ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.clearcoat_roughness, func=self.setup_clearcoat_roughness
            ),
            "IOR": lambda: partial(mapping_helper_non_color, channel_map=map.ior, func=self.setup_ior),
            "TRANSMISSION_ROUGHNESS": lambda: partial(
                mapping_helper_non_color, channel_map=map.transmission_roughness, func=self.setup_transmission_roughness
            ),
            "EMISSION_STRENGTH": lambda: partial(
                mapping_helper_non_color, channel_map=map.emission_strength, func=self.setup_emission_strength
            ),
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
            # Map
            "BASE_COLOR": self.bake_base_color,
            "EMISSION": self.bake_emission,
            "NORMAL": partial(normal_multires_helper, func=self.bake_normal),
            "CLEARCOAT_NORMAL": self.bake_clearcoat_normal,
            "SUBSURFACE_COLOR": self.bake_subsurface_color,
            "TANGENT": self.bake_tangent,
            # Channel
            # PBR
            "DISPLACEMENT": partial(displacement_multires_helper, func=self.bake_displacement),
            "GLOSSINESS": self.bake_glossiness,
            "METALLIC": self.bake_metallic,
            "ROUGHNESS": self.bake_roughness,
            "SPECULAR": self.bake_specular,
            # Principled BSDF
            "ALPHA": self.bake_alpha,
            "SUBSURFACE": self.bake_subsurface,
            "SUBSURFACE_IOR": self.bake_subsurface_ior,
            "SUBSURFACE_ANISOTROPY": self.bake_subsurface_anisotropy,
            "SPECULAR_TINT": self.bake_specular_tint,
            "ANISOTROPIC": self.bake_anisotropic,
            "ANISOTROPIC_ROTATION": self.bake_anisotropic_rotation,
            "SHEEN": self.bake_sheen,
            "SHEEN_TINT": self.bake_sheen_tint,
            "CLEARCOAT": self.bake_clearcoat,
            "CLEARCOAT_ROUGHNESS": self.bake_clearcoat_roughness,
            "IOR": self.bake_ior,
            "TRANSMISSION_ROUGHNESS": self.bake_transmission_roughness,
            "EMISSION_STRENGTH": self.bake_emission_strength,
        }
        if func := mapping.get(channel, None):
            channel_image = func(context, map)
        else:
            channel_image = None

        map.name = origin_map_id

        if channel_image:
            name = f"{map.name}_{channel_label}"
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
            "DISPLACEMENT": (
                partial(setup_displacement_multires_helper, func=self.setup_displacement),
                partial(bake_displacement_multires_helper, func=self.bake_displacement),
            ),
            "EMISSION": (self.setup_emission, self.bake_emission),
            "GLOSSINESS": (self.setup_glossiness, self.bake_glossiness),
            "METALLIC": (self.setup_metallic, self.bake_metallic),
            "NORMAL": (
                partial(setup_normal_multires_helper, func=self.setup_normal),
                partial(bake_normal_multires_helper, func=self.bake_normal),
            ),
            "ROUGHNESS": (self.setup_roughness, self.bake_roughness),
            "SPECULAR": (self.setup_specular, self.bake_specular),
            "CHANNEL_PACK": (
                partial(self.setup_channel_pack, channel=channel),
                partial(self.bake_channel_pack, channel=channel),
            ),
            # Principled BSDF
            "ALPHA": (self.setup_alpha, self.bake_alpha),
            "SUBSURFACE": (self.setup_subsurface, self.bake_subsurface),
            "SUBSURFACE_COLOR": (self.setup_subsurface_color, self.bake_subsurface_color),
            "SUBSURFACE_IOR": (self.setup_subsurface_ior, self.bake_subsurface_ior),
            "SUBSURFACE_ANISOTROPY": (self.setup_subsurface_anisotropy, self.bake_subsurface_anisotropy),
            "SPECULAR_TINT": (self.setup_specular_tint, self.bake_specular_tint),
            "ANISOTROPIC": (self.setup_anisotropic, self.bake_anisotropic),
            "ANISOTROPIC_ROTATION": (self.setup_anisotropic_rotation, self.bake_anisotropic_rotation),
            "SHEEN": (self.setup_sheen, self.bake_sheen),
            "SHEEN_TINT": (self.setup_sheen_tint, self.bake_sheen_tint),
            "CLEARCOAT": (self.setup_clearcoat, self.bake_clearcoat),
            "CLEARCOAT_ROUGHNESS": (self.setup_clearcoat_roughness, self.bake_clearcoat_roughness),
            "IOR": (self.setup_ior, self.bake_ior),
            "TRANSMISSION_ROUGHNESS": (self.setup_transmission_roughness, self.bake_transmission_roughness),
            "EMISSION_STRENGTH": (self.setup_emission_strength, self.bake_emission_strength),
            "CLEARCOAT_NORMAL": (self.setup_clearcoat_normal, self.bake_clearcoat_normal),
            "TANGENT": (
                self.setup_tangent,
                self.bake_tangent,
            ),
        }
        return mapping[map.type]

    def bake_map(self, context, map: bpy.types.PropertyGroup, bake_operation):
        if image_id := self.baked_maps.get(map.type) and map.type != "CHANNEL_PACK":
            image = bpy.data.images[image_id]
        else:
            image = bake_operation(context, map)

        if image:
            Image.save_image(image=image, path=self.bake_path, name=map.name)

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
        try:
            batch_name = self.bake_settings.build_filename(
                bpy.context,
                bake_group_name=self.active_material.material.name.strip(),
                map_suffix=map.suffix.strip(),
                extra_tokens={"material": self.active_material.material.name.strip()},
            )
        except Exception:
            # Fallback: simple default name to avoid chained .replace usage
            batch_name = f"{self.active_material.material.name.strip()}_{map.suffix.strip()}"

        source = "FILE"
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
                    # Determine folder name according to naming_name_source
                    folder_name = self.active_material.material.name
                    try:
                        name_source = getattr(self.bake_settings, "naming_name_source", "BAKEGROUP")
                    except Exception:
                        name_source = "BAKEGROUP"

                    if name_source == "OBJECT":
                        obj_name = None
                        for obj in bpy.data.objects:
                            if obj.type == "MESH":
                                for slot in getattr(obj, "material_slots", []):
                                    if slot and slot.material is self.active_material.material:
                                        obj_name = obj.name
                                        break
                                if obj_name:
                                    break
                        folder_name = obj_name or self.active_material.material.name
                    elif name_source == "MATERIAL":
                        folder_name = self.active_material.material.name
                    else:
                        folder_name = self.active_material.material.name

                    path = os.path.join(path, folder_name)

        extra = {"material": self.active_material.material.name.strip()}
        try:
            name_source = getattr(self.bake_settings, "naming_name_source", "BAKEGROUP")
        except Exception:
            name_source = "BAKEGROUP"
        if name_source == "OBJECT":
            for obj in bpy.data.objects:
                if obj.type == "MESH":
                    for slot in getattr(obj, "material_slots", []):
                        if slot and slot.material is self.active_material.material:
                            extra["object"] = obj.name
                            break
                    if "object" in extra:
                        break

        try:
            name = self.bake_settings.build_filename(
                bpy.context,
                bake_group_name=self.active_material.material.name.strip(),
                map_suffix=map.suffix.strip(),
                extra_tokens=extra,
            )
        except Exception:
            # Fallback: simple default name to avoid chained .replace usage
            name = f"{self.active_material.material.name.strip()}_{map.suffix.strip()}"

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
        # PBR
        map_types = {
            # PBR
            "BASE_COLOR": ("base_color", "RGBA" if map.base_color.use_alpha else "RGB"),
            "DISPLACEMENT": ("displacement", "RGB"),
            "EMISSION": ("emission", "RGB"),
            "GLOSSINESS": ("glossiness", "BW"),
            "METALLIC": ("metallic", "BW"),
            "NORMAL": ("normal", "RGB"),
            "ROUGHNESS": ("roughness", "BW"),
            "SPECULAR": ("specular", "BW"),
            "CHANNEL_PACK": ("channel_pack", "RGBA"),
            # Principled BSDF
            "ALPHA": ("alpha", "BW"),
            "SUBSURFACE": ("subsurface", "BW"),
            "SUBSURFACE_COLOR": ("subsurface_color", "RGB"),
            "SUBSURFACE_IOR": ("subsurface_ior", "BW"),
            "SUBSURFACE_ANISOTROPY": ("subsurface_anisotropy", "BW"),
            "SPECULAR_TINT": ("specular_tint", "RGB"),
            "ANISOTROPIC": ("anisotropic", "BW"),
            "ANISOTROPIC_ROTATION": ("anisotropic_rotation", "BW"),
            "SHEEN": ("sheen", "BW"),
            "SHEEN_TINT": ("sheen_tint", "RGB"),
            "CLEARCOAT": ("clearcoat", "BW"),
            "CLEARCOAT_ROUGHNESS": ("clearcoat_roughness", "BW"),
            "IOR": ("ior", "BW"),
            "TRANSMISSION_ROUGHNESS": ("transmission_roughness", "BW"),
            "EMISSION_STRENGTH": ("emission_strength", "BW"),
            "CLEARCOAT_NORMAL": ("clearcoat_normal", "RGB"),
            "TANGENT": ("tangent", "RGB"),
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

    def bake_materials(self, context, active_material: bpy.types.PropertyGroup, maps: list, bake_path: str):
        """Bake materials.

        Args:
            active_material (bpy.types.PropertyGroup) - The active material to bake.
            maps (list): Maps to bake.
            bake_path (str): Path to bake to.
        """
        material_baker = context.scene.qbaker.material_baker
        self.bake_path = bake_path
        self.cage = None
        self.active_material = active_material
        self.maps = maps
        self.bake_settings = material_baker.bake if material_baker.use_bake_global else self.active_material.bake
        self.prepare_render_settings(context)
        self.context = context

        for col in context.scene.collection.children_recursive:
            col.hide_select = False
            col.hide_viewport = False
            col.hide_render = False
            layer_col = Collection.get_layer_collection(collection=col)
            layer_col.exclude = False
            layer_col.hide_viewport = False

        plane_object = bpy.data.objects.get("Plane")

        for map, channel in self.maps:
            if not map.use_include:
                continue

            self.use_clear = True
            setup_operation, bake_operation = self.get_operations(map, channel)
            need_bake = False

            if self.baked_maps.get(map.type) is None:
                context.view_layer.objects.active = plane_object

                if plane_object.data.materials:
                    plane_object.data.materials[0] = self.active_material.material
                else:
                    plane_object.data.materials.append(self.active_material.material)

                self.node_tree = self.active_material.material.node_tree
                self.deselect_nodes(self.node_tree)
                setup_operation(context, map)
                need_bake = True

            if need_bake:
                self.bake_map(context, map, bake_operation)
                self.use_clear = False

            if channel is not None:
                continue

            self.save_map(context, map)
