import bpy

class T4A_PT_PROD_FilesManagement(bpy.types.Panel):
    bl_label = "Files Management"
    bl_idname = "T4A_PT_PROD_files_management"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Files Management — (vide pour le moment)")


classes = (
    T4A_PT_PROD_FilesManagement,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
