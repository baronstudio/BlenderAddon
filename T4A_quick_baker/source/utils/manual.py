import bpy

manual = (
    # bake groups
    ("bpy.ops.qbaker.bake_group_add", "bake-groups.html#add"),
    ("bpy.ops.qbaker.bake_group_remove", "bake-groups.html#remove"),
    # groups
    ("bpy.ops.qbaker.group_add", "groups.html#add"),
    ("bpy.ops.qbaker.group_remove", "groups.html#remove"),
    ("bpy.ops.qbaker.group_load", "groups.html#load"),
    ("bpy.ops.qbaker.group_select", "groups.html#select"),
    # high poly
    ("bpy.ops.qbaker.high_poly_add", "groups.html#high-poly"),
    ("bpy.ops.qbaker.high_poly_remove", "groups.html#high-poly"),
    # low poly
    ("bpy.ops.qbaker.low_poly_add", "groups.html#low-poly"),
    ("bpy.ops.qbaker.low_poly_remove", "groups.html#low-poly"),
    # objects
    ("bpy.ops.qbaker.object_add", "objects.html#add"),
    ("bpy.ops.qbaker.object_remove", "objects.html#remove"),
    # maps
    ("bpy.ops.qbaker.map_add", "maps.html#add"),
    ("bpy.ops.qbaker.map_preset", "maps.html#preset"),
    ("bpy.ops.qbaker.map_preset_global", "maps.html#preset"),
    # bake
    ("bpy.ops.qbaker.folder_add", "bake.html#add"),
    ("bpy.ops.qbaker.folder_remove", "bake.html#remove"),
    ("bpy.ops.qbaker.folder_load", "bake.html#load"),
    ("bpy.ops.qbaker.node_bake", "bake.html#node"),
    ("bpy.ops.qbaker.bake", "bake.html"),
)


def manual_hook():
    return ("https://b3dhub.github.io/quick-baker-docs/", manual)


def register():
    bpy.utils.register_manual_map(manual_hook)


def unregister():
    bpy.utils.unregister_manual_map(manual_hook)
