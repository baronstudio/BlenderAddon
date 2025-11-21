import os
import datetime

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup

from .bake_group import extrude_cage, remove_cages
from .preview import QBAKER_map_preview


class QBAKER_PG_bake_settings(PropertyGroup):
    size: EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("512", "512", "512x512 px"),
            ("1024", "1K", "1024x1024 px"),
            ("2048", "2K", "2048x2048 px"),
            ("4096", "4K", "4096x4096 px"),
            ("8192", "8K", "8192x8192 px"),
            ("CUSTOM", "Custom", "Custom bake size"),
        ),
        default="1024",
    )

    width: IntProperty(
        name="Width",
        description="Number of horizontal pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    height: IntProperty(
        name="Height",
        description="Number of vertical pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    anti_aliasing: EnumProperty(
        name="Anti-Aliasing",
        description="Super-sampling level for anti-aliasing",
        items=(
            ("1", "None", "No anti-aliasing"),
            ("2", "2x", "2x samples"),
            ("4", "4x", "4x samples"),
            ("8", "8x", "8x samples"),
            ("16", "16x", "16x samples"),
        ),
        default="1",
    )

    format: EnumProperty(
        name="Format",
        description="File format to save the rendered images as",
        items=(
            ("PNG", "PNG", "Output image in PNG format"),
            ("JPEG", "JPEG", "Output image in JPEG format"),
            ("TARGA", "Targa", "Output image in Targa format"),
            ("TIFF", "TIFF", "Output image in TIFF format"),
            ("OPEN_EXR", "OpenEXR", "Output image in OpenEXR format"),
            ("HDR", "Radiance HDR", "Output image in Radiance HDR format"),
            ("WEBP", "WebP", "Output image in WebP format"),
        ),
        default="PNG",
    )

    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("8", "8", "8-bit color channels"),
            ("16", "16", "16-bit color channels"),
        ),
    )

    color_depth_exr: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("16", "16", "16-bit color channels"),
            ("32", "32", "32-bit color channels"),
        ),
        default="32",
    )

    compression: IntProperty(
        name="Compression",
        description="Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=15,
    )

    quality: IntProperty(
        name="Quality",
        description="Quality for image formats that support lossy compression",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=90,
    )

    exr_codec: EnumProperty(
        name="Codec",
        description="Codec settings for OpenEXR",
        items=(
            ("NONE", "None", ""),
            ("PXR24", "Pxr24 (lossy)", ""),
            ("ZIP", "ZIP (lossless)", ""),
            ("PIZ", "PIZ (lossless)", ""),
            ("RLE", "RLE (lossless)", ""),
            ("ZIPS", "ZIPS (lossless)", ""),
            ("B44", "B44 (lossy)", ""),
            ("B44A", "B44A (lossy)", ""),
            ("DWAA", "DWAA (lossy)", ""),
            ("DWAB", "DWAB (lossy)", ""),
        ),
        default="ZIP",
    )

    tiff_codec: EnumProperty(
        name="Compression",
        description="Compression mode for TIFF",
        items=(
            ("NONE", "None", ""),
            ("DEFLATE", "Deflate", ""),
            ("LZW", "LZW", ""),
            ("PACKBITS", "Pack Bits", ""),
        ),
        default="DEFLATE",
    )

    def draw(self, context, layout):
        layout.use_property_split = True
        col = layout.column()

        subcol = col.column(align=True)
        subcol.prop(self, "size")
        if self.size == "CUSTOM":
            subcol.prop(self, "width")
            subcol.prop(self, "height")

        col.prop(self, "format")
        col.prop(self, "anti_aliasing")

        if self.format in {"PNG", "TIFF"}:
            row = col.row(align=True)
            row.prop(self, "color_depth", expand=True)
            if self.format in {"TIFF"}:
                col.prop(self, "tiff_codec")

        if self.format in {"OPEN_EXR"}:
            row = col.row(align=True)
            row.prop(self, "color_depth_exr", expand=True)
            col.prop(self, "exr_codec")

        if self.format in {"PNG"}:
            col.prop(self, "compression")

        if self.format in {"JPEG", "WEBP"}:
            col.prop(self, "quality")


class QBakerPropertyGroup(PropertyGroup):
    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=1,
    )

    denoise: BoolProperty(
        name="Denoise",
        description="Denoise the baked map",
        default=False,
    )

    custom: BoolProperty(
        name="Custom",
        description="Custom bake settings",
    )

    bake: PointerProperty(type=QBAKER_PG_bake_settings)

    image: PointerProperty(
        name="Image",
        description="Bake into the existing image",
        type=bpy.types.Image,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            box = layout.box()
            self.bake.draw(context, layout=box)
            if self.image:
                box.prop(self, "image")
            else:
                box.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


# PBR


class QBAKER_PG_base_color(QBakerPropertyGroup):
    only_local = False  # only as a placeholder

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Color",
    )

    use_alpha: BoolProperty(
        name="Alpha",
        description="Bake alpha channel",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "use_alpha")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            box = layout.box()
            self.bake.draw(context, layout=box)
            if self.image:
                box.prop(self, "image")
            else:
                box.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_emission(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Emission",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    non_color: BoolProperty(
        name="32-bit Float",
        description="Create image with 32-bit floating-point bit depth",
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "non_color")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            box = layout.box()
            self.bake.draw(context, layout=box)
            if self.image:
                box.prop(self, "image")
            else:
                box.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "non_color")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_glossiness(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Glossiness",
    )


class QBAKER_PG_metallic(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Metallic",
    )


class QBAKER_PG_normal(QBakerPropertyGroup):
    suffix_mapping = {
        "OPENGL": "NormalGL",
        "DIRECTX": "NormalDX",
        "CUSTOM": "Normal",
    }

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="NormalGL",
    )

    def update_suffix(self, context):
        self.suffix = f"{self.suffix_mapping[self.type]}"

    space: EnumProperty(
        name="Space",
        description="Choose normal space for baking",
        items=(
            ("TANGENT", "Tangent", "Bake the normals in tangent space"),
            ("OBJECT", "Object", "Bake the normals in object space"),
        ),
    )

    type: EnumProperty(
        name="Type",
        description="Normal type",
        items=(
            ("OPENGL", "OpenGL", "Unity Engine"),
            ("DIRECTX", "DirectX", "Unreal Engine"),
            ("CUSTOM", "Custom", ""),
        ),
        update=update_suffix,
    )

    r: EnumProperty(
        name="R",
        description="Axis to bake in red channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    g: EnumProperty(
        name="G",
        description="Axis to bake in green channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    b: EnumProperty(
        name="B",
        description="Axis to bake in blue channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    source: EnumProperty(
        name="Source",
        description="Source of normal information",
        items=(
            ("SHADER", "Shader", "Bake the normals from the shader"),
            ("MULTIRES", "Multires", "Bake the normals from the multires modifier"),
            ("SHADER_MULTIRES", "Shader and Multires", "Bake the normals from both the shader and multires modifier"),
        ),
        default="SHADER",
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "source")
        subcol = col.column()
        subcol.active = self.source in {"SHADER", "SHADER_MULTIRES"}
        subcol.prop(self, "space")
        subcol.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column()
        col.prop(self, "samples")
        subcol = col.column(align=True)
        subcol.prop(self, "denoise")
        subcol.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "source")
        subcol = col.column()
        subcol.active = self.source in {"SHADER", "SHADER_MULTIRES"}
        subcol.prop(self, "space")
        subcol.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_occlusion(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.occlusion_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Occlusion",
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
        update=QBAKER_map_preview.occlusion_preview,
    )

    distance: FloatProperty(
        name="Distance",
        description="Ambient occlusion distance",
        min=0.1,
        soft_max=1,
        step=0.1,
        default=0.5,
        update=QBAKER_map_preview.occlusion_preview,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself when computing AO",
        default=True,
        update=QBAKER_map_preview.occlusion_preview,
    )

    invert_ao: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.occlusion_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "distance")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "only_local")
        col.prop(self, "invert_ao")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "distance")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "only_local")
        col.prop(self, "invert_ao")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_roughness(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Roughness",
    )


class QBAKER_PG_specular(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Specular",
    )


# Mesh


class QBAKER_PG_alpha(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Alpha",
    )


class QBAKER_PG_bevel_normal(QBakerPropertyGroup):
    suffix_mapping = {
        "OPENGL": "Bevel_NormalGL",
        "DIRECTX": "Bevel_NormalDX",
        "CUSTOM": "Bevel_Normal",
    }

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Bevel_NormalGL",
    )

    def update_suffix(self, context):
        self.suffix = f"{self.suffix_mapping[self.type]}"

    space: EnumProperty(
        name="Space",
        description="Choose normal space for baking",
        items=(
            ("TANGENT", "Tangent", "Bake the normals in tangent space"),
            ("OBJECT", "Object", "Bake the normals in object space"),
        ),
    )

    type: EnumProperty(
        name="Type",
        description="Normal type",
        items=(
            ("OPENGL", "OpenGL", "Unity Engine"),
            ("DIRECTX", "DirectX", "Unreal Engine"),
            ("CUSTOM", "Custom", ""),
        ),
        update=update_suffix,
    )

    r: EnumProperty(
        name="R",
        description="Axis to bake in red channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    g: EnumProperty(
        name="G",
        description="Axis to bake in green channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    b: EnumProperty(
        name="B",
        description="Axis to bake in blue channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    radius: FloatProperty(
        name="Radius",
        description="Bevel normal radius",
        min=0.01,
        soft_max=1,
        step=0.1,
        default=0.01,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column()
        col.prop(self, "radius")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_cavity(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.cavity_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Cavity",
    )

    power: FloatProperty(
        name="Power",
        description="Cavity power",
        min=1,
        soft_max=2,
        step=0.1,
        default=1,
        update=QBAKER_map_preview.cavity_preview,
    )

    invert_cavity: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.cavity_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "power")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_cavity")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "power")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_cavity")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_curvature(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.curvature_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Curvature",
    )

    power: FloatProperty(
        name="Power",
        description="Curvature power",
        min=1,
        soft_max=2,
        step=0.1,
        default=1,
        update=QBAKER_map_preview.curvature_preview,
    )

    invert_curvature: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.curvature_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "power")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_curvature")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "power")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_curvature")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_displacement(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Displacement",
    )

    invert_displacement: BoolProperty(
        name="Invert",
        description="Invert map",
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_displacement")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_displacement")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_edge(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.edge_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Edge",
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
        update=QBAKER_map_preview.edge_preview,
    )

    radius: FloatProperty(
        name="Radius",
        description="Edge radius",
        min=0.01,
        soft_max=1,
        step=0.1,
        default=0.1,
        update=QBAKER_map_preview.edge_preview,
    )

    invert_edge: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.edge_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "radius")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_edge")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "radius")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_edge")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_gradient(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.gradient_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Gradient_XYZ",
    )

    direction: EnumProperty(
        name="Direction",
        description="Gradient direction",
        items=(
            ("XYZ", "XYZ", "Red channel is X\nGreen channel is Y\nBlue channel is Z"),
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", ""),
        ),
        default="XYZ",
        update=QBAKER_map_preview.gradient_preview,
    )

    invert_gradient: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.gradient_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "direction", expand=True)
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_gradient")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "direction", expand=True)
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_gradient")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_height(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.heightmap_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Heightmap",
    )

    type: EnumProperty(
        name="Type",
        description="Heightmap type",
        items=(
            ("DISPLACEMENT", "Displacement", "Heightmap based on displacement"),
            ("NORMAL", "Normal", "Heightmap based on normal"),
        ),
        update=QBAKER_map_preview.heightmap_preview,
    )

    invert_height: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.heightmap_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "type")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_height")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "samples")
        col.prop(self, "type")
        col = layout.column(align=True)
        col.prop(self, "invert_height")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_material_id(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Material_ID",
    )

    type: EnumProperty(
        name="Type",
        description="Type of Material ID map",
        items=(
            ("MATERIAL", "Material", "Material ID map based on materials"),
            ("OBJECT", "Object", "Material ID map based on objects"),
            ("VERTEX_COLOR", "Vertex Color", "Material ID map based on vertex colors"),
        ),
    )

    def get_color_attributes(self, context):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        vertex_colors = {}

        if bake_group.use_high_to_low:
            for group in bake_group.groups:
                if group.high_poly:
                    for item in group.high_poly:
                        for attribute in item.object.data.color_attributes:
                            vertex_colors.setdefault(attribute.name, (attribute.name, attribute.name, ""))
            return list(vertex_colors.values()) + [("None", "None", "")]

        for item in bake_group.objects:
            for attribute in item.object.data.color_attributes:
                vertex_colors.setdefault(attribute.name, (attribute.name, attribute.name, ""))
        return list(vertex_colors.values()) + [("None", "None", "")]

    def update_color_attributes(self, context):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.use_high_to_low and bake_group.groups:
            for group in bake_group.groups:
                if group.high_poly:
                    for item in group.high_poly:
                        if attribute := item.object.data.color_attributes.get(self.group_color_attribute):
                            item.object.data.color_attributes.active_color = attribute

        elif not bake_group.use_high_to_low and bake_group.objects:
            for item in bake_group.objects:
                if attribute := item.object.data.color_attributes.get(self.object_color_attribute):
                    item.object.data.color_attributes.active_color = attribute

    group_color_attribute: EnumProperty(
        name="Color Attribute",
        description="Select the vertex color attribute",
        items=get_color_attributes,
        update=update_color_attributes,
    )

    object_color_attribute: EnumProperty(
        name="Color Attribute",
        description="Select the vertex color attribute",
        items=get_color_attributes,
        update=update_color_attributes,
    )

    def draw(self, context, layout):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "type")
        if self.type == "VERTEX_COLOR":
            if bake_group.use_high_to_low:
                col.prop(self, "group_color_attribute")
            else:
                col.prop(self, "object_color_attribute")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        col = layout.column()
        col.prop(self, "type")
        if self.type == "VERTEX_COLOR":
            if bake_group.use_high_to_low:
                col.prop(self, "group_color_attribute")
            else:
                col.prop(self, "object_color_attribute")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_thickness(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.thickness_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Thickness",
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
        update=QBAKER_map_preview.thickness_preview,
    )

    distance: FloatProperty(
        name="Distance",
        description="Thickness distance",
        min=0.1,
        soft_max=1,
        step=0.1,
        default=0.5,
        update=QBAKER_map_preview.thickness_preview,
    )

    invert_thickness: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.thickness_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "distance")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_thickness")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "distance")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_thickness")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_toon_shadow(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.toon_shadow_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Toon_Shadow",
    )

    size: FloatProperty(
        name="Size",
        description="Size of the toon shadow",
        soft_min=0.0,
        soft_max=1.0,
        default=0.5,
        update=QBAKER_map_preview.toon_shadow_preview,
    )

    smooth: FloatProperty(
        name="Smooth",
        description="Smoothness of the toon shadow",
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        update=QBAKER_map_preview.toon_shadow_preview,
    )

    use_pass_direct: BoolProperty(
        name="Direct",
        description="Add direct lighting contribution",
        default=True,
    )

    use_pass_indirect: BoolProperty(
        name="Indirect",
        description="Add indirect lighting contribution",
        default=False,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself when computing toon shadow",
        default=True,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=128,
        update=QBAKER_map_preview.toon_shadow_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "size")
        col.prop(self, "smooth")
        col = layout.column(heading="Lighting", align=True)
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "only_local")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column(heading="Lighting", align=True)
        col.prop(self, "suffix")
        col.prop(self, "size")
        col.prop(self, "smooth")
        col = layout.column(heading="Lighting", align=True)
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "only_local")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_vdm(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="VDM",
    )


