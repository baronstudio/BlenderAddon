import bpy
import re

class T4A_PT_PROD_FilesReviews(bpy.types.Panel):
    bl_label = "Files Reviews"
    bl_idname = "T4A_PT_PROD_files_reviews"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Files Reviews")
        layout.separator()

        # --- General Scene Info box ---
        box = layout.box()
        box.label(text="General Scene Info")
        try:
            scene = context.scene
            system = getattr(scene, 't4a_unit_system', None)
            scale = getattr(scene, 't4a_scale_length', None)
            if not system:
                try:
                    us = scene.unit_settings
                    system = getattr(us, 'system', 'unknown')
                except Exception:
                    system = 'unknown'
            if scale is None or (isinstance(scale, float) and scale == 0.0):
                try:
                    us = scene.unit_settings
                    scale = getattr(us, 'scale_length', 'n/a')
                except Exception:
                    scale = 'n/a'
            box.label(text=f"Unit System: {system}")
            box.label(text=f"Scale Length: {scale}")
        except Exception:
            box.label(text="Scene unit info unavailable")

        # --- Import Summary box ---
        ibox = layout.box()
        ibox.label(text="Import Summary")
        try:
            scene = context.scene
            imported = getattr(scene, 't4a_last_imported_count', None)
            failed = getattr(scene, 't4a_last_import_failed', None)
            if imported is None:
                imported = 0
            if failed is None:
                failed = 0
            ibox.label(text=f"Last Imported: {imported}")
            ibox.label(text=f"Last Failed: {failed}")
        except Exception:
            ibox.label(text="No import information available")

        # --- Per-file Dimension Results (collapsible boxes, closed by default) ---
        try:
            scene = context.scene
            dims = getattr(scene, 't4a_dimensions', None)
            if dims is not None and len(dims) > 0:
                for item in dims:
                    row = layout.row()
                    # draw a simple expander using the BoolProperty on the item
                    row.prop(item, 'expanded', icon='TRIA_DOWN' if item.expanded else 'TRIA_RIGHT', emboss=False, text=item.name)
                    if item.expanded:
                        sub = layout.box()
                        try:
                            dtext = (item.dimensions or '').strip()
                            if not dtext:
                                sub.label(text="Dimensions: (empty)")
                            else:
                                # split on semicolons or newlines and show one value per line
                                parts = [p.strip() for p in re.split(r"[;\n]+", dtext) if p.strip()]
                                if len(parts) > 1:
                                    for p in parts:
                                        sub.label(text=p)
                                else:
                                    # fallback single-line display
                                    sub.label(text=dtext)
                        except Exception:
                            sub.label(text=f"Dimensions: {item.dimensions}")
            else:
                layout.label(text="No dimension results available")
        except Exception:
            layout.label(text="Dimension results unavailable")


classes = (
    T4A_PT_PROD_FilesReviews,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
