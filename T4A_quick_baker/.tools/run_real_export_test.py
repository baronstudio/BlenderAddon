# Blender background test script: simulate export by building filenames and writing dummy files
# Usage (example):
# blender "path/to/file.blend" --background --python ".tools/run_real_export_test.py"

import os
import sys
import bpy

OUT_SUBDIR = os.path.join("TestScenes", "BackeOutput")

EXT_MAP = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "TARGA": ".tga",
    "TIFF": ".tif",
    "OPEN_EXR": ".exr",
    "HDR": ".hdr",
    "WEBP": ".webp",
}


def safe_suffix(map_obj):
    # Try common direct attributes
    try:
        val = getattr(map_obj, "suffix", None)
        if val:
            return str(val).strip()
    except Exception:
        pass
    try:
        val = getattr(map_obj, "type", None)
        if val:
            return str(val).strip()
    except Exception:
        pass
    # Try nested known subgroups
    for sub in ("wireframe", "channel_pack", "base_color", "diffuse"):
        try:
            subobj = getattr(map_obj, sub, None)
            if subobj:
                val = getattr(subobj, "suffix", None)
                if val:
                    return str(val).strip()
        except Exception:
            pass
    return ""


def safe_extra_for_bakegroup(bg):
    extra = {}
    # object candidate
    try:
        if getattr(bg, "use_high_to_low", False):
            objs = [item.object for group in bg.groups for item in group.high_poly]
        else:
            objs = [item.object for item in bg.objects]
        for o in objs:
            if o is not None:
                extra["object"] = o.name
                break
    except Exception:
        pass
    # material candidate
    try:
        mat_name = None
        for item in getattr(bg, "objects", []):
            obj = getattr(item, "object", None)
            if obj and getattr(obj, "material_slots", None):
                for slot in obj.material_slots:
                    if slot and slot.material:
                        mat_name = slot.material.name
                        break
            if mat_name:
                break
        if mat_name:
            extra["material"] = mat_name
    except Exception:
        pass
    return extra


def main():
    blend = bpy.data.filepath
    if not blend:
        print("No .blend loaded. Run this script with a .blend file.")
        return

    root = os.path.dirname(bpy.data.filepath)
    out_dir = os.path.join(root, OUT_SUBDIR)
    os.makedirs(out_dir, exist_ok=True)

    # Find qbaker
    if not hasattr(bpy.context.scene, 'qbaker'):
        print("Scene has no qbaker data. Exiting.")
        return

    baker = bpy.context.scene.qbaker
    if not baker.bake_groups:
        print("No bake_groups present. Exiting.")
        return

    bg = baker.bake_groups[baker.active_bake_group_index]
    bake_settings = baker.bake if baker.use_bake_global else bg.bake

    extra_preview = safe_extra_for_bakegroup(bg)

    # iterate maps in bake group
    created = []
    for map_obj in bg.maps:
        if not getattr(map_obj, 'use_include', True):
            continue
        suffix = safe_suffix(map_obj)
        try:
            name = bake_settings.build_filename(bpy.context, bake_group_name=bg.name.strip(), map_suffix=suffix, extra_tokens=extra_preview or None)
        except Exception as e:
            print("build_filename failed:", e)
            name = f"{bg.name.strip()}_{suffix}"

        # choose extension from bake settings format
        fmt = getattr(bake_settings, 'format', 'PNG')
        ext = EXT_MAP.get(fmt, ".png")

        # if UDIM auto, append placeholder
        if getattr(bake_settings, 'use_auto_udim', False):
            filename = name + ext
        else:
            filename = name + ext

        filepath = os.path.join(out_dir, filename)

        # write an empty dummy file (safe)
        try:
            with open(filepath, 'wb') as f:
                f.write(b"")
            created.append(filepath)
            print(f"Created: {filepath}")
        except Exception as e:
            print(f"Failed to write {filepath}: {e}")

    print(f"Done. Created {len(created)} files in {out_dir}")


if __name__ == '__main__':
    main()