class QBAKER_PG_wireframe(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Wireframe",
    )

    size: EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("512", "512", "512x512 px"),
            ("1024", "1K", "1024x1024 px"),
            ("2048", "2K", "2048x2048 px"),
            ("4096", "4K", "4096x4096 px"),
        ),
        default="1024",
    )

    width: IntProperty(
        name="Width",
        description="Number of horizontal pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    height: IntProperty(
        name="Height",
        description="Number of vertical pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    format: EnumProperty(
        name="Format",
        description="File format to export the UV layout to",
        items=(
            ("PNG", "PNG", "Export the UV layout to a bitmap image (.png)"),
            ("SVG", "SVG", "Export the UV layout to a vector SVG file (.svg)"),
        ),
        default="PNG",
    )

    export_tiles: EnumProperty(
        name="Export Tiles",
        description="Choose whether to export only the [0, 1] range, or all UV tiles",
        items=(
            ("NONE", "None", "Export only UVs in the [0, 1] range"),
            ("UDIM", "UDIM", "Export tiles in the UDIM numbering scheme: 1001 + u_tile + 10*v_tile"),
            ("UV", "UVTILE", "Export tiles in the UVTILE numbering scheme: u(u_tile + 1)_v(v_tile + 1)"),
        ),
    )

    face_color: FloatVectorProperty(
        name="Face Color",
        description="Color for UV faces",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.8, 0.8, 0.8, 1.0),
    )

    line_color: FloatVectorProperty(
        name="Line Color",
        description="Color for UV lines",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.0, 0.0, 0.0, 1.0),
    )

    line_width: FloatProperty(
        name="Line Width",
        description="Line width for UV lines",
        min=0.1,
        soft_max=1.0,
        default=1,
    )

    export_all: BoolProperty(
        name="All UVs",
        description="Export all UVs in this mesh (not just visible ones)",
        default=False,
    )

    modified: BoolProperty(
        name="Modified",
        description="Exports UVs from the modified mesh",
        default=False,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "size")
        col.prop(self, "format")
        col.prop(self, "export_tiles")
        col.prop(self, "face_color")

        if self.format != "SVG":
            col.prop(self, "line_color")

        col.prop(self, "line_width")

        col = layout.column(align=True)
        col.prop(self, "export_all")
        col.prop(self, "modified")


class QBAKER_PG_xyz(QBakerPropertyGroup, QBAKER_map_preview):
    use_preview: BoolProperty(
        name="Preview",
        description="Works with cycles engine",
        update=QBAKER_map_preview.xyz_preview,
    )

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="XYZ",
    )

    direction: EnumProperty(
        name="Direction",
        description="XYZ mask direction",
        items=(
            ("XYZ", "XYZ", "Red channel is X\nGreen channel is Y\nBlue channel is Z"),
            ("X", "X", ""),
            ("Y", "Y", ""),
            ("Z", "Z", ""),
        ),
        default="XYZ",
        update=QBAKER_map_preview.xyz_preview,
    )

    invert_xyz: BoolProperty(
        name="Invert",
        description="Invert map",
        update=QBAKER_map_preview.xyz_preview,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "direction", expand=True)
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_xyz")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "direction", expand=True)
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "invert_xyz")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


# Principled BSDF


# IOR
class QBAKER_PG_ior(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="IOR",
    )


# Subsurface
class QBAKER_PG_subsurface_weight(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Subsurface_Weight",
    )


class QBAKER_PG_subsurface_scale(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Subsurface_Scale",
    )


class QBAKER_PG_subsurface_ior(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Subsurface_IOR",
    )


class QBAKER_PG_subsurface_anisotropy(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Subsurface_Anisotropy",
    )


# Specular


class QBAKER_PG_specular_tint(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Specular_Tint",
    )


class QBAKER_PG_anisotropic(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Anisotropic",
    )


class QBAKER_PG_anisotropic_rotation(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Anisotropic_Rotation",
    )


class QBAKER_PG_tangent(QBakerPropertyGroup):
    suffix_mapping = {
        "OPENGL": "TangentGL",
        "DIRECTX": "TangentDX",
        "CUSTOM": "Tangent",
    }

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="TangentGL",
    )

    def update_suffix(self, context):
        self.suffix = f"{self.suffix_mapping[self.type]}"

    space: EnumProperty(
        name="Space",
        description="Choose normal space for baking",
        items=(
            ("TANGENT", "Tangent", "Bake the normals in tangent space"),
            ("OBJECT", "Object", "Bake the normals in object space"),
        ),
    )

    type: EnumProperty(
        name="Type",
        description="Normal type",
        items=(
            ("OPENGL", "OpenGL", "Unity Engine"),
            ("DIRECTX", "DirectX", "Unreal Engine"),
            ("CUSTOM", "Custom", ""),
        ),
        update=update_suffix,
    )

    r: EnumProperty(
        name="R",
        description="Axis to bake in red channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    g: EnumProperty(
        name="G",
        description="Axis to bake in green channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    b: EnumProperty(
        name="B",
        description="Axis to bake in blue channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


# Transmission


class QBAKER_PG_transmission_weight(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Transmission_Weight",
    )


# Coat


class QBAKER_PG_coat_weight(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Coat_Weight",
    )


class QBAKER_PG_coat_roughness(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Coat_Roughness",
    )


class QBAKER_PG_coat_ior(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Coat_IOR",
    )


class QBAKER_PG_coat_tint(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Coat_Tint",
    )


class QBAKER_PG_coat_normal(QBakerPropertyGroup):
    suffix_mapping = {
        "OPENGL": "Coat_NormalGL",
        "DIRECTX": "Coat_NormalDX",
        "CUSTOM": "Coat_Normal",
    }

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Coat_NormalGL",
    )

    def update_suffix(self, context):
        self.suffix = f"{self.suffix_mapping[self.type]}"

    space: EnumProperty(
        name="Space",
        description="Choose normal space for baking",
        items=(
            ("TANGENT", "Tangent", "Bake the normals in tangent space"),
            ("OBJECT", "Object", "Bake the normals in object space"),
        ),
    )

    type: EnumProperty(
        name="Type",
        description="Normal type",
        items=(
            ("OPENGL", "OpenGL", "Unity Engine"),
            ("DIRECTX", "DirectX", "Unreal Engine"),
            ("CUSTOM", "Custom", ""),
        ),
        update=update_suffix,
    )

    r: EnumProperty(
        name="R",
        description="Axis to bake in red channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    g: EnumProperty(
        name="G",
        description="Axis to bake in green channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    b: EnumProperty(
        name="B",
        description="Axis to bake in blue channel",
        items=(
            ("POS_X", "+X", ""),
            ("POS_Y", "+Y", ""),
            ("POS_Z", "+Z", ""),
            ("NEG_X", "-X", ""),
            ("NEG_Y", "-Y", ""),
            ("NEG_Z", "-Z", ""),
        ),
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "space")
        col.prop(self, "type")
        if self.type == "CUSTOM":
            col = col.column(align=True)
            col.prop(self, "r")
            col.prop(self, "g")
            col.prop(self, "b")
        col = layout.column(align=True)
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


# Sheen


class QBAKER_PG_sheen_weight(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Sheen_Weight",
    )


class QBAKER_PG_sheen_roughness(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Sheen_Roughness",
    )


class QBAKER_PG_sheen_tint(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Sheen_Tint",
    )


# Emission


class QBAKER_PG_emission_strength(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Emission_Strength",
    )


# Cycles


class QBAKER_PG_ambient_occlusion(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Ambient_Occlusion",
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself when computing AO",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "only_local")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            box = layout.box()
            self.bake.draw(context, layout=box)
            if self.image:
                box.prop(self, "image")
            else:
                box.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "only_local")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_combined(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Combined",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    use_pass_direct: BoolProperty(
        name="Direct",
        description="Add direct lighting contribution",
        default=True,
    )

    use_pass_indirect: BoolProperty(
        name="Indirect",
        description="Add indirect lighting contribution",
        default=True,
    )

    use_pass_diffuse: BoolProperty(
        name="Diffuse",
        description="Add diffuse contribution",
        default=True,
    )

    use_pass_glossy: BoolProperty(
        name="Glossy",
        description="Add glossy contribution",
        default=True,
    )

    use_pass_transmission: BoolProperty(
        name="Transmission",
        description="Add transmision contribution",
        default=True,
    )

    use_pass_emit: BoolProperty(
        name="Emit",
        description="Add emission contribution",
        default=True,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=128,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself",
        default=True,
    )

    use_alpha: BoolProperty(
        name="Alpha",
        description="Bake alpha channel",
        default=True,
    )

    non_color: BoolProperty(
        name="32-bit Float",
        description="Create image with 32-bit floating-point bit depth",
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col = layout.column(heading="Lighting", align=True)
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col = layout.column(heading="Contributions", align=True)
        col.enabled = self.use_pass_direct or self.use_pass_indirect
        col.prop(self, "use_pass_diffuse")
        col.prop(self, "use_pass_glossy")
        col.prop(self, "use_pass_transmission")
        col.prop(self, "use_pass_emit")
        col.prop(self, "only_local")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "use_alpha")
        col.prop(self, "non_color")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column(heading="Lighting", align=True)
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col = layout.column(heading="Contributions", align=True)
        col.enabled = self.use_pass_direct or self.use_pass_indirect
        col.prop(self, "use_pass_diffuse")
        col.prop(self, "use_pass_glossy")
        col.prop(self, "use_pass_transmission")
        col.prop(self, "use_pass_emit")
        col.prop(self, "only_local")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "non_color")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_diffuse(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Diffuse",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    use_pass_direct: BoolProperty(
        name="Direct",
        description="Add direct lighting contribution",
        default=True,
    )

    use_pass_indirect: BoolProperty(
        name="Indirect",
        description="Add indirect lighting contribution",
        default=True,
    )

    use_pass_color: BoolProperty(
        name="Color",
        description="Color the pass",
        default=True,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself",
        default=True,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
    )

    use_alpha: BoolProperty(
        name="Alpha",
        description="Bake alpha channel",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col.prop(self, "only_local")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "use_alpha")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col.prop(self, "only_local")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_environment(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Environment",
    )


class QBAKER_PG_glossy(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Glossy",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    use_pass_direct: BoolProperty(
        name="Direct",
        description="Add direct lighting contribution",
        default=True,
    )

    use_pass_indirect: BoolProperty(
        name="Indirect",
        description="Add indirect lighting contribution",
        default=True,
    )

    use_pass_color: BoolProperty(
        name="Color",
        description="Color the pass",
        default=True,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_position(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Position",
    )


class QBAKER_PG_shadow(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Shadow",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
    )

    only_local: BoolProperty(
        name="Only Local",
        description="Only consider the object itself",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "only_local")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col.prop(self, "only_local")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_transmission(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="Transmission",
    )

    view_from: EnumProperty(
        name="View From",
        description="Source of reflection ray directions",
        items=(
            ("ABOVE_SURFACE", "Above Surface", "Cast rays from above the surface"),
            ("ACTIVE_CAMERA", "Active Camera", "Use the active camera's position to cast rays"),
        ),
    )

    use_pass_direct: BoolProperty(
        name="Direct",
        description="Add direct lighting contribution",
        default=True,
    )

    use_pass_indirect: BoolProperty(
        name="Indirect",
        description="Add indirect lighting contribution",
        default=True,
    )

    use_pass_color: BoolProperty(
        name="Color",
        description="Color the pass",
        default=True,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=10,
    )

    use_alpha: BoolProperty(
        name="Alpha",
        description="Bake alpha channel",
        default=True,
    )

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col = layout.column(align=True)
        col.prop(self, "use_alpha")
        col.prop(self, "denoise")
        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)
            if self.image:
                layout.prop(self, "image")
            else:
                layout.template_ID(self, "image", text="Image", open="image.open")

    def draw_channel(self, context, layout):
        col = layout.column(align=True, heading="Contributions")
        col.prop(self, "use_pass_direct")
        col.prop(self, "use_pass_indirect")
        col.prop(self, "use_pass_color")
        col = layout.column()
        col.prop(self, "view_from")
        col.prop(self, "samples")
        col.prop(self, "denoise")
        if self.image:
            layout.prop(self, "image")
        else:
            layout.template_ID(self, "image", text="Image", open="image.open")


class QBAKER_PG_uv(QBakerPropertyGroup):
    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        default="UV",
    )


