import bpy
import uuid

baker = bpy.context.scene.qbaker
baker.maps.clear()

# Base
item_sub_1 = baker.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Base Color"
item_sub_1.use_include = True
item_sub_1.type = "BASE_COLOR"
item_sub_1.base_color.name = ""
item_sub_1.base_color.samples = 1
item_sub_1.base_color.denoise = False
item_sub_1.base_color.custom = False
item_sub_1.base_color.bake.name = ""
item_sub_1.base_color.bake.size = "1024"
item_sub_1.base_color.bake.anti_aliasing = "1"
item_sub_1.base_color.bake.format = "PNG"
item_sub_1.base_color.bake.color_depth = "8"
item_sub_1.base_color.bake.color_depth_exr = "32"
item_sub_1.base_color.bake.compression = 15
item_sub_1.base_color.bake.quality = 90
item_sub_1.base_color.bake.exr_codec = "ZIP"
item_sub_1.base_color.bake.tiff_codec = "DEFLATE"
item_sub_1.base_color.image = None
item_sub_1.base_color.suffix = "Color"
item_sub_1.base_color.use_alpha = True

# Normal
item_sub_1 = baker.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Normal"
item_sub_1.use_include = True
item_sub_1.type = "NORMAL"
item_sub_1.normal.name = ""
item_sub_1.normal.samples = 1
item_sub_1.normal.denoise = False
item_sub_1.normal.custom = False
item_sub_1.normal.bake.name = ""
item_sub_1.normal.bake.size = "1024"
item_sub_1.normal.bake.anti_aliasing = "1"
item_sub_1.normal.bake.format = "PNG"
item_sub_1.normal.bake.color_depth = "8"
item_sub_1.normal.bake.color_depth_exr = "32"
item_sub_1.normal.bake.compression = 15
item_sub_1.normal.bake.quality = 90
item_sub_1.normal.bake.exr_codec = "ZIP"
item_sub_1.normal.bake.tiff_codec = "DEFLATE"
item_sub_1.normal.image = None
item_sub_1.normal.suffix = "NormalGL"
item_sub_1.normal.space = "TANGENT"
item_sub_1.normal.type = "OPENGL"
item_sub_1.normal.r = "POS_X"
item_sub_1.normal.g = "POS_X"
item_sub_1.normal.b = "POS_X"

# Metallic
item_sub_1 = baker.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Metallic"
item_sub_1.use_include = True
item_sub_1.type = "METALLIC"
item_sub_1.metallic.name = ""
item_sub_1.metallic.samples = 1
item_sub_1.metallic.denoise = False
item_sub_1.metallic.custom = False
item_sub_1.metallic.bake.name = ""
item_sub_1.metallic.bake.size = "1024"
item_sub_1.metallic.bake.anti_aliasing = "1"
item_sub_1.metallic.bake.format = "PNG"
item_sub_1.metallic.bake.color_depth = "8"
item_sub_1.metallic.bake.color_depth_exr = "32"
item_sub_1.metallic.bake.compression = 15
item_sub_1.metallic.bake.quality = 90
item_sub_1.metallic.bake.exr_codec = "ZIP"
item_sub_1.metallic.bake.tiff_codec = "DEFLATE"
item_sub_1.metallic.image = None
item_sub_1.metallic.suffix = "Metallic"

# Roughness
item_sub_1 = baker.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Roughness"
item_sub_1.use_include = True
item_sub_1.type = "ROUGHNESS"
item_sub_1.roughness.name = ""
item_sub_1.roughness.samples = 1
item_sub_1.roughness.denoise = False
item_sub_1.roughness.custom = False
item_sub_1.roughness.bake.name = ""
item_sub_1.roughness.bake.size = "1024"
item_sub_1.roughness.bake.anti_aliasing = "1"
item_sub_1.roughness.bake.format = "PNG"
item_sub_1.roughness.bake.color_depth = "8"
item_sub_1.roughness.bake.color_depth_exr = "32"
item_sub_1.roughness.bake.compression = 15
item_sub_1.roughness.bake.quality = 90
item_sub_1.roughness.bake.exr_codec = "ZIP"
item_sub_1.roughness.bake.tiff_codec = "DEFLATE"
item_sub_1.roughness.image = None
item_sub_1.roughness.suffix = "Roughness"

# Emission
item_sub_1 = baker.maps.add()
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Emission"
item_sub_1.use_include = True
item_sub_1.type = "EMISSION"
item_sub_1.emission.name = ""
item_sub_1.emission.samples = 1
item_sub_1.emission.denoise = False
item_sub_1.emission.custom = False
item_sub_1.emission.bake.name = ""
item_sub_1.emission.bake.size = "1024"
item_sub_1.emission.bake.anti_aliasing = "1"
item_sub_1.emission.bake.format = "PNG"
item_sub_1.emission.bake.color_depth = "8"
item_sub_1.emission.bake.color_depth_exr = "32"
item_sub_1.emission.bake.compression = 15
item_sub_1.emission.bake.quality = 90
item_sub_1.emission.bake.exr_codec = "ZIP"
item_sub_1.emission.bake.tiff_codec = "DEFLATE"
item_sub_1.emission.image = None
item_sub_1.emission.suffix = "Emission"
item_sub_1.emission.view_from = "ABOVE_SURFACE"
item_sub_1.emission.non_color = False

# Occlusion
item_sub_1 = baker.maps.add()
baker.active_map_index = len(baker.maps) - 1
item_sub_1.name = uuid.uuid4().hex[:8]
item_sub_1.label = "Occlusion"
item_sub_1.use_include = True
item_sub_1.type = "OCCLUSION"
item_sub_1.occlusion.name = ""
item_sub_1.occlusion.samples = 10
item_sub_1.occlusion.denoise = False
item_sub_1.occlusion.custom = False
item_sub_1.occlusion.bake.name = ""
item_sub_1.occlusion.bake.size = "1024"
item_sub_1.occlusion.bake.anti_aliasing = "1"
item_sub_1.occlusion.bake.format = "PNG"
item_sub_1.occlusion.bake.color_depth = "8"
item_sub_1.occlusion.bake.color_depth_exr = "32"
item_sub_1.occlusion.bake.compression = 15
item_sub_1.occlusion.bake.quality = 90
item_sub_1.occlusion.bake.exr_codec = "ZIP"
item_sub_1.occlusion.bake.tiff_codec = "DEFLATE"
item_sub_1.occlusion.image = None
item_sub_1.occlusion.use_preview = False
item_sub_1.occlusion.suffix = "Occlusion"
item_sub_1.occlusion.distance = 0.5
item_sub_1.occlusion.only_local = True
item_sub_1.occlusion.invert_ao = False
