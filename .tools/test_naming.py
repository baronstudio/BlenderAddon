import sys
import os

# Ensure repo root is on sys.path
repo_root = r"c:\Travail\DEV\Devdivers\BlenderAddon"
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import bpy
from T4A_quick_baker.source.utils import props_v4

class Dummy:
    def __init__(self):
        # template
        self.batch_name = "$name_$size_$type"
        # filename prefix/suffix options
        self.naming_use_custom_prefix = False
        self.naming_custom_prefix = ""
        self.naming_include_date = False
        self.naming_include_time = False
        self.naming_include_blendname = False
        self.naming_include_collection = False
        self.naming_custom_suffix = ""
        # toggles
        self.naming_include_name = True
        self.naming_include_size = True
        self.naming_include_object = True
        self.naming_name_source = "OBJECT"
        self.naming_force_material_filename = True
        # size
        self.size = "1024"
        self.width = 1024
        self.height = 1024
        # format / margins etc (not used)
        self.format = "PNG"
        self.anti_aliasing = "1"
        self.margin = 8
        self.processes = 1

# Run tests
print("Starting build_filename tests")

d = Dummy()
# Case 1: extra contains object and material
extra = {"object": "MyObject", "material": "MyMaterial"}
res = props_v4.QBAKER_PG_bake.build_filename(d, bpy.context, bake_group_name="BakeGroupName", map_suffix="BC", extra_tokens=extra)
print("With force_material=True => result:", res)

# Case 2: force disabled
d.naming_force_material_filename = False
res2 = props_v4.QBAKER_PG_bake.build_filename(d, bpy.context, bake_group_name="BakeGroupName", map_suffix="BC", extra_tokens=extra)
print("With force_material=False => result:", res2)

# Case 3: Name Source BAKEGROUP but force True and material available
d.naming_name_source = "BAKEGROUP"
d.naming_force_material_filename = True
res3 = props_v4.QBAKER_PG_bake.build_filename(d, bpy.context, bake_group_name="BakeGroupName", map_suffix="BC", extra_tokens=extra)
print("NameSource=BAKEGROUP + force True => result:", res3)

# Exit Blender (script ends)
print("Done tests")