class QBAKER_PG_channel_pack(PropertyGroup):
    type = "CHANNEL_PACK"

    suffix_mapping = {
        "BASE_COLOR": "BC",
        "EMISSION": "E",
        "GLOSSINESS": "G",
        "METALLIC": "M",
        "NORMAL": "N",
        "OCCLUSION": "O",
        "ROUGHNESS": "R",
        "SPECULAR": "S",
        "ALPHA": "A",
        "BEVEL_NORMAL": "BN",
        "CAVITY": "CA",
        "CURVATURE": "CU",
        "DISPLACEMENT": "D",
        "EDGE": "E",
        "GRADIENT": "G",
        "HEIGHT": "H",
        "MATERIAL_ID": "ID",
        "THICKNESS": "T",
        "TOON_SHADOW": "TS",
        "VDM": "VDM",
        "XYZ": "XYZ",
        "IOR": "IOR",
        "SUBSURFACE_WEIGHT": "SSW",
        "SUBSURFACE_SCALE": "SSCLE",
        "SUBSURFACE_IOR": "SSIOR",
        "SUBSURFACE_ANISOTROPY": "SSA",
        "SPECULAR_TINT": "SPECT",
        "ANISOTROPIC": "ANIS",
        "ANISOTROPIC_ROTATION": "ANISROT",
        "TANGENT": "TANG",
        "TRANSMISSION_WEIGHT": "TRANSW",
        "COAT_WEIGHT": "CW",
        "COAT_ROUGHNESS": "CR",
        "COAT_IOR": "CIOR",
        "COAT_TINT": "CT",
        "COAT_NORMAL": "CN",
        "SHEEN_WEIGHT": "SW",
        "SHEEN_ROUGHNESS": "SR",
        "SHEEN_TINT": "ST",
        "EMISSION_STRENGTH": "ES",
        "AO": "AO",
        "COMBINED": "COMB",
        "DIFFUSE": "DIFF",
        "ENVIRONMENT": "ENV",
        "GLOSSY": "GLOS",
        "POSITION": "POS",
        "SHADOW": "SHDW",
        "TRANSMISSION": "TRANS",
        "UV": "UV",
    }

    def get_suffix(self):
        if self.mode == "RGBA":
            suffix = f"{f'{self.suffix_mapping[self.r_channel]}' if self.r_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.g_channel]}' if self.g_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.b_channel]}' if self.b_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.a_channel]}' if self.a_channel != 'NONE' else ''}"
        else:
            suffix = f"{self.suffix_mapping[self.rgb_channel]}{f'_{self.suffix_mapping[self.a_channel]}' if self.a_channel != 'NONE' else ''}"
        return self.get("suffix", suffix)

    def set_suffix(self, value):
        self["suffix"] = value

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        get=get_suffix,
        set=set_suffix,
    )

    mode: EnumProperty(
        name="Mode",
        items=(
            ("RGBA", "Channels", "R + G + B + A"),
            ("RGB_A", "Map + Channel", "RGB + A"),
        ),
        default="RGBA",
    )

    channel_items = (
        ("", "PBR", "", "SHADING_RENDERED", 0),
        ("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"),
        ("METALLIC", "Metallic", "Metallic Map"),
        ("OCCLUSION", "Occlusion", "Ambient Occlusion Map"),
        ("ROUGHNESS", "Roughness", "Roughness Map"),
        ("SPECULAR", "Specular", "Specular Map"),
        ("", "Mesh", "", "MESH_DATA", 0),
        ("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"),
        ("CAVITY", "Cavity", "Cavity / Concavity Map"),
        ("CURVATURE", "Curvature", "Curvature Map"),
        ("DISPLACEMENT", "Displacement", "Displacement / Bump Map"),
        ("EDGE", "Edge", "Edge / Convexity Map"),
        ("HEIGHT", "Heightmap", "Height Map"),
        ("THICKNESS", "Thickness", "Thickness / Translucency Map"),
        ("TOON_SHADOW", "Toon Shadow", "Toon Shadow Map"),
        ("", "Principled BSDF", "", "NODE", 0),
        ("IOR", "IOR", "IOR Map"),
        ("SUBSURFACE_WEIGHT", "Subsurface Weight", "Subsurface Weight Map"),
        ("SUBSURFACE_SCALE", "Subsurface Scale", "Subsurface Scale Map"),
        ("SUBSURFACE_IOR", "Subsurface IOR", "Subsurface IOR Map"),
        ("SUBSURFACE_ANISOTROPY", "Subsurface Anisotropy", "Subsurface Anisotropy Map"),
        ("ANISOTROPIC", "Anisotropic", "Anisotropic Map"),
        ("ANISOTROPIC_ROTATION", "Anisotropic Rotation", "Anisotropic Rotation Map"),
        ("TRANSMISSION_WEIGHT", "Transmission Weight", "Transmission Weight Map"),
        ("COAT_WEIGHT", "Coat Weight", "Coat Weight Map"),
        ("COAT_ROUGHNESS", "Coat Roughness", "Coat Roughness Map"),
        ("COAT_IOR", "Coat IOR", "Coat IOR Map"),
        ("SHEEN_WEIGHT", "Sheen Weight", "Sheen Weight Map"),
        ("SHEEN_ROUGHNESS", "Sheen Roughness", "Sheen Roughness Map"),
        ("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"),
        ("", "Cycles", "", "SHADING_TEXTURE", 0),
        ("AO", "Ambient Occlusion", "Cycles Ambient Occlusion Map"),
        ("SHADOW", "Shadow", "Shadow Map"),
        ("", "", "", "", 0),
        ("NONE", "None", ""),
    )

    r_channel: EnumProperty(
        name="R",
        description="Red Channel",
        items=channel_items,
        default="OCCLUSION",
    )

    g_channel: EnumProperty(
        name="G",
        description="Green Channel",
        items=channel_items,
        default="METALLIC",
    )

    b_channel: EnumProperty(
        name="B",
        description="Blue Channel",
        items=channel_items,
        default="ROUGHNESS",
    )

    rgb_channel: EnumProperty(
        name="RGB",
        description="RGB Channel",
        items=(
            ("", "PBR", "", "SHADING_RENDERED", 0),
            ("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"),
            ("EMISSION", "Emission", "Emission Map"),
            ("NORMAL", "Normal", "Normal"),
            ("", "Mesh", "", "MESH_DATA", 0),
            ("BEVEL_NORMAL", "Bevel Normal", "Bevel Normal Map"),
            ("GRADIENT", "Gradient", "Gradient Map"),
            ("MATERIAL_ID", "Material ID", "Material ID Map"),
            ("VDM", "Vector Displacement", "Vector Displacement Map"),
            ("XYZ", "XYZ", "XYZ Map"),
            ("", "Principled BSDF", "", "NODE", 0),
            ("SPECULAR_TINT", "Specular Tint", "Specular Tint Map"),
            ("TANGENT", "Tangent", "Tangent Map"),
            ("COAT_TINT", "Coat Tint", "Coat Tint Map"),
            ("COAT_NORMAL", "Coat Normal", "Coat Normal Map"),
            ("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"),
            ("", "Cycles", "", "SHADING_TEXTURE", 0),
            ("COMBINED", "Combined", "Combined Map"),
            ("DIFFUSE", "Diffuse", "Diffuse Map"),
            ("ENVIRONMENT", "Environment", "Environment Map"),
            ("GLOSSY", "Glossy", "Glossy Map"),
            ("POSITION", "Position", "Position Map"),
            ("TRANSMISSION", "Transmission", "Transmission Map"),
            ("UV", "UV", "UV Map"),
        ),
        default="BASE_COLOR",
    )

    a_channel: EnumProperty(
        name="A",
        description="Alpha Channel",
        items=channel_items,
        default="ALPHA",
    )

    base_color: PointerProperty(type=QBAKER_PG_base_color)
    emission: PointerProperty(type=QBAKER_PG_emission)
    glossiness: PointerProperty(type=QBAKER_PG_glossiness)
    metallic: PointerProperty(type=QBAKER_PG_metallic)
    normal: PointerProperty(type=QBAKER_PG_normal)
    occlusion: PointerProperty(type=QBAKER_PG_occlusion)
    roughness: PointerProperty(type=QBAKER_PG_roughness)
    specular: PointerProperty(type=QBAKER_PG_specular)

    alpha: PointerProperty(type=QBAKER_PG_alpha)
    bevel_normal: PointerProperty(type=QBAKER_PG_bevel_normal)
    cavity: PointerProperty(type=QBAKER_PG_cavity)
    curvature: PointerProperty(type=QBAKER_PG_curvature)
    displacement: PointerProperty(type=QBAKER_PG_displacement)
    edge: PointerProperty(type=QBAKER_PG_edge)
    gradient: PointerProperty(type=QBAKER_PG_gradient)
    height: PointerProperty(type=QBAKER_PG_height)
    material_id: PointerProperty(type=QBAKER_PG_material_id)
    thickness: PointerProperty(type=QBAKER_PG_thickness)
    toon_shadow: PointerProperty(type=QBAKER_PG_toon_shadow)
    vdm: PointerProperty(type=QBAKER_PG_vdm)
    xyz: PointerProperty(type=QBAKER_PG_xyz)

    ior: PointerProperty(type=QBAKER_PG_ior)
    subsurface_weight: PointerProperty(type=QBAKER_PG_subsurface_weight)
    subsurface_scale: PointerProperty(type=QBAKER_PG_subsurface_scale)
    subsurface_ior: PointerProperty(type=QBAKER_PG_subsurface_ior)
    subsurface_anisotropy: PointerProperty(type=QBAKER_PG_subsurface_anisotropy)
    specular_tint: PointerProperty(type=QBAKER_PG_specular_tint)
    anisotropic: PointerProperty(type=QBAKER_PG_anisotropic)
    anisotropic_rotation: PointerProperty(type=QBAKER_PG_anisotropic_rotation)
    tangent: PointerProperty(type=QBAKER_PG_tangent)
    transmission_weight: PointerProperty(type=QBAKER_PG_transmission_weight)
    coat_weight: PointerProperty(type=QBAKER_PG_coat_weight)
    coat_roughness: PointerProperty(type=QBAKER_PG_coat_roughness)
    coat_ior: PointerProperty(type=QBAKER_PG_coat_ior)
    coat_tint: PointerProperty(type=QBAKER_PG_coat_tint)
    coat_normal: PointerProperty(type=QBAKER_PG_coat_normal)
    sheen_weight: PointerProperty(type=QBAKER_PG_sheen_weight)
    sheen_roughness: PointerProperty(type=QBAKER_PG_sheen_roughness)
    sheen_tint: PointerProperty(type=QBAKER_PG_sheen_tint)
    emission_strength: PointerProperty(type=QBAKER_PG_emission_strength)

    ambient_occlusion: PointerProperty(type=QBAKER_PG_ambient_occlusion)
    combined: PointerProperty(type=QBAKER_PG_combined)
    diffuse: PointerProperty(type=QBAKER_PG_diffuse)
    environment: PointerProperty(type=QBAKER_PG_environment)
    glossy: PointerProperty(type=QBAKER_PG_glossy)
    position: PointerProperty(type=QBAKER_PG_position)
    shadow: PointerProperty(type=QBAKER_PG_shadow)
    transmission: PointerProperty(type=QBAKER_PG_transmission)
    uv: PointerProperty(type=QBAKER_PG_uv)

    custom: BoolProperty(
        name="Custom",
        description="Custom bake settings",
    )

    bake: PointerProperty(type=QBAKER_PG_bake_settings)

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "mode")

        col = layout.column()
        if self.mode == "RGBA":
            col.prop(self, "r_channel")
            col.prop(self, "g_channel")
            col.prop(self, "b_channel")
        else:
            col.prop(self, "rgb_channel")
        col.prop(self, "a_channel")

        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)

    def get_single_channel_map(self, channel):
        if channel == "GLOSSINESS":
            return self.glossiness
        elif channel == "METALLIC":
            return self.metallic
        elif channel == "OCCLUSION":
            return self.occlusion
        elif channel == "ROUGHNESS":
            return self.roughness
        elif channel == "SPECULAR":
            return self.specular

        elif channel == "ALPHA":
            return self.alpha
        elif channel == "CAVITY":
            return self.cavity
        elif channel == "CURVATURE":
            return self.curvature
        elif channel == "DISPLACEMENT":
            return self.displacement
        elif channel == "EDGE":
            return self.edge
        elif channel == "HEIGHT":
            return self.height
        elif channel == "THICKNESS":
            return self.thickness
        elif channel == "TOON_SHADOW":
            return self.toon_shadow

        elif channel == "IOR":
            return self.ior
        elif channel == "SUBSURFACE_WEIGHT":
            return self.subsurface_weight
        elif channel == "SUBSURFACE_SCALE":
            return self.subsurface_scale
        elif channel == "SUBSURFACE_IOR":
            return self.subsurface_ior
        elif channel == "SUBSURFACE_ANISOTROPY":
            return self.subsurface_anisotropy
        elif channel == "ANISOTROPIC":
            return self.anisotropic
        elif channel == "ANISOTROPIC_ROTATION":
            return self.anisotropic_rotation
        elif channel == "TRANSMISSION_WEIGHT":
            return self.transmission_weight
        elif channel == "COAT_WEIGHT":
            return self.coat_weight
        elif channel == "COAT_ROUGHNESS":
            return self.coat_roughness
        elif channel == "COAT_IOR":
            return self.coat_ior
        elif channel == "SHEEN_WEIGHT":
            return self.sheen_weight
        elif channel == "SHEEN_ROUGHNESS":
            return self.sheen_roughness
        elif channel == "EMISSION_STRENGTH":
            return self.emission_strength

        elif channel == "AO":
            return self.ambient_occlusion
        elif channel == "SHADOW":
            return self.shadow

    def get_multi_channel_map(self, channel):
        if channel == "BASE_COLOR":
            return self.base_color
        elif channel == "EMISSION":
            return self.emission
        elif channel == "NORMAL":
            return self.normal

        elif channel == "BEVEL_NORMAL":
            return self.bevel_normal
        elif channel == "GRADIENT":
            return self.gradient
        elif channel == "MATERIAL_ID":
            return self.material_id
        elif channel == "VDM":
            return self.vdm
        elif channel == "XYZ":
            return self.xyz

        elif channel == "SPECULAR_TINT":
            return self.specular_tint
        elif channel == "TANGENT":
            return self.tangent
        elif channel == "COAT_TINT":
            return self.coat_tint
        elif channel == "COAT_NORMAL":
            return self.coat_normal
        elif channel == "SHEEN_TINT":
            return self.sheen_tint

        elif channel == "COMBINED":
            return self.combined
        elif channel == "DIFFUSE":
            return self.diffuse
        elif channel == "ENVIRONMENT":
            return self.environment
        elif channel == "GLOSSY":
            return self.glossy
        elif channel == "POSITION":
            return self.position
        elif channel == "TRANSMISSION":
            return self.transmission
        elif channel == "UV":
            return self.uv


