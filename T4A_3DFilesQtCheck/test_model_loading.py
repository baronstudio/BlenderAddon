"""
Test script pour vérifier la mécanique de chargement des modèles
Ce script peut être exécuté dans Blender pour tester le système
"""

def test_model_loading():
    """Test la mécanique de chargement de la liste des modèles."""
    
    print("[T4A Test] Test du chargement de la liste des modèles")
    
    try:
        import bpy
        import json
        
        # Get addon preferences
        addon_name = 'T4A_3DFilesQtCheck'
        prefs = bpy.context.preferences.addons[addon_name].preferences
        
        print(f"✓ Addon trouvé: {addon_name}")
        
        # Check current model list
        model_list_json = getattr(prefs, 'model_list_json', '')
        model_list_ts = getattr(prefs, 'model_list_ts', 0)
        model_name = getattr(prefs, 'model_name', '')
        
        print(f"Raw model_list_json: {model_list_json}")
        print(f"Model list timestamp: {model_list_ts}")
        print(f"Selected model: {model_name}")
        
        # Parse model list
        try:
            models = json.loads(model_list_json or '[]')
            print(f"✓ JSON parsé avec succès: {len(models)} modèles")
            
            for i, model in enumerate(models[:3]):  # Show first 3 models
                if isinstance(model, dict):
                    name = model.get('name', 'Unknown')
                    compatible = model.get('compatible', False)
                    print(f"  {i+1}. {name} (compatible: {compatible})")
                else:
                    print(f"  {i+1}. {model} (format ancien)")
                    
        except json.JSONDecodeError as e:
            print(f"✗ Erreur JSON: {e}")
        
        # Test _model_items function
        try:
            from PROD_Parameters import _model_items
            items = _model_items(prefs, None)
            print(f"✓ _model_items retourne {len(items)} éléments")
            for i, item in enumerate(items[:3]):
                print(f"  {i+1}. {item[0]} -> {item[1]}")
        except Exception as e:
            print(f"✗ Erreur _model_items: {e}")
        
        # Test list_models function
        try:
            api_key = getattr(prefs, 'google_api_key', '')
            if api_key:
                from PROD_gemini import list_models
                result = list_models(api_key)
                print(f"✓ list_models appelé: success={result.get('success')}")
                if result.get('success'):
                    detail = result.get('detail', [])
                    print(f"  Modèles reçus: {len(detail)}")
                    compatible_count = sum(1 for m in detail if isinstance(m, dict) and m.get('compatible', False))
                    print(f"  Compatibles: {compatible_count}")
                else:
                    print(f"  Erreur: {result.get('detail')}")
            else:
                print("⚠ Pas de clé API configurée pour tester list_models")
                
        except Exception as e:
            print(f"✗ Erreur list_models: {e}")
        
        print("[T4A Test] Tests terminés")
        
    except Exception as e:
        print(f"[T4A Test] Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()