"""
Système de remplacement de tags pour les prompts Gemini.

Fonctions pour remplacer les tags dans les prompts avec les valeurs contextuelles.
"""
import os
import bpy


def get_context_variables(context=None, **kwargs):
    """Récupère les variables de contexte pour le remplacement des tags.
    
    Args:
        context: Contexte Blender (optionnel)
        **kwargs: Variables supplémentaires à inclure
        
    Returns:
        dict: Dictionnaire des variables de contexte
    """
    variables = {}
    
    try:
        # Variables depuis le contexte Blender
        if context:
            scene = context.scene
            if scene:
                # Informations de la scène
                try:
                    us = scene.unit_settings
                    variables['UNIT_SYSTEM'] = getattr(us, 'system', 'METRIC')
                    variables['SCENE_SCALE'] = str(getattr(us, 'scale_length', 1.0))
                except Exception:
                    variables['UNIT_SYSTEM'] = 'METRIC'
                    variables['SCENE_SCALE'] = '1.0'
        else:
            # Fallback si pas de contexte
            variables['UNIT_SYSTEM'] = 'METRIC'
            variables['SCENE_SCALE'] = '1.0'
            
        # Variables depuis les préférences
        try:
            from . import PROD_Parameters
            prefs = PROD_Parameters.get_addon_preferences()
            if prefs:
                variables['MODEL_NAME'] = getattr(prefs, 'model_name', 'gemini-2.5-flash-lite')
                variables['DIMENSION_TOLERANCE'] = str(getattr(prefs, 'dimension_tolerance', 0.05))
                variables['API_TIMEOUT'] = str(getattr(prefs, 'api_timeout', 30))
                variables['DEFAULT_MODEL'] = getattr(prefs, 'default_model_fallback', 'models/gemini-2.5-flash-lite')
            else:
                variables['MODEL_NAME'] = 'gemini-2.5-flash-lite'
                variables['DIMENSION_TOLERANCE'] = '0.05'
                variables['API_TIMEOUT'] = '30'
                variables['DEFAULT_MODEL'] = 'models/gemini-2.5-flash-lite'
        except Exception:
            variables['MODEL_NAME'] = 'gemini-2.5-flash-lite'
            variables['DIMENSION_TOLERANCE'] = '0.05'
            variables['API_TIMEOUT'] = '30'
            variables['DEFAULT_MODEL'] = 'models/gemini-2.5-flash-lite'
            
        # Variables supplémentaires passées en paramètre
        variables.update(kwargs)
        
    except Exception:
        # Fallback en cas d'erreur
        variables.update({
            'UNIT_SYSTEM': 'METRIC',
            'SCENE_SCALE': '1.0',
            'MODEL_NAME': 'gemini-2.5-flash-lite',
            'DIMENSION_TOLERANCE': '0.05',
            'API_TIMEOUT': '30',
            'DEFAULT_MODEL': 'models/gemini-2.5-flash-lite'
        })
        variables.update(kwargs)
    
    return variables


def replace_prompt_tags(prompt_template: str, context=None, **kwargs) -> str:
    """Remplace les tags dans un prompt avec les valeurs contextuelles.
    
    Args:
        prompt_template: Le template de prompt avec des tags {TAG_NAME}
        context: Contexte Blender (optionnel)
        **kwargs: Variables supplémentaires à remplacer
        
    Returns:
        str: Le prompt avec les tags remplacés
    """
    if not prompt_template:
        return ""
        
    try:
        # Récupérer toutes les variables de contexte
        variables = get_context_variables(context, **kwargs)
        
        # Remplacer les tags dans le prompt
        result = prompt_template
        for key, value in variables.items():
            tag = f"{{{key}}}"
            if tag in result:
                result = result.replace(tag, str(value))
                
        return result
        
    except Exception:
        # En cas d'erreur, retourner le prompt original
        return prompt_template