class QBAKER_PG_map(PropertyGroup):
    label: StringProperty()

    use_include: BoolProperty(
        name="Include",
        description="Include this map",
        default=True,
    )

    type: EnumProperty(
        name="Texture Type",
        description="Texture type",
        items=(
            # PBR
            ("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"),
            ("EMISSION", "Emission", "Emission Map"),
            ("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"),
            ("METALLIC", "Metallic", "Metallic Map"),
            ("NORMAL", "Normal", "Normal Map"),
            ("OCCLUSION", "Occlusion", "Occlusion Map"),
            ("ROUGHNESS", "Roughness", "Roughness Map"),
            ("SPECULAR", "Specular", "Specular Map"),
            ("CHANNEL_PACK", "Channel Pack", "Channel Pack Map"),
            # Mesh
            ("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"),
            ("BEVEL_NORMAL", "Bevel Normal", "Bevel Normal Map"),
            ("CAVITY", "Cavity", "Cavity / Concavity Map"),
            ("CURVATURE", "Curvature", "Curvature Map"),
            ("DISPLACEMENT", "Displacement", "Displacement / Bump Map"),
            ("EDGE", "Edge", "Edge / Convexity Map"),
            ("GRADIENT", "Gradient", "Gradient Map"),
            ("HEIGHT", "Heightmap", "Height Map"),
            ("MATERIAL_ID", "Material ID", "Material ID Map"),
            ("THICKNESS", "Thickness", "Thickness / Translucency Map"),
            ("TOON_SHADOW", "Toon Shadow", "Toon Shadow Map"),
            ("VDM", "Vector Displacement", "Vector Displacement Map"),
            ("WIREFRAME", "Wireframe", "Wireframe / UV Layout Map"),
            ("XYZ", "XYZ", "XYZ Map"),
            # Principled BSDF
            ("IOR", "IOR", "IOR Map"),
            ("SUBSURFACE_WEIGHT", "Subsurface Weight", "Subsurface Weight Map"),
            ("SUBSURFACE_SCALE", "Subsurface Scale", "Subsurface Scale Map"),
            ("SUBSURFACE_IOR", "Subsurface IOR", "Subsurface IOR Map"),
            ("SUBSURFACE_ANISOTROPY", "Subsurface Anisotropy", "Subsurface Anisotropy Map"),
            ("SPECULAR_TINT", "Specular Tint", "Specular Tint Map"),
            ("ANISOTROPIC", "Anisotropic", "Anisotropic Map"),
            ("ANISOTROPIC_ROTATION", "Anisotropic Rotation", "Anisotropic Rotation Map"),
            ("TANGENT", "Tangent", "Tangent Map"),
            ("TRANSMISSION_WEIGHT", "Transmission Weight", "Transmission Weight Map"),
            ("COAT_WEIGHT", "Coat Weight", "Coat Weight Map"),
            ("COAT_ROUGHNESS", "Coat Roughness", "Coat Roughness Map"),
            ("COAT_IOR", "Coat IOR", "Coat IOR Map"),
            ("COAT_TINT", "Coat Tint", "Coat Tint Map"),
            ("COAT_NORMAL", "Coat Normal", "Coat Normal Map"),
            ("SHEEN_WEIGHT", "Sheen Weight", "Sheen Weight Map"),
            ("SHEEN_ROUGHNESS", "Sheen Roughness", "Sheen Roughness Map"),
            ("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"),
            ("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"),
            # Cycles
            ("AO", "Ambient Occlusion", "Ambient Occlusion Map"),
            ("COMBINED", "Combined", "Combined Map"),
            ("DIFFUSE", "Diffuse", "Diffuse Map"),
            ("ENVIRONMENT", "Environment", "Environment Map"),
            ("GLOSSY", "Glossy", "Glossy Map"),
            ("POSITION", "Position", "Position Map"),
            ("SHADOW", "Shadow", "Shadow Map"),
            ("TRANSMISSION", "Transmission", "Transmission Map"),
            ("UV", "UV", "UV Map"),
        ),
    )

    base_color: PointerProperty(type=QBAKER_PG_base_color)
    emission: PointerProperty(type=QBAKER_PG_emission)
    glossiness: PointerProperty(type=QBAKER_PG_glossiness)
    metallic: PointerProperty(type=QBAKER_PG_metallic)
    normal: PointerProperty(type=QBAKER_PG_normal)
    occlusion: PointerProperty(type=QBAKER_PG_occlusion)
    roughness: PointerProperty(type=QBAKER_PG_roughness)
    specular: PointerProperty(type=QBAKER_PG_specular)
    channel_pack: PointerProperty(type=QBAKER_PG_channel_pack)

    alpha: PointerProperty(type=QBAKER_PG_alpha)
    bevel_normal: PointerProperty(type=QBAKER_PG_bevel_normal)
    cavity: PointerProperty(type=QBAKER_PG_cavity)
    curvature: PointerProperty(type=QBAKER_PG_curvature)
    displacement: PointerProperty(type=QBAKER_PG_displacement)
    edge: PointerProperty(type=QBAKER_PG_edge)
    gradient: PointerProperty(type=QBAKER_PG_gradient)
    height: PointerProperty(type=QBAKER_PG_height)
    material_id: PointerProperty(type=QBAKER_PG_material_id)
    thickness: PointerProperty(type=QBAKER_PG_thickness)
    toon_shadow: PointerProperty(type=QBAKER_PG_toon_shadow)
    vdm: PointerProperty(type=QBAKER_PG_vdm)
    wireframe: PointerProperty(type=QBAKER_PG_wireframe)
    xyz: PointerProperty(type=QBAKER_PG_xyz)

    ior: PointerProperty(type=QBAKER_PG_ior)
    subsurface_weight: PointerProperty(type=QBAKER_PG_subsurface_weight)
    subsurface_scale: PointerProperty(type=QBAKER_PG_subsurface_scale)
    subsurface_ior: PointerProperty(type=QBAKER_PG_subsurface_ior)
    subsurface_anisotropy: PointerProperty(type=QBAKER_PG_subsurface_anisotropy)
    specular_tint: PointerProperty(type=QBAKER_PG_specular_tint)
    anisotropic: PointerProperty(type=QBAKER_PG_anisotropic)
    anisotropic_rotation: PointerProperty(type=QBAKER_PG_anisotropic_rotation)
    tangent: PointerProperty(type=QBAKER_PG_tangent)
    transmission_weight: PointerProperty(type=QBAKER_PG_transmission_weight)
    coat_weight: PointerProperty(type=QBAKER_PG_coat_weight)
    coat_roughness: PointerProperty(type=QBAKER_PG_coat_roughness)
    coat_ior: PointerProperty(type=QBAKER_PG_coat_ior)
    coat_tint: PointerProperty(type=QBAKER_PG_coat_tint)
    coat_normal: PointerProperty(type=QBAKER_PG_coat_normal)
    sheen_weight: PointerProperty(type=QBAKER_PG_sheen_weight)
    sheen_roughness: PointerProperty(type=QBAKER_PG_sheen_roughness)
    sheen_tint: PointerProperty(type=QBAKER_PG_sheen_tint)
    emission_strength: PointerProperty(type=QBAKER_PG_emission_strength)

    ambient_occlusion: PointerProperty(type=QBAKER_PG_ambient_occlusion)
    combined: PointerProperty(type=QBAKER_PG_combined)
    diffuse: PointerProperty(type=QBAKER_PG_diffuse)
    environment: PointerProperty(type=QBAKER_PG_environment)
    glossy: PointerProperty(type=QBAKER_PG_glossy)
    position: PointerProperty(type=QBAKER_PG_position)
    shadow: PointerProperty(type=QBAKER_PG_shadow)
    transmission: PointerProperty(type=QBAKER_PG_transmission)
    uv: PointerProperty(type=QBAKER_PG_uv)

    def draw(self, context, layout):
        layout.active = self.use_include

        if self.type == "BASE_COLOR":
            self.base_color.draw(context, layout)
        elif self.type == "EMISSION":
            self.emission.draw(context, layout)
        elif self.type == "GLOSSINESS":
            self.glossiness.draw(context, layout)
        elif self.type == "METALLIC":
            self.metallic.draw(context, layout)
        elif self.type == "NORMAL":
            self.normal.draw(context, layout)
        elif self.type == "OCCLUSION":
            self.occlusion.draw(context, layout)
        elif self.type == "ROUGHNESS":
            self.roughness.draw(context, layout)
        elif self.type == "SPECULAR":
            self.specular.draw(context, layout)
        elif self.type == "CHANNEL_PACK":
            self.channel_pack.draw(context, layout)

        elif self.type == "ALPHA":
            self.alpha.draw(context, layout)
        elif self.type == "BEVEL_NORMAL":
            self.bevel_normal.draw(context, layout)
        elif self.type == "CAVITY":
            self.cavity.draw(context, layout)
        elif self.type == "CURVATURE":
            self.curvature.draw(context, layout)
        elif self.type == "DISPLACEMENT":
            self.displacement.draw(context, layout)
        elif self.type == "EDGE":
            self.edge.draw(context, layout)
        elif self.type == "GRADIENT":
            self.gradient.draw(context, layout)
        elif self.type == "HEIGHT":
            self.height.draw(context, layout)
        elif self.type == "MATERIAL_ID":
            self.material_id.draw(context, layout)
        elif self.type == "THICKNESS":
            self.thickness.draw(context, layout)
        elif self.type == "TOON_SHADOW":
            self.toon_shadow.draw(context, layout)
        elif self.type == "VDM":
            self.vdm.draw(context, layout)
        elif self.type == "WIREFRAME":
            self.wireframe.draw(context, layout)
        elif self.type == "XYZ":
            self.xyz.draw(context, layout)

        elif self.type == "IOR":
            self.ior.draw(context, layout)
        elif self.type == "SUBSURFACE_WEIGHT":
            self.subsurface_weight.draw(context, layout)
        elif self.type == "SUBSURFACE_SCALE":
            self.subsurface_scale.draw(context, layout)
        elif self.type == "SUBSURFACE_IOR":
            self.subsurface_ior.draw(context, layout)
        elif self.type == "SUBSURFACE_ANISOTROPY":
            self.subsurface_anisotropy.draw(context, layout)
        elif self.type == "SPECULAR_TINT":
            self.specular_tint.draw(context, layout)
        elif self.type == "ANISOTROPIC":
            self.anisotropic.draw(context, layout)
        elif self.type == "ANISOTROPIC_ROTATION":
            self.anisotropic_rotation.draw(context, layout)
        elif self.type == "TANGENT":
            self.tangent.draw(context, layout)
        elif self.type == "TRANSMISSION_WEIGHT":
            self.transmission_weight.draw(context, layout)
        elif self.type == "COAT_WEIGHT":
            self.coat_weight.draw(context, layout)
        elif self.type == "COAT_ROUGHNESS":
            self.coat_roughness.draw(context, layout)
        elif self.type == "COAT_IOR":
            self.coat_ior.draw(context, layout)
        elif self.type == "COAT_TINT":
            self.coat_tint.draw(context, layout)
        elif self.type == "COAT_NORMAL":
            self.coat_normal.draw(context, layout)
        elif self.type == "SHEEN_WEIGHT":
            self.sheen_weight.draw(context, layout)
        elif self.type == "SHEEN_ROUGHNESS":
            self.sheen_roughness.draw(context, layout)
        elif self.type == "SHEEN_TINT":
            self.sheen_tint.draw(context, layout)
        elif self.type == "EMISSION_STRENGTH":
            self.emission_strength.draw(context, layout)

        elif self.type == "AO":
            self.ambient_occlusion.draw(context, layout)
        elif self.type == "COMBINED":
            self.combined.draw(context, layout)
        elif self.type == "DIFFUSE":
            self.diffuse.draw(context, layout)
        elif self.type == "ENVIRONMENT":
            self.environment.draw(context, layout)
        elif self.type == "GLOSSY":
            self.glossy.draw(context, layout)
        elif self.type == "POSITION":
            self.position.draw(context, layout)
        elif self.type == "SHADOW":
            self.shadow.draw(context, layout)
        elif self.type == "TRANSMISSION":
            self.transmission.draw(context, layout)
        elif self.type == "UV":
            self.uv.draw(context, layout)


class QBAKER_PG_folder(PropertyGroup):
    path: StringProperty(subtype="DIR_PATH")
    use_subfolder: BoolProperty()


