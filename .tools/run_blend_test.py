import bpy
import os

print("Running blend test script")

# Attempt to access scene qbaker data
scene = bpy.context.scene
if not hasattr(scene, 'qbaker'):
    print("No scene.qbaker found")
    raise SystemExit(1)

baker = scene.qbaker
if not baker.bake_groups:
    print("No bake groups present")
    raise SystemExit(1)

bg_index = getattr(baker, 'active_bake_group_index', 0)
bake_group = baker.bake_groups[bg_index]
print(f"Using bake_group: {bake_group.name}")

# Get bake props
bake_props = bake_group.bake
print(f"Name Source: {getattr(bake_props, 'naming_name_source', 'MISSING')}")
print(f"Force material filename: {getattr(bake_props, 'naming_force_material_filename', 'MISSING')}")

# Gather candidate objects
objs = []
try:
    if getattr(bake_group, 'use_high_to_low', False):
        for group in bake_group.groups:
            for item in group.high_poly:
                if getattr(item, 'object', None):
                    objs.append(item.object)
    else:
        for item in bake_group.objects:
            if getattr(item, 'object', None):
                objs.append(item.object)
except Exception as e:
    print('Error while gathering objects:', e)

print(f"Found {len(objs)} objects in bake_group")

obj_name = None
mat_name = None
for o in objs:
    if o is None:
        continue
    if not obj_name:
        obj_name = o.name
    # check material slots
    try:
        mats = []
        if hasattr(o, 'material_slots') and o.material_slots:
            mats = [s.material for s in o.material_slots if s and s.material]
        if not mats and hasattr(o, 'data') and hasattr(o.data, 'materials'):
            mats = [m for m in o.data.materials if m]
        if mats and not mat_name:
            mat_name = mats[0].name
    except Exception:
        pass

print('Representative object:', obj_name)
print('Representative material:', mat_name)

extra = {}
if obj_name:
    extra['object'] = obj_name
if mat_name:
    extra['material'] = mat_name

# call build_filename
try:
    # For test: force Name Source = OBJECT and force material filename
    try:
        bake_props.naming_name_source = 'OBJECT'
        bake_props.naming_force_material_filename = True
    except Exception:
        pass

    print('After forcing: Name Source =', getattr(bake_props, 'naming_name_source', None),
          'Force material =', getattr(bake_props, 'naming_force_material_filename', None))

    result = bake_props.build_filename(bpy.context, bake_group_name=bake_group.name.strip(), map_suffix='BC', extra_tokens=extra or None)
    print('build_filename result:', result)
except Exception as e:
    print('build_filename raised:', e)

print('Test script finished')
