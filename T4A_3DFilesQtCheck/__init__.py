bl_info = {
    "name": "T4A_3DFilesQtCheck",
    "author": "Tech4Art Conseil <tech4artconseil@gmail.com>",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "View3D > Sidebar > T4A",
    "description": "Outils de contrôle de fichiers 3D — vérification qualité de maillage, textures, UV, matériaux et échelles.",
    "warning": "Work in progress",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View",
}
import bpy
import os
import json
import time

# Parameters module centralisé (doit être chargé en premier)
from . import PROD_Parameters

# Import explicite des modules de l'addon (méthode fiable)
from . import (
    PROD_Parameters,
    PROD_panel_about,
    PROD_panel_checklist,
    PROD_panel_files,
    PROD_panel_reviews,
    PROD_panel_dimension_checker,
    PROD_mesh_analysis,
    PROD_image_analysis,
    PROD_Files_manager,
    PROD_Utilitaire,
    PROD_dimension_checker,
    PROD_prompt_manager,
    PROD_texture_manager,
    PROD_uv_analyzer,
    PROD_topology_analyzer,
    PROD_texel_density,
    PROD_dimension_analyzer,
)
from . import PROD_dependency_installer

_MODULES = (
    PROD_Parameters,
    PROD_mesh_analysis,
    PROD_image_analysis,
    PROD_Files_manager,
    PROD_Utilitaire,
    PROD_dimension_checker,
    PROD_prompt_manager,
    PROD_texture_manager,
    PROD_uv_analyzer,
    PROD_topology_analyzer,
    PROD_texel_density,
    PROD_dimension_analyzer,
    PROD_panel_files,
    PROD_panel_checklist,
    PROD_panel_reviews,
    PROD_panel_dimension_checker,
    PROD_panel_about,
    PROD_dependency_installer,
)

def register():
    import traceback
    # register scene properties and property groups first so modules can read them
    try:
        PROD_Parameters.register_scene_props()
    except Exception:
        pass
    try:
        PROD_Parameters.register_all()
    except Exception:
        pass

    for mod in _MODULES:
        try:
            if hasattr(mod, "register"):
                mod.register()
        except Exception:
            print(f"[T4A] Erreur lors de l'enregistrement de {getattr(mod, '__name__', str(mod))}")
            # Only print stack trace if debug mode is enabled
            try:
                if PROD_Parameters.is_debug_mode():
                    traceback.print_exc()
            except Exception:
                pass
    try:
        bpy.utils.register_class(PROD_Parameters.T4A_AddonPreferences)
    except Exception as e:
        # Show registration errors to help debug preferences UI issues
        print(f"[T4A] Error registering T4A_AddonPreferences: {e}")
        try:
            import traceback
            traceback.print_exc()
        except Exception:
            pass

    # Try to fetch available models at addon startup and persist them in prefs
    try:
        addon_name = 'T4A_3DFilesQtCheck'  # Must match bl_info["name"] and bl_idname
        prefs = bpy.context.preferences.addons[addon_name].preferences
        api_key = getattr(prefs, 'google_api_key', '') or os.environ.get('GOOGLE_API_KEY', '')
        try:
            from . import PROD_gemini
            res = PROD_gemini.list_models(api_key)
            if res.get('success'):
                detail = res.get('detail')
                # detail is now a list of dicts with 'name' and 'compatible' keys
                if detail and isinstance(detail, list):
                    try:
                        # Store the full list (with compatibility info) in JSON format
                        prefs.model_list_json = json.dumps(detail)
                        prefs.model_list_ts = time.time()
                        
                        # Set selected model if empty - use first compatible model
                        if not getattr(prefs, 'model_name', None):
                            try:
                                # Find first compatible model, fallback to first model
                                first_compatible = None
                                first_model = None
                                for model_info in detail:
                                    if isinstance(model_info, dict):
                                        name = model_info.get('name', '')
                                        if name:
                                            if first_model is None:
                                                first_model = name
                                            if model_info.get('compatible', False) and first_compatible is None:
                                                first_compatible = name
                                
                                prefs.model_name = first_compatible or first_model or 'models/gemini-2.5-flash-lite'
                            except Exception:
                                prefs.model_name = 'models/gemini-2.5-flash-lite'
                    except Exception:
                        pass
        except Exception:
            pass
    except Exception:
        pass

    # Ensure scene units are set to meters on addon startup
    try:
        scene = bpy.context.scene
        us = scene.unit_settings
        changed = False
        # Blender uses 'METRIC' to represent metric units (meters)
        if getattr(us, 'system', None) != 'METRIC':
            try:
                us.system = 'METRIC'
                changed = True
            except Exception:
                pass
        # Ensure scale_length is 1.0 (1.0 = meters)
        if getattr(us, 'scale_length', None) is not None and us.scale_length != 1.0:
            try:
                us.scale_length = 1.0
                changed = True
            except Exception:
                pass
        if changed:
            print('[T4A] Les unités de la scène ont été réglées sur le système métrique (mètres).')
        # store unit info into scene props if available
        try:
            scene.t4a_unit_system = getattr(us, 'system', '')
            scene.t4a_scale_length = getattr(us, 'scale_length', 1.0)
        except Exception:
            pass
        # Also populate props for all scenes (safer if bpy.context.scene is not available)
        try:
            PROD_Parameters.update_scene_unit_props()
        except Exception:
            pass
    except Exception:
        # bpy may not be available in test/static analysis environments
        pass


def unregister():
    import traceback
    for mod in reversed(_MODULES):
        try:
            if hasattr(mod, "unregister"):
                mod.unregister()
        except Exception:
            print(f"[T4A] Erreur lors de l'unregister de {getattr(mod, '__name__', str(mod))}")
            # Only print stack trace if debug mode is enabled
            try:
                if PROD_Parameters.is_debug_mode():
                    traceback.print_exc()
            except Exception:
                pass
    try:
        bpy.utils.unregister_class(PROD_Parameters.T4A_AddonPreferences)
    except Exception:
        pass
    # unregister scene props and property groups last
    try:
        PROD_Parameters.unregister_scene_props()
    except Exception:
        pass
    try:
        PROD_Parameters.unregister_all()
    except Exception:
        pass


if __name__ == "__main__":
    register()