class QBAKER_PG_bake(PropertyGroup):
    batch_name: StringProperty(
        name="Batch Name",
        description="Name the maps with additional info\n\n$name - Name of the Bakegroup\n$size    - Size of the map\n$type   - Type of the map\n\ne.g. (Bakegroup_1K_Color)",
        default="$name_$size_$type",
    )

    # --- Filename customization properties ---
    naming_use_custom_prefix: BoolProperty(
        name="Use Prefix",
        description="Ajouter un préfixe personnalisé avant le nom généré",
        default=False,
    )

    naming_custom_prefix: StringProperty(
        name="Custom Prefix",
        description="Texte ajouté au début du nom (avant les autres éléments)",
        default="",
    )

    naming_include_date: BoolProperty(
        name="Include Date",
        description="Insère la date actuelle (YYYYMMDD)",
        default=False,
    )

    naming_include_name: BoolProperty(
        name="Include $name",
        description="Inclure le nom du Bakegroup ($name) dans le nom de fichier",
        default=True,
    )

    naming_include_size: BoolProperty(
        name="Include $size",
        description="Inclure la taille ($size) dans le nom de fichier",
        default=True,
    )

    naming_include_object: BoolProperty(
        name="Include $object",
        description="Inclure le nom de l'objet porteur ($object) dans le nom de fichier",
        default=True,
    )

    naming_name_source: EnumProperty(
        name="Name Source",
        description="Source utilisée pour le token $name (BakeGroup / Material / Object)",
        items=(
            ("BAKEGROUP", "BakeGroup", "Utiliser le nom du BakeGroup pour $name"),
            ("MATERIAL", "Material", "Utiliser le nom du matériau pour $name si disponible"),
            ("OBJECT", "Object", "Utiliser le nom de l'objet pour $name si disponible"),
        ),
        default="BAKEGROUP",
    )

    naming_force_material_filename: BoolProperty(
        name="Force Material Filename",
        description="Forcer le nom de fichier final à utiliser le nom du matériau (si disponible). Le nom du sous-dossier reste contrôlé par 'Name Source'.",
        default=False,
    )

    naming_include_time: BoolProperty(
        name="Include Time",
        description="Insère l'heure actuelle (HHMMSS)",
        default=False,
    )

    naming_include_blendname: BoolProperty(
        name="Include .blend name",
        description="Insère le nom du fichier .blend (sans extension)",
        default=False,
    )

    naming_include_collection: BoolProperty(
        name="Include Active Collection",
        description="Insère le nom de la collection active (si disponible)",
        default=False,
    )

    naming_custom_suffix: StringProperty(
        name="Custom Suffix",
        description="Texte ajouté avant le suffix existant (optionnel). Ne remplace pas le suffix géré par la map.",
        default="",
    )

    use_auto_udim: BoolProperty(
        name="Auto UDIM",
        description="Automatically create UDIM textures based on UV layout",
        default=True,
    )

    folders: CollectionProperty(type=QBAKER_PG_folder)
    folder_index: IntProperty(name="Active Folder Index")

    use_sub_folder: BoolProperty(
        name="Sub Folder",
        description="Create a sub folder for baked textures\n\nNote: The sub folder name will follow the 'Name Source' selection (BakeGroup / Material / Object)",
        default=False,
    )

    size: EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("512", "512", "512x512 px"),
            ("1024", "1K", "1024x1024 px"),
            ("2048", "2K", "2048x2048 px"),
            ("4096", "4K", "4096x4096 px"),
            ("8192", "8K", "8192x8192 px"),
            ("CUSTOM", "Custom", "Custom bake size"),
        ),
        default="1024",
    )

    width: IntProperty(
        name="Width",
        description="Number of horizontal pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    height: IntProperty(
        name="Height",
        description="Number of vertical pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    anti_aliasing: EnumProperty(
        name="Anti-Aliasing",
        description="Super-sampling level for anti-aliasing",
        items=(
            ("1", "None", "No anti-aliasing"),
            ("2", "2x", "2x samples"),
            ("4", "4x", "4x samples"),
            ("8", "8x", "8x samples"),
            ("16", "16x", "16x samples"),
        ),
        default="1",
    )

    format: EnumProperty(
        name="Format",
        description="File format to save the rendered images as",
        items=(
            ("PNG", "PNG", "Output image in PNG format"),
            ("JPEG", "JPEG", "Output image in JPEG format"),
            ("TARGA", "Targa", "Output image in Targa format"),
            ("TIFF", "TIFF", "Output image in TIFF format"),
            ("OPEN_EXR", "OpenEXR", "Output image in OpenEXR format"),
            ("HDR", "Radiance HDR", "Output image in Radiance HDR format"),
            ("WEBP", "WebP", "Output image in WebP format"),
        ),
        default="PNG",
    )

    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("8", "8", "8-bit color channels"),
            ("16", "16", "16-bit color channels"),
        ),
    )

    color_depth_exr: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("16", "16", "16-bit color channels"),
            ("32", "32", "32-bit color channels"),
        ),
        default="32",
    )

    compression: IntProperty(
        name="Compression",
        description="Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=15,
    )

    quality: IntProperty(
        name="Quality",
        description="Quality for image formats that support lossy compression",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=90,
    )

    exr_codec: EnumProperty(
        name="Codec",
        description="Codec settings for OpenEXR",
        items=(
            ("NONE", "None", ""),
            ("PXR24", "Pxr24 (lossy)", ""),
            ("ZIP", "ZIP (lossless)", ""),
            ("PIZ", "PIZ (lossless)", ""),
            ("RLE", "RLE (lossless)", ""),
            ("ZIPS", "ZIPS (lossless)", ""),
            ("B44", "B44 (lossy)", ""),
            ("B44A", "B44A (lossy)", ""),
            ("DWAA", "DWAA (lossy)", ""),
            ("DWAB", "DWAB (lossy)", ""),
        ),
        default="ZIP",
    )

    tiff_codec: EnumProperty(
        name="Compression",
        description="Compression mode for TIFF",
        items=(
            ("NONE", "None", ""),
            ("DEFLATE", "Deflate", ""),
            ("LZW", "LZW", ""),
            ("PACKBITS", "Pack Bits", ""),
        ),
        default="DEFLATE",
    )

    margin_type: EnumProperty(
        name="Margin Type",
        description="Algorithm to extend the baked result",
        items=(
            (
                "ADJACENT_FACES",
                "Adjacent Faces",
                "Use pixels from adjacent faces across UV seams",
            ),
            ("EXTEND", "Extend", "Extend border pixels outwards"),
        ),
        default="ADJACENT_FACES",
    )

    margin: IntProperty(
        name="Margin Size",
        description="Extends the baked result as a post process filter",
        subtype="PIXEL",
        min=0,
        soft_max=64,
        default=8,
    )

    def get_cpu_count():
        try:
            cpu_count = len(os.sched_getaffinity(0))
        except AttributeError:
            cpu_count = os.cpu_count()
        return cpu_count

    processes: IntProperty(
        name="Processes",
        description="Processes used while baking\nUse lower number if you bake 4K or higher to avoid 'Out of Memory' error",
        min=1,
        soft_max=get_cpu_count() // 4,
        max=get_cpu_count() // 2,
        default=1,
    )

    use_create_material: BoolProperty(
        name="Create Material",
        description="Create a material for baked textures",
        default=True,
    )

    use_duplicate_objects: BoolProperty(
        name="Duplicate Objects",
        description="Duplicate objects to join them into one object\nNote: This will duplicate the original objects, only the objects used for baking",
        default=False,
    )

    use_join_objects: BoolProperty(
        name="Join Objects",
        description="Join multiple duplicate objects into one object",
        default=True,
    )

    use_hide_objects: BoolProperty(
        name="Hide Objects",
        description="Hide original objects after duplicating",
        default=True,
    )

    def build_filename(self, context, bake_group_name: str, map_suffix: str, extra_tokens: dict = None):
        """
        Construire le nom de fichier (sans extension ni UDIM).
        Les éléments de pré-nommage (prefix/date/time/blend/collection/custom suffix)
        sont placés avant la template `batch_name`. Le suffix de la map (`map_suffix`)
        est conservé et placé à la fin si nécessaire.
        """
        parts = []

        # custom prefix
        if getattr(self, "naming_use_custom_prefix", False) and self.naming_custom_prefix:
            parts.append(self.naming_custom_prefix.strip())

        # date/time
        now = datetime.datetime.now()
        if getattr(self, "naming_include_date", False):
            parts.append(now.strftime("%Y%m%d"))
        if getattr(self, "naming_include_time", False):
            parts.append(now.strftime("%H%M%S"))

        # blend name
        if getattr(self, "naming_include_blendname", False):
            blend_path = bpy.data.filepath
            if blend_path:
                parts.append(os.path.splitext(os.path.basename(blend_path))[0])
            else:
                parts.append("untitled")

        # active collection
        if getattr(self, "naming_include_collection", False):
            col_name = None
            try:
                col = context.collection
                if col:
                    col_name = col.name
            except Exception:
                col_name = None
            if not col_name:
                try:
                    col_name = context.view_layer.active_layer_collection.collection.name
                except Exception:
                    col_name = None
            if col_name:
                parts.append(col_name)

        # custom suffix (placed before the map's suffix)
        if self.naming_custom_suffix:
            parts.append(self.naming_custom_suffix.strip())

        # Render existing batch_name template (it already handles $name, $size, $type etc.)
        template = self.batch_name or "$name_$size_$type"

        # Respect toggles: allow user to disable automatic inclusion of $name, $size and/or $object.
        # We remove tokens from the template before rendering (they will be replaced by empty string).
        if not getattr(self, "naming_include_name", True):
            template = template.replace("$name", "")
        if not getattr(self, "naming_include_size", True):
            template = template.replace("$size", "")
        if not getattr(self, "naming_include_object", True):
            template = template.replace("$object", "")

        # Mapping for tokens we support
        mapping = {
            "name": bake_group_name,
            "size": (f"{self.width}x{self.height}" if self.size == "CUSTOM" else self.size),
            "type": map_suffix,
            "format": getattr(self, "format", ""),
            "aa": getattr(self, "anti_aliasing", ""),
            "margin": str(getattr(self, "margin", "")),
            "processes": str(getattr(self, "processes", "")),
            "width": str(getattr(self, "width", "")),
            "height": str(getattr(self, "height", "")),
        }

        # Merge any extra tokens provided by the caller (eg. material, node, socket)
        if extra_tokens:
            # ensure all keys are strings
            mapping.update({str(k): str(v) for k, v in extra_tokens.items()})

        # Debugging: when Blender runs in background/batch, print received tokens and overrides
        try:
            import bpy as _bpy
            if getattr(_bpy.app, "background", False):
                print(f"QB_DEBUG build_filename: bake_group='{bake_group_name}', map_suffix='{map_suffix}', extra_tokens={extra_tokens}")
                sys.stdout.flush()
        except Exception:
            pass

        # Resolve the effective $name value according to the user's selection
        # - BAKEGROUP: $name -> bake_group_name (default)
        # - MATERIAL: if a material token is provided, use it for $name
        # - OBJECT: if an object token is provided and inclusion is enabled, use it for $name
        effective_name = bake_group_name
        if getattr(self, "naming_name_source", "BAKEGROUP") == "OBJECT":
            # prefer object token when present and allowed
            obj_val = mapping.get("object")
            if obj_val and getattr(self, "naming_include_object", True):
                effective_name = obj_val
        elif getattr(self, "naming_name_source", "BAKEGROUP") == "MATERIAL":
            mat_val = mapping.get("material")
            if mat_val:
                effective_name = mat_val

        mapping["name"] = effective_name

        # If the user requests to force the final filename to use the material name,
        # override the resolved $name with the material token if available.
        if getattr(self, "naming_force_material_filename", False):
            mat_val = mapping.get("material")
            if mat_val:
                old_name = mapping.get("name")
                mapping["name"] = mat_val
                try:
                    import bpy as _bpy
                    if getattr(_bpy.app, "background", False):
                        print(f"QB_DEBUG build_filename: overriding name '{old_name}' -> '{mat_val}' due to naming_force_material_filename")
                        sys.stdout.flush()
                except Exception:
                    pass

        # Replace tokens like $name, $size, $type, $format, etc.
        rendered = template
        for key, val in mapping.items():
            rendered = rendered.replace(f"${key}", str(val))

        # Combine prefix parts then the rendered template.
        prefix_part = "_".join([p for p in parts if p])
        if prefix_part:
            name = f"{prefix_part}_{rendered}"
        else:
            name = rendered

        # Ensure suffix presence: if map_suffix not already inside name (end), append
        if map_suffix and not name.endswith(str(map_suffix)):
            name = f"{name}_{map_suffix}"

        # Normalize: replace spaces by underscore and remove duplicate underscores
        name = name.strip()
        name = name.replace(" ", "_")
        while "__" in name:
            name = name.replace("__", "_")

        return name

    def draw_path(self, context, layout):
        row = layout.row()
        row.template_list(
            "QBAKER_UL_folder",
            "",
            dataptr=self,
            propname="folders",
            active_dataptr=self,
            active_propname="folder_index",
            item_dyntip_propname="path",
            rows=4 if len(self.folders) > 1 else 3,
            sort_lock=True,
        )

        col = row.column(align=True)
        col.operator("qbaker.folder_add", text="", icon="ADD")
        col.operator("qbaker.folder_load", text="", icon="FILE_REFRESH")
        col.separator()
        if self.folders:
            if self.folders[self.folder_index].path:
                col.prop(self, "use_sub_folder", text="", icon="NEWFOLDER")

    def draw(self, context, layout):
        col = layout.column()
        col.use_property_split = True

        subcol = col.column(align=True)
        subcol.prop(self, "size")
        if self.size == "CUSTOM":
            subcol.prop(self, "width")
            subcol.prop(self, "height")

        col.prop(self, "format")
        col.prop(self, "anti_aliasing")
        col.prop(context.scene.view_settings, "view_transform", text="Color Management")

        if self.format in {"PNG", "TIFF"}:
            row = col.row(align=True)
            row.prop(self, "color_depth", expand=True)
            if self.format in {"TIFF"}:
                col.prop(self, "tiff_codec")

        if self.format in {"OPEN_EXR"}:
            row = col.row(align=True)
            row.prop(self, "color_depth_exr", expand=True)
            col.prop(self, "exr_codec")

        if self.format in {"PNG"}:
            col.prop(self, "compression")

        if self.format in {"JPEG", "WEBP"}:
            col.prop(self, "quality")

        col.prop(self, "margin_type")
        col.prop(self, "margin", text="Margin Size")
        col.prop(self, "processes")

        # Filename options UI
        box = layout.box()
        box.label(text="Filename Options")
        row = box.row(align=True)
        row.prop(self, "naming_use_custom_prefix", text="Prefix")
        if self.naming_use_custom_prefix:
            box.prop(self, "naming_custom_prefix", text="")

        row = box.row(align=True)
        row.prop(self, "naming_include_date", text="Date")
        row.prop(self, "naming_include_time", text="Time")

        # Allow toggling inclusion of $size token (we hide $name/$object checkboxes here)
        row = box.row(align=True)
        row.prop(self, "naming_include_size", text="Include $size")

        # Name source selection and optional force-to-material filename toggle
        row = box.row(align=True)
        row.prop(self, "naming_name_source", text="Name Source")
        row = box.row(align=True)
        row.prop(self, "naming_force_material_filename", text="Force filename to material")

        row = box.row(align=True)
        row.prop(self, "naming_include_blendname", text="Blend name")
        row.prop(self, "naming_include_collection", text="Collection")

        box.prop(self, "naming_custom_suffix", text="Custom suffix before map suffix")

        # Preview (use example bake group name and $type as placeholder for map suffix)
        try:
            bake_group_name = "BakeGroup"
            if hasattr(context.scene, 'qbaker') and context.scene.qbaker.bake_groups:
                bg_index = context.scene.qbaker.active_bake_group_index
                if context.scene.qbaker.bake_groups:
                    bake_group_name = context.scene.qbaker.bake_groups[bg_index].name
        except Exception:
            bake_group_name = "BakeGroup"
        # Build representative extra tokens for preview so the preview reflects
        # the effect of 'Name Source' and 'Force filename to material'. We attempt
        # to find a representative object and material from the active bake group.
        extra_preview = {}
        try:
            baker = context.scene.qbaker
            bg = baker.bake_groups[baker.active_bake_group_index]
        except Exception:
            bg = None

        if bg:
            # candidate object
            try:
                if getattr(bg, "use_high_to_low", False):
                    objs = [item.object for group in bg.groups for item in group.high_poly]
                else:
                    objs = [item.object for item in bg.objects]
                for o in objs:
                    if o is not None:
                        extra_preview["object"] = o.name
                        break
            except Exception:
                pass

            # candidate material
            try:
                mat_name = None
                for item in getattr(bg, "objects", []):
                    obj = getattr(item, "object", None)
                    if obj and getattr(obj, "material_slots", None):
                        for slot in obj.material_slots:
                            if slot and slot.material:
                                mat_name = slot.material.name
                                break
                    if mat_name:
                        break
                if mat_name:
                    extra_preview["material"] = mat_name
            except Exception:
                pass

        preview_name = self.build_filename(context, bake_group_name=bake_group_name, map_suffix="$type", extra_tokens=extra_preview or None)
        box.label(text=f"Preview: {preview_name}")

        col = layout.column(heading="Post Bake", align=True)
        col.use_property_split = True
        col.prop(self, "use_create_material")
        col.prop(self, "use_duplicate_objects")
        subcol = col.column(align=True)
        subcol.enabled = self.use_duplicate_objects
        subcol.prop(self, "use_join_objects")
        subcol.prop(self, "use_hide_objects")


class QBAKER_PG_bake_group_material(PropertyGroup):
    material: PointerProperty(
        name="Material",
        type=bpy.types.Material,
    )


class QBAKER_PG_bake_group_object(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
    )

    def uv_maps(self, context):
        if self.object:
            return [(uv.name, uv.name, "") for uv in self.object.data.uv_layers]
        else:
            return [("NONE", "None", "")]

    def update_uvmap(self, context):
        if self.object is None or self.object.data is None or not hasattr(self.object.data, "uv_layers"):
            return
        self.object.data.uv_layers.active = self.object.data.uv_layers[self.uv_map]

    uv_map: EnumProperty(
        name="UV Map",
        description="Select a UV Map to bake",
        items=uv_maps,
        update=update_uvmap,
    )

    def update_material_list(self, context):
        if self.materials and self.materials[self.active_material_index].material:
            self.object.material_slots.data.active_material_index = self.object.material_slots.find(
                self.materials[self.active_material_index].material.name
            )

    materials: CollectionProperty(type=QBAKER_PG_bake_group_material)
    active_material_index: IntProperty(
        name="Active Material Index",
        update=update_material_list,
    )

    def get_synchronize_material(self):
        return self.get("synchronize_material", True)

    def set_synchronize_material(self, value):
        if (value or value != self.get("synchronize_material", True)) and self.object:
            self.materials.clear()
            for slot in self.object.material_slots:
                if not slot.material:
                    continue
                material_slot = self.materials.add()
                material_slot.material = slot.material
            self.active_material_index = min(len(self.materials) - 1, self.object.active_material_index)

        self["synchronize_material"] = value

    synchronize_material: BoolProperty(
        name="Synchronize Material",
        get=get_synchronize_material,
        set=set_synchronize_material,
        default=True,
    )


class QBAKER_PG_group_high_poly(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
    )


class QBAKER_PG_group_low_poly(PropertyGroup):
    object: PointerProperty(
        name="Object",
        type=bpy.types.Object,
    )

    def poll_cage_object(self, object):
        return (
            object.type == "MESH"
            and object.users > 0
            and not object.name.startswith(".")  # Ignore hidden objects
            and "_high" not in object.name.lower()
            and "_decal" not in object.name.lower()
            and "_low" not in object.name.lower()
        )

    cage_object: PointerProperty(
        name="Cage Object",
        description="Object to use as cage instead of calculating the cage from the low poly object with cage extrusion",
        type=bpy.types.Object,
        poll=poll_cage_object,
    )

    auto_cage_object: PointerProperty(type=bpy.types.Object)

    def get_extrusion(self):
        if self.get("extrusion_user_hold", False):
            try:
                self["extrusion_user_hold"] = bpy.ops.qbaker.check_press("INVOKE_DEFAULT") != {"FINISHED"}
                if not self["extrusion_user_hold"]:
                    remove_cages(bpy.context)
            except RuntimeError:
                # Suppress error when operator can't be called during drawing/rendering
                pass
        return self.get("cage_extrusion", 0.1)

    def set_extrusion(self, value):
        self["extrusion_user_hold"] = True
        self["cage_extrusion"] = value
        self.get_extrusion()

    cage_extrusion: FloatProperty(
        name="Cage Extrusion",
        description="Inflate the cage object by the specified distance for baking. This helps matching to points nearer to the outside of the high poly objects\n\nAlt  •  Extrude the cage object of all the groups",
        min=0,
        step=0.1,
        default=0.1,
        get=get_extrusion,
        set=set_extrusion,
        update=extrude_cage,
    )

    ray_distance: FloatProperty(
        name="Ray Distance",
        description="The maximum ray distance for matching points between the active and selected objects. If zero, there is no limit.",
        subtype="DISTANCE",
        min=0,
        soft_max=1,
    )

    def uv_maps(self, context):
        if self.object:
            return [(uv.name, uv.name, "") for uv in self.object.data.uv_layers]
        else:
            return [("NONE", "None", "")]

    def update_uvmap(self, context):
        if self.object is None or self.object.data is None or not hasattr(self.object.data, "uv_layers"):
            return
        self.object.data.uv_layers.active = self.object.data.uv_layers[self.uv_map]

    uv_map: EnumProperty(
        name="UV Map",
        description="Select a UV Map to bake",
        items=uv_maps,
        update=update_uvmap,
    )


