"""
Script de test pour valider le nouveau système de dimensions amélioré
Exécuter dans Blender pour tester la fonctionnalité
"""

import bpy
import sys
import os

def test_dimension_system():
    """Test la fonctionnalité des dimensions améliorées"""
    
    print("=== TEST DU SYSTÈME DE DIMENSIONS AMÉLIORÉ ===")
    
    try:
        # 1. Vérifier que les nouvelles propriétés existent
        print("\n1. Vérification des propriétés T4A_DimResult...")
        
        scene = bpy.context.scene
        dims = getattr(scene, 't4a_dimensions', None)
        
        if dims is None:
            print("❌ Collection t4a_dimensions non trouvée")
            return False
            
        # Créer un élément de test
        test_item = dims.add()
        test_item.name = "TEST_DIMENSIONS"
        
        # Vérifier les nouvelles propriétés
        new_properties = [
            'ai_dimensions', 'ai_analysis_success', 'ai_analysis_error',
            'scene_dimensions', 'scene_width', 'scene_height', 'scene_depth'
        ]
        
        for prop in new_properties:
            if not hasattr(test_item, prop):
                print(f"❌ Propriété {prop} manquante")
                return False
            else:
                print(f"✅ Propriété {prop} présente")
        
        # 2. Test de l'analyseur de dimensions
        print("\n2. Test de l'analyseur de dimensions...")
        
        try:
            # Import du module
            sys.path.append(os.path.dirname(__file__))
            from PROD_dimension_analyzer import (
                parse_ai_dimensions, 
                calculate_dimension_difference,
                determine_tolerance_status,
                analyze_collection_dimensions
            )
            
            print("✅ Module PROD_dimension_analyzer importé avec succès")
            
            # Test du parsing des dimensions IA
            test_ai_text = "L:10.5 H:20.0 P:5.2 cm"
            parsed_dims = parse_ai_dimensions(test_ai_text)
            
            if parsed_dims and len(parsed_dims) == 3:
                print(f"✅ Parsing IA réussi: {parsed_dims}")
            else:
                print(f"❌ Parsing IA échoué: {parsed_dims}")
                return False
            
            # Test du calcul de différence
            scene_dims = (10.0, 19.8, 5.1)
            diff_percent = calculate_dimension_difference(parsed_dims, scene_dims)
            print(f"✅ Calcul différence: {diff_percent:.2f}%")
            
            # Test du statut de tolérance
            status = determine_tolerance_status(diff_percent)
            print(f"✅ Statut tolérance: {status}")
            
        except ImportError as e:
            print(f"❌ Erreur import module: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur test analyseur: {e}")
            return False
        
        # 3. Test de l'interface utilisateur
        print("\n3. Test des nouvelles propriétés UI...")
        
        # Assigner des valeurs de test
        test_item.ai_dimensions = "L:15.2 H:25.8 P:7.3 cm"
        test_item.ai_analysis_success = True
        test_item.scene_dimensions = "L:15.0 H:26.0 P:7.5 cm"
        test_item.scene_width = 15.0
        test_item.scene_height = 26.0
        test_item.scene_depth = 7.5
        test_item.tolerance_status = 'WARNING'
        test_item.difference_percentage = 5.2
        
        print("✅ Propriétés assignées avec succès")
        print(f"   - IA: {test_item.ai_dimensions}")
        print(f"   - Scène: {test_item.scene_dimensions}")
        print(f"   - Statut: {test_item.tolerance_status}")
        print(f"   - Différence: {test_item.difference_percentage}%")
        
        # 4. Test de l'opérateur de recalcul
        print("\n4. Test de l'opérateur de recalcul...")
        
        # Vérifier que l'opérateur est disponible
        if "t4a.recalculate_dimensions" in bpy.ops.t4a.__dict__:
            print("✅ Opérateur t4a.recalculate_dimensions disponible")
        else:
            print("❌ Opérateur t4a.recalculate_dimensions non disponible")
        
        # Nettoyage
        dims.remove(len(dims) - 1)
        
        print("\n=== TEST RÉUSSI ✅ ===")
        print("Le système de dimensions amélioré est opérationnel!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_elements():
    """Test les éléments d'interface pour le nouveau système"""
    
    print("\n=== TEST DES ÉLÉMENTS UI ===")
    
    try:
        # Vérifier que le panneau existe
        panel_class = None
        for cls_name, cls in bpy.types.__dict__.items():
            if "T4A_PT_PROD_FilesReviews" in cls_name:
                panel_class = cls
                break
        
        if panel_class:
            print("✅ Panneau T4A_PT_PROD_FilesReviews trouvé")
        else:
            print("❌ Panneau T4A_PT_PROD_FilesReviews non trouvé")
            return False
        
        # Simuler l'affichage avec données de test
        scene = bpy.context.scene
        dims = getattr(scene, 't4a_dimensions', None)
        
        if dims is None:
            print("❌ Pas de collection dimensions pour test UI")
            return False
        
        # Ajouter un élément de test pour l'UI
        ui_test_item = dims.add()
        ui_test_item.name = "UI_TEST_MODEL"
        ui_test_item.expanded = True
        
        # Données de test complètes
        ui_test_item.ai_dimensions = "Largeur: 12.5cm, Hauteur: 18.0cm, Profondeur: 6.2cm"
        ui_test_item.ai_analysis_success = True
        ui_test_item.scene_dimensions = "L:12.7 H:17.8 P:6.3 cm"
        ui_test_item.scene_width = 12.7
        ui_test_item.scene_height = 17.8
        ui_test_item.scene_depth = 6.3
        ui_test_item.tolerance_status = 'OK'
        ui_test_item.difference_percentage = 3.1
        
        print("✅ Données UI de test créées")
        print(f"   - Nom: {ui_test_item.name}")
        print(f"   - Expandé: {ui_test_item.expanded}")
        print(f"   - Statut: {ui_test_item.tolerance_status}")
        
        # Test avec erreur IA
        error_test_item = dims.add()
        error_test_item.name = "ERROR_TEST_MODEL"
        error_test_item.expanded = True
        error_test_item.ai_analysis_success = False
        error_test_item.ai_analysis_error = "Format non reconnu dans le document"
        error_test_item.tolerance_status = 'AI_ERROR'
        
        print("✅ Données d'erreur UI créées")
        
        # Forcer la mise à jour de l'interface
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        
        print("\n=== TEST UI RÉUSSI ✅ ===")
        print("Les éléments d'interface sont prêts à être testés!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR TEST UI: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Exécution des tests du système de dimensions amélioré...")
    
    # Test 1: Système de base
    success1 = test_dimension_system()
    
    # Test 2: Interface utilisateur
    success2 = test_ui_elements()
    
    if success1 and success2:
        print("\n🎉 TOUS LES TESTS RÉUSSIS! 🎉")
        print("Le système de dimensions amélioré est prêt à être utilisé.")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("Vérifiez les erreurs ci-dessus.")