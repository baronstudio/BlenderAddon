"""
Test script pour l'analyse d'images avec Gemini Vision
Ce script peut être exécuté dans Blender pour tester la nouvelle fonctionnalité
"""

def test_image_analysis():
    """Test l'analyse d'images avec Gemini dans l'addon T4A."""
    
    print("[T4A Test] Test de l'analyse d'images avec Gemini Vision")
    
    try:
        # Test d'import des modules
        from PROD_gemini import analyze_image_with_ocr
        from PROD_Files_manager import T4A_OT_AnalyzeImageFile
        print("✓ Modules importés avec succès")
        
        # Test de validation de fichier
        result = analyze_image_with_ocr(None, "inexistant.jpg")
        expected_error = "Image file not found"
        if expected_error in result.get('detail', ''):
            print("✓ Validation de fichier fonctionne")
        else:
            print(f"✗ Validation échouée: {result}")
        
        # Vérifier que l'opérateur est bien défini
        if hasattr(T4A_OT_AnalyzeImageFile, 'bl_idname'):
            print(f"✓ Opérateur défini: {T4A_OT_AnalyzeImageFile.bl_idname}")
        else:
            print("✗ Opérateur mal défini")
            
        print("[T4A Test] Tests terminés")
        
    except Exception as e:
        print(f"[T4A Test] Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_analysis()