class QBAKER_PG_group(PropertyGroup):
    use_include: BoolProperty(
        name="Include",
        description="Include this group",
        default=True,
    )

    def update_highpoly_outliner(self, context):
        if self.high_poly and self.high_poly[self.active_high_poly_index].object:
            for obj in context.selected_objects:
                obj.select_set(False)

            self.high_poly[self.active_high_poly_index].object.select_set(True)
            context.view_layer.objects.active = self.high_poly[self.active_high_poly_index].object

    high_poly: CollectionProperty(type=QBAKER_PG_bake_group_object)
    active_high_poly_index: IntProperty(
        name="Active High Poly Index",
        update=update_highpoly_outliner,
    )

    def update_lowpoly_outliner(self, context):
        if self.low_poly and self.low_poly[self.active_low_poly_index].object:
            for obj in context.selected_objects:
                obj.select_set(False)

            self.low_poly[self.active_low_poly_index].object.select_set(True)
            context.view_layer.objects.active = self.low_poly[self.active_low_poly_index].object

    low_poly: CollectionProperty(type=QBAKER_PG_group_low_poly)
    active_low_poly_index: IntProperty(
        name="Active Low Poly Index",
        update=update_lowpoly_outliner,
    )

    use_auto_cage: BoolProperty(
        name="Auto Cage",
        description="Create cage object for every low poly object",
        default=True,
    )


class QBAKER_PG_bake_group(PropertyGroup):
    use_include: BoolProperty(
        name="Include",
        description="Include this bake group",
        default=True,
    )

    use_high_to_low: BoolProperty(
        name="High to Low",
        description="Bake from high to low poly object",
        default=False,
    )

    groups: CollectionProperty(type=QBAKER_PG_group)
    active_group_index: IntProperty(
        name="Active Group Index",
        description="Container for the high and low poly objects",
    )

    def update_outliner(self, context):
        if self.objects and self.objects[self.active_object_index].object:
            for obj in context.selected_objects:
                obj.select_set(False)

            self.objects[self.active_object_index].object.select_set(True)
            context.view_layer.objects.active = self.objects[self.active_object_index].object

    objects: CollectionProperty(type=QBAKER_PG_bake_group_object)
    active_object_index: IntProperty(
        name="Active Object Index",
        update=update_outliner,
    )

    use_uvmap_global: BoolProperty(
        name="Global UV Map",
        description="Same UV Map for all the objects",
        default=True,
    )

    def uv_maps(self, context):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        uvmaps = {}

        if bake_group.use_high_to_low:
            for group in bake_group.groups:
                if group.low_poly:
                    for item in group.low_poly:
                        for uv in item.object.data.uv_layers:
                            uvmaps.setdefault(uv.name, (uv.name, uv.name, ""))
            return list(uvmaps.values())

        for item in bake_group.objects:
            for uv in item.object.data.uv_layers:
                uvmaps.setdefault(uv.name, (uv.name, uv.name, ""))
        return list(uvmaps.values())

    def update_uvmap(self, context):
        baker = self.id_data.qbaker
        bake_group = baker.bake_groups[baker.active_bake_group_index]

        if bake_group.use_high_to_low and bake_group.groups:
            for group in bake_group.groups:
                if group.low_poly:
                    for item in group.low_poly:
                        if self.group_uv_map != "NONE":
                            uv_map = item.object.data.uv_layers.get(
                                self.group_uv_map
                            ) or item.object.data.uv_layers.new(name=self.group_uv_map)
                            item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]

        elif not bake_group.use_high_to_low and bake_group.objects:
            for item in bake_group.objects:
                if self.object_uv_map != "NONE":
                    uv_map = item.object.data.uv_layers.get(self.object_uv_map) or item.object.data.uv_layers.new(
                        name=self.object_uv_map
                    )
                    item.object.data.uv_layers.active = item.object.data.uv_layers[uv_map.name]

    group_uv_map: EnumProperty(
        name="UV Map",
        description="Select a UV Map to bake",
        items=uv_maps,
        update=update_uvmap,
    )

    object_uv_map: EnumProperty(
        name="UV Map",
        description="Select a UV Map to bake",
        items=uv_maps,
        update=update_uvmap,
    )

    maps: CollectionProperty(type=QBAKER_PG_map)
    active_map_index: IntProperty(name="Active Map Index")
    bake: PointerProperty(type=QBAKER_PG_bake)


class QBAKER_PG_material_channel_pack(PropertyGroup):
    type = "CHANNEL_PACK"

    suffix_mapping = {
        "BASE_COLOR": "BC",
        "DISPLACEMENT": "D",
        "EMISSION": "E",
        "GLOSSINESS": "G",
        "METALLIC": "M",
        "NORMAL": "N",
        "ROUGHNESS": "R",
        "SPECULAR": "S",
        "ALPHA": "A",
        "IOR": "IOR",
        "SUBSURFACE_WEIGHT": "SSW",
        "SUBSURFACE_SCALE": "SSCLE",
        "SUBSURFACE_IOR": "SSIOR",
        "SUBSURFACE_ANISOTROPY": "SSA",
        "SPECULAR_TINT": "SPECT",
        "ANISOTROPIC": "ANIS",
        "ANISOTROPIC_ROTATION": "ANISROT",
        "TANGENT": "TANG",
        "TRANSMISSION_WEIGHT": "TRANSW",
        "COAT_WEIGHT": "CW",
        "COAT_ROUGHNESS": "CR",
        "COAT_IOR": "CIOR",
        "COAT_TINT": "CT",
        "COAT_NORMAL": "CN",
        "SHEEN_WEIGHT": "SW",
        "SHEEN_ROUGHNESS": "SR",
        "SHEEN_TINT": "ST",
        "EMISSION_STRENGTH": "ES",
    }

    def get_suffix(self):
        if self.mode == "RGBA":
            suffix = f"{f'{self.suffix_mapping[self.r_channel]}' if self.r_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.g_channel]}' if self.g_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.b_channel]}' if self.b_channel != 'NONE' else ''}{f'_{self.suffix_mapping[self.a_channel]}' if self.a_channel != 'NONE' else ''}"
        else:
            suffix = f"{self.suffix_mapping[self.rgb_channel]}{f'_{self.suffix_mapping[self.a_channel]}' if self.a_channel != 'NONE' else ''}"
        return self.get("suffix", suffix)

    def set_suffix(self, value):
        self["suffix"] = value

    suffix: StringProperty(
        name="Suffix",
        description="Suffix of the map",
        get=get_suffix,
        set=set_suffix,
    )

    mode: EnumProperty(
        name="Mode",
        items=(
            ("RGBA", "Channels", "R + G + B + A"),
            ("RGB_A", "Map + Channel", "RGB + A"),
        ),
        default="RGBA",
    )

    channel_items = (
        ("", "PBR", "", "SHADING_RENDERED", 0),
        ("DISPLACEMENT", "Displacement", "Displacement / Bump Map"),
        ("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"),
        ("METALLIC", "Metallic", "Metallic Map"),
        ("ROUGHNESS", "Roughness", "Roughness Map"),
        ("SPECULAR", "Specular", "Specular Map"),
        ("", "Principled BSDF", "", "NODE", 0),
        ("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"),
        ("IOR", "IOR", "IOR Map"),
        ("SUBSURFACE_WEIGHT", "Subsurface Weight", "Subsurface Weight Map"),
        ("SUBSURFACE_SCALE", "Subsurface Scale", "Subsurface Scale Map"),
        ("SUBSURFACE_IOR", "Subsurface IOR", "Subsurface IOR Map"),
        ("SUBSURFACE_ANISOTROPY", "Subsurface Anisotropy", "Subsurface Anisotropy Map"),
        ("ANISOTROPIC", "Anisotropic", "Anisotropic Map"),
        ("ANISOTROPIC_ROTATION", "Anisotropic Rotation", "Anisotropic Rotation Map"),
        ("TRANSMISSION_WEIGHT", "Transmission Weight", "Transmission Weight Map"),
        ("COAT_WEIGHT", "Coat Weight", "Coat Weight Map"),
        ("COAT_ROUGHNESS", "Coat Roughness", "Coat Roughness Map"),
        ("COAT_IOR", "Coat IOR", "Coat IOR Map"),
        ("SHEEN_WEIGHT", "Sheen Weight", "Sheen Weight Map"),
        ("SHEEN_ROUGHNESS", "Sheen Roughness", "Sheen Roughness Map"),
        ("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"),
        ("", "", "", "", 0),
        ("NONE", "None", ""),
    )

    r_channel: EnumProperty(
        name="R",
        description="Red Channel",
        items=channel_items,
        default="METALLIC",
    )

    g_channel: EnumProperty(
        name="G",
        description="Green Channel",
        items=channel_items,
        default="ROUGHNESS",
    )

    b_channel: EnumProperty(
        name="B",
        description="Blue Channel",
        items=channel_items,
        default="SPECULAR",
    )

    rgb_channel: EnumProperty(
        name="RGB",
        description="RGB Channel",
        items=(
            ("", "PBR", "", "SHADING_RENDERED", 0),
            ("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"),
            ("EMISSION", "Emission", "Emission Map"),
            ("NORMAL", "Normal", "Normal"),
            ("", "Principled BSDF", "", "NODE", 0),
            ("SPECULAR_TINT", "Specular Tint", "Specular Tint Map"),
            ("TANGENT", "Tangent", "Tangent Map"),
            ("COAT_TINT", "Coat Tint", "Coat Tint Map"),
            ("COAT_NORMAL", "Coat Normal", "Coat Normal Map"),
            ("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"),
        ),
        default="BASE_COLOR",
    )

    a_channel: EnumProperty(
        name="A",
        description="Alpha Channel",
        items=channel_items,
        default="ALPHA",
    )

    base_color: PointerProperty(type=QBAKER_PG_base_color)
    displacement: PointerProperty(type=QBAKER_PG_displacement)
    emission: PointerProperty(type=QBAKER_PG_emission)
    glossiness: PointerProperty(type=QBAKER_PG_glossiness)
    metallic: PointerProperty(type=QBAKER_PG_metallic)
    normal: PointerProperty(type=QBAKER_PG_normal)
    roughness: PointerProperty(type=QBAKER_PG_roughness)
    specular: PointerProperty(type=QBAKER_PG_specular)

    ior: PointerProperty(type=QBAKER_PG_ior)
    alpha: PointerProperty(type=QBAKER_PG_alpha)
    subsurface_weight: PointerProperty(type=QBAKER_PG_subsurface_weight)
    subsurface_scale: PointerProperty(type=QBAKER_PG_subsurface_scale)
    subsurface_ior: PointerProperty(type=QBAKER_PG_subsurface_ior)
    subsurface_anisotropy: PointerProperty(type=QBAKER_PG_subsurface_anisotropy)
    specular_tint: PointerProperty(type=QBAKER_PG_specular_tint)
    anisotropic: PointerProperty(type=QBAKER_PG_anisotropic)
    anisotropic_rotation: PointerProperty(type=QBAKER_PG_anisotropic_rotation)
    tangent: PointerProperty(type=QBAKER_PG_tangent)
    transmission_weight: PointerProperty(type=QBAKER_PG_transmission_weight)
    coat_weight: PointerProperty(type=QBAKER_PG_coat_weight)
    coat_roughness: PointerProperty(type=QBAKER_PG_coat_roughness)
    coat_ior: PointerProperty(type=QBAKER_PG_coat_ior)
    coat_tint: PointerProperty(type=QBAKER_PG_coat_tint)
    coat_normal: PointerProperty(type=QBAKER_PG_coat_normal)
    sheen_weight: PointerProperty(type=QBAKER_PG_sheen_weight)
    sheen_roughness: PointerProperty(type=QBAKER_PG_sheen_roughness)
    sheen_tint: PointerProperty(type=QBAKER_PG_sheen_tint)
    emission_strength: PointerProperty(type=QBAKER_PG_emission_strength)

    custom: BoolProperty(
        name="Custom",
        description="Custom bake settings",
    )

    bake: PointerProperty(type=QBAKER_PG_bake_settings)

    def draw(self, context, layout):
        col = layout.column()
        col.prop(self, "suffix")
        col.prop(self, "mode")

        col = layout.column()
        if self.mode == "RGBA":
            col.prop(self, "r_channel")
            col.prop(self, "g_channel")
            col.prop(self, "b_channel")
        else:
            col.prop(self, "rgb_channel")
        col.prop(self, "a_channel")

        col.prop(self, "custom")
        if self.custom:
            self.bake.draw(context, layout)

    def get_single_channel_map(self, channel):
        if channel == "DISPLACEMENT":
            return self.displacement
        elif channel == "GLOSSINESS":
            return self.glossiness
        elif channel == "METALLIC":
            return self.metallic
        elif channel == "ROUGHNESS":
            return self.roughness
        elif channel == "SPECULAR":
            return self.specular

        elif channel == "ALPHA":
            return self.alpha
        elif channel == "IOR":
            return self.ior
        elif channel == "SUBSURFACE_WEIGHT":
            return self.subsurface_weight
        elif channel == "SUBSURFACE_SCALE":
            return self.subsurface_scale
        elif channel == "SUBSURFACE_IOR":
            return self.subsurface_ior
        elif channel == "SUBSURFACE_ANISOTROPY":
            return self.subsurface_anisotropy
        elif channel == "ANISOTROPIC":
            return self.anisotropic
        elif channel == "ANISOTROPIC_ROTATION":
            return self.anisotropic_rotation
        elif channel == "TRANSMISSION_WEIGHT":
            return self.transmission_weight
        elif channel == "COAT_WEIGHT":
            return self.coat_weight
        elif channel == "COAT_ROUGHNESS":
            return self.coat_roughness
        elif channel == "COAT_IOR":
            return self.coat_ior
        elif channel == "SHEEN_WEIGHT":
            return self.sheen_weight
        elif channel == "SHEEN_ROUGHNESS":
            return self.sheen_roughness
        elif channel == "EMISSION_STRENGTH":
            return self.emission_strength

    def get_multi_channel_map(self, channel):
        if channel == "BASE_COLOR":
            return self.base_color
        elif channel == "EMISSION":
            return self.emission
        elif channel == "NORMAL":
            return self.normal

        elif channel == "SPECULAR_TINT":
            return self.specular_tint
        elif channel == "TANGENT":
            return self.tangent
        elif channel == "COAT_TINT":
            return self.coat_tint
        elif channel == "COAT_NORMAL":
            return self.coat_normal
        elif channel == "SHEEN_TINT":
            return self.sheen_tint


