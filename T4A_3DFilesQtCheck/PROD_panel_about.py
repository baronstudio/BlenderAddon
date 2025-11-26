import bpy

class T4A_PT_PROD_About(bpy.types.Panel):
    bl_label = "About T4A_3DFilesQtCheck"
    bl_idname = "T4A_PT_PROD_about"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = 'T4A_3DFilesQtCheck'

    def draw(self, context):
        layout = self.layout
        try:
            from . import bl_info
            version = ".".join(map(str, bl_info.get('version', ('0','0','0'))))
            author = bl_info.get('author', 'Tech4Art Conseil')
        except Exception:
            version = "0.1.0"
            author = "Tech4Art Conseil"

        layout.label(text=f"Nom: T4A_3DFilesQtCheck")
        layout.label(text=f"Version: {version}")
        layout.label(text=f"Maintainer: {author}")
        layout.separator()
        layout.label(text="Description:")
        layout.label(text="Outils de contrôle qualité pour fichiers 3D.")
        layout.separator()
        layout.operator("wm.url_open", text="GitHub Repository").url = "https://github.com/baronstudio/BlenderAddon"
        layout.separator()
        # Show active Gemini model and redacted API key from addon preferences
        try:
            pkg = __package__ or 'T4A_3DFilesQtCheck'
            prefs = context.preferences.addons[pkg].preferences
            model = getattr(prefs, 'model_name', '') or '(not set)'
            raw_key = (getattr(prefs, 'google_api_key', '') or '').strip()
            if not raw_key:
                key_display = '(not set)'
            else:
                if len(raw_key) <= 10:
                    key_display = '<redacted>'
                else:
                    key_display = f"{raw_key[:6]}...{raw_key[-4:]}"
        except Exception:
            model = '(unknown)'
            key_display = '(unknown)'

        layout.label(text=f"Gemini model: {model}")
        layout.label(text=f"API Key: {key_display}")


classes = (
    T4A_PT_PROD_About,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
