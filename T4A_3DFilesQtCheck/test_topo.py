#!/usr/bin/env python3
"""
Test script autonome pour l'analyse topologique.
Lance depuis PowerShell pour tester le module topologie sur un fichier GLB spécifique.

Usage:
python test_topo.py
"""

import sys
import os
import time
import traceback

# Ajouter le chemin du module Blender si nécessaire
try:
    import bpy
    print("✅ Blender Python API disponible")
except ImportError:
    print("❌ Blender Python API non disponible")
    print("Ce script doit être lancé avec le Python de Blender:")
    print('"C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe" --background --python test_topo.py')
    sys.exit(1)

# Ajouter le répertoire de l'addon au path Python
addon_path = os.path.dirname(os.path.abspath(__file__))
if addon_path not in sys.path:
    sys.path.append(addon_path)

print(f"📁 Addon path: {addon_path}")

# Fichier de test
TEST_FILE = r"C:\Travail\CLIENTS\OFFICEPro_Configurateur_2025\DOC\3DSources\export_Pcon\ARCO BEIGE PIEDS PYRAMIDAL.glb"

def setup_logging():
    """Configuration du logging détaillé."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    return logging.getLogger("TEST_TOPO")

def clear_scene():
    """Nettoie la scène Blender."""
    print("🧹 Nettoyage de la scène...")
    
    # Supprimer tous les objets
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Supprimer toutes les collections (sauf Master Collection)
    for collection in list(bpy.data.collections):
        if collection != bpy.context.scene.collection:
            bpy.data.collections.remove(collection)
    
    print("✅ Scène nettoyée")

def import_test_file():
    """Importe le fichier de test GLB."""
    print(f"📥 Import du fichier: {TEST_FILE}")
    
    if not os.path.exists(TEST_FILE):
        raise FileNotFoundError(f"Fichier non trouvé: {TEST_FILE}")
    
    # Import GLB
    try:
        bpy.ops.import_scene.gltf(filepath=TEST_FILE)
        print("✅ Import réussi")
        
        # Lister les objets importés
        mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        print(f"📊 {len(mesh_objects)} objets mesh importés:")
        for i, obj in enumerate(mesh_objects, 1):
            mesh = obj.data
            print(f"  {i}. {obj.name}: {len(mesh.vertices)} vertices, {len(mesh.polygons)} faces")
        
        return mesh_objects
        
    except Exception as e:
        raise Exception(f"Erreur lors de l'import: {e}")

def test_topology_functions(mesh_objects):
    """Test des fonctions individuelles de topologie."""
    logger = setup_logging()
    
    try:
        # Import des modules de topologie
        print("📦 Import des modules de topologie...")
        import PROD_topology_analyzer as topo
        print("✅ Module topologie importé")
        
        print("🔧 Test des préférences...")
        prefs = topo.get_topology_preferences()
        print(f"✅ Préférences: {prefs}")
        
        # Test sur le premier mesh
        if not mesh_objects:
            print("❌ Aucun mesh à tester")
            return
        
        test_mesh = mesh_objects[0]
        print(f"\n🧪 Test sur mesh: {test_mesh.name}")
        
        # Test 1: Données de base
        print("📊 Test 1: get_mesh_topology_data")
        start_time = time.time()
        try:
            topo_data = topo.get_mesh_topology_data(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Données récupérées en {elapsed:.3f}s: {topo_data}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 2: Analyse manifold
        print("\n🔍 Test 2: detect_manifold_issues")
        start_time = time.time()
        try:
            manifold_result = topo.detect_manifold_issues(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Manifold analysé en {elapsed:.3f}s")
            print(f"   Problèmes: {manifold_result['has_manifold_issues']}")
            print(f"   Erreurs: {manifold_result['manifold_error_count']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur manifold après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 3: Analyse normales
        print("\n📐 Test 3: analyze_face_normals")
        start_time = time.time()
        try:
            normals_result = topo.analyze_face_normals(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Normales analysées en {elapsed:.3f}s")
            print(f"   Cohérence: {normals_result['normal_consistency']:.1f}%")
            print(f"   Faces inversées: {normals_result['inverted_faces_count']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur normales après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 4: Vertices isolés
        print("\n🔍 Test 4: find_isolated_vertices")
        start_time = time.time()
        try:
            isolated_result = topo.find_isolated_vertices(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Vertices isolés analysés en {elapsed:.3f}s")
            print(f"   Vertices isolés: {isolated_result['isolated_vertices_count']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur vertices isolés après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 5: Vertices dupliqués
        print("\n🔍 Test 5: detect_duplicate_vertices")
        start_time = time.time()
        try:
            duplicates_result = topo.detect_duplicate_vertices(test_mesh, prefs['duplicate_tolerance'])
            elapsed = time.time() - start_time
            print(f"✅ Vertices dupliqués analysés en {elapsed:.3f}s")
            print(f"   Vertices dupliqués: {duplicates_result['duplicate_vertices_count']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur vertices dupliqués après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 6: Vertex colors
        print("\n🎨 Test 6: check_vertex_colors")
        start_time = time.time()
        try:
            colors_result = topo.check_vertex_colors(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Vertex colors analysés en {elapsed:.3f}s")
            print(f"   A des vertex colors: {colors_result['has_vertex_colors']}")
            print(f"   Couches: {colors_result['vertex_color_layers_count']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur vertex colors après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 7: Distribution polygones
        print("\n📊 Test 7: analyze_polygon_distribution")
        start_time = time.time()
        try:
            poly_result = topo.analyze_polygon_distribution(test_mesh)
            elapsed = time.time() - start_time
            print(f"✅ Distribution polygones analysée en {elapsed:.3f}s")
            print(f"   Triangles: {poly_result['triangles_percentage']:.1f}%")
            print(f"   Quads: {poly_result['quads_percentage']:.1f}%")
            print(f"   N-Gons: {poly_result['ngons_percentage']:.1f}%")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur distribution polygones après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        # Test 8: Analyse complète d'un mesh
        print("\n🔬 Test 8: analyze_mesh_topology (complet)")
        start_time = time.time()
        try:
            full_result = topo.analyze_mesh_topology(test_mesh, prefs)
            elapsed = time.time() - start_time
            print(f"✅ Analyse complète en {elapsed:.3f}s")
            print(f"   Succès: {full_result['analysis_success']}")
            if full_result['analysis_error']:
                print(f"   Erreur: {full_result['analysis_error']}")
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur analyse complète après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            return
        
        print("\n✅ Tous les tests individuels réussis!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        traceback.print_exc()

def test_collection_analysis():
    """Test de l'analyse complète de collection."""
    print("\n🗂️ Test de l'analyse de collection...")
    
    try:
        import PROD_topology_analyzer as topo
        
        # Trouver la collection principal (ou créer une)
        if len(bpy.data.collections) == 0:
            collection = bpy.data.collections.new("TestCollection")
            bpy.context.scene.collection.children.link(collection)
        else:
            collection = bpy.context.scene.collection
        
        print(f"📁 Collection: {collection.name}")
        mesh_objects = [obj for obj in collection.all_objects if obj.type == 'MESH']
        print(f"📊 Objets mesh dans collection: {len(mesh_objects)}")
        
        # Test avec progression
        print("🚀 Lancement analyse collection avec progression...")
        start_time = time.time()
        
        try:
            # Créer un context mock simple
            class MockContext:
                def __init__(self):
                    self.window_manager = self
                    
                def progress_begin(self, min_val, max_val):
                    print(f"🔄 Progression initialisée: {min_val}-{max_val}")
                    
                def progress_update(self, progress):
                    print(f"🔄 Progression: {progress:.1%}")
                    
                def progress_end(self):
                    print("🔄 Progression terminée")
            
            mock_context = MockContext()
            
            collection_result = topo.analyze_collection_topology(collection, mock_context)
            elapsed = time.time() - start_time
            
            print(f"✅ Analyse collection terminée en {elapsed:.3f}s")
            print(f"   Objets total: {collection_result['total_objects']}")
            print(f"   Objets analysés: {collection_result['analyzed_objects']}")
            print(f"   Succès: {collection_result['summary']['analysis_success']}")
            
            if collection_result['summary']['analysis_error']:
                print(f"   Erreur: {collection_result['summary']['analysis_error']}")
            
            # Résumé des résultats
            summary = collection_result['summary']
            print(f"\n📈 Résumé:")
            print(f"   Erreurs manifold: {summary['total_manifold_issues']}")
            print(f"   Faces inversées: {summary['total_inverted_faces']}")
            print(f"   Vertices isolés: {summary['total_isolated_vertices']}")
            print(f"   Vertices dupliqués: {summary['total_duplicate_vertices']}")
            print(f"   Objets avec vertex colors: {summary['objects_with_vertex_colors']}")
            print(f"   % Quads moyen: {summary['average_quad_percentage']:.1f}%")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Erreur analyse collection après {elapsed:.3f}s: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur lors du test collection: {e}")
        traceback.print_exc()

def main():
    """Fonction principale du test."""
    print("🚀 DÉBUT TEST TOPOLOGIE")
    print("=" * 50)
    
    try:
        # Étape 1: Nettoyer la scène
        clear_scene()
        
        # Étape 2: Importer le fichier de test
        mesh_objects = import_test_file()
        
        # Étape 3: Tester les fonctions individuelles
        test_topology_functions(mesh_objects)
        
        # Étape 4: Tester l'analyse de collection
        test_collection_analysis()
        
        print("\n" + "=" * 50)
        print("✅ TEST TOPOLOGIE TERMINÉ AVEC SUCCÈS")
        
    except Exception as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()