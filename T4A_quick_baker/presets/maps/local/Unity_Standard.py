import bpy
import uuid

baker = bpy.context.scene.qbaker
baker_group = baker.bake_groups[baker.active_bake_group_index]
baker_group.maps.clear()

# Albedo
item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Albedo"
item_sub_1.use_include = True
item_sub_1.type = "BASE_COLOR"
item_sub_1.base_color.name = ""
item_sub_1.base_color.suffix = "Albedo"
item_sub_1.base_color.samples = 1
item_sub_1.base_color.use_alpha = True
item_sub_1.base_color.denoise = False
item_sub_1.base_color.custom = False
item_sub_1.base_color.bake.name = ""
item_sub_1.base_color.bake.size = "1024"

item_sub_1.base_color.bake.format = "PNG"
item_sub_1.base_color.bake.color_depth = "8"
item_sub_1.base_color.bake.color_depth_exr = "32"
item_sub_1.base_color.bake.compression = 15
item_sub_1.base_color.bake.quality = 90
item_sub_1.base_color.bake.exr_codec = "ZIP"
item_sub_1.base_color.bake.tiff_codec = "DEFLATE"
item_sub_1.base_color.image = None

# Metallic
item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Metallic"
item_sub_1.use_include = True
item_sub_1.type = "CHANNEL_PACK"
item_sub_1.channel_pack.name = "Channel Pack"
item_sub_1.channel_pack.suffix = "Metallic"
item_sub_1.channel_pack.mode = "RGBA"
item_sub_1.channel_pack.r_channel = "METALLIC"
item_sub_1.channel_pack.g_channel = "NONE"
item_sub_1.channel_pack.b_channel = "NONE"
item_sub_1.channel_pack.rgb_channel = "BASE_COLOR"
item_sub_1.channel_pack.a_channel = "GLOSSINESS"
item_sub_1.channel_pack.glossiness.name = ""
item_sub_1.channel_pack.glossiness.image = None
item_sub_1.channel_pack.glossiness.samples = 1
item_sub_1.channel_pack.glossiness.denoise = False
item_sub_1.channel_pack.glossiness.custom = False
item_sub_1.channel_pack.glossiness.bake.name = ""
item_sub_1.channel_pack.glossiness.bake.size = "1024"

item_sub_1.channel_pack.glossiness.bake.format = "PNG"
item_sub_1.channel_pack.glossiness.bake.color_depth = "8"
item_sub_1.channel_pack.glossiness.bake.color_depth_exr = "32"
item_sub_1.channel_pack.glossiness.bake.compression = 15
item_sub_1.channel_pack.glossiness.bake.quality = 90
item_sub_1.channel_pack.glossiness.bake.exr_codec = "ZIP"
item_sub_1.channel_pack.glossiness.bake.tiff_codec = "DEFLATE"
item_sub_1.channel_pack.glossiness.suffix = "Glossiness"
item_sub_1.channel_pack.metallic.name = ""
item_sub_1.channel_pack.metallic.image = None
item_sub_1.channel_pack.metallic.samples = 1
item_sub_1.channel_pack.metallic.denoise = False
item_sub_1.channel_pack.metallic.custom = False
item_sub_1.channel_pack.metallic.bake.name = ""
item_sub_1.channel_pack.metallic.bake.size = "1024"

item_sub_1.channel_pack.metallic.bake.format = "PNG"
item_sub_1.channel_pack.metallic.bake.color_depth = "8"
item_sub_1.channel_pack.metallic.bake.color_depth_exr = "32"
item_sub_1.channel_pack.metallic.bake.compression = 15
item_sub_1.channel_pack.metallic.bake.quality = 90
item_sub_1.channel_pack.metallic.bake.exr_codec = "ZIP"
item_sub_1.channel_pack.metallic.bake.tiff_codec = "DEFLATE"
item_sub_1.channel_pack.metallic.suffix = "Metallic"

