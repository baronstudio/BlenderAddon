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
    for map_obj in bg.maps:
        if not getattr(map_obj,'use_include',True):
            continue
        suffix = safe_suffix(map_obj)
        extra = {}
        # try to get object/material
        try:
            if getattr(bg,'use_high_to_low',False):
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
        print('Map', getattr(map_obj,'name','<map>'), '->', name)

if __name__=='__main__':
    main()
