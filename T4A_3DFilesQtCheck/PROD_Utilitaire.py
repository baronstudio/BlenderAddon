"""Utilities: parsing, measures and helper operators for T4A addon.

Contient :
- fonctions utilitaires pour parser les dimensions retournées par l'IA
- mesure de bounding box d'une collection
- création / suppression d'objets helper (boîte wireframe)
- opérateur `t4a.clear_helpers` pour nettoyer les helpers créés
"""
import re
import bpy
import mathutils
from typing import Optional, Tuple, Dict

# Si True, force la (re)création d'une helper box même si un objet helper existe déjà
forceHelperBoxCreation: bool = True


def parse_dimensions_string(s: str) -> Dict[str, Optional[float]]:
    """Parse une chaîne de dimensions et renvoie des valeurs en mètres.

    Exemple attendu: "width: 1.23 m; height: 0.45 m; depth: 2.00 m"
    Retourne dict {'width': float|None, 'height': float|None, 'depth': float|None}
    Gère unités m, cm, mm. Si unité manquante, on suppose mètres.
    """
    res = {'width': None, 'height': None, 'depth': None}
    try:
        text = (s or '').lower()
        # split into parts
        parts = [p.strip() for p in re.split(r"[;\n]+", text) if p.strip()]
        for p in parts:
            # find value and optional unit
            m = re.search(r"([a-z]+)\s*[:]?\s*([0-9,.]+)\s*(m|cm|mm)?", p)
            if m:
                key = m.group(1)
                val = float(m.group(2).replace(',', '.'))
                unit = m.group(3) or 'm'
                # normalize to meters
                if unit == 'mm':
                    val = val / 1000.0
                elif unit == 'cm':
                    val = val / 100.0
                # map common key names
                if 'width' in key or 'w' == key:
                    res['width'] = val
                elif 'height' in key or 'h' == key:
                    res['height'] = val
                elif 'depth' in key or 'd' == key or 'length' in key:
                    res['depth'] = val
        return res
    except Exception:
        return res


def measure_collection_bbox(coll: bpy.types.Collection) -> Optional[Dict[str, object]]:
    """Measure axis-aligned world-space bounding box for a collection.

    Retourne dict {'width': w, 'height': h, 'depth': d, 'center': Vector} ou None si impossible.
    Convention: X -> width, Z -> height, Y -> depth.
    """
    try:
        
        objs = [o for o in coll.all_objects if o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}]
        if not objs:
            return None
        coords = []
        for o in objs:
            # Use evaluated bound_box in local space, then transform to world
            try:
                for corner in o.bound_box:
                    v = mathutils.Vector(corner)
                    world_v = o.matrix_world @ v
                    coords.append(world_v)
            except Exception:
                # fallback: use object origin
                coords.append(o.matrix_world.to_translation())

        xs = [v.x for v in coords]
        ys = [v.y for v in coords]
        zs = [v.z for v in coords]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        minz, maxz = min(zs), max(zs)
        width = maxx - minx
        depth = maxy - miny
        height = maxz - minz
        center = mathutils.Vector(((minx + maxx) / 2.0, (miny + maxy) / 2.0, (minz + maxz) / 2.0))
        return {'width': width, 'height': height, 'depth': depth, 'center': center}
    except Exception:
        return None


def create_or_update_helper_box(name: str, dims: Dict[str, float], center: mathutils.Vector) -> bpy.types.Object:
    """Create or update a wireframe helper box named with prefix `T4A_HELPER_`.

    dims keys: width, height, depth (in meters)
    center: world-space center position
    Returns the helper object.
    """
    try:
        helper_name = f"T4A_HELPER_BOX_{name}"
        # remove existing object with same name if present (force recreation if requested)
        existing = bpy.data.objects.get(helper_name)
        if existing and forceHelperBoxCreation:
            try:
                for uc in list(existing.users_collection):
                    try:
                        uc.objects.unlink(existing)
                    except Exception:
                        pass
                bpy.data.objects.remove(existing, do_unlink=True)
                existing = None
            except Exception:
                existing = None

        if existing:
            # update scale and location
            existing.location = center
            existing.scale = ( (dims.get('width',0.0) / 2.0), (dims.get('depth',0.0) / 2.0), (dims.get('height',0.0) / 2.0) )
            return existing

        # create cube
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=center)
        obj = bpy.context.active_object
        if obj is None:
            # fallback: create mesh data manually
            mesh = bpy.data.meshes.new(helper_name + '_mesh')
            obj = bpy.data.objects.new(helper_name, mesh)
            bpy.context.collection.objects.link(obj)

        obj.name = helper_name
        obj.scale = ( (dims.get('width',0.0) / 2.0), (dims.get('depth',0.0) / 2.0), (dims.get('height',0.0) / 2.0) )
        # ensure in helpers collection
        coll_name = 'T4A_Helpers'
        coll = bpy.data.collections.get(coll_name)
        if coll is None:
            coll = bpy.data.collections.new(coll_name)
            try:
                bpy.context.scene.collection.children.link(coll)
            except Exception:
                pass
        # link object to helpers collection and unlink from others
        try:
            for uc in list(obj.users_collection):
                try:
                    uc.objects.unlink(obj)
                except Exception:
                    pass
            if obj.name not in [o.name for o in coll.objects]:
                coll.objects.link(obj)
        except Exception:
            pass

        # display wire
        try:
            obj.display_type = 'WIRE'
        except Exception:
            try:
                obj.show_wire = True
            except Exception:
                pass

        # try to set color material (best-effort)
        try:
            mat_name = 'T4A_Helper_Red'
            mat = bpy.data.materials.get(mat_name)
            if mat is None:
                mat = bpy.data.materials.new(mat_name)
                mat.diffuse_color = (1.0, 0.0, 0.0, 1.0)
            if obj.data and hasattr(obj.data, 'materials'):
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(mat)
                else:
                    obj.data.materials[0] = mat
        except Exception:
            pass

        return obj
    except Exception:
        return None


class T4A_OT_ClearHelpers(bpy.types.Operator):
    bl_idname = 't4a.clear_helpers'
    bl_label = 'Clear T4A Helpers'
    bl_description = 'Remove T4A helper objects and helper collection'

    def execute(self, context):
        removed = 0
        try:
            # remove objects with helper prefix
            prefix = 'T4A_HELPER_'
            for obj in list(bpy.data.objects):
                if obj.name.startswith(prefix):
                    try:
                        # unlink from collections then remove
                        for uc in list(obj.users_collection):
                            try:
                                uc.objects.unlink(obj)
                            except Exception:
                                pass
                        bpy.data.objects.remove(obj, do_unlink=True)
                        removed += 1
                    except Exception:
                        pass

            # remove helpers collection if exists
            coll = bpy.data.collections.get('T4A_Helpers')
            if coll:
                try:
                    # unlink from scene and remove
                    for parent in list(bpy.context.scene.collection.children):
                        if parent.name == coll.name:
                            try:
                                bpy.context.scene.collection.children.unlink(coll)
                            except Exception:
                                pass
                    # remove objects inside coll
                    for o in list(coll.objects):
                        try:
                            coll.objects.unlink(o)
                        except Exception:
                            pass
                    bpy.data.collections.remove(coll)
                except Exception:
                    pass

            self.report({'INFO'}, f"Cleared {removed} helper objects")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f'Clear helpers failed: {e}')
            return {'CANCELLED'}


classes = (T4A_OT_ClearHelpers,)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass


__all__ = ('parse_dimensions_string', 'measure_collection_bbox', 'create_or_update_helper_box', 'T4A_OT_ClearHelpers')