# Normal
item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Normal"
item_sub_1.use_include = True
item_sub_1.type = "NORMAL"
item_sub_1.normal.name = "Normal"
item_sub_1.normal.image = None
item_sub_1.normal.suffix = "NormalGL"
item_sub_1.normal.space = "TANGENT"
item_sub_1.normal.type = "OPENGL"
item_sub_1.normal.r = "POS_X"
item_sub_1.normal.g = "POS_X"
item_sub_1.normal.b = "POS_X"
item_sub_1.normal.samples = 1
item_sub_1.normal.denoise = False
item_sub_1.normal.custom = False
item_sub_1.normal.bake.name = ""
item_sub_1.normal.bake.size = "1024"

item_sub_1.normal.bake.format = "PNG"
item_sub_1.normal.bake.color_depth = "8"
item_sub_1.normal.bake.color_depth_exr = "32"
item_sub_1.normal.bake.compression = 15
item_sub_1.normal.bake.quality = 90
item_sub_1.normal.bake.exr_codec = "ZIP"
item_sub_1.normal.bake.tiff_codec = "DEFLATE"

# Height
item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Height"
item_sub_1.use_include = True
item_sub_1.type = "DISPLACEMENT"
item_sub_1.displacement.name = "Displacement"
item_sub_1.displacement.image = None
item_sub_1.displacement.suffix = "Height"
item_sub_1.displacement.samples = 1
item_sub_1.displacement.invert_displacement = False
item_sub_1.displacement.denoise = False
item_sub_1.displacement.custom = False
item_sub_1.displacement.bake.name = ""
item_sub_1.displacement.bake.size = "1024"

item_sub_1.displacement.bake.format = "PNG"
item_sub_1.displacement.bake.color_depth = "8"
item_sub_1.displacement.bake.color_depth_exr = "32"
item_sub_1.displacement.bake.compression = 15
item_sub_1.displacement.bake.quality = 90
item_sub_1.displacement.bake.exr_codec = "ZIP"
item_sub_1.displacement.bake.tiff_codec = "DEFLATE"

# Occlusion
item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Occlusion"
item_sub_1.use_include = True
item_sub_1.type = "OCCLUSION"
item_sub_1.occlusion.name = "Occlusion"
item_sub_1.occlusion.image = None
item_sub_1.occlusion.use_preview = False
item_sub_1.occlusion.suffix = "Occlusion"
item_sub_1.occlusion.samples = 10
item_sub_1.occlusion.distance = 0.5
item_sub_1.occlusion.only_local = True
item_sub_1.occlusion.invert_ao = False
item_sub_1.occlusion.denoise = False
item_sub_1.occlusion.custom = False
item_sub_1.occlusion.bake.name = ""
item_sub_1.occlusion.bake.size = "1024"

item_sub_1.occlusion.bake.format = "PNG"
item_sub_1.occlusion.bake.color_depth = "8"
item_sub_1.occlusion.bake.color_depth_exr = "32"
item_sub_1.occlusion.bake.compression = 15
item_sub_1.occlusion.bake.quality = 90
item_sub_1.occlusion.bake.exr_codec = "ZIP"
item_sub_1.occlusion.bake.tiff_codec = "DEFLATE"

# Emission
item_sub_1 = baker_group.maps.add()
baker.active_map_index = len(baker_group.maps) - 1
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Emission"
item_sub_1.use_include = True
item_sub_1.type = "EMISSION"
item_sub_1.emission.name = "Emission"
item_sub_1.emission.image = None
item_sub_1.emission.samples = 1
item_sub_1.emission.denoise = False
item_sub_1.emission.custom = False
item_sub_1.emission.bake.name = ""
item_sub_1.emission.bake.size = "1024"

item_sub_1.emission.bake.format = "PNG"
item_sub_1.emission.bake.color_depth = "8"
item_sub_1.emission.bake.color_depth_exr = "32"
item_sub_1.emission.bake.compression = 15
item_sub_1.emission.bake.quality = 90
item_sub_1.emission.bake.exr_codec = "ZIP"
item_sub_1.emission.bake.tiff_codec = "DEFLATE"
item_sub_1.emission.suffix = "Emission"
