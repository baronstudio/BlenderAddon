import bpy

from . import bake, bake_group, group, material_bake, node_bake, vertex_color

if bpy.app.version >= (4, 0, 0):
    from . import bake_v4 as bake_op
    from . import map_v4 as map
    from . import material_bake_v4 as material_bake_op
    from . import material_map_v4 as material_map
else:
    from . import bake_v3 as bake_op
    from . import map_v3 as map
    from . import material_bake_v3 as material_bake_op
    from . import material_map_v3 as material_map


def register():
    bake_group.register()
    group.register()
    bake.register()
    material_bake.register()
    node_bake.register()
    vertex_color.register()

    bake_op.register()
    map.register()
    material_map.register()
    material_bake_op.register()


def unregister():
    bake_group.unregister()
    group.unregister()
    bake.unregister()
    material_bake.unregister()
    node_bake.unregister()
    vertex_color.unregister()

    bake_op.unregister()
    map.unregister()
    material_map.unregister()
    material_bake_op.unregister()
