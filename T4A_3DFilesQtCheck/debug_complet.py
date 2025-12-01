# DEBUG COMPLET - À copier-coller dans la console Blender

print("=== DEBUG COMPLET TOPOLOGIE ===")

# 1. Vérifier les imports
try:
    from . import PROD_topology_analyzer
    print("✅ PROD_topology_analyzer importé")
except Exception as e:
    print(f"❌ Erreur import PROD_topology_analyzer: {e}")

# 2. Vérifier la scène
scene = bpy.context.scene
dims = getattr(scene, 't4a_dimensions', None)
print(f"Scène: {scene.name}")
print(f"t4a_dimensions: {'✅' if dims else '❌'}")

if dims:
    print(f"Nombre d'entrées dims: {len(dims)}")
    for i, item in enumerate(dims):
        print(f"  {i}: '{item.name}'")
        # Vérifier les propriétés topologie
        if hasattr(item, 'topology_result'):
            topo = item.topology_result
            print(f"    topology_result: ✅")
            print(f"    analysis_success: {topo.analysis_success}")
            if topo.analysis_success:
                print(f"    vertices: {topo.total_vertices}, polygons: {topo.total_polygons}")
            else:
                print(f"    error: '{topo.analysis_error}'")
        else:
            print(f"    topology_result: ❌")

# 3. Vérifier les collections GLB
print("\n=== COLLECTIONS GLB ===")
glb_collections = [c for c in bpy.data.collections if c.name.startswith("GLB_")]
if glb_collections:
    for coll in glb_collections:
        print(f"Collection: '{coll.name}' - {len(coll.objects)} objets")
        
        # Test direct d'analyse si possible
        if len(coll.objects) > 0:
            print(f"  Test analyse directe...")
            try:
                result = PROD_topology_analyzer.analyze_collection_topology(coll, bpy.context)
                summary = result.get('summary', {})
                print(f"  ✅ Analyse OK: success={summary.get('analysis_success', False)}")
                if 'analysis_error' in summary:
                    print(f"  ❌ Erreur: {summary['analysis_error']}")
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                import traceback
                traceback.print_exc()
else:
    print("Aucune collection GLB trouvée")

# 4. Test UI refresh
print("\n=== TEST RAFRAÎCHISSEMENT UI ===")
try:
    refreshed = 0
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
            refreshed += 1
    print(f"✅ {refreshed} areas VIEW_3D rafraîchies")
except Exception as e:
    print(f"❌ Erreur rafraîchissement: {e}")

print("\n=== FIN DEBUG ===")