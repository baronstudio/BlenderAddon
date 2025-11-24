import bpy

class T4A_PT_PROD_FilesReviews(bpy.types.Panel):
    bl_label = "Files Reviews"
    bl_idname = "T4A_PT_PROD_files_reviews"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Files Reviews — (vide pour le moment)")


classes = (
    T4A_PT_PROD_FilesReviews,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
