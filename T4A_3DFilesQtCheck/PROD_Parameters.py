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
        for m in lst:
            items.append((m, m, ""))
        if not items:
            items = [('models/gemini-2.5-flash-lite', 'models/gemini-2.5-flash-lite', '')]
        return items
    except Exception:
        return [('models/gemini-2.5-flash-lite', 'models/gemini-2.5-flash-lite', '')]


class T4A_AddonPreferences(bpy.types.AddonPreferences):
    # Use the package name as bl_idname so Blender shows these prefs
    # under the main addon entry (not under the submodule name).
    bl_idname = __package__ if __package__ else "T4A_3DFilesQtCheck"

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
        description="Internal storage for available model names (JSON list)",
        default='["models/gemini-2.5-flash-lite"]',
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

    # Note: Vertex/Service Account mode removed in favor of google-generativeai (API key)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scan_path")
        layout.prop(self, "google_api_key")
        layout.separator()
        # model_name is an EnumProperty populated from model_list_json
        try:
            layout.prop(self, "model_name")
        except Exception:
            layout.label(text='Model selection unavailable')

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

        row = layout.row()
        try:
            install_available = _op_exists('t4a.install_dependencies')
        except Exception:
            install_available = False

        if install_available:
            row.operator('t4a.install_dependencies', icon='FILE_SCRIPT')
        else:
            row.label(text='Install operator unavailable')
            row.label(text='Install operator unavailable')

        row = layout.row()
        try:
            list_available = _op_exists('t4a.list_gemini_models')
        except Exception:
            list_available = False

        if list_available:
            row.operator('t4a.list_gemini_models', icon='PLUGIN')
        else:
            row.label(text='List models operator unavailable')
            row.label(text='List models operator unavailable')


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


__all__ = (
    'T4A_AddonPreferences',
    'register_scene_props',
    'unregister_scene_props',
    'update_scene_unit_props',
)
