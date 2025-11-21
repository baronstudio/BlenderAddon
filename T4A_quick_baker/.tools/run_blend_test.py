# Simple Blender background script to print build_filename results for the active bake group
import bpy
import os

def safe_suffix(map_obj):
    val = getattr(map_obj, 'suffix', None)
    if val:
        return str(val).strip()
    val = getattr(map_obj, 'type', None)
    if val:
        return str(val).strip()
    for sub in ('wireframe','channel_pack'):
        subobj = getattr(map_obj, sub, None)
        if subobj:
            val = getattr(subobj,'suffix',None)
            if val:
                return str(val).strip()
    return ''


def main():
    if not hasattr(bpy.context.scene, 'qbaker'):
        print('No qbaker in scene')
        return
    baker = bpy.context.scene.qbaker
    bg = baker.bake_groups[baker.active_bake_group_index]
    bake_settings = baker.bake if baker.use_bake_global else bg.bake
    print('Bake group:', bg.name)
    # Choose maps: prefer bake group maps, but fall back to global maps when configured
    maps_list = []
    try:
        if getattr(baker, 'use_map_global', False) and getattr(baker, 'maps', None):
            maps_list = baker.maps
            print('Using global maps from scene.qbaker (use_map_global=True)')
        else:
            maps_list = bg.maps
    except Exception:
        maps_list = bg.maps

    total_maps = len(maps_list) if hasattr(maps_list, '__len__') else 0
    print(f'Total maps considered: {total_maps}')
    if total_maps == 0:
        print('Note: no maps found in bake group or global maps.')

    for i, map_obj in enumerate(maps_list):
        name_prop = getattr(map_obj, 'name', f'<map_{i}>')
        use_inc = getattr(map_obj, 'use_include', False)
        suffix = safe_suffix(map_obj)
        print(f'Map[{i}] name="{name_prop}", type="{getattr(map_obj, "type", "")}", use_include={use_inc}, suffix="{suffix}"')

        # still compute and print the filename even if not included to aid debugging
        extra = {}
        try:
            if getattr(bg, 'use_high_to_low', False):
                objs = [item.object for group in bg.groups for item in group.high_poly]
            else:
                objs = [item.object for item in bg.objects]
            for o in objs:
                if o:
                    extra['object'] = o.name
                    break
        except Exception:
            pass

        try:
            name = bake_settings.build_filename(bpy.context, bake_group_name=bg.name.strip(), map_suffix=suffix, extra_tokens=extra or None)
        except Exception as e:
            name = f'{bg.name}_{suffix}'
        print('  -> Generated filename:', name)

if __name__=='__main__':
    main()
