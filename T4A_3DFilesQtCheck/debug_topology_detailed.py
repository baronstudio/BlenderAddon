# Script de test à exécuter dans la console Blender pour tester directement l'analyse topologique

import bpy
from . import PROD_topology_analyzer

def test_topology_analysis_on_current_scene():
    """Teste l'analyse topologique sur la scène actuelle."""
    print("\n=== TEST ANALYSE TOPOLOGIE ===")
    
    # Lister toutes les collections
    print("Collections disponibles:")
    for i, coll in enumerate(bpy.data.collections):
        print(f"  {i}: '{coll.name}' - {len(coll.objects)} objets")
        if len(coll.objects) > 0:
            obj_names = [obj.name for obj in coll.objects[:3]]  # Premiers 3 objets
            print(f"      Objets: {', '.join(obj_names)}{'...' if len(coll.objects) > 3 else ''}")
    
    # Chercher la collection importée (commence par "GLB_")
    target_collection = None
    for coll in bpy.data.collections:
        if coll.name.startswith("GLB_") and len(coll.objects) > 0:
            target_collection = coll
            break
    
    if target_collection is None:
        print("❌ Aucune collection GLB_ trouvée avec des objets")
        return
    
    print(f"\n✅ Collection trouvée: '{target_collection.name}'")
    print(f"   Objets: {len(target_collection.objects)}")
    
    # Test de l'analyse topologique
    try:
        print("\n--- Début de l'analyse topologique ---")
        context = bpy.context
        result = PROD_topology_analyzer.analyze_collection_topology(target_collection, context)
        
        print("✅ Analyse terminée sans erreur")
        print(f"Type du résultat: {type(result)}")
        
        if isinstance(result, dict):
            print("Clés principales:")
            for key in result.keys():
                print(f"  - {key}: {type(result[key])}")
            
            summary = result.get('summary', {})
            print(f"\nRésumé de l'analyse:")
            print(f"  - analysis_success: {summary.get('analysis_success', 'N/A')}")
            print(f"  - analyzed_objects: {result.get('analyzed_objects', 'N/A')}")
            if 'analysis_error' in summary:
                print(f"  - analysis_error: {summary['analysis_error']}")
            
            # Statistiques principales
            if summary.get('analysis_success', False):
                print(f"  - total_manifold_issues: {summary.get('total_manifold_issues', 'N/A')}")
                print(f"  - total_inverted_faces: {summary.get('total_inverted_faces', 'N/A')}")
                print(f"  - total_isolated_vertices: {summary.get('total_isolated_vertices', 'N/A')}")
                print(f"  - total_duplicate_vertices: {summary.get('total_duplicate_vertices', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse topologique: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Vérifier si les données sont stockées dans les propriétés de scène
    print("\n--- Vérification stockage des données ---")
    scene = bpy.context.scene
    dims = getattr(scene, 't4a_dimensions', None)
    
    if dims is None:
        print("❌ Propriétés t4a_dimensions non trouvées")
        return
    
    print(f"✅ t4a_dimensions trouvées: {len(dims)} entrées")
    
    # Chercher l'entrée correspondant à notre fichier
    target_filename = target_collection.name.replace("GLB_", "")
    print(f"Recherche de l'entrée pour: '{target_filename}'")
    
    found_item = None
    for item in dims:
        print(f"  Entrée trouvée: '{item.name}'")
        if item.name == target_filename:
            found_item = item
            break
    
    if found_item is None:
        print(f"❌ Aucune entrée trouvée pour '{target_filename}'")
        return
    
    print(f"✅ Entrée trouvée: '{found_item.name}'")
    
    # Vérifier les données topologiques
    if hasattr(found_item, 'topology_result'):
        topo_res = found_item.topology_result
        if topo_res:
            print("✅ topology_result existe")
            print(f"  - analysis_success: {topo_res.analysis_success}")
            if topo_res.analysis_success:
                print(f"  - total_vertices: {topo_res.total_vertices}")
                print(f"  - total_polygons: {topo_res.total_polygons}")
                print(f"  - has_manifold_issues: {topo_res.has_manifold_issues}")
            else:
                print(f"  - analysis_error: '{topo_res.analysis_error}'")
        else:
            print("❌ topology_result est None/vide")
    else:
        print("❌ topology_result n'existe pas")

if __name__ == "__main__":
    test_topology_analysis_on_current_scene()