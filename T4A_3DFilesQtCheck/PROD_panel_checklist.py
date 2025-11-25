import bpy

class T4A_PT_PROD_CheckList(bpy.types.Panel):
    bl_label = "Check Liste"
    bl_idname = "T4A_PT_PROD_check_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Check Liste — (vide pour le moment)")


classes = (
    T4A_PT_PROD_CheckList,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
