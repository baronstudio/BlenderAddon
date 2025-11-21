import bpy
import os
import sys

OUT_DIR = "C:\\Travail\\DEV\\Devdivers\\BlenderAddon\\T4A_quick_baker\\TestScenes\\BackeOutput\\"

print("Starting real export naming test")

scene = bpy.context.scene
if not hasattr(scene, 'qbaker'):
    print('No qbaker data in scene')
    sys.exit(1)

baker = scene.qbaker
os.makedirs(OUT_DIR, exist_ok=True)

# Iterate over bake groups
for i, bake_group in enumerate(baker.bake_groups):
    if not bake_group.use_include:
        continue
    bake_settings = baker.bake if baker.use_bake_global else bake_group.bake
    print(f"Testing bake_group [{i}] = {bake_group.name}")

    # determine maps to use
    maps = baker.maps if baker.use_map_global else bake_group.maps
    for map_id, map_obj in enumerate(maps):
        if not map_obj.use_include:
            continue
        # Determine folder path
        folder_base = OUT_DIR
        if bake_settings.folders and bake_settings.folders[bake_settings.folder_index].path:
            base = bake_settings.folders[bake_settings.folder_index].path
            # but user asked to use OUT_DIR — override base to OUT_DIR
            base = OUT_DIR
        else:
            base = OUT_DIR

        folder_name = bake_group.name
        try:
            name_source = getattr(bake_settings, 'naming_name_source', 'BAKEGROUP')
        except Exception:
            name_source = 'BAKEGROUP'

        if name_source == 'OBJECT':
            # try first object
            try:
                if getattr(bake_group, 'use_high_to_low', False):
                    objs = [item.object for group in bake_group.groups for item in group.high_poly]
                else:
                    objs = [item.object for item in bake_group.objects]
                obj_name = None
                for o in objs:
                    if o is not None:
                        obj_name = o.name
                        break
                if obj_name:
                    folder_name = obj_name
            except Exception:
                folder_name = bake_group.name
        elif name_source == 'MATERIAL':
            # find material used
            mat_name = None
            try:
                for item in getattr(bake_group, 'objects', []):
                    obj = getattr(item, 'object', None)
                    if not obj:
                        continue
                    for slot in getattr(obj, 'material_slots', []):
                        if slot and slot.material:
                            mat_name = slot.material.name
                            break
                    if mat_name:
                        break
            except Exception:
                mat_name = None
            folder_name = mat_name or bake_group.name
        else:
            folder_name = bake_group.name

        dest_folder = os.path.join(OUT_DIR, folder_name)
        os.makedirs(dest_folder, exist_ok=True)

        # prepare extra tokens
        extra = {}
        if name_source == 'OBJECT':
            try:
                if getattr(bake_group, 'use_high_to_low', False):
                    objs = [item.object for group in bake_group.groups for item in group.high_poly]
                else:
                    objs = [item.object for item in bake_group.objects]
                for o in objs:
                    if o is not None:
                        extra['object'] = o.name
                        break
            except Exception:
                pass
        elif name_source == 'MATERIAL':
            try:
                for item in getattr(bake_group, 'objects', []):
                    obj = getattr(item, 'object', None)
                    if obj:
                        for slot in getattr(obj, 'material_slots', []):
                            if slot and slot.material:
                                extra['material'] = slot.material.name
                                break
                    if 'material' in extra:
                        break
            except Exception:
                pass

        # if force material filename enabled, try to find material and add token
        try:
            force_mat = getattr(bake_settings, 'naming_force_material_filename', False)
        except Exception:
            force_mat = False
        if force_mat and 'material' not in extra:
            # search for any material on objects
            try:
                if getattr(bake_group, 'use_high_to_low', False):
                    objs = [item.object for group in bake_group.groups for item in group.high_poly]
                else:
                    objs = [item.object for item in bake_group.objects]
                for o in objs:
                    if o is None:
                        continue
                    mats = []
                    if getattr(o, 'material_slots', None):
                        mats = [s.material for s in o.material_slots if s and s.material]
                    if not mats and getattr(o, 'data', None) and getattr(o.data, 'materials', None):
                        mats = [m for m in o.data.materials if m]
                    if mats:
                        extra['material'] = mats[0].name
                        break
            except Exception:
                pass

        # build filename using bake_settings.build_filename
        try:
            filename = bake_settings.build_filename(bpy.context, bake_group_name=bake_group.name.strip(), map_suffix=map_obj.suffix.strip(), extra_tokens=extra or None)
        except Exception as e:
            print('build_filename error:', e)
            filename = f"{bake_group.name.strip()}_{map_obj.suffix.strip()}"

        # append extension according to format
        ext = map_obj.format.lower() if hasattr(map_obj, 'format') else 'png'
        fullpath = os.path.join(dest_folder, f"{filename}.{ext}")

        # create a dummy file to simulate exported texture
        try:
            with open(fullpath, 'wb') as f:
                f.write(b'')
            print(f"WROTE: {fullpath}")
        except Exception as e:
            print('Failed to write file:', fullpath, e)

print('Real export naming test finished')
