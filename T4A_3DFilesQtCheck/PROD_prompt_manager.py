"""
Opérateur pour réinitialiser les prompts aux valeurs par défaut.
"""
import bpy


class T4A_OT_ResetPrompt(bpy.types.Operator):
    bl_idname = "t4a.reset_prompt"
    bl_label = "Reset Prompt to Default"
    bl_description = "Réinitialise le prompt sélectionné à sa valeur par défaut"

    prompt_type: bpy.props.StringProperty(name="Prompt Type", default="")

    def execute(self, context):
        try:
            from . import PROD_Parameters
            prefs = PROD_Parameters.get_addon_preferences()
            if not prefs:
                self.report({'ERROR'}, 'Impossible d\'accéder aux préférences')
                return {'CANCELLED'}

            prompt_type = self.prompt_type
            
            # Prompts par défaut
            default_prompts = {
                "text_analysis": "Extract the 3D model dimensions from the following text. Return the result as a compact string in meters in the format: width: <value> m; height: <value> m; depth: <value> m. If no dimensions are present, reply: NOT_FOUND. \nFile: {FILE_NAME} ({FILE_TYPE})\nText:\n{TEXT_CONTENT}",
                
                "image_analysis": """Analyze this image thoroughly and extract all relevant information for 3D modeling and quality control:

1. **TEXT EXTRACTION (OCR)**: Extract all visible text, numbers, dimensions, specifications, labels, and technical information.

2. **3D MODEL ANALYSIS**: If this shows a 3D model or technical drawing:
   - Identify dimensions, measurements, scale information
   - Note any quality issues (missing textures, geometry problems, UV mapping issues)
   - Describe materials, colors, and surface properties
   - Identify object types and their relationships

3. **TECHNICAL SPECIFICATIONS**: Look for:
   - Size specifications (length, width, height, diameter, etc.)
   - Material specifications
   - Quality control information
   - Manufacturing details
   - Part numbers or model references

4. **VISUAL ANALYSIS**: Describe:
   - Overall composition and layout
   - Image quality and clarity
   - Any visible defects or anomalies
   - Color accuracy and lighting

Image file: {FILE_NAME} ({FILE_TYPE})
Provide detailed analysis focusing on 3D modeling requirements.""",
                
                "connection_test": "Ping test for model {MODEL_NAME}: say hello briefly and confirm you are working."
            }
            
            if prompt_type in default_prompts:
                if prompt_type == "text_analysis":
                    prefs.text_analysis_prompt = default_prompts[prompt_type]
                elif prompt_type == "image_analysis":
                    prefs.image_analysis_prompt = default_prompts[prompt_type]
                elif prompt_type == "connection_test":
                    prefs.connection_test_prompt = default_prompts[prompt_type]
                    
                self.report({'INFO'}, f'Prompt "{prompt_type}" réinitialisé')
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f'Type de prompt inconnu: {prompt_type}')
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f'Erreur lors de la réinitialisation: {e}')
            return {'CANCELLED'}


def register():
    try:
        bpy.utils.register_class(T4A_OT_ResetPrompt)
    except Exception:
        pass


def unregister():
    try:
        bpy.utils.unregister_class(T4A_OT_ResetPrompt)
    except Exception:
        pass


classes = (
    T4A_OT_ResetPrompt,
)

__all__ = ('T4A_OT_ResetPrompt',)