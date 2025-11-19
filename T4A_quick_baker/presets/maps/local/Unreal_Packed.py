import bpy
import uuid

baker = bpy.context.scene.qbaker
baker_group = baker.bake_groups[baker.active_bake_group_index]
baker_group.maps.clear()

item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Albedo"
item_sub_1.use_include = True
item_sub_1.type = "BASE_COLOR"
item_sub_1.base_color.name = "Base Color"
item_sub_1.base_color.image = None
item_sub_1.base_color.samples = 1
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
item_sub_1.base_color.suffix = "Albedo"

item_sub_1 = baker_group.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Normal"
item_sub_1.use_include = True
item_sub_1.type = "NORMAL"
item_sub_1.normal.name = "Normal"
item_sub_1.normal.image = None
item_sub_1.normal.suffix = "NormalDX"
item_sub_1.normal.space = "TANGENT"
item_sub_1.normal.type = "DIRECTX"
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

item_sub_1 = baker_group.maps.add()
baker.active_map_index = len(baker_group.maps) - 1
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "OMRA"
item_sub_1.use_include = True
item_sub_1.type = "CHANNEL_PACK"
item_sub_1.channel_pack.name = "Channel Pack"
item_sub_1.channel_pack.suffix = "OMRA"
item_sub_1.channel_pack.mode = "RGBA"
item_sub_1.channel_pack.r_channel = "OCCLUSION"
item_sub_1.channel_pack.g_channel = "METALLIC"
item_sub_1.channel_pack.b_channel = "ROUGHNESS"
item_sub_1.channel_pack.rgb_channel = "BASE_COLOR"
item_sub_1.channel_pack.a_channel = "ALPHA"
item_sub_1.channel_pack.alpha.name = ""
item_sub_1.channel_pack.alpha.image = None
item_sub_1.channel_pack.alpha.samples = 1
item_sub_1.channel_pack.alpha.denoise = False
item_sub_1.channel_pack.alpha.custom = False
item_sub_1.channel_pack.alpha.bake.name = ""
item_sub_1.channel_pack.alpha.bake.size = "1024"

item_sub_1.channel_pack.alpha.bake.format = "PNG"
item_sub_1.channel_pack.alpha.bake.color_depth = "8"
item_sub_1.channel_pack.alpha.bake.color_depth_exr = "32"
item_sub_1.channel_pack.alpha.bake.compression = 15
item_sub_1.channel_pack.alpha.bake.quality = 90
item_sub_1.channel_pack.alpha.bake.exr_codec = "ZIP"
item_sub_1.channel_pack.alpha.bake.tiff_codec = "DEFLATE"
item_sub_1.channel_pack.alpha.suffix = "Alpha"
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
item_sub_1.channel_pack.occlusion.name = ""
item_sub_1.channel_pack.occlusion.image = None
item_sub_1.channel_pack.occlusion.use_preview = False
item_sub_1.channel_pack.occlusion.suffix = "Occlusion"
item_sub_1.channel_pack.occlusion.samples = 10
item_sub_1.channel_pack.occlusion.distance = 0.5
item_sub_1.channel_pack.occlusion.only_local = True
item_sub_1.channel_pack.occlusion.invert_ao = False
item_sub_1.channel_pack.occlusion.denoise = False
item_sub_1.channel_pack.occlusion.custom = False
item_sub_1.channel_pack.occlusion.bake.name = ""
item_sub_1.channel_pack.occlusion.bake.size = "1024"

item_sub_1.channel_pack.occlusion.bake.format = "PNG"
item_sub_1.channel_pack.occlusion.bake.color_depth = "8"
item_sub_1.channel_pack.occlusion.bake.color_depth_exr = "32"
item_sub_1.channel_pack.occlusion.bake.compression = 15
item_sub_1.channel_pack.occlusion.bake.quality = 90
item_sub_1.channel_pack.occlusion.bake.exr_codec = "ZIP"
item_sub_1.channel_pack.occlusion.bake.tiff_codec = "DEFLATE"
item_sub_1.channel_pack.roughness.name = ""
item_sub_1.channel_pack.roughness.image = None
item_sub_1.channel_pack.roughness.samples = 1
item_sub_1.channel_pack.roughness.denoise = False
item_sub_1.channel_pack.roughness.custom = False
item_sub_1.channel_pack.roughness.bake.name = ""
item_sub_1.channel_pack.roughness.bake.size = "1024"

item_sub_1.channel_pack.roughness.bake.format = "PNG"
item_sub_1.channel_pack.roughness.bake.color_depth = "8"
item_sub_1.channel_pack.roughness.bake.color_depth_exr = "32"
item_sub_1.channel_pack.roughness.bake.compression = 15
item_sub_1.channel_pack.roughness.bake.quality = 90
item_sub_1.channel_pack.roughness.bake.exr_codec = "ZIP"
item_sub_1.channel_pack.roughness.bake.tiff_codec = "DEFLATE"
item_sub_1.channel_pack.roughness.suffix = "Roughness"
