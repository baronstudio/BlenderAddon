"""Centralise les propriétés partagées de l'addon.

Contient :
- la classe `T4A_AddonPreferences` (préférence d'addon `scan_path`)
- les helpers `register_scene_props` / `unregister_scene_props`

Ce module est chargé en premier par `__init__.py` pour garantir
que les propriétés soient disponibles aux autres modules.
"""
import bpy
import json


def _model_items(prefs, context):
    """Return enum items for model selection from the stored JSON list.

    Note: the first argument will be the preferences object when called by Blender.
    """
    try:
        raw = getattr(prefs, 'model_list_json', '[]') or '[]'
        lst = json.loads(raw)
        items = []
        # Handle both old format (list of strings) and new format (list of dicts)
        for m in lst:
            if isinstance(m, dict):
                # New format: {'name': 'model-name', 'compatible': true/false}
                name = m.get('name', '')
                if name:
                    items.append((name, name, ""))
            else:
                # Old format: just strings
                items.append((str(m), str(m), ""))
        if not items:
            items = [('models/gemini-2.5-flash-lite', 'models/gemini-2.5-flash-lite', '')]
        return items
    except Exception:
        return [('models/gemini-2.5-flash-lite', 'models/gemini-2.5-flash-lite', '')]


class T4A_AddonPreferences(bpy.types.AddonPreferences):
    # Use the addon name as bl_idname so Blender shows these prefs
    # under the main addon entry (must match bl_info["name"]).
    bl_idname = "T4A_3DFilesQtCheck"

    scan_path: bpy.props.StringProperty(
        name="Scan Path",
        description="Répertoire à scanner pour rechercher les fichiers à analyser",
        subtype='DIR_PATH',
        default=""
    )
    google_api_key: bpy.props.StringProperty(
        name="Google API Key",
        description="Clé API pour Google Generative AI (ne pas committer)",
        default=""
    )

    # Persist the list of models as JSON so it survives restarts.
    model_list_json: bpy.props.StringProperty(
        name="Model List (JSON)",
        description="Internal storage for available model names with compatibility info (JSON list)",
        default='[{"name": "models/gemini-2.5-flash-lite", "compatible": true}]',
    )

    # Timestamp (epoch seconds) when `model_list_json` was last updated
    model_list_ts: bpy.props.FloatProperty(
        name="Model list timestamp",
        description="Internal timestamp for model list cache (epoch seconds)",
        default=0.0,
    )

    model_name: bpy.props.EnumProperty(
        name="Model Name",
        description="Nom du modèle à utiliser pour les requêtes Gemini",
        items=_model_items,
    )

    debug_mode: bpy.props.BoolProperty(
        name="Debug Mode",
        description="Active les messages de debug détaillés et les stack traces",
        default=False,
    )

    # --- PROMPTS CONFIGURABLES ---
    text_analysis_prompt: bpy.props.StringProperty(
        name="Prompt Analyse Texte",
        description="Prompt utilisé pour l'analyse de texte avec Gemini. Tags: {TEXT_CONTENT}, {FILE_NAME}, {FILE_TYPE}",
        default="Extract the 3D model dimensions from the following text. Return the result as a compact string in meters in the format: width: <value> m; height: <value> m; depth: <value> m. If no dimensions are present, reply: NOT_FOUND. \nFile: {FILE_NAME} ({FILE_TYPE})\nText:\n{TEXT_CONTENT}",
        maxlen=2000
    )

    image_analysis_prompt: bpy.props.StringProperty(
        name="Prompt Analyse Image", 
        description="Prompt utilisé pour l'analyse d'image avec Gemini Vision. Tags: {IMAGE_PATH}, {FILE_NAME}, {FILE_TYPE}",
        default="""Analyze this image thoroughly and extract all relevant information for 3D modeling and quality control:

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
        maxlen=3000
    )

    connection_test_prompt: bpy.props.StringProperty(
        name="Prompt Test Connexion",
        description="Prompt utilisé pour tester la connexion Gemini. Tags: {MODEL_NAME}",
        default="Ping test for model {MODEL_NAME}: say hello briefly and confirm you are working.",
        maxlen=500
    )

    # --- VARIABLES D'ADDON ---
    dimension_tolerance: bpy.props.FloatProperty(
        name="Tolérance Dimensions",
        description="Tolérance en pourcentage pour la comparaison des dimensions (ex: 0.05 = 5%)",
        default=0.05,
        min=0.001,
        max=1.0,
        step=0.01
    )

    api_timeout: bpy.props.IntProperty(
        name="Timeout API",
        description="Timeout en secondes pour les requêtes API Gemini",
        default=30,
        min=5,
        max=300
    )

    model_cache_ttl: bpy.props.IntProperty(
        name="TTL Cache Modèles",
        description="Durée de vie du cache de la liste des modèles en secondes",
        default=3600,
        min=300,
        max=86400
    )

    default_model_fallback: bpy.props.StringProperty(
        name="Modèle par Défaut",
        description="Nom du modèle à utiliser si aucun modèle n'est configuré",
        default="models/gemini-2.5-flash-lite"
    )

    # Note: Vertex/Service Account mode removed in favor of google-generativeai (API key)

    def draw(self, context):
        layout = self.layout
        
        # --- CONFIGURATION DE BASE ---
        box = layout.box()
        box.label(text="Configuration de Base", icon='SETTINGS')
        box.prop(self, "scan_path")
        box.prop(self, "google_api_key")
        box.separator()
        box.prop(self, "debug_mode")
        box.separator()
        # model_name is an EnumProperty populated from model_list_json
        try:
            box.prop(self, "model_name")
            # Check if selected model is compatible with generateContent
            self._check_model_compatibility(box)
        except Exception:
            box.label(text='Model selection unavailable')

        layout.separator()

        # --- VARIABLES D'ADDON ---
        var_box = layout.box()
        var_box.label(text="Variables d'Addon", icon='PROPERTIES')
        
        row = var_box.row()
        row.prop(self, "dimension_tolerance")
        row.prop(self, "api_timeout")
        
        row = var_box.row()
        row.prop(self, "model_cache_ttl")
        row.prop(self, "default_model_fallback")

        layout.separator()

        # --- PROMPTS CONFIGURABLES ---
        prompt_box = layout.box()
        prompt_box.label(text="Prompts Configurables", icon='TEXT')
        
        # Tags disponibles
        info_box = prompt_box.box()
        info_box.label(text="Tags disponibles:", icon='INFO')
        col = info_box.column()
        col.scale_y = 0.8
        col.label(text="{TEXT_CONTENT} - Contenu du texte à analyser")
        col.label(text="{IMAGE_PATH} - Chemin de l'image")
        col.label(text="{FILE_NAME} - Nom du fichier")
        col.label(text="{FILE_TYPE} - Type de fichier (PDF, JPG, etc.)")
        col.label(text="{MODEL_NAME} - Nom du modèle Gemini")
        col.label(text="{SCENE_SCALE} - Échelle de la scène")
        col.label(text="{UNIT_SYSTEM} - Système d'unités")
        
        prompt_box.separator()
        
        # Prompt analyse texte
        prompt_box.label(text="Prompt Analyse Texte:")
        row = prompt_box.row()
        row.prop(self, "text_analysis_prompt", text="")
        reset_op = row.operator("t4a.reset_prompt", text="", icon='FILE_REFRESH')
        reset_op.prompt_type = "text_analysis"
        
        # Prompt analyse image
        prompt_box.label(text="Prompt Analyse Image:")
        row = prompt_box.row()
        row.prop(self, "image_analysis_prompt", text="")
        reset_op = row.operator("t4a.reset_prompt", text="", icon='FILE_REFRESH')
        reset_op.prompt_type = "image_analysis"
        
        # Prompt test connexion
        prompt_box.label(text="Prompt Test Connexion:")
        row = prompt_box.row()
        row.prop(self, "connection_test_prompt", text="")
        reset_op = row.operator("t4a.reset_prompt", text="", icon='FILE_REFRESH')
        reset_op.prompt_type = "connection_test"

        layout.separator()

        layout.separator()

        # --- OPÉRATEURS ---
        # Attempt to ensure operator modules are registered so buttons appear
        try:
            # Import and call register on modules that define preference operators.
            # register() implementations are idempotent / guarded, so this is safe.
            from . import PROD_dependency_installer, PROD_Files_manager
            try:
                if hasattr(PROD_dependency_installer, 'register'):
                    PROD_dependency_installer.register()
            except Exception:
                pass
            try:
                if hasattr(PROD_Files_manager, 'register'):
                    PROD_Files_manager.register()
            except Exception:
                pass
        except Exception:
            # best-effort: ignore import failures (happens in tests/outside Blender)
            pass

        # Installer les dépendances Python nécessaires pour l'addon
        def _op_exists(op_id: str) -> bool:
            try:
                parts = op_id.split('.')
                if len(parts) != 2:
                    return False
                mod = getattr(bpy.ops, parts[0], None)
                return bool(mod and hasattr(mod, parts[1]))
            except Exception:
                return False

        ops_box = layout.box()
        ops_box.label(text="Opérations", icon='TOOL_SETTINGS')
        
        row = ops_box.row()
        try:
            install_available = _op_exists('t4a.install_dependencies')
        except Exception:
            install_available = False

        if install_available:
            row.operator('t4a.install_dependencies', icon='FILE_SCRIPT')
        else:
            row.label(text='Install operator unavailable')

        row = ops_box.row()
        try:
            list_available = _op_exists('t4a.list_gemini_models')
        except Exception:
            list_available = False

        if list_available:
            row.operator('t4a.list_gemini_models', icon='PLUGIN')
        else:
            row.label(text='List models operator unavailable')

    def _check_model_compatibility(self, layout):
        """Check if selected model is compatible with generateContent and show warning if not."""
        try:
            current_model = getattr(self, 'model_name', '')
            if not current_model:
                return
            
            # Parse model list to find compatibility info
            raw = getattr(self, 'model_list_json', '[]') or '[]'
            models_data = json.loads(raw)
            
            for model_info in models_data:
                if isinstance(model_info, dict) and model_info.get('name') == current_model:
                    if not model_info.get('compatible', True):
                        # Show warning for incompatible model
                        box = layout.box()
                        row = box.row()
                        row.alert = True
                        row.label(text="⚠ Ce modèle n'est pas compatible avec generateContent", icon='ERROR')
                        row = box.row()
                        row.label(text="Utilisez 'Lister les modèles Gemini' pour voir les modèles compatibles")
                    break
        except Exception:
            # Ignore errors in compatibility check
            pass


def register_scene_props():
    """Déclare des propriétés sur `bpy.types.Scene` pour stocker l'info d'unités."""
    bpy.types.Scene.t4a_unit_system = bpy.props.StringProperty(
        name="T4A Unit System",
        description="Stocke le système d'unités actuel de la scène",
        default=""
    )
    bpy.types.Scene.t4a_scale_length = bpy.props.FloatProperty(
        name="T4A Scale Length",
        description="Stocke la valeur de scale_length de la scène",
        default=1.0
    )
    # Import counters (last run)
    bpy.types.Scene.t4a_last_imported_count = bpy.props.IntProperty(
        name="T4A Last Imported Count",
        description="Nombre de fichiers importés lors du dernier scan/import",
        default=0
    )
    bpy.types.Scene.t4a_last_import_failed = bpy.props.IntProperty(
        name="T4A Last Import Failures",
        description="Nombre d'échecs lors du dernier scan/import",
        default=0
    )


class T4A_DimResult(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="File Name")
    dimensions: bpy.props.StringProperty(name="Dimensions", default="")
    expanded: bpy.props.BoolProperty(name="Expanded", default=False)


def register_all():
    """Register property group and attach collection to Scene."""
    try:
        bpy.utils.register_class(T4A_DimResult)
    except Exception:
        pass
    try:
        bpy.types.Scene.t4a_dimensions = bpy.props.CollectionProperty(type=T4A_DimResult)
    except Exception:
        pass


def unregister_all():
    try:
        del bpy.types.Scene.t4a_dimensions
    except Exception:
        pass
    try:
        bpy.utils.unregister_class(T4A_DimResult)
    except Exception:
        pass


def unregister_scene_props():
    try:
        del bpy.types.Scene.t4a_unit_system
    except Exception:
        pass
    try:
        del bpy.types.Scene.t4a_scale_length
    except Exception:
        pass
    try:
        del bpy.types.Scene.t4a_last_imported_count
    except Exception:
        pass
    try:
        del bpy.types.Scene.t4a_last_import_failed
    except Exception:
        pass


def update_scene_unit_props():
    """Populate the `t4a_*` props for all scenes from each scene's unit_settings."""
    try:
        for sc in bpy.data.scenes:
            try:
                us = sc.unit_settings
                sc.t4a_unit_system = getattr(us, 'system', '')
                sc.t4a_scale_length = getattr(us, 'scale_length', 1.0)
            except Exception:
                # skip problematic scenes
                pass
    except Exception:
        pass


def is_debug_mode():
    """Check if debug mode is enabled in addon preferences."""
    try:
        # Use consistent addon name for preferences access
        prefs = bpy.context.preferences.addons['T4A_3DFilesQtCheck'].preferences
        return getattr(prefs, 'debug_mode', False)
    except Exception:
        return False


def get_addon_preferences():
    """Get addon preferences instance safely."""
    try:
        return bpy.context.preferences.addons['T4A_3DFilesQtCheck'].preferences
    except Exception:
        return None


__all__ = (
    'T4A_AddonPreferences',
    'register_scene_props',
    'unregister_scene_props',
    'update_scene_unit_props',
    'is_debug_mode',
    'get_addon_preferences',
)
