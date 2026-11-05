# -----------------------------------------------------------------------------
# T4A Thumbnailer
# Copyright (c) 2026 Tech4Art Conseil
# Author: Tech4Art Conseil
# Licensed under the GNU General Public License v3.0 (GPL-3.0-or-later)
# See LICENSE file for details.
# -----------------------------------------------------------------------------
import os
import re
from contextlib import contextmanager

import bpy

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_filename(name):
    """Strip characters that are not allowed in file names on Windows/macOS/Linux."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name).strip(" .")
    return cleaned or "thumbnail"


def resolve_output_folder(props):
    """Return the absolute output folder, creating it if needed, or None if unset."""
    if not props.output_folder.strip():
        return None
    folder = bpy.path.abspath(props.output_folder)
    os.makedirs(folder, exist_ok=True)
    return folder


@contextmanager
def jpeg_render_settings(scene, props):
    """Temporarily switch the scene render output to a JPEG still, then restore it."""
    rs = scene.render
    img = rs.image_settings
    # Blender 5.0 added `media_type`; `file_format` only accepts formats valid
    # for the current media type, so it must be switched to IMAGE first.
    has_media_type = hasattr(img, "media_type")
    backup = {
        "resolution_x": rs.resolution_x,
        "resolution_y": rs.resolution_y,
        "resolution_percentage": rs.resolution_percentage,
        "filepath": rs.filepath,
        "media_type": img.media_type if has_media_type else None,
        "file_format": img.file_format,
        "quality": img.quality,
    }
    try:
        rs.resolution_x = props.resolution_x
        rs.resolution_y = props.resolution_y
        rs.resolution_percentage = 100
        if has_media_type:
            img.media_type = 'IMAGE'
        img.file_format = 'JPEG'
        img.quality = props.jpeg_quality
        yield rs
    finally:
        rs.resolution_x = backup["resolution_x"]
        rs.resolution_y = backup["resolution_y"]
        rs.resolution_percentage = backup["resolution_percentage"]
        rs.filepath = backup["filepath"]
        if has_media_type:
            img.media_type = backup["media_type"]
        img.file_format = backup["file_format"]
        img.quality = backup["quality"]


def render_still(rs, filepath):
    rs.filepath = filepath
    bpy.ops.render.render(write_still=True, use_viewport=False)


class _ThumbnailOperatorBase:
    """Shared checks for the thumbnail operators."""

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.scene.camera is not None

    @classmethod
    def description(cls, context, properties):
        if context.active_object is None:
            return cls.bl_description + "\n\nAucun objet actif"
        if context.scene.camera is None:
            return cls.bl_description + "\n\nAucune caméra active dans la scène"
        return cls.bl_description

    def get_output_folder(self, props):
        try:
            folder = resolve_output_folder(props)
        except OSError as exc:
            self.report({'ERROR'}, f"Impossible de créer le dossier: {exc}")
            return None
        if folder is None:
            self.report({'ERROR'}, "Spécifier un dossier d'enregistrement")
        return folder


class T4A_OT_thumbnail_render_active(_ThumbnailOperatorBase, bpy.types.Operator):
    bl_idname = "t4a.thumbnail_render_active"
    bl_label = "Render thumbnail (active)"
    bl_description = "Rend une vignette à partir de la caméra active en utilisant le matériau actif"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        props = scene.t4a_thumbnailer
        obj = context.active_object

        out_folder = self.get_output_folder(props)
        if out_folder is None:
            return {'CANCELLED'}

        mat = obj.active_material
        if mat is None:
            mat = next((s.material for s in obj.material_slots if s.material), None)

        base_name = mat.name if mat is not None else obj.name
        filename = os.path.join(out_folder, safe_filename(f"{base_name}{props.filename_suffix}") + ".jpg")

        with jpeg_render_settings(scene, props) as rs:
            render_still(rs, filename)

        self.report({'INFO'}, f"Thumbnail sauvegardé: {filename}")
        return {'FINISHED'}


class T4A_OT_thumbnail_batch(_ThumbnailOperatorBase, bpy.types.Operator):
    bl_idname = "t4a.thumbnail_batch"
    bl_label = "Batch render materials"
    bl_description = "Applique chaque matériau assigné à l'objet et rend un thumbnail pour chacun"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        props = scene.t4a_thumbnailer
        obj = context.active_object

        out_folder = self.get_output_folder(props)
        if out_folder is None:
            return {'CANCELLED'}

        slots = obj.material_slots
        mats = []
        for slot in slots:
            if slot.material is not None and slot.material not in mats:
                mats.append(slot.material)

        if not mats:
            self.report({'ERROR'}, "Aucun matériau trouvé sur l'objet sélectionné")
            return {'CANCELLED'}

        # Go through the slots (not obj.data.materials) so slots linked to the
        # object instead of the mesh data are handled too.
        original_mats = [slot.material for slot in slots]

        try:
            with jpeg_render_settings(scene, props) as rs:
                for mat in mats:
                    for slot in slots:
                        slot.material = mat
                    filename = os.path.join(
                        out_folder, safe_filename(f"{mat.name}{props.filename_suffix}") + ".jpg"
                    )
                    render_still(rs, filename)
        finally:
            for slot, original in zip(slots, original_mats):
                slot.material = original

        self.report({'INFO'}, f"{len(mats)} thumbnails sauvegardés dans: {out_folder}")
        return {'FINISHED'}