class QBAKER_PG_material_map(PropertyGroup):
    label: StringProperty()

    use_include: BoolProperty(
        name="Include",
        description="Include this map",
        default=True,
    )

    type: EnumProperty(
        name="Map Type",
        description="Map type",
        items=(
            ("BASE_COLOR", "Base Color", "Base Color / Albedo / Diffuse Map"),
            ("DISPLACEMENT", "Displacement", "Displacement / Bump Map"),
            ("EMISSION", "Emission", "Emission Map"),
            ("GLOSSINESS", "Glossiness", "Glossiness / Smoothness Map"),
            ("METALLIC", "Metallic", "Metallic Map"),
            ("NORMAL", "Normal", "Normal Map"),
            ("ROUGHNESS", "Roughness", "Roughness Map"),
            ("SPECULAR", "Specular", "Specular Map"),
            ("CHANNEL_PACK", "Channel Pack", "Channel Pack Map"),
            ("ALPHA", "Alpha", "Alpha / Opacity / Transparency Map"),
            ("IOR", "IOR", "IOR Map"),
            ("SUBSURFACE_WEIGHT", "Subsurface Weight", "Subsurface Weight Map"),
            ("SUBSURFACE_SCALE", "Subsurface Scale", "Subsurface Scale Map"),
            ("SUBSURFACE_IOR", "Subsurface IOR", "Subsurface IOR Map"),
            ("SUBSURFACE_ANISOTROPY", "Subsurface Anisotropy", "Subsurface Anisotropy Map"),
            ("SPECULAR_TINT", "Specular Tint", "Specular Tint Map"),
            ("ANISOTROPIC", "Anisotropic", "Anisotropic Map"),
            ("ANISOTROPIC_ROTATION", "Anisotropic Rotation", "Anisotropic Rotation Map"),
            ("TANGENT", "Tangent", "Tangent Map"),
            ("TRANSMISSION_WEIGHT", "Transmission Weight", "Transmission Weight Map"),
            ("COAT_WEIGHT", "Coat Weight", "Coat Weight Map"),
            ("COAT_ROUGHNESS", "Coat Roughness", "Coat Roughness Map"),
            ("COAT_IOR", "Coat IOR", "Coat IOR Map"),
            ("COAT_TINT", "Coat Tint", "Coat Tint Map"),
            ("COAT_NORMAL", "Coat Normal", "Coat Normal Map"),
            ("SHEEN_WEIGHT", "Sheen Weight", "Sheen Weight Map"),
            ("SHEEN_ROUGHNESS", "Sheen Roughness", "Sheen Roughness Map"),
            ("SHEEN_TINT", "Sheen Tint", "Sheen Tint Map"),
            ("EMISSION_STRENGTH", "Emission Strength", "Emission Strength Map"),
        ),
    )

    # PBR
    base_color: PointerProperty(type=QBAKER_PG_base_color)
    displacement: PointerProperty(type=QBAKER_PG_displacement)
    emission: PointerProperty(type=QBAKER_PG_emission)
    glossiness: PointerProperty(type=QBAKER_PG_glossiness)
    metallic: PointerProperty(type=QBAKER_PG_metallic)
    normal: PointerProperty(type=QBAKER_PG_normal)
    roughness: PointerProperty(type=QBAKER_PG_roughness)
    specular: PointerProperty(type=QBAKER_PG_specular)
    channel_pack: PointerProperty(type=QBAKER_PG_material_channel_pack)

    # Principled BSDF
    alpha: PointerProperty(type=QBAKER_PG_alpha)
    ior: PointerProperty(type=QBAKER_PG_ior)
    subsurface_weight: PointerProperty(type=QBAKER_PG_subsurface_weight)
    subsurface_scale: PointerProperty(type=QBAKER_PG_subsurface_scale)
    subsurface_ior: PointerProperty(type=QBAKER_PG_subsurface_ior)
    subsurface_anisotropy: PointerProperty(type=QBAKER_PG_subsurface_anisotropy)
    specular_tint: PointerProperty(type=QBAKER_PG_specular_tint)
    anisotropic: PointerProperty(type=QBAKER_PG_anisotropic)
    anisotropic_rotation: PointerProperty(type=QBAKER_PG_anisotropic_rotation)
    tangent: PointerProperty(type=QBAKER_PG_tangent)
    transmission_weight: PointerProperty(type=QBAKER_PG_transmission_weight)
    coat_weight: PointerProperty(type=QBAKER_PG_coat_weight)
    coat_roughness: PointerProperty(type=QBAKER_PG_coat_roughness)
    coat_ior: PointerProperty(type=QBAKER_PG_coat_ior)
    coat_tint: PointerProperty(type=QBAKER_PG_coat_tint)
    coat_normal: PointerProperty(type=QBAKER_PG_coat_normal)
    sheen_weight: PointerProperty(type=QBAKER_PG_sheen_weight)
    sheen_roughness: PointerProperty(type=QBAKER_PG_sheen_roughness)
    sheen_tint: PointerProperty(type=QBAKER_PG_sheen_tint)
    emission_strength: PointerProperty(type=QBAKER_PG_emission_strength)

    def draw(self, context, layout):
        layout.enabled = self.use_include

        if self.type == "BASE_COLOR":
            self.base_color.draw(context, layout)
        elif self.type == "DISPLACEMENT":
            self.displacement.draw(context, layout)
        elif self.type == "EMISSION":
            self.emission.draw(context, layout)
        elif self.type == "GLOSSINESS":
            self.glossiness.draw(context, layout)
        elif self.type == "METALLIC":
            self.metallic.draw(context, layout)
        elif self.type == "NORMAL":
            self.normal.draw(context, layout)
        elif self.type == "OCCLUSION":
            self.occlusion.draw(context, layout)
        elif self.type == "ROUGHNESS":
            self.roughness.draw(context, layout)
        elif self.type == "SPECULAR":
            self.specular.draw(context, layout)
        elif self.type == "CHANNEL_PACK":
            self.channel_pack.draw(context, layout)

        elif self.type == "ALPHA":
            self.alpha.draw(context, layout)
        elif self.type == "IOR":
            self.ior.draw(context, layout)
        elif self.type == "SUBSURFACE_WEIGHT":
            self.subsurface_weight.draw(context, layout)
        elif self.type == "SUBSURFACE_SCALE":
            self.subsurface_scale.draw(context, layout)
        elif self.type == "SUBSURFACE_IOR":
            self.subsurface_ior.draw(context, layout)
        elif self.type == "SUBSURFACE_ANISOTROPY":
            self.subsurface_anisotropy.draw(context, layout)
        elif self.type == "SPECULAR_TINT":
            self.specular_tint.draw(context, layout)
        elif self.type == "ANISOTROPIC":
            self.anisotropic.draw(context, layout)
        elif self.type == "ANISOTROPIC_ROTATION":
            self.anisotropic_rotation.draw(context, layout)
        elif self.type == "TANGENT":
            self.tangent.draw(context, layout)
        elif self.type == "TRANSMISSION_WEIGHT":
            self.transmission_weight.draw(context, layout)
        elif self.type == "COAT_WEIGHT":
            self.coat_weight.draw(context, layout)
        elif self.type == "COAT_ROUGHNESS":
            self.coat_roughness.draw(context, layout)
        elif self.type == "COAT_IOR":
            self.coat_ior.draw(context, layout)
        elif self.type == "COAT_TINT":
            self.coat_tint.draw(context, layout)
        elif self.type == "COAT_NORMAL":
            self.coat_normal.draw(context, layout)
        elif self.type == "SHEEN_WEIGHT":
            self.sheen_weight.draw(context, layout)
        elif self.type == "SHEEN_ROUGHNESS":
            self.sheen_roughness.draw(context, layout)
        elif self.type == "SHEEN_TINT":
            self.sheen_tint.draw(context, layout)
        elif self.type == "EMISSION_STRENGTH":
            self.emission_strength.draw(context, layout)


class QBAKER_PG_material_bake(PropertyGroup):
    folders: CollectionProperty(type=QBAKER_PG_folder)
    folder_index: IntProperty(name="Active Folder Index")

    use_sub_folder: BoolProperty(
        name="Sub Folder",
        description="Create a sub folder for baked textures\n\nNote: The sub folder name will be the same as the material name",
        default=False,
    )

    batch_name: StringProperty(
        name="Batch Name",
        description="Name the maps with additional info\n\n$material  - Name of the material\n$size          - Size of the map\n$type         - Type of the map",
        default="$material_$size_$type",
    )

    size: EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("512", "512", "512x512 px"),
            ("1024", "1K", "1024x1024 px"),
            ("2048", "2K", "2048x2048 px"),
            ("4096", "4K", "4096x4096 px"),
            ("8192", "8K", "8192x8192 px"),
            ("CUSTOM", "Custom", "Custom bake size"),
        ),
        default="1024",
    )

    width: IntProperty(
        name="Width",
        description="Number of horizontal pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    height: IntProperty(
        name="Height",
        description="Number of vertical pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    anti_aliasing: EnumProperty(
        name="Anti-Aliasing",
        description="Super-sampling level for anti-aliasing",
        items=(
            ("1", "None", "No anti-aliasing"),
            ("2", "2x", "2x samples"),
            ("4", "4x", "4x samples"),
            ("8", "8x", "8x samples"),
            ("16", "16x", "16x samples"),
        ),
        default="1",
    )

    format: EnumProperty(
        name="Format",
        description="File format to save the rendered images as",
        items=(
            ("PNG", "PNG", "Output image in PNG format"),
            ("JPEG", "JPEG", "Output image in JPEG format"),
            ("TARGA", "Targa", "Output image in Targa format"),
            ("TIFF", "TIFF", "Output image in TIFF format"),
            ("OPEN_EXR", "OpenEXR", "Output image in OpenEXR format"),
            ("HDR", "Radiance HDR", "Output image in Radiance HDR format"),
            ("WEBP", "WebP", "Output image in WebP format"),
        ),
        default="PNG",
    )

    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("8", "8", "8-bit color channels"),
            ("16", "16", "16-bit color channels"),
        ),
    )

    color_depth_exr: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("16", "16", "16-bit color channels"),
            ("32", "32", "32-bit color channels"),
        ),
        default="32",
    )

    compression: IntProperty(
        name="Compression",
        description="Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=15,
    )

    quality: IntProperty(
        name="Quality",
        description="Quality for image formats that support lossy compression",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=90,
    )

    exr_codec: EnumProperty(
        name="Codec",
        description="Codec settings for OpenEXR",
        items=(
            ("NONE", "None", ""),
            ("PXR24", "Pxr24 (lossy)", ""),
            ("ZIP", "ZIP (lossless)", ""),
            ("PIZ", "PIZ (lossless)", ""),
            ("RLE", "RLE (lossless)", ""),
            ("ZIPS", "ZIPS (lossless)", ""),
            ("B44", "B44 (lossy)", ""),
            ("B44A", "B44A (lossy)", ""),
            ("DWAA", "DWAA (lossy)", ""),
            ("DWAB", "DWAB (lossy)", ""),
        ),
        default="ZIP",
    )

    tiff_codec: EnumProperty(
        name="Compression",
        description="Compression mode for TIFF",
        items=(
            ("NONE", "None", ""),
            ("DEFLATE", "Deflate", ""),
            ("LZW", "LZW", ""),
            ("PACKBITS", "Pack Bits", ""),
        ),
        default="DEFLATE",
    )

    margin_type: EnumProperty(
        name="Margin Type",
        description="Algorithm to extend the baked result",
        items=(
            (
                "ADJACENT_FACES",
                "Adjacent Faces",
                "Use pixels from adjacent faces across UV seams",
            ),
            ("EXTEND", "Extend", "Extend border pixels outwards"),
        ),
        default="ADJACENT_FACES",
    )

    margin: IntProperty(
        name="Margin Size",
        description="Extends the baked result as a post process filter",
        subtype="PIXEL",
        min=0,
        soft_max=64,
        default=8,
    )

    def get_cpu_count():
        try:
            cpu_count = len(os.sched_getaffinity(0))
        except AttributeError:
            cpu_count = os.cpu_count()
        return cpu_count

    processes: IntProperty(
        name="Processes",
        description="Processes used while baking\nUse lower number if you bake 4K or higher to avoid 'Out of Memory' error",
        min=1,
        soft_max=get_cpu_count() // 4,
        max=get_cpu_count() // 2,
        default=1,
    )

    def draw_path(self, context, layout):
        row = layout.row()
        row.template_list(
            "QBAKER_UL_material_folder",
            "",
            dataptr=self,
            propname="folders",
            active_dataptr=self,
            active_propname="folder_index",
            item_dyntip_propname="path",
            rows=4 if len(self.folders) > 1 else 3,
            sort_lock=True,
        )

        col = row.column(align=True)
        col.operator("qbaker.material_bake_folder_add", text="", icon="ADD")
        col.operator("qbaker.material_bake_folder_load", text="", icon="FILE_REFRESH")
        col.separator()
        if self.folders:
            if self.folders[self.folder_index].path:
                col.prop(self, "use_sub_folder", text="", icon="NEWFOLDER")

    def draw(self, context, layout):
        col = layout.column()
        col.use_property_split = True

        col.prop(self, "batch_name", text="Name")

        subcol = col.column(align=True)
        subcol.prop(self, "size")
        if self.size == "CUSTOM":
            subcol.prop(self, "width")
            subcol.prop(self, "height")

        col.prop(self, "format")
        col.prop(context.scene.view_settings, "view_transform", text="Color Management")

        if self.format in {"PNG", "TIFF"}:
            row = col.row(align=True)
            row.prop(self, "color_depth", expand=True)
            if self.format in {"TIFF"}:
                col.prop(self, "tiff_codec")

        if self.format in {"OPEN_EXR"}:
            row = col.row(align=True)
            row.prop(self, "color_depth_exr", expand=True)
            col.prop(self, "exr_codec")

        if self.format in {"PNG"}:
            col.prop(self, "compression")

        if self.format in {"JPEG", "WEBP"}:
            col.prop(self, "quality")

        col.prop(self, "margin_type")
        col.prop(self, "margin", text="Margin Size")
        col.prop(self, "processes")


class QBAKER_PG_material(PropertyGroup):
    material: PointerProperty(
        name="Material",
        type=bpy.types.Material,
    )

    maps: CollectionProperty(type=QBAKER_PG_material_map)
    active_map_index: IntProperty(name="Active Map Index")

    bake: PointerProperty(type=QBAKER_PG_material_bake)


