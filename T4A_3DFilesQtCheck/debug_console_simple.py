# Script de test simple à copier-coller dans la console Blender

# 1. Vérifier les collections
print("=== Collections dans la scène ===")
for coll in bpy.data.collections:
    print(f"'{coll.name}': {len(coll.objects)} objets")

# 2. Chercher la collection GLB_
target_coll = None
for coll in bpy.data.collections:
    if coll.name.startswith("GLB_") and len(coll.objects) > 0:
        target_coll = coll
        break

if target_coll:
    print(f"\n=== Collection trouvée: {target_coll.name} ===")
    
    # 3. Test direct de l'analyse topologique
    try:
        from . import PROD_topology_analyzer
        result = PROD_topology_analyzer.analyze_collection_topology(target_coll, bpy.context)
        print(f"Analyse terminée: {result.get('analyzed_objects', 'N/A')} objets")
        summary = result.get('summary', {})
        print(f"Succès: {summary.get('analysis_success', False)}")
        if 'analysis_error' in summary:
            print(f"Erreur: {summary['analysis_error']}")
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Vérifier les données stockées
    scene = bpy.context.scene
    dims = getattr(scene, 't4a_dimensions', None)
    if dims:
        target_name = target_coll.name.replace("GLB_", "")
        print(f"\n=== Recherche entrée '{target_name}' dans {len(dims)} items ===")
        for item in dims:
            print(f"Item: '{item.name}'")
            if item.name == target_name and hasattr(item, 'topology_result'):
                topo = item.topology_result
                print(f"  Topologie: success={topo.analysis_success}, vertices={topo.total_vertices}")
else:
    print("Aucune collection GLB_ trouvée")