def get_text_analysis_prompt(text_content: str, file_path: str = "", context=None, content_type: str = "text") -> str:
    """Construit le prompt d'analyse de texte avec remplacement des tags.
    
    Args:
        text_content: Le contenu texte à analyser
        file_path: Le chemin du fichier (optionnel)
        context: Contexte Blender (optionnel)
        content_type: Type de contenu "text" ou "image" (optionnel)
        
    Returns:
        str: Le prompt final avec tags remplacés
    """
    try:
        from . import PROD_Parameters
        prefs = PROD_Parameters.get_addon_preferences()
        if prefs:
            template = prefs.text_analysis_prompt
        else:
            template = "Extract the 3D model dimensions from the following text. Return the result as a compact string in meters in the format: width: <value> m; height: <value> m; depth: <value> m. If no dimensions are present, reply: NOT_FOUND. \nFile: {FILE_NAME} ({FILE_TYPE})\nText:\n{TEXT_CONTENT}"
    except Exception:
        template = "Extract the 3D model dimensions from the following text. Return the result as a compact string in meters in the format: width: <value> m; height: <value> m; depth: <value> m. If no dimensions are present, reply: NOT_FOUND. \nFile: {FILE_NAME} ({FILE_TYPE})\nText:\n{TEXT_CONTENT}"
    
    # Préparer les variables spécifiques
    file_name = os.path.basename(file_path) if file_path else "unknown"
    file_ext = os.path.splitext(file_name)[1].lstrip('.').upper() if file_path else "TXT"
    
    variables = {
        'TEXT_CONTENT': text_content or "",
        'FILE_NAME': file_name,
        'FILE_TYPE': file_ext,
        'IMAGE_PATH': file_path or "",
        'CONTENT_TYPE': content_type.upper()
    }
    
    return replace_prompt_tags(template, context, **variables)


def get_image_analysis_prompt(image_path: str = "", context=None) -> str:
    """Construit le prompt d'analyse d'image avec remplacement des tags.
    
    Args:
        image_path: Le chemin de l'image
        context: Contexte Blender (optionnel)
        
    Returns:
        str: Le prompt final avec tags remplacés
    """
    try:
        from . import PROD_Parameters
        prefs = PROD_Parameters.get_addon_preferences()
        if prefs:
            template = prefs.image_analysis_prompt
        else:
            template = """Analyze this image thoroughly and extract all relevant information for 3D modeling and quality control:

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
Provide detailed analysis focusing on 3D modeling requirements."""
    except Exception:
        template = "Analyze this image for 3D modeling: Image file: {FILE_NAME} ({FILE_TYPE})"
    
    # Préparer les variables spécifiques
    file_name = os.path.basename(image_path) if image_path else "unknown"
    file_ext = os.path.splitext(file_name)[1].lstrip('.').upper() if image_path else "JPG"
    
    variables = {
        'IMAGE_PATH': image_path or "",
        'FILE_NAME': file_name,
        'FILE_TYPE': file_ext
    }
    
    return replace_prompt_tags(template, context, **variables)


def get_connection_test_prompt(context=None) -> str:
    """Construit le prompt de test de connexion avec remplacement des tags.
    
    Args:
        context: Contexte Blender (optionnel)
        
    Returns:
        str: Le prompt final avec tags remplacés
    """
    try:
        from . import PROD_Parameters
        prefs = PROD_Parameters.get_addon_preferences()
        if prefs:
            template = prefs.connection_test_prompt
        else:
            template = "Ping test for model {MODEL_NAME}: say hello briefly and confirm you are working."
    except Exception:
        template = "Ping test for model {MODEL_NAME}: say hello briefly and confirm you are working."
    
    return replace_prompt_tags(template, context)


__all__ = (
    'get_context_variables',
    'replace_prompt_tags', 
    'get_text_analysis_prompt',
    'get_image_analysis_prompt',
    'get_connection_test_prompt'
)