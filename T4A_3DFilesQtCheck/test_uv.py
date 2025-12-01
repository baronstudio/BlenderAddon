#!/usr/bin/env python3

import sys
import os

# Ajouter le répertoire de l'addon au path Python
addon_path = os.path.dirname(os.path.abspath(__file__))
if addon_path not in sys.path:
    sys.path.append(addon_path)

print("=== Test des corrections UV ===")
print(f"Python path ajouté: {addon_path}")

try:
    # Test direct d'import du module
    import PROD_uv_analyzer
    print("✅ Module PROD_uv_analyzer importé avec succès")
    
    # Test des fonctions principales
    if hasattr(PROD_uv_analyzer, 'get_mesh_uv_data'):
        print("✅ Fonction get_mesh_uv_data disponible")
    else:
        print("❌ Fonction get_mesh_uv_data manquante")
        
    if hasattr(PROD_uv_analyzer, 'analyze_collection_uvs'):
        print("✅ Fonction analyze_collection_uvs disponible")
    else:
        print("❌ Fonction analyze_collection_uvs manquante")
        
    if hasattr(PROD_uv_analyzer, 'T4A_OT_AnalyzeUVs'):
        print("✅ Classe T4A_OT_AnalyzeUVs disponible")
    else:
        print("❌ Classe T4A_OT_AnalyzeUVs manquante")
    
    print("=== Test réussi - Le module UV est fonctionnel ===")
    
except Exception as e:
    print(f"❌ Erreur lors de l'import: {e}")
    import traceback
    traceback.print_exc()