class QBAKER_PG_material_baker(PropertyGroup):
    materials: CollectionProperty(type=QBAKER_PG_material)
    active_material_index: IntProperty(name="Active Material Index")

    use_map_global: BoolProperty(
        name="Global Maps",
        description="Same maps for all the materials",
        default=True,
    )

    maps: CollectionProperty(type=QBAKER_PG_material_map)
    active_map_index: IntProperty(name="Active Map Index")

    use_bake_global: BoolProperty(
        name="Global Bake",
        description="Same bake settings for all the materials",
        default=True,
    )

    bake: PointerProperty(type=QBAKER_PG_material_bake)

    progress: IntProperty(
        name="Progress",
        min=-1,
        soft_min=0,
        soft_max=100,
        max=100,
        subtype="PERCENTAGE",
        default=-1,
    )


class QBAKER_PG_node_baker(PropertyGroup):
    batch_name: StringProperty(
        name="Batch Name",
        description="Name the maps with additional info\n\n$node     - Name of the node\n$size       - Size of the texture\n$socket  - Name of the node socket\n$uvmap  - Name of the selected uv map",
        default="$node_$size_$socket",
    )

    def build_filename(self, context, bake_group_name: str, map_suffix: str, extra_tokens: dict = None):
        """
        Build filename for node baker templates. Supports tokens: $node, $size, $socket, $uvmap.
        Returns a normalized filename base (no UDIM/extension).
        """
        template = self.batch_name or "$node_$size_$socket"

        size_str = (
            f"{self.width}x{self.height}" if getattr(self, "size", "") == "CUSTOM" else getattr(self, "size", "")
        )

        mapping = {
            "node": bake_group_name,
            "size": size_str,
            "socket": str(extra_tokens.get("socket", "")) if extra_tokens else "",
            "uvmap": str(extra_tokens.get("uvmap", "")) if extra_tokens else "",
        }

        if extra_tokens:
            mapping.update({str(k): str(v) for k, v in extra_tokens.items()})

        rendered = template
        for key, val in mapping.items():
            rendered = rendered.replace(f"${key}", str(val))

        name = rendered
        if map_suffix and not name.endswith(str(map_suffix)):
            name = f"{name}_{map_suffix}"

        name = name.strip().replace(" ", "_")
        while "__" in name:
            name = name.replace("__", "_")

        return name

    use_auto_udim: BoolProperty(
        name="Auto UDIM",
        description="Automatically create UDIM textures based on UV layout",
        default=True,
    )

    folders: CollectionProperty(type=QBAKER_PG_folder)
    folder_index: IntProperty(name="Active Folder Index")

    use_sub_folder: BoolProperty(
        name="Sub Folder",
        description="Create a sub folder for baked textures\n\nNote: The sub folder name will be the same as the node name",
        default=False,
    )

    size: EnumProperty(
        name="Size",
        description="Texture size",
        items=(
            ("512", "512", "512x512 px"),
            ("1024", "1K", "1024x1024 px"),
            ("2048", "2K", "2048x2048 px"),
            ("4096", "4K", "4096x4096 px"),
            ("8192", "8K", "8192x8192 px"),
            ("CUSTOM", "Custom", "Custom bake size"),
        ),
        default="1024",
    )

    width: IntProperty(
        name="Width",
        description="Number of horizontal pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    height: IntProperty(
        name="Height",
        description="Number of vertical pixels",
        subtype="PIXEL",
        min=2,
        default=1024,
    )

    format: EnumProperty(
        name="Format",
        description="File format to save the rendered images as",
        items=(
            ("PNG", "PNG", "Output image in PNG format"),
            ("JPEG", "JPEG", "Output image in JPEG format"),
            ("TARGA", "Targa", "Output image in Targa format"),
            ("TIFF", "TIFF", "Output image in TIFF format"),
            ("OPEN_EXR", "OpenEXR", "Output image in OpenEXR format"),
            ("HDR", "Radiance HDR", "Output image in Radiance HDR format"),
            ("WEBP", "WebP", "Output image in WebP format"),
        ),
        default="PNG",
    )

    color_depth: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("8", "8", "8-bit color channels"),
            ("16", "16", "16-bit color channels"),
        ),
    )

    color_depth_exr: EnumProperty(
        name="Color Depth",
        description="Bit depth per channel",
        items=(
            ("16", "16", "16-bit color channels"),
            ("32", "32", "32-bit color channels"),
        ),
        default="32",
    )

    compression: IntProperty(
        name="Compression",
        description="Amount of time to determine best compression: 0 = no compression with fast file output, 100 = maximum lossless compression with slow file output",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=15,
    )

    quality: IntProperty(
        name="Quality",
        description="Quality for image formats that support lossy compression",
        subtype="PERCENTAGE",
        min=0,
        max=100,
        default=90,
    )

    exr_codec: EnumProperty(
        name="Codec",
        description="Codec settings for OpenEXR",
        items=(
            ("NONE", "None", ""),
            ("PXR24", "Pxr24 (lossy)", ""),
            ("ZIP", "ZIP (lossless)", ""),
            ("PIZ", "PIZ (lossless)", ""),
            ("RLE", "RLE (lossless)", ""),
            ("ZIPS", "ZIPS (lossless)", ""),
            ("B44", "B44 (lossy)", ""),
            ("B44A", "B44A (lossy)", ""),
            ("DWAA", "DWAA (lossy)", ""),
            ("DWAB", "DWAB (lossy)", ""),
        ),
        default="ZIP",
    )

    tiff_codec: EnumProperty(
        name="Compression",
        description="Compression mode for TIFF",
        items=(
            ("NONE", "None", ""),
            ("DEFLATE", "Deflate", ""),
            ("LZW", "LZW", ""),
            ("PACKBITS", "Pack Bits", ""),
        ),
        default="DEFLATE",
    )

    margin_type: EnumProperty(
        name="Margin Type",
        description="Algorithm to extend the baked result",
        items=(
            (
                "ADJACENT_FACES",
                "Adjacent Faces",
                "Use pixels from adjacent faces across UV seams",
            ),
            ("EXTEND", "Extend", "Extend border pixels outwards"),
        ),
        default="ADJACENT_FACES",
    )

    margin: IntProperty(
        name="Margin Size",
        description="Extends the baked result as a post process filter",
        subtype="PIXEL",
        min=0,
        soft_max=64,
        default=8,
    )

    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1,
        soft_max=128,
        default=1,
    )

    def uv_maps(self, context):
        if context.object and context.object.type == "MESH":
            return [(uv.name, uv.name, "") for uv in context.object.data.uv_layers]
        else:
            return [("NONE", "None", "")]

    def update_uv_map(self, context):
        if context.object is None or context.object.data is None or not hasattr(context.object.data, "uv_layers"):
            return

        context.object.data.uv_layers.active = context.object.data.uv_layers[self.uv_map]

    uv_map: EnumProperty(
        name="UV Map",
        description="Select a UV Map to bake",
        items=uv_maps,
        update=update_uv_map,
    )

    def sockets(self, context):
        if context.active_node and context.active_node.outputs:
            return [(output.name, output.name, "") for output in context.active_node.outputs]
        else:
            return [("NONE", "None", "")]

    socket: EnumProperty(
        name="Socket",
        description="Select the output socket of the active node to bake",
        items=sockets,
    )

    use_sockets: BoolProperty(
        name="All Sockets",
        description="Bake all the output sockets of the active node",
    )

    def draw_path(self, context, layout):
        row = layout.row()
        row.template_list(
            "QBAKER_UL_node_folder",
            "",
            dataptr=self,
            propname="folders",
            active_dataptr=self,
            active_propname="folder_index",
            item_dyntip_propname="path",
            rows=4 if len(self.folders) > 1 else 3,
            sort_lock=True,
        )

        col = row.column(align=True)
        col.operator("qbaker.node_bake_folder_add", text="", icon="ADD")
        col.operator("qbaker.node_bake_folder_load", text="", icon="FILE_REFRESH")
        col.separator()
        if self.folders:
            if self.folders[self.folder_index].path:
                col.prop(self, "use_sub_folder", text="", icon="NEWFOLDER")

    def draw(self, context, layout):
        layout.use_property_decorate = False
        layout.use_property_split = True

        col = layout.column()
        col.prop(self, "batch_name", text="Name")

        subcol = col.column(align=True)
        subcol.prop(self, "size")
        if self.size == "CUSTOM":
            subcol.prop(self, "width")
            subcol.prop(self, "height")

        col.prop(self, "margin_type")
        col.prop(self, "margin", text="Margin Size")
        col.prop(self, "samples")

        subcol = col.column()
        subcol.alert = not self.uv_map
        subcol.prop(self, "uv_map")

        subcol = col.column()
        subcol.enabled = not self.use_sockets
        subcol.prop(self, "socket")

        col.prop(self, "use_sockets")


class SCENE_PG_qbaker(PropertyGroup):
    bake_groups: CollectionProperty(type=QBAKER_PG_bake_group)
    active_bake_group_index: IntProperty(
        name="Active Bake Group Index",
        description="Used for the baked texture name",
    )

    use_map_global: BoolProperty(
        name="Global Maps",
        description="Same maps for all the bake groups",
        default=True,
    )

    maps: CollectionProperty(type=QBAKER_PG_map)
    active_map_index: IntProperty(name="Active Map Index")

    use_bake_global: BoolProperty(
        name="Global Bake",
        description="Same bake settings for all the bake groups",
        default=True,
    )

    bake: PointerProperty(type=QBAKER_PG_bake)
    material_baker: PointerProperty(type=QBAKER_PG_material_baker)
    node_baker: PointerProperty(type=QBAKER_PG_node_baker)

    progress: IntProperty(
        name="Progress",
        min=-1,
        soft_min=0,
        soft_max=100,
        max=100,
        subtype="PERCENTAGE",
        default=-1,
    )

    vertex_color_name: StringProperty(
        name="Name",
        description="Vertex color name",
        default="VertexColor",
    )

    vertex_color: FloatVectorProperty(
        name="",
        subtype="COLOR_GAMMA",
        size=3,
        min=0.0,
        max=1.0,
        default=(1, 1, 1),
    )

    def hex_to_rgb(self):
        rgb = [int(self[i : i + 2], 16) for i in (0, 2, 4)]
        r = pow(rgb[0] / 255, 1)
        g = pow(rgb[1] / 255, 1)
        b = pow(rgb[2] / 255, 1)
        return r, g, b

    hex = [
        "FF0000",
        "00FF00",
        "0000FF",
        "FFFF00",
        "FF00FF",
        "00FFFF",
        "F44336",
        "E91E63",
        "9C27B0",
        "673AB7",
        "3F51B5",
        "2196F3",
        "03A9F4",
        "00BCD4",
        "009688",
        "4CAF50",
        "8BC34A",
        "CDDC39",
        "FFEB3B",
        "FFC107",
        "FF9800",
        "FF5722",
        "795548",
        "9E9E9E",
        "607D8B",
    ]

    for h in hex:
        rgb = hex_to_rgb(h)
        exec(
            f"""vc_{h} : FloatVectorProperty(
                            name="#{h}",
                            description='read-only',
                            subtype='COLOR_GAMMA',
                            size=3,
                            min=0.0, max=1.0,
                            default= {rgb},
                            get= lambda self: {rgb},
                            set= lambda self, value: None
                        )"""
        )


classes = (
    QBAKER_PG_bake_settings,
    QBAKER_PG_base_color,
    QBAKER_PG_emission,
    QBAKER_PG_glossiness,
    QBAKER_PG_metallic,
    QBAKER_PG_normal,
    QBAKER_PG_occlusion,
    QBAKER_PG_roughness,
    QBAKER_PG_specular,
    QBAKER_PG_alpha,
    QBAKER_PG_bevel_normal,
    QBAKER_PG_cavity,
    QBAKER_PG_curvature,
    QBAKER_PG_displacement,
    QBAKER_PG_edge,
    QBAKER_PG_gradient,
    QBAKER_PG_height,
    QBAKER_PG_material_id,
    QBAKER_PG_thickness,
    QBAKER_PG_toon_shadow,
    QBAKER_PG_vdm,
    QBAKER_PG_wireframe,
    QBAKER_PG_xyz,
    QBAKER_PG_ior,
    QBAKER_PG_subsurface_weight,
    QBAKER_PG_subsurface_scale,
    QBAKER_PG_subsurface_ior,
    QBAKER_PG_subsurface_anisotropy,
    QBAKER_PG_specular_tint,
    QBAKER_PG_anisotropic,
    QBAKER_PG_anisotropic_rotation,
    QBAKER_PG_tangent,
    QBAKER_PG_transmission_weight,
    QBAKER_PG_coat_weight,
    QBAKER_PG_coat_roughness,
    QBAKER_PG_coat_ior,
    QBAKER_PG_coat_tint,
    QBAKER_PG_coat_normal,
    QBAKER_PG_sheen_weight,
    QBAKER_PG_sheen_roughness,
    QBAKER_PG_sheen_tint,
    QBAKER_PG_emission_strength,
    QBAKER_PG_ambient_occlusion,
    QBAKER_PG_combined,
    QBAKER_PG_diffuse,
    QBAKER_PG_environment,
    QBAKER_PG_glossy,
    QBAKER_PG_position,
    QBAKER_PG_shadow,
    QBAKER_PG_transmission,
    QBAKER_PG_uv,
    QBAKER_PG_channel_pack,
    QBAKER_PG_map,
    QBAKER_PG_folder,
    QBAKER_PG_bake,
    QBAKER_PG_bake_group_material,
    QBAKER_PG_bake_group_object,
    QBAKER_PG_group_high_poly,
    QBAKER_PG_group_low_poly,
    QBAKER_PG_group,
    QBAKER_PG_bake_group,
    QBAKER_PG_material_channel_pack,
    QBAKER_PG_material_bake,
    QBAKER_PG_material_map,
    QBAKER_PG_material,
    QBAKER_PG_material_baker,
    QBAKER_PG_node_baker,
    SCENE_PG_qbaker,
)


# Function to be called when an object is removed
@bpy.app.handlers.persistent
def object_removed(scene):
    baker = scene.qbaker

    if baker.bake_groups:
        for bake_group in baker.bake_groups:
            if bake_group.groups:
                for group in bake_group.groups:
                    if group.high_poly:
                        for item in group.high_poly:
                            if item.object not in list(scene.objects):
                                group.high_poly.remove(group.high_poly.find(item.name))
                                group.active_high_poly_index = min(
                                    max(0, group.active_high_poly_index - 1),
                                    len(group.high_poly) - 1,
                                )
                    if group.low_poly:
                        for item in group.low_poly:
                            if item.object not in list(scene.objects):
                                group.low_poly.remove(group.low_poly.find(item.name))
                                group.active_low_poly_index = min(
                                    max(0, group.active_low_poly_index - 1),
                                    len(group.low_poly) - 1,
                                )

                            if item.cage_object not in list(scene.objects):
                                item.cage_object = None

            if bake_group.objects:
                for item in bake_group.objects:
                    if item.object not in list(scene.objects):
                        bake_group.objects.remove(bake_group.objects.find(item.name))
                        bake_group.active_object_index = min(
                            max(0, bake_group.active_object_index - 1),
                            len(bake_group.objects) - 1,
                        )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.qbaker = PointerProperty(type=SCENE_PG_qbaker)
    bpy.app.handlers.depsgraph_update_post.append(object_removed)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.qbaker
    bpy.app.handlers.depsgraph_update_post.remove(object_removed)
