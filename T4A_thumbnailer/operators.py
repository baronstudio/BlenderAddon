import bpy
import os

from bpy.props import StringProperty


def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


class T4A_OT_thumbnail_render_active(bpy.types.Operator):
    bl_idname = "t4a.thumbnail_render_active"
    bl_label = "Render thumbnail (active)"
    bl_description = "Rend une vignette à partir de la caméra active en utilisant le matériau actif"

    def execute(self, context):
        scene = context.scene
        props = scene.t4a_thumbnailer

        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "Aucun objet sélectionné")
            return {'CANCELLED'}

        cam = scene.camera
        if cam is None:
            self.report({'ERROR'}, "Aucune caméra active dans la scène")
            return {'CANCELLED'}

        out_folder = bpy.path.abspath(props.output_folder)
        if not out_folder:
            self.report({'ERROR'}, "Spécifier un dossier d'enregistrement")
            return {'CANCELLED'}
        ensure_folder(out_folder)

        # Determine material name to use
        mat = None
        # try active material from object
        if hasattr(obj, 'active_material') and obj.active_material is not None:
            mat = obj.active_material
        else:
            # fallback to first material slot
            if hasattr(obj.data, 'materials') and len(obj.data.materials) > 0:
                mat = obj.data.materials[0]

        name = mat.name if mat is not None else obj.name
        filename = os.path.join(out_folder, f"{name}.jpg")

        # backup render settings
        rs = scene.render
        prev_res_x = rs.resolution_x
        prev_res_y = rs.resolution_y
        prev_filepath = rs.filepath
        prev_format = rs.image_settings.file_format
        prev_quality = rs.image_settings.quality

        try:
            rs.resolution_x = props.resolution_x
            rs.resolution_y = props.resolution_y
            rs.image_settings.file_format = 'JPEG'
            rs.image_settings.quality = props.jpeg_quality
            rs.filepath = filename

            # Render using active camera
            bpy.ops.render.render(write_still=True, use_viewport=False)
        finally:
            rs.resolution_x = prev_res_x
            rs.resolution_y = prev_res_y
            rs.filepath = prev_filepath
            rs.image_settings.file_format = prev_format
            rs.image_settings.quality = prev_quality

        self.report({'INFO'}, f"Thumbnail sauvegardé: {filename}")
        return {'FINISHED'}


class T4A_OT_thumbnail_batch(bpy.types.Operator):
    bl_idname = "t4a.thumbnail_batch"
    bl_label = "Batch render materials"
    bl_description = "Applique chaque matériau assigné à l'objet et rend un thumbnail pour chacun"

    def execute(self, context):
        scene = context.scene
        props = scene.t4a_thumbnailer

        obj = context.active_object
        if obj is None:
            self.report({'ERROR'}, "Aucun objet sélectionné")
            return {'CANCELLED'}

        cam = scene.camera
        if cam is None:
            self.report({'ERROR'}, "Aucune caméra active dans la scène")
            return {'CANCELLED'}

        out_folder = bpy.path.abspath(props.output_folder)
        if not out_folder:
            self.report({'ERROR'}, "Spécifier un dossier d'enregistrement")
            return {'CANCELLED'}
        ensure_folder(out_folder)

        # Collect materials assigned to object
        mats = []
        if hasattr(obj.data, 'materials'):
            for m in obj.data.materials:
                if m is not None and m.name not in [x.name for x in mats]:
                    mats.append(m)

        if not mats:
            self.report({'ERROR'}, "Aucun matériau trouvé sur l'objet sélectionné")
            return {'CANCELLED'}

        # Backup original materials per slot
        original_mats = [m for m in obj.data.materials]

        rs = scene.render
        prev_res_x = rs.resolution_x
        prev_res_y = rs.resolution_y
        prev_filepath = rs.filepath
        prev_format = rs.image_settings.file_format
        prev_quality = rs.image_settings.quality

        try:
            rs.resolution_x = props.resolution_x
            rs.resolution_y = props.resolution_y
            rs.image_settings.file_format = 'JPEG'
            rs.image_settings.quality = props.jpeg_quality

            for mat in mats:
                # assign material to all slots (simple approach)
                for i in range(len(obj.data.materials)):
                    obj.data.materials[i] = mat

                filename = os.path.join(out_folder, f"{mat.name}.jpg")
                rs.filepath = filename
                bpy.ops.render.render(write_still=True, use_viewport=False)

        finally:
            # restore original materials
            for i in range(len(original_mats)):
                obj.data.materials[i] = original_mats[i]
            rs.resolution_x = prev_res_x
            rs.resolution_y = prev_res_y
            rs.filepath = prev_filepath
            rs.image_settings.file_format = prev_format
            rs.image_settings.quality = prev_quality

        self.report({'INFO'}, f"Batch thumbnails sauvegardés dans: {out_folder}")
        return {'FINISHED